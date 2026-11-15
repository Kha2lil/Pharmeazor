"""Construit le catalogue CIS -> substances depuis CIS_COMPO (aucune requête au site)."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.bdpm_outils import CATALOGUE, lire_compo, norm

df = lire_compo()
df = df[df["nature"].str.strip() == "SA"]

catalogue = {}
for _, r in df.iterrows():
    e = catalogue.setdefault(r["cis"], {"cis": r["cis"], "substances": [], "substances_norm": []})
    e["substances"].append(r["nom_substance"].strip())
    e["substances_norm"].append(norm(r["nom_substance"]))

CATALOGUE.parent.mkdir(parents=True, exist_ok=True)
CATALOGUE.write_text(json.dumps(list(catalogue.values()), ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(catalogue)} CIS enregistrés dans {CATALOGUE}")