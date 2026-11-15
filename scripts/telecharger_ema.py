"""Télécharge les Product information EMA des DCI de la liste (rejouable, sans doublons)."""
import sys
import time

import pandas as pd
import pymupdf as fitz

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.provenance import register
from src.collecte.ema_outils import (DOSSIER, LISTE, HEADERS, charger_medicaments,
                                     correspond, lien_notice, slug)
import requests

medicaments = charger_medicaments()
liste = pd.read_excel(LISTE, sheet_name="Médicaments")

deja_vus = set()
nouveaux = existants = erreurs = 0
for dci_liste in liste["DCI (nom de la substance)"]:
    for _, ligne in correspond(dci_liste, medicaments).iterrows():
        num = str(ligne["EMA product number"]).replace("/", "_")
        if num in deja_vus:
            continue
        deja_vus.add(num)
        dossier = DOSSIER / slug(dci_liste)
        pdf = dossier / f"{num}.pdf"
        txt = dossier / f"{num}.txt"
        if pdf.exists():
            existants += 1
            continue
        try:
            url_pdf = lien_notice(ligne["Medicine URL"])
            if not url_pdf:
                raise ValueError("lien 'Product information' introuvable")
            r = requests.get(url_pdf, headers=HEADERS, timeout=60)
            r.raise_for_status()
            dossier.mkdir(parents=True, exist_ok=True)
            pdf.write_bytes(r.content)
            with fitz.open(pdf) as doc:
                texte = "\n".join(page.get_text() for page in doc)
            txt.write_text(texte, encoding="utf-8")
            register(dci_liste, "ema", url_pdf, "en", pdf)
            nouveaux += 1
            print(f"OK  {dci_liste} | {ligne['Name of medicine']} | {len(texte)} caractères")
        except Exception as e:
            erreurs += 1
            print(f"ERR {dci_liste} | {ligne['Name of medicine']} : {e}")
        time.sleep(2)

print(f"\nNouveaux : {nouveaux} | déjà présents : {existants} | erreurs : {erreurs}")