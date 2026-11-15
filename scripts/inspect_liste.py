"""Affiche la structure du fichier Excel de l'enseignant (lecture seule)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
f = ROOT / "data" / "reference" / "liste_40_medicaments.xlsx"

xl = pd.ExcelFile(f)
print("Feuilles :", xl.sheet_names)
for nom in xl.sheet_names:
    df = xl.parse(nom)
    print(f"\n=== Feuille '{nom}' : {len(df)} lignes ===")
    print("Colonnes :", list(df.columns))
    print(df.head(5).to_string())