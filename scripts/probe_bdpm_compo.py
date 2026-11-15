"""Test : lire CIS_COMPO_bdpm.txt et vérifier les colonnes (aucune requête au site)."""
import sys

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.bdpm_outils import COMPO, COLONNES, lire_compo, norm

df = lire_compo()
print("Fichier :", COMPO)
print("Lignes :", len(df))
print("Colonnes attendues :", COLONNES)
print("Valeurs de 'nature' :", df["nature"].str.strip().value_counts().to_dict())
exemple = df[df["nom_substance"].apply(lambda s: "PARACETAMOL" in norm(s))]
print(exemple[["cis", "nom_substance", "nature"]].head(5).to_string())