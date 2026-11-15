"""Compare la liste des 40 DCI avec le catalogue BDPM (aucune requête au site)."""
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.bdpm_outils import LISTE, charger_catalogue, cis_correspondants

catalogue = charger_catalogue()
liste = pd.read_excel(LISTE, sheet_name="Médicaments")

absents = 0
for _, row in liste.iterrows():
    dci = row["DCI (nom de la substance)"]
    total = len(cis_correspondants(dci, catalogue))
    if total == 0:
        absents += 1
    print(f"{int(row['N°']):>2}. {dci:<45} total={total}")

print(f"\n{absents} DCI sur {len(liste)} sans aucun CIS dans le catalogue BDPM")