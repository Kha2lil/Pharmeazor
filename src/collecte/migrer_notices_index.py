"""Migration UNIQUE et rejouable : intègre les notices ANSM de notices_ansm/_index.csv
dans data/metadata/documents.csv, via provenance.register() (même mécanisme que les RCP).
- _index.csv n'est ni modifié ni supprimé (archive).
- Doublons évités par register() (clé = sha256 du fichier) : on peut relancer sans risque.
- Seules les notices disponibles (avec fichier) sont enregistrées ; les autres lignes sont ignorées."""
import csv
import shutil
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.bdpm_outils import INDEX_NOTICES, NOTICES
from src.collecte.provenance import index_path, register, sha256_file

SOURCE = "ansm_notice"

if not INDEX_NOTICES.exists():
    sys.exit(f"Introuvable : {INDEX_NOTICES}")

# Sauvegarde de sécurité de documents.csv avant toute écriture
docs = index_path()
if docs.exists():
    sauvegarde = docs.with_name(f"documents.backup_{datetime.now():%Y%m%d_%H%M%S}.csv")
    shutil.copy2(docs, sauvegarde)
    print(f"Sauvegarde : {sauvegarde}")

with open(INDEX_NOTICES, encoding="utf-8-sig") as f:
    lignes = list(csv.DictReader(f))

ajoutes = deja = 0
manquants, sha_differents = [], 0
for r in lignes:
    if r["statut"] != "disponible" or not r["fichier"]:
        continue
    chemin = NOTICES / r["fichier"].replace("\\", "/")
    if not chemin.exists():
        manquants.append((r["cis"], str(chemin)))
        continue
    if r["sha256"] and sha256_file(chemin) != r["sha256"]:
        sha_differents += 1          # informatif (ex. fins de ligne Windows) : register() hache le fichier réel
    fiche = register(r["dci"], SOURCE, r["source_url"], r["langue"] or "fr", chemin,
                     date_collecte=r["date_collecte"])
    if fiche is None:
        deja += 1
    else:
        ajoutes += 1

print(f"Ajoutées à documents.csv : {ajoutes} | déjà présentes : {deja}")
print(f"sha256 du fichier ≠ sha256 de l'index : {sha_differents} (informatif)")
print(f"Fichiers manquants sur disque : {len(manquants)}")
for cis, c in manquants[:20]:
    print("  MANQUANT", cis, c)