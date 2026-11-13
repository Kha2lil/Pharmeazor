"""Rejoue le jeu de test (tests/jeu_de_test.json) depuis le cache et affiche les métriques. TODO : brancher le pipeline."""
import json
from pathlib import Path

jeu = json.loads((Path(__file__).parent / "jeu_de_test.json").read_text(encoding="utf-8"))
print(f"{len(jeu)} questions chargées (objectif : ≥ 30).")
