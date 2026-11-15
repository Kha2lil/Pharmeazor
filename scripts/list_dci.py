"""Affiche toutes les DCI distinctes du catalogue ANPP (aucune requête au site)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

catalogue = json.loads((ROOT / "data" / "raw" / "anpp" / "catalogue_index.json").read_text(encoding="utf-8"))
dcis = sorted({p["dci"].strip().upper() for p in catalogue})
print(len(dcis), "DCI distinctes :\n")
print(" | ".join(dcis))