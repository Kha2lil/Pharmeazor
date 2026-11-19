"""Télécharge les notices patient BDPM (ANSM, France) des DCI de la liste des 40.
Sortie : data/raw/notices_ansm/<dci>/<CIS>_notice.txt + .json, et _index.csv (traçabilité)."""
import csv
import hashlib
import json
import sys
import time
from datetime import date

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.bdpm_outils import (NOTICES, INDEX_NOTICES, LISTE, charger_catalogue,
                                      cis_correspondants, extraire_notice, slug,
                                      telecharger_page, url_extrait)

COLONNES = ["dci", "cis", "designation", "source", "source_url", "langue",
            "pays_source", "date_collecte", "statut", "fichier", "sha256"]

catalogue = charger_catalogue()
liste = pd.read_excel(LISTE, sheet_name="Médicaments")

lignes_index = []
if INDEX_NOTICES.exists():
    with open(INDEX_NOTICES, encoding="utf-8-sig") as f:
        lignes_index = list(csv.DictReader(f))
connus = {(r["cis"]) for r in lignes_index}

def ecrire_index():
    INDEX_NOTICES.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_NOTICES, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        w.writerows(lignes_index)

deja_vus, nouveaux, absentes, erreurs = set(), 0, 0, 0
for dci in liste["DCI (nom de la substance)"]:
    for m in cis_correspondants(dci, catalogue):
        cis = m["cis"]
        if cis in deja_vus:
            continue
        deja_vus.add(cis)
        if cis in connus:
            continue
        url = url_extrait(cis)
        dossier = NOTICES / slug(dci)
        base = dossier / f"{cis}_notice"
        try:
            notice = extraire_notice(telecharger_page(cis))
            if notice is None:
                absentes += 1
                lignes_index.append({"dci": dci, "cis": cis, "designation": "",
                                     "source": "ansm_notice", "source_url": url,
                                     "langue": "fr", "pays_source": "France",
                                     "date_collecte": date.today().isoformat(),
                                     "statut": "non trouvée", "fichier": "", "sha256": ""})
                print(f"ABS {dci} | CIS {cis}")
            else:
                dossier.mkdir(parents=True, exist_ok=True)
                txt = notice["texte"]
                (base.with_suffix(".txt")).write_text(txt, encoding="utf-8")
                json_doc = {"dci": dci, "cis": cis, "titre": notice["titre"],
                            "source_url": url, "sections": notice["sections"]}
                (base.with_suffix(".json")).write_text(
                    json.dumps(json_doc, ensure_ascii=False, indent=1), encoding="utf-8")
                sha = hashlib.sha256(txt.encode("utf-8")).hexdigest()
                lignes_index.append({"dci": dci, "cis": cis, "designation": notice["titre"],
                                     "source": "ansm_notice", "source_url": url,
                                     "langue": "fr", "pays_source": "France",
                                     "date_collecte": date.today().isoformat(),
                                     "statut": "disponible",
                                     "fichier": str(base.relative_to(NOTICES)) + ".txt",
                                     "sha256": sha})
                nouveaux += 1
                print(f"OK  {dci} | {notice['titre']} | {len(notice['sections'])} sections")
            connus.add(cis)
            ecrire_index()
        except Exception as e:
            erreurs += 1
            print(f"ERR {dci} | CIS {cis} : {e}")
        time.sleep(2)

ecrire_index()
print(f"\nNouvelles : {nouveaux} | non trouvées : {absentes} | erreurs : {erreurs}")
print(f"Index : {INDEX_NOTICES}")