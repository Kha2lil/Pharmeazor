"""Test rapide : pour chaque DCI, vérifie qu'au moins un CIS a un RCP (1 requête par DCI)."""
import sys
import time

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.bdpm_outils import LISTE, charger_catalogue, cis_correspondants, telecharger_page, extraire_rcp

catalogue = charger_catalogue()
liste = pd.read_excel(LISTE, sheet_name="Médicaments")

avec = 0
for _, row in liste.iterrows():
    dci = row["DCI (nom de la substance)"]
    cis_liste = cis_correspondants(dci, catalogue)
    if not cis_liste:
        print(f"{int(row['N°']):>2}. {dci:<45} aucun CIS")
        continue
    cis = cis_liste[0]["cis"]
    try:
        ok = extraire_rcp(telecharger_page(cis)) is not None
    except Exception as e:
        ok, msg = False, str(e)
    else:
        msg = ""
    avec += ok
    print(f"{int(row['N°']):>2}. {dci:<45} CIS {cis} -> {'RCP OK' if ok else 'PAS DE RCP ' + msg}")
    time.sleep(2)

print(f"\n{avec} DCI sur {len(liste)} ont un RCP (testé sur un CIS par DCI)")