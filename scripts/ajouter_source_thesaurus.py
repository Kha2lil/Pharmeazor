"""Ajoute la source Thésaurus à data/metadata/sources.csv (sans casser les colonnes)."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
FICHIER = Path(__file__).resolve().parent.parent / "data" / "metadata" / "sources.csv"

VALEURS = {
    "source": "thesaurus",
    "nom": "Thésaurus des interactions médicamenteuses (ANSM)",
    "url": "https://ansm.sante.fr/documents/reference/thesaurus-des-interactions-medicamenteuses-1",
    "editeur": "ANSM",
    "licence": "À vérifier (mentions légales ANSM)",
    "langue": "fr",
    "autorite": "1",
    "url_telechargement": "https://ansm.sante.fr/documents/reference/thesaurus-des-interactions-medicamenteuses-1",
    "remarque": "Référence des interactions uniquement (pas un RCP). Version figée 15/09/2023, accessible jusqu'au 15/06/2027.",
}

with open(FICHIER, encoding="utf-8", newline="") as f:
    lignes = list(csv.reader(f))

entete = [c.strip().lower() for c in lignes[0]]
if any(l and l[0].strip().lower() == "thesaurus" for l in lignes[1:]):
    print("La source 'thesaurus' existe déjà.")
else:
    with open(FICHIER, "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow([VALEURS.get(c, "") for c in entete])
    print("Ajouté. Colonnes vides :", [c for c in entete if c not in VALEURS])