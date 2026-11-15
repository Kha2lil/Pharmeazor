"""Compare la liste des 40 DCI de l'enseignant avec le catalogue ANPP (aucune requête au site)."""
import json
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent


def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


catalogue = json.loads((ROOT / "data" / "raw" / "anpp" / "catalogue_index.json").read_text(encoding="utf-8"))
liste = pd.read_excel(ROOT / "data" / "reference" / "liste_40_medicaments.xlsx", sheet_name="Médicaments")

absents = 0
for _, row in liste.iterrows():
    dci = norm(row["DCI (nom de la substance)"])
    seul = sum(1 for p in catalogue if norm(p["dci"]) == dci)
    total = sum(1 for p in catalogue if dci in norm(p["dci"]))
    if total == 0:
        absents += 1
    print(f"{int(row['N°']):>2}. {row['DCI (nom de la substance)']:<28} seul={seul:<3} total={total}")

print(f"\n{absents} DCI sur {len(liste)} sans aucun RCP dans le catalogue ANPP")