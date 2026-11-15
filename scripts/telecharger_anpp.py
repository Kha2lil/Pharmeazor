"""Télécharge les RCP ANPP dont la DCI contient une DCI de la liste des 40 (rejouable, sans doublons)."""
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests

from src.collecte.provenance import register

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent


def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", norm(s).lower()).strip("_")


catalogue = json.loads((ROOT / "data" / "raw" / "anpp" / "catalogue_index.json").read_text(encoding="utf-8"))
liste = pd.read_excel(ROOT / "data" / "reference" / "liste_40_medicaments.xlsx", sheet_name="Médicaments")

deja_vus = set()
nouveaux = existants = erreurs = 0
for dci_liste in liste["DCI (nom de la substance)"]:
    cle = norm(dci_liste)
    for p in catalogue:
        if cle not in norm(p["dci"]) or p["url"] in deja_vus:
            continue
        deja_vus.add(p["url"])
        dest = ROOT / "data" / "raw" / "anpp" / slug(dci_liste) / p["url"].rsplit("/", 1)[-1]
        if dest.exists():
            existants += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = requests.get(p["url"], timeout=60, headers={"User-Agent": "PharmeazorStudentProject"})
            r.raise_for_status()
            dest.write_bytes(r.content)
            register(dci_liste, "anpp", p["url"], "fr", dest)
            nouveaux += 1
            print(f"OK  {dci_liste} | {p['marque']}")
        except Exception as e:
            erreurs += 1
            print(f"ERR {dci_liste} | {p['marque']} : {e}")
        time.sleep(3)

print(f"\nNouveaux : {nouveaux} | déjà présents : {existants} | erreurs : {erreurs}")