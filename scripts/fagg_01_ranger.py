"""FAGG/AFMPS (Belgique) : range les RCP PDF téléchargés à la main dans un dossier par DCI de la liste,
puis les enregistre dans documents.csv. Classement sur la dénomination (rubrique 1) et la composition
(rubrique 2). Seules les fiches à substance unique de la liste (et les 3 associations de la liste) sont gardées.
Rejouable, sans doublons."""
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
DOSSIER = ROOT / "data" / "raw" / "afmps"
VRAC = DOSSIER / "_vrac"
A_VERIFIER = DOSSIER / "_a_verifier"
BASE_URL = "https://medicinesdatabase.be"
SOURCE = "afmps"

# associations présentes dans la liste : toutes les racines doivent apparaître
COMBOS = {
    "PARACETAMOL + CODEINE": ["PARACETAMOL", "CODEINE"],
    "AMOXICILLINE + ACIDE CLAVULANIQUE": ["AMOXICILLINE", "CLAVULAN"],
    "COTRIMOXAZOLE (SULFAMETHOXAZOLE + TRIMETHOPRIME)": ["SULFAMETHOXAZOLE", "TRIMETHOPRIM"],
}
# racines particulières (le RCP écrit parfois autrement que la liste)
RACINES = {"ACIDE ACETYLSALICYLIQUE": "ACETYLSALICYLIQUE"}

# mots de sel/forme qui suivent « mg de » sans être une autre substance
NEUTRES = {
    "CHLORHYDRATE", "PHOSPHATE", "SULFATE", "SULFATES", "MALEATE", "FUMARATE", "TARTRATE", "BESILATE",
    "MESILATE", "SUCCINATE", "ACETATE", "CITRATE", "SODIUM", "POTASSIUM", "CALCIUM", "BROMHYDRATE",
    "HYDROCHLORURE", "DE", "D", "SEL",
    "GEL", "SOLUTION", "SUSPENSION", "SIROP", "CREME", "POMMADE", "EMPLATRE", "COMPRIME", "POUDRE",
    "LOTION", "PATCH", "GELULE", "AMPOULE", "SERINGUE", "FLACON", "DOSE", "SODIQUE", "POTASSIQUE",
    "DIETHYLAMINE", "EPOLAMINE", "MONOHYDRATE", "HEMIHYDRATE", "TRIHYDRATE",
    "SOLVANT", "EAU", "CHLORURE", "GLUCOSE", "ANHYDRE", "DIHYDRATE", "PENTAHYDRATE", "HEPTAHYDRATE", "SESQUIHYDRATE", "HYDRATE", "TOSILATE", "TOSYLATE", "ERBUMINE", "ARGININE", "TERT-BUTYLAMINE", "HEMIFUMARATE", "NITRATE",
    "BROMURE", "LACTATE", "MAGNESIUM", "OXALATE", "MALATE", "GLUCONATE", "DIPROPIONATE", "VALERATE",
}


def norm(s):
    s = unicodedata.normalize("NFD", str(s).replace("’", "'"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", norm(s).lower()).strip("_")


def lire(pdf):
    """Retourne (dénomination, composition, n° AMM) en majuscules sans accents."""
    with fitz.open(pdf) as doc:
        brut = " ".join(page.get_text() for page in doc)
    t = norm(re.sub(r"\s+", " ", brut))          # espaces et sauts de ligne unifiés
    amm = re.search(r"\bBE\d{6,7}\b", t)
    i2 = re.search(r"2\s*\.?\s*COMPOSITION QUALITATIVE", t)
    if not i2:
        return "", "", (amm.group(0) if amm else "")
    avant, apres = t[:i2.start()], t[i2.end():]
    fin = re.search(r"3\s*\.?\s*FORME PHARMACEUTIQUE|FORME PHARMACEUTIQUE", apres)
    compo = apres[:fin.start()] if fin else apres[:1500]
    compo = compo.split("EXCIPIENT")[0]          # on ne compte pas les excipients
    m1 = re.search(r"1\s*\.?\s*(?:D\W{0,3}E?\W{0,3}NOMINATION|NOM) DU M\W{0,3}E?\W{0,3}DICAMENT(.*)$", avant)
    denom = m1.group(1) if m1 else avant[-300:]
    return denom, compo, (amm.group(0) if amm else "")


def mots_substances(compo):
    """Mots qui suivent « mg de/d' » ; même radical (7 lettres) = même substance."""
    mots = re.findall(r"(?:MG|MCG|G|UI|ML)\s+(?:D'|DE |DU |DES )\s*([A-Z0-9-]+)", compo)
    vus = {}
    for m in mots:
        if m in NEUTRES or m.isdigit():
            continue
        vus.setdefault(m[:7], m)
    return list(vus.values())


def nb_substances(compo):
    return len(mots_substances(compo))


liste = pd.read_excel(ROOT / "data" / "reference" / "liste_40_medicaments.xlsx", sheet_name="Médicaments")
DCIS = list(liste["DCI (nom de la substance)"])
SLUGS = {slug(d): d for d in DCIS}
SIMPLES = {d: RACINES.get(norm(d), norm(d)) for d in DCIS if norm(d) not in COMBOS}
ASSOCS = {d: COMBOS[norm(d)] for d in DCIS if norm(d) in COMBOS}


def classer(denom, compo):
    """Retourne (dci, raison). dci = None si le RCP est à vérifier."""
    texte = compo or denom
    if not texte:
        return None, "rubriques 1/2 introuvables (PDF scanné ou en néerlandais ?)"
    n = nb_substances(compo)

    touches = [d for d, r in ASSOCS.items() if all(x in texte for x in r)]
    if touches:
        if len(touches) == 1 and n <= len(ASSOCS[touches[0]]):
            return touches[0], ""
        return None, "association ambiguë ou substance en plus"

    trouvees = [d for d, r in SIMPLES.items() if r in texte]
    if not trouvees:
        return None, "aucune DCI de la liste"
    if len(trouvees) > 1:
        return None, "plusieurs DCI de la liste : " + ", ".join(trouvees)
    if "+" in denom or n > 1 or (n == 0 and re.search(r"[A-Z]{4,}\s*/\s*[A-Z]{4,}", denom)):
        return None, "association ? substances comptées : " + ", ".join(mots_substances(compo))
    return trouvees[0], ""


def enregistrer(dci, pdf, amm):
    url = BASE_URL + (f"#AMM={amm}" if amm else "")
    return register(dci, SOURCE, url, "fr", pdf)


VRAC.mkdir(parents=True, exist_ok=True)
A_VERIFIER.mkdir(parents=True, exist_ok=True)

ranges = refuses = nouveaux = doublons = 0

# 1) fichiers en vrac : classement puis déplacement
for f in sorted(VRAC.glob("*.pdf")):
    try:
        denom, compo, amm = lire(f)
        dci, raison = classer(denom, compo)
    except Exception as e:
        print(f"ERR {f.name} : {e}")
        continue
    if dci is None:
        shutil.move(str(f), str(A_VERIFIER / f.name))
        print(f"?   {f.name} -> _a_verifier ({raison}) | {denom[:70]}")
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

# 2) enregistrement de tous les fichiers rangés (rejouable : register ignore les doublons)
for dossier in sorted(p for p in DOSSIER.iterdir() if p.is_dir() and not p.name.startswith("_")):
    dci = SLUGS.get(dossier.name)
    if dci is None:
        print(f"Dossier inconnu (pas dans la liste) : {dossier.name}")
        continue
    for pdf in sorted(dossier.glob("*.pdf")):
        try:
            amm = lire(pdf)[2]
        except Exception:
            amm = ""
        if enregistrer(dci, pdf, amm):
            nouveaux += 1
            print(f"OK  {dci} | {pdf.name}")
        else:
            doublons += 1

print(f"\nRangés : {ranges} | enregistrés : {nouveaux} | déjà enregistrés/doublons : {doublons} | à vérifier : {refuses}")

# 3) DCI de la liste sans aucun fichier
manquants = [d for d in DCIS if not list((DOSSIER / slug(d)).glob("*.pdf"))]
print(f"\nDCI sans aucun RCP FAGG ({len(manquants)}/{len(DCIS)}) :")
for d in manquants:
    print(" -", d)