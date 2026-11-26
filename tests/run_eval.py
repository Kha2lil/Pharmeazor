"""Rejoue le jeu de test (tests/jeu_de_test.json) depuis le cache et affiche les métriques. TODO : brancher le pipeline."""
import csv
import json
import sys
from pathlib import Path

# Windows console is cp1252 by default -> accents crash the script.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
jeu = json.loads((Path(__file__).parent / "jeu_de_test.json").read_text(encoding="utf-8"))

valides = [q for q in jeu if q.get("statut") == "valide"]
gabarits = [q for q in jeu if q.get("statut") != "valide"]

print(f"{len(jeu)} questions chargées (objectif : ≥ 30) — {len(valides)} valides, {len(gabarits)} gabarits.")

# Vérifie que chaque doc_id cité existe réellement dans le manifeste.
manifeste = ROOT / "data" / "metadata" / "documents.csv"
connus = set()
if manifeste.exists():
    with open(manifeste, encoding="utf-8", newline="") as f:
        connus = {r["doc_id"] for r in csv.DictReader(f)}

manquants = sorted({
    doc_id
    for q in valides
    for doc_id in q.get("doc_ids", [])
    if doc_id not in connus
})

if manquants:
    print(f"doc_id absents du manifeste : {', '.join(manquants)}")
else:
    print("Tous les doc_id des questions valides sont présents dans data/metadata/documents.csv.")
