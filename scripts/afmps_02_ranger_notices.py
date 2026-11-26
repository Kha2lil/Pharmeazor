"""AFMPS (Belgique) : range les NOTICES (notice patient) PDF téléchargées à la main dans un dossier par DCI
de la liste, puis les enregistre dans documents.csv (source « afmps_notice »).
Classement sur la rubrique 6 (« La substance active est ... »), avec repli sur le titre de la notice.
Substance unique de la liste, ou une des 3 associations de la liste. Rejouable, sans doublons."""
import re
import shutil
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import pymupdf as fitz

from src.collecte.provenance import register

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DOSSIER_RCP = ROOT / "data" / "raw" / "afmps"
DOSSIER = DOSSIER_RCP / "afmps_notice"
VRAC = DOSSIER / "_vrac"
A_VERIFIER = DOSSIER / "_a_verifier"
BASE_URL = "https://medicinesdatabase.be"
SOURCE = "afmps_notice"

COMBOS = {
    "PARACETAMOL + CODEINE": ["PARACETAMOL", "CODEINE"],
    "AMOXICILLINE + ACIDE CLAVULANIQUE": ["AMOXICILLINE", "CLAVULAN"],
    "COTRIMOXAZOLE (SULFAMETHOXAZOLE + TRIMETHOPRIME)": ["SULFAMETHOXAZOLE", "TRIMETHOPRIM"],
}
RACINES = {"ACIDE ACETYLSALICYLIQUE": "ACETYLSALICYLIQUE"}


def norm(s):
    s = unicodedata.normalize("NFD", str(s).replace("’", "'"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", norm(s).lower()).strip("_")


def lire(pdf):
    """Retourne (début du titre, texte des substances actives, pluriel ?, type, n° AMM)."""
    with fitz.open(pdf) as doc:
        brut = " ".join(page.get_text() for page in doc)
    t = norm(re.sub(r"\s+", " ", brut))
    amm = re.search(r"\bBE\d{6,7}\b", t)
    if "RESUME DES CARACTERISTIQUES DU PRODUIT" in t[:800]:
        type_doc = "RCP"
    elif any(k in t[:2500] for k in ("NOTICE", "INFORMATION DE L'UTILISATEUR", "LISEZ ATTENTIVEMENT")):
        type_doc = "NOTICE"
    elif "BIJSLUITER" in t[:2500]:
        type_doc = "NEERLANDAIS"
    else:
        type_doc = "?"

    motif = re.compile(r"(LA SUBSTANCE ACTIVE|LES SUBSTANCES ACTIVES|LE PRINCIPE ACTIF|LES PRINCIPES ACTIFS)"
                       r"\s*(?:EST|SONT)?\s*:?(.{0,400}?)"
                       r"(?:LES AUTRES (?:COMPOSANTS|INGREDIENTS)|L'AUTRE COMPOSANT|AUTRES COMPOSANTS|EXCIPIENT)")
    debut6 = t.rfind("QUE CONTIENT")             # début de la rubrique 6 (« Que contient X ? »)
    zone = t[debut6:] if debut6 >= 0 else t
    actif, pluriel = "", False
    for m in motif.finditer(zone):
        texte = m.group(2).strip()
        if (len(texte) < 4 or texte.startswith((",", "OU ", "A L'UN", "A UN DES", "AUX "))
                or "L'UN DES" in texte[-25:] or "PREPARATIONS CONTENANT" in texte):
            continue                              # formule de la rubrique 2 (« ... ou à l'un des ... »)
        actif = texte
        pluriel = m.group(1) in ("LES SUBSTANCES ACTIVES", "LES PRINCIPES ACTIFS")
        break
    return t[:250], actif, pluriel, type_doc, (amm.group(0) if amm else "")


liste = pd.read_excel(ROOT / "data" / "reference" / "liste_40_medicaments.xlsx", sheet_name="Médicaments")
DCIS = list(liste["DCI (nom de la substance)"])
SLUGS = {slug(d): d for d in DCIS}
SIMPLES = {d: RACINES.get(norm(d), norm(d)) for d in DCIS if norm(d) not in COMBOS}
ASSOCS = {d: COMBOS[norm(d)] for d in DCIS if norm(d) in COMBOS}


def classer(actif, pluriel, type_doc, debut=""):
    """Retourne (dci, raison). dci = None si la notice est à vérifier."""
    if type_doc == "RCP":
        return None, "c'est un RCP (à ranger avec afmps_01)"
    if type_doc == "NEERLANDAIS":
        return None, "notice en néerlandais"
    if type_doc != "NOTICE":
        return None, "type de document non reconnu"

    if not actif:
        # repli : le titre de la notice donne le nom du produit
        if "+" in debut or re.search(r"\bCO-", debut):
            return None, "rubrique 6 introuvable et titre d'association"
        if any(all(x in debut for x in r) for r in ASSOCS.values()):
            return None, "rubrique 6 introuvable et titre d'association de la liste"
        trouvees = [d for d, r in SIMPLES.items() if r in debut]
        if len(trouvees) == 1:
            r = SIMPLES[trouvees[0]]
            # « / » collé au nom de la DCI = association ; « INJECTABLE/POUR » = simple forme
            if re.search(rf"{r}\w*\s*/\s*[A-Z]{{4,}}|[A-Z]{{4,}}\s*/\s*\w*{r}", debut):
                return None, "titre : association probable (« / » à côté de la DCI)"
            return trouvees[0], ""
        return None, "rubrique 6 introuvable, titre sans DCI unique"

    touches = [d for d, r in ASSOCS.items() if all(x in actif for x in r)]
    if touches:
        return (touches[0], "") if len(touches) == 1 else (None, "association ambiguë")
    if pluriel:
        return None, "plusieurs substances actives non listées"

    trouvees = [d for d, r in SIMPLES.items() if r in actif]
    if not trouvees:
        return None, "aucune DCI de la liste"
    if len(trouvees) > 1:
        return None, "plusieurs DCI de la liste : " + ", ".join(trouvees)
    return trouvees[0], ""


VRAC.mkdir(parents=True, exist_ok=True)
A_VERIFIER.mkdir(parents=True, exist_ok=True)

ranges = refuses = nouveaux = doublons = 0

# 1) fichiers en vrac : classement puis déplacement
for f in sorted(VRAC.glob("*.pdf")):
    try:
        debut, actif, pluriel, type_doc, amm = lire(f)
        dci, raison = classer(actif, pluriel, type_doc, debut)
    except Exception as e:
        print(f"ERR {f.name} : {e}")
        continue
    if dci is None:
        shutil.move(str(f), str(A_VERIFIER / f.name))
        print(f"?   {f.name} -> _a_verifier ({raison}) | {debut[:70]} | actif={actif[:80]!r}")
        refuses += 1
        continue
    dest = DOSSIER / slug(dci) / f.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"=   {f.name} existe déjà dans {slug(dci)}, ignoré")
        continue
    shutil.move(str(f), str(dest))
    ranges += 1
    print(f"->  {f.name} -> {slug(dci)}")

# 2) enregistrement de toutes les notices rangées (rejouable)
for dossier in sorted(p for p in DOSSIER.iterdir() if p.is_dir() and not p.name.startswith("_")):
    dci = SLUGS.get(dossier.name)
    if dci is None:
        print(f"Dossier inconnu (pas dans la liste) : {dossier.name}")
        continue
    for pdf in sorted(dossier.glob("*.pdf")):
        try:
            amm = lire(pdf)[4]
        except Exception:
            amm = ""
        url = BASE_URL + (f"#AMM={amm}" if amm else "")
        if register(dci, SOURCE, url, "fr", pdf):
            nouveaux += 1
            print(f"OK  {dci} | {pdf.name}")
        else:
            doublons += 1

print(f"\nRangés : {ranges} | enregistrés : {nouveaux} | déjà enregistrés/doublons : {doublons} | à vérifier : {refuses}")

# 3) DCI sans notice, et DCI qui ont un RCP mais pas de notice
sans_notice = [d for d in DCIS if not list((DOSSIER / slug(d)).glob("*.pdf"))]
rcp_sans_notice = [d for d in sans_notice if list((DOSSIER_RCP / slug(d)).glob("*.pdf"))]
print(f"\nDCI sans aucune notice ({len(sans_notice)}/{len(DCIS)}) :")
for d in sans_notice:
    print(" -", d, "(RCP déjà collecté)" if d in rcp_sans_notice else "")