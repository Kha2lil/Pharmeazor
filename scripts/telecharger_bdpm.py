"""Télécharge les RCP BDPM des DCI de la liste des 40 (rejouable, sans doublons)."""
import json
import sys
import time

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.provenance import register
from src.collecte.bdpm_outils import (DOSSIER, LISTE, charger_catalogue, slug, cis_correspondants,
                                      telecharger_page, extraire_rcp, url_extrait)

catalogue = charger_catalogue()
liste = pd.read_excel(LISTE, sheet_name="Médicaments")

deja_vus = set()
nouveaux = existants = erreurs = 0
for dci_liste in liste["DCI (nom de la substance)"]:
    for m in cis_correspondants(dci_liste, catalogue):
        if m["cis"] in deja_vus:
            continue
        deja_vus.add(m["cis"])
        dest = DOSSIER / slug(dci_liste) / f"{m['cis']}.json"
        if dest.exists():
            existants += 1
            continue
        try:
            doc = extraire_rcp(telecharger_page(m["cis"]))
            if doc is None:
                raise ValueError("RCP introuvable")
            doc.update(cis=m["cis"], dci=dci_liste, source_url=url_extrait(m["cis"]))
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
            register(dci_liste, "bdpm", url_extrait(m["cis"]), "fr", dest)
            nouveaux += 1
            print(f"OK  {dci_liste} | {doc['titre']} | {len(doc['sections'])} sections")
        except Exception as e:
            erreurs += 1
            print(f"ERR {dci_liste} | CIS {m['cis']} : {e}")
        time.sleep(2)

print(f"\nNouveaux : {nouveaux} | déjà présents : {existants} | erreurs : {erreurs}")