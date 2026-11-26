"""F2 - Retrouve les rubriques utiles dans un texte, quels que soient les titres.

Rubrics obligatoires : indications, contre-indications, posologie, interactions.
Les effets indésirables sont facultatifs mais extraits lorsqu'ils sont présents.

Un titre est reconnu par trois signaux complémentaires :
  1. un mot-clé (FR / EN) en début de ligne ;
  2. un numéro de rubrique RCP (4.1, 4.2, 4.3, 4.5, 4.8) ;
  3. une formulation en question des notices patient.
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

MOTIFS: dict[str, tuple[str, ...]] = {
    "indications": (
        r"(?:therapeutic )?indications?\b",
        r"qu['’]est[- ]?ce\b.+\bdans quel[s]? cas\b",
        r"indications?\s+and\s+usage\b",
        r"uses(?:\s+and\s+usage)?\s*$",
        r"what is\b.+\bused for\b",
    ),
    "contre_indications": (
        r"contre[\s-]*indications?\b",
        r"\bcontraindications?\b",
        r"quelles sont les informations\b.+\bavant de (?:prendre|utiliser)\b",
        r"do not use(?:\s+if)?\s*$",
        r"when (?:not|must not) (?:use|take)\b",
        r"warnings?\s*$",
    ),
    "posologie": (
        r"posologie\b",
        r"posology\b",
        r"mode d['’]emploi\b",
        r"comment (?:prendre|utiliser)\b",
        r"dosage and administration\b",
        r"how to (?:take|use)\b",
        r"directions?(?:\s+for use)?\s*$",
    ),
    "interactions": (
        r"interactions?\b",
        r"interaction with\b",
        r"interactions?\s+m[ée]dicamenteuses?\b",
        r"associations?\s+m[ée]dicamenteuses?\b",
        r"autres m[ée]dicaments et\b",
        r"drug interactions?\b",
    ),
    "effets_indesirables": (
        r"effets?\s+ind[ée]sirables?\b",
        r"side effects?\b",
        r"adverse reactions?\b",
    ),
}

NUMEROS_RCP = {
    "4.1": "indications",
    "4.2": "posologie",
    "4.3": "contre_indications",
    "4.5": "interactions",
    "4.8": "effets_indesirables",
}

RE_NUMERO = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,2})\s*[\.\)\-:]?\s*(.*)$")
RE_QUESTION = re.compile(r"^(qu['’]est|quelles sont|comment|quels sont|what is|how to)")
LONGUEUR_MIN = 80


def normaliser(texte: str) -> str:
    t = unicodedata.normalize("NFD", str(texte or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("’", "'").replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip().lower()


def titre_vers_rubrique(ligne: str) -> tuple[str | None, str]:
    """Renvoie (rubrique, méthode) pour une ligne qui semble être un titre."""
    brut = str(ligne or "").strip()
    if not brut or len(brut) > 240:
        return None, ""
    s = normaliser(brut)
    m = RE_NUMERO.match(s)
    numero, corps = (m.group(1), m.group(2)) if m else ("", s)
    if not corps:
        return None, ""
    mots = corps.split()
    question = bool(RE_QUESTION.match(corps))
    if len(corps) > (220 if question else 130):
        return None, ""
    if len(mots) > (40 if question else 18):
        return None, ""  # phrase de corps de texte, pas un titre
    for rubrique, motifs in MOTIFS.items():
        for motif in motifs:
            if re.match(motif, corps):
                return rubrique, "numero+titre" if numero else "titre"
    if numero in NUMEROS_RCP:
        return NUMEROS_RCP[numero], "numero"
    return None, ""


def offsets_lignes(texte: str) -> list[int]:
    resultat, pos = [], 0
    for ligne in texte.split("\n"):
        resultat.append(pos)
        pos += len(ligne) + 1
    return resultat


def extraire_rubriques(texte: str) -> dict[str, dict]:
    """Découpe le texte en rubriques. Chaque passage est le texte d'origine intact."""
    lignes = texte.split("\n")
    off = offsets_lignes(texte)
    candidats: list[dict] = []
    for i, ligne in enumerate(lignes):
        rubrique, methode = titre_vers_rubrique(ligne)
        if rubrique:
            numero = RE_NUMERO.match(normaliser(ligne))
            numero = numero.group(1) if numero else ""
            corps = normaliser(ligne)
            if numero:
                corps = RE_NUMERO.match(corps).group(2)
            qualite = 3 if numero in NUMEROS_RCP else (2 if numero else 1)
            candidats.append({
                "rubrique": rubrique,
                "methode": methode,
                "titre": ligne.strip(),
                "debut": off[i],
                "numero": numero,
                "_qualite": qualite,
                "_question": bool(RE_QUESTION.match(corps)),
            })

    # Portée de chaque titre = distance jusqu'au titre suivant.
    for c in candidats:
        suivant = min(
            (o for o in (x["debut"] for x in candidats) if o > c["debut"]),
            default=len(texte),
        )
        c["_portee"] = suivant - c["debut"]

    max_portee: dict[str, int] = {}
    for c in candidats:
        r = c["rubrique"]
        max_portee[r] = max(max_portee.get(r, 0), c["_portee"])

    # Un vrai titre RCP (4.1, 4.2, 4.3, 4.5, 4.8) est toujours prioritaire,
    # même s'il est suivi immédiatement par un sous-titre : ce n'est PAS un
    # sommaire. Les autres titres trop courts sont écartés comme sommaire.
    meilleurs: dict[str, dict] = {}
    for c in candidats:
        rcp = c["numero"] in NUMEROS_RCP
        court = (
            c["_portee"] < 2 * len(c["titre"]) + 20
            or c["_portee"] < 0.25 * max_portee[r]
        )
        if rcp:
            c["_rang"] = 2
        elif not court:
            c["_rang"] = 1 if c["numero"] else 0
        else:
            c["_rang"] = -1
        actuel = meilleurs.get(c["rubrique"])
        cle = (c["_rang"], c["_portee"])
        cle_actuelle = (
            (actuel["_rang"], actuel["_portee"]) if actuel else (-2, -1)
        )
        if cle > cle_actuelle:
            meilleurs[c["rubrique"]] = c

    bornes = sorted(c["debut"] for c in meilleurs.values())
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
        fin = min((b for b in bornes if b > c["debut"]), default=len(texte))
        passage = texte[c["debut"]:fin].strip()
        # Une vraie rubrique RCP peut être courte (ex. « Traitement des
        # douleurs modérées à sévères. ») : on ne la rejette pas comme sommaire.
        seuil = len(c["titre"]) + 5 if c["numero"] in NUMEROS_RCP else LONGUEUR_MIN
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
