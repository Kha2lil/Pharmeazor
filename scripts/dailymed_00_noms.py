"""Affiche, pour chaque DCI de la liste, les noms génériques existants dans DailyMed (40 requêtes légères)."""
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
API = "https://dailymed.nlm.nih.gov/dailymed/services/v2/drugnames.json"
HEADERS = {"User-Agent": "PharmeazorStudentProject"}

ALIAS = {
    "PARACETAMOL": "ACETAMINOPHEN",
    "IBUPROFENE": "IBUPROFEN",
    "KETOPROFENE": "KETOPROFEN",
    "NAPROXENE": "NAPROXEN",
    "ACIDE ACETYLSALICYLIQUE": "ASPIRIN",
    "PARACETAMOL + CODEINE": "ACETAMINOPHEN AND CODEINE",
    "AMOXICILLINE": "AMOXICILLIN",
    "AMOXICILLINE + ACIDE CLAVULANIQUE": "AMOXICILLIN AND CLAVULANATE",
    "AZITHROMYCINE": "AZITHROMYCIN",
    "CLARITHROMYCINE": "CLARITHROMYCIN",
    "CIPROFLOXACINE": "CIPROFLOXACIN",
    "LEVOFLOXACINE": "LEVOFLOXACIN",
    "COTRIMOXAZOLE (SULFAMETHOXAZOLE + TRIMETHOPRIME)": "SULFAMETHOXAZOLE AND TRIMETHOPRIM",
    "GENTAMICINE": "GENTAMICIN",
    "CLINDAMYCINE": "CLINDAMYCIN",
    "PERINDOPRIL": "PERINDOPRIL ERBUMINE",
    "BISOPROLOL": "BISOPROLOL FUMARATE",
    "NEFOPAM": "NEFOPAM",          # probablement absent des USA
}


def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


liste = pd.read_excel(ROOT / "data" / "reference" / "liste_40_medicaments.xlsx", sheet_name="Médicaments")
for _, row in liste.iterrows():
    dci = row["DCI (nom de la substance)"]
    nom = ALIAS.get(norm(dci), norm(dci))
    try:
        r = requests.get(API, params={"drug_name": nom, "name_type": "generic", "pagesize": 100},
                         headers=HEADERS, timeout=(15, 60))
        r.raise_for_status()
        noms = sorted({d["drug_name"].upper() for d in r.json().get("data", [])})
    except Exception as e:
        print(f"{int(row['N°']):>2}. {dci:<28} ERR {e}")
        continue
    seuls = [n for n in noms if n == nom]
    print(f"{int(row['N°']):>2}. {dci:<28} ({nom}) exact={'oui' if seuls else 'NON'} | {len(noms)} noms : {' | '.join(noms[:6])}")
    time.sleep(1)