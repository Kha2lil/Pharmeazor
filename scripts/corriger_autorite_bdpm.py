"""Corrige l'autorité des enregistrements BDPM dans documents.csv (5 -> 3).
Ne modifie que les lignes source=bdpm ; les autres sources restent intactes.
Usage : python -m scripts.corriger_autorite_bdpm          (test, rien n'est écrit)
        python -m scripts.corriger_autorite_bdpm --apply  (écriture + sauvegarde)"""
import csv
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
FICHIER = ROOT / "data" / "metadata" / "documents.csv"
SOURCES = {"bdpm": ("5", "3")}   # source : (ancienne autorité, nouvelle autorité)
APPLIQUER = "--apply" in sys.argv

with open(FICHIER, encoding="utf-8", newline="") as f:
    lecteur = csv.DictReader(f)
    champs = lecteur.fieldnames
    lignes = list(lecteur)

a_corriger = 0
for ligne in lignes:
    source = ligne["source"].strip()
    if source in SOURCES:
        ancienne, nouvelle = SOURCES[source]
        if ligne["autorite"].strip() == ancienne:
            ligne["autorite"] = nouvelle
            a_corriger += 1

print(f"{len(lignes)} lignes lues, {a_corriger} ligne(s) BDPM à corriger (5 -> 3)")
if not APPLIQUER:
    print("Mode test : aucun fichier modifié. Relancer avec --apply pour corriger.")
    sys.exit(0)

sauvegarde = FICHIER.with_suffix(".csv.bak")
shutil.copy(FICHIER, sauvegarde)
temp = FICHIER.with_suffix(".csv.tmp")
with open(temp, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=champs)
    w.writeheader()
    w.writerows(lignes)
temp.replace(FICHIER)
print(f"Corrigé. Sauvegarde conservée : {sauvegarde.name}")