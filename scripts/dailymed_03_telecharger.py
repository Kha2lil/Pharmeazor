"""Télécharge les fiches DailyMed (PDF ou XML) du catalogue. Rejouable, sans doublons."""
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

from src.collecte.provenance import register

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

FORMAT = "pdf"          # "pdf" (comme ANPP) ou "xml" (texte structuré par sections, plus facile à parser)
MAX_PAR_DCI = 5         # certaines DCI ont des centaines de génériques : on limite
PAUSE = 2               # secondes entre deux téléchargements


def slug(s):
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


catalogue = json.loads((ROOT / "data" / "raw" / "dailymed" / "catalogue_index.json").read_text(encoding="utf-8"))

compteur = {}
nouveaux = existants = erreurs = 0
for p in catalogue:
    compteur[p["dci_liste"]] = compteur.get(p["dci_liste"], 0) + 1
    if compteur[p["dci_liste"]] > MAX_PAR_DCI:
        continue
    url = p["url_pdf"] if FORMAT == "pdf" else p["url_xml"]
    dest = ROOT / "data" / "raw" / "dailymed" / slug(p["dci_liste"]) / f"{p['setid']}.{FORMAT}"
    if dest.exists():
        existants += 1
        continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(url, timeout=60, headers={"User-Agent": "PharmeazorStudentProject"})
        r.raise_for_status()
        dest.write_bytes(r.content)
        register(p["dci_liste"], "dailymed", url, "en", dest)
        nouveaux += 1
        print(f"OK  {p['dci_liste']} | {p['titre'][:70]}")
    except Exception as e:
        erreurs += 1
        print(f"ERR {p['dci_liste']} | {p['titre'][:50]} : {e}")
    time.sleep(PAUSE)

print(f"\nNouveaux : {nouveaux} | déjà présents : {existants} | erreurs : {erreurs}")