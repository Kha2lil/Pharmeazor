"""F2 - Retrouve les rubriques utiles dans un texte, quels que soient les titres.

Rubrics obligatoires : indications, contre-indications, posologie, interactions.
Les effets indésirables sont facultatifs mais extraits lorsqu'ils sont présents.

Un titre est reconnu par trois signaux complémentaires :
  1. un mot-clé (FR / EN) en début de ligne, du plus précis au plus général ;
  2. un numéro de rubrique RCP (4.1, 4.2, 4.3, 4.5, 4.8) ;
  3. une formulation en question des notices patient.

Points de vigilance intégrés (mesure sur 20 documents, 27/11/2026) :
  - `WARNINGS` n'est PAS une contre-indication ;
  - pour les notices patient, la contre-indication est le bloc
    « Ne prenez jamais… » / « N'utilisez jamais… », pas la section entière
    « Quelles sont les informations… avant de prendre… » ;
  - un numéro seul sur une ligne est recollé au titre de la ligne suivante ;
  - un titre répété (sommaire) est remplacé par sa dernière occurrence ;
  - un numéro RCP exige un séparateur réel (`4.3%` n'est pas la rubrique 4.3) ;
  - la fin d'une rubrique s'arrête à un titre de niveau égal ou supérieur,
    pas à n'importe quel sous-titre.

Les phrases d'origine sont conservées telles quelles dans le passage renvoyé.
"""
from __future__ import annotations

import re
import unicodedata

RUBRIQUES = (
    "indications",
    "contre_indications",
    "posologie",
    "interactions",
    "effets_indesirables",
)
OBLIGATOIRES = RUBRIQUES[:4]

# Ordre = priorité : le premier motif qui correspond donne la meilleure
# spécificité. Les motifs généraux viennent donc toujours en dernier.
MOTIFS: dict[str, tuple[str, ...]] = {
    "indications": (
        r"indications?\s+and\s+usage\b",
        r"indications?\s+th[ée]rapeutiques?\b",
        r"qu['’]est[- ]?ce\b.+\bdans quel[s]? cas\b",
        r"what is\b.+\bused for\b",
        r"(?:therapeutic )?indications?\b",
        r"uses(?:\s+and\s+usage)?\s*$",
    ),
    "contre_indications": (
        r"ne prenez jamais\b",
        r"n['’]utilisez jamais\b",
        r"ne doit pas [êe]tre administr[ée]\b",
        r"n['’]utilisez pas\b",
        r"contre[\s-]*indications?\b",
        r"\bcontraindications?\b",
        r"do not (?:use|take)\b",
        r"when (?:not|must not) (?:use|take)\b",
    ),
    "posologie": (
        r"dosage and administration\b",
        r"posologie et mode d['’]emploi\b",
        r"posologie,? mode et/ou voie\(s\) d['’]administration\b",
        r"comment (?:prendre|utiliser)\b",
        r"posologie\b",
        r"posology\b",
        r"mode d['’]emploi\b",
        r"how to (?:take|use)\b",
        r"directions?(?:\s+for use)?\s*$",
    ),
    "interactions": (
        r"interactions?\s+avec\s+(?:d['’]autres\s+)?m[ée]dicaments?\b",
        r"autres m[ée]dicaments et\b",
        r"drug interactions?\b",
        r"interactions?\s+m[ée]dicamenteuses?\b",
        r"associations?\s+m[ée]dicamenteuses?\b",
        r"interactions?\s+with\b",
        r"interactions?\b",
    ),
    "effets_indesirables": (
        r"effets?\s+ind[ée]sirables?\b",
        r"quels sont les effets\b",
        r"side effects?\b",
        r"adverse reactions?\b",
    ),
}

# Titres structurants qui ne sont pas des rubriques mais doivent pouvoir
# terminer un passage (ex. : « Ne prenez jamais… » s'arrête aux avertissements).
STOP_MOTIFS: tuple[str, ...] = (
    r"avertissements? et pr[ée]cautions?\b",
    r"pr[ée]cautions? d['’]emploi\b",
    r"mises en garde\b",
    r"grossesse(?:,? allaitement et fertilit[ée])?\b",
    r"allaitement\b",
    r"conduite de v[ée]hicules\b",
    r"avec des aliments et des boissons\b",
    r"utilisation chez les enfants\b",
    r"suivi m[ée]dical\b",
    r"warnings? and pr[ée]cautions\b",
    r"use in specific populations\b",
    r"overdosage\b",
    r"patient counseling information\b",
)

NUMEROS_RCP = {
    "4.1": "indications",
    "4.2": "posologie",
    "4.3": "contre_indications",
    "4.5": "interactions",
    "4.8": "effets_indesirables",
}

# Un numéro doit être suivi d'un séparateur ou d'un espace : `4.3%` ne
# correspond donc pas à la rubrique 4.3.
RE_NUMERO = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,2})(?:[\.\)\-:]\s*|\s+)(.*)$")
RE_NUMERO_SEUL = re.compile(r"^\d{1,2}(?:\.\d{1,2}){0,2}\s*[\.\)\-:]?$")
RE_QUESTION = re.compile(r"^(qu['’]est|quelles sont|comment|quels sont|what is|how to)")
LONGUEUR_MIN = 80


def normaliser(texte: str) -> str:
    t = unicodedata.normalize("NFD", str(texte or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("’", "'").replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip().lower()


def classer_ligne(ligne: str) -> tuple[str | None, str, str, int]:
    """Renvoie (rubrique, méthode, numéro, spécificité).

    La spécificité est d'autant plus grande que le motif est précis. Le
    pseudo-rubrique `__stop__` désigne un titre structurant sans rubrique.
    """
    brut = str(ligne or "").strip()
    if not brut or len(brut) > 240:
        return None, "", "", 0
    s = normaliser(brut)
    m = RE_NUMERO.match(s)
    numero, corps = (m.group(1), m.group(2)) if m else ("", s)
    if not corps or corps[:1] in "%0123456789":
        return None, "", "", 0
    mots = corps.split()
    question = bool(RE_QUESTION.match(corps))
    if len(corps) > (220 if question else 130):
        return None, "", "", 0
    if len(mots) > (40 if question else 18):
        return None, "", "", 0  # phrase de corps de texte, pas un titre

    methode = "numero+titre" if numero else "titre"
    # « N'utilisez pas ce médicament après la date de péremption » parle de
    # conservation, pas d'une contre-indication.
    if re.search(r"(?:apr[eè]s la )?date de p[ée]reemption", corps):
        return None, "", "", 0
    # Une référence croisée (« CONTRAINDICATIONS]. » ou « Voir aussi la
    # rubrique « Ne prenez jamais… » ») n'est pas un titre.
    if corps.endswith("].") or corps.endswith("].)"):
        return None, "", "", 0
    if re.match(r"(?:voir|cf)\b[\s,.:]", corps):
        return None, "", "", 0

    for rubrique, motifs in MOTIFS.items():
        for i, motif in enumerate(motifs):
            # Seul « … ne doit pas être administré » peut être précédé du
            # nom du médicament (néfopam). Les autres blocs sont en début
            # de ligne : une recherche anywhere attraperait les renvois.
            chercher = re.search if motif.startswith("ne doit pas") else re.match
            if not chercher(motif, corps):
                continue
            # « Do not use … » n'est un titre que s'il est court ou suivi
            # de « : ». Sinon c'est une phrase du corps du texte.
            if motif.startswith("do not ") and not (
                corps.endswith(":") or len(corps) <= 14
            ):
                continue
            # Une phrase du corps commençant par « effets indésirables »
            # n'est pas le titre de la rubrique.
            if rubrique == "effets_indesirables" and len(corps) > 80:
                continue
            return rubrique, methode, numero, len(motifs) - i
    for motif in STOP_MOTIFS:
        if re.match(motif, corps):
            return "__stop__", "stop", numero, 0
    if numero in NUMEROS_RCP:
        # `4.1 ND` (tableau) n'est pas la rubrique 4.1.
        if len(corps) >= 12 and len(mots) >= 2:
            return NUMEROS_RCP[numero], "numero", numero, 0
    return None, "", "", 0


def titre_vers_rubrique(ligne: str) -> tuple[str | None, str]:
    """Renvoie (rubrique, méthode) pour une ligne qui semble être un titre."""
    rubrique, methode, _, _ = classer_ligne(ligne)
    if rubrique == "__stop__":
        return None, ""
    return rubrique, methode


def offsets_lignes(texte: str) -> list[int]:
    resultat, pos = [], 0
    for ligne in texte.split("\n"):
        resultat.append(pos)
        pos += len(ligne) + 1
    return resultat


def _unites(lignes: list[str], off: list[int]) -> list[tuple[str, int, str]]:
    """Recolle un numéro isolé au titre de la ligne suivante.

    Certains PDF coupent `4.1-` et `Indications thérapeutiques` en deux
    lignes. On garde la position de la première ligne pour ne pas perdre le
    titre numéroté au profit d'un en-tête de tableau plus bas.
    """
    unites: list[tuple[str, int, str]] = []
    i = 0
    while i < len(lignes):
        brut = lignes[i].strip()
        if RE_NUMERO_SEUL.match(brut) and i + 1 < len(lignes):
            suivant = lignes[i + 1].strip()
            if suivant and not RE_NUMERO_SEUL.match(suivant):
                titre = f"{brut} {suivant}"
                unites.append((titre, off[i], titre))
                i += 2
                continue
        unites.append((lignes[i], off[i], lignes[i].strip()))
        i += 1
    return unites


def _niveau(numero: str) -> int:
    """2 = titre de section majeur, 1 = sous-titre."""
    if numero in NUMEROS_RCP or re.fullmatch(r"\d{1,2}", numero):
        return 2
    return 1


def _rang_base(c: dict) -> int:
    if c["numero"] in NUMEROS_RCP:
        return 2
    return 1 if c["numero"] else 0


def extraire_rubriques(texte: str) -> dict[str, dict]:
    """Découpe le texte en rubriques. Chaque passage est le texte d'origine intact."""
    lignes = texte.split("\n")
    off = offsets_lignes(texte)
    candidats: list[dict] = []
    for contenu, debut, titre in _unites(lignes, off):
        rubrique, methode, numero, specificite = classer_ligne(contenu)
        if not rubrique:
            continue
        candidats.append({
            "rubrique": rubrique,
            "methode": methode,
            "titre": titre,
            "debut": debut,
            "numero": numero,
            "niveau": _niveau(numero),
            "specificite": specificite,
            "_portee": 0,
        })

    deuits = sorted(c["debut"] for c in candidats)
    for c in candidats:
        c["_portee"] = min(
            (d for d in deuits if d > c["debut"]), default=len(texte)
        ) - c["debut"]

    # Un titre répété est un sommaire : on ne garde que sa dernière occurrence,
    # qui est la vraie section. Le numéro est ignoré dans la clé car les
    # sommaires écrivent souvent « 7 DRUG INTERACTIONS » et le corps le même
    # titre sans numéro (ou inversement).
    par_titre: dict[str, dict] = {}
    for c in candidats:
        cle_titre = normaliser(
            re.sub(r"^\d{1,2}(?:\.\d{1,2}){0,2}\s*[\.\)\-:]?\s*", "", c["titre"])
        )
        actuel = par_titre.get(cle_titre)
        # En cas de doublon, on garde le titre le plus structuré (numéroté),
        # puis la dernière occurrence — la vraie section après le sommaire.
        if actuel is None or (_rang_base(c), c["debut"]) >= (
            _rang_base(actuel), actuel["debut"]
        ):
            par_titre[cle_titre] = c
    candidats = list(par_titre.values())

    par_debut = {c["debut"]: c for c in candidats}
    bornes = sorted(par_debut)

    # Le « Medication Guide » répète le RCP en fin de document : ses titres
    # ne doivent pas couper une section de la notice précédente.
    guide_debut = len(texte)
    for i, ligne in enumerate(lignes):
        if re.fullmatch(r"\s*medication guide\s*", normaliser(ligne)):
            guide_debut = off[i]
            break

    meilleurs: dict[str, dict] = {}
    for c in candidats:
        r = c["rubrique"]
        if r == "__stop__":
            continue
        court = not c["numero"] and c["_portee"] < 2 * len(c["titre"]) + 20
        if court:
            rang = -1
        else:
            rang = _rang_base(c)
        c["_rang"] = rang
        cle = (rang, c["specificite"], c["_portee"])
        actuel = meilleurs.get(r)
        cle_actuelle = (
            (actuel["_rang"], actuel["specificite"], actuel["_portee"])
            if actuel else (-2, -1, -1)
        )
        if cle > cle_actuelle:
            meilleurs[r] = c

    resultat: dict[str, dict] = {}
    for rubrique in RUBRIQUES:
        c = meilleurs.get(rubrique)
        if c is None:
            resultat[rubrique] = {
                "trouve": False, "raison": "titre introuvable",
                "titre": "", "methode": "", "debut": None, "fin": None,
                "passage": "",
            }
            continue

        # La fin est le premier titre de niveau >= au nôtre. Un sous-titre
        # de la même rubrique ne coupe pas un passage trop court (ex. le
        # « Do not use » qui suit « Contraindications » dans les Drug Facts).
        fin = len(texte)
        for b in bornes:
            if b <= c["debut"]:
                continue
            if c["debut"] < guide_debut <= b:
                continue
            suivant = par_debut[b]
            if suivant["niveau"] < c["niveau"]:
                continue
            if (
                suivant["rubrique"] == rubrique
                and b - c["debut"] < LONGUEUR_MIN
            ):
                continue
            fin = b
            break

        passage = texte[c["debut"]:fin].strip()
        seuil = max(10, len(c["titre"]))
        if len(passage) < seuil:
            resultat[rubrique] = {
                "trouve": False, "raison": "passage trop court (sommaire probable)",
                "titre": c["titre"], "methode": c["methode"],
                "debut": None, "fin": None, "passage": "",
            }
            continue
        resultat[rubrique] = {
            "trouve": True, "raison": "",
            "titre": c["titre"], "methode": c["methode"],
            "debut": c["debut"], "fin": fin, "passage": passage,
        }
    return resultat
