"""Combien de fiches DailyMed par DCI de la liste (aucune requête au site)."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

catalogue = json.loads((ROOT / "data" / "raw" / "dailymed" / "catalogue_index.json").read_text(encoding="utf-8"))
liste = pd.read_excel(ROOT / "data" / "reference" / "liste_40_medicaments.xlsx", sheet_name="Médicaments")

absents = 0
for _, row in liste.iterrows():
    dci = row["DCI (nom de la substance)"]
    n = sum(1 for p in catalogue if p["dci_liste"] == dci)
    if n == 0:
        absents += 1
    print(f"{int(row['N°']):>2}. {dci:<28} fiches={n}")

print(f"\n{absents} DCI sur {len(liste)} sans aucune fiche dans DailyMed")