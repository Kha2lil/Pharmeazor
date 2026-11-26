"""Import rejouable des documents AFMPS de origin/main dans documents.csv.

Lit le manifeste de la branche distante (sans l'écraser), garde uniquement les
lignes afmps/afmps_notice/afmps_dhpc, convertit les chemins absolus Windows en
chemins relatifs, puis enregistre via provenance.register() (déduplication par
sha256, schéma 14 colonnes préservé).
"""
import csv
import io
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

from src.config import ROOT
from src.collecte.provenance import register

REF = "origin/main"
SOURCES = {"afmps", "afmps_notice", "afmps_dhpc"}


def manifeste_reference() -> list[dict]:
    brut = subprocess.check_output(
        ["git", "show", f"{REF}:data/metadata/documents.csv"], cwd=ROOT
    )
    return list(csv.DictReader(io.StringIO(brut.decode("utf-8"))))


def chemin_relatif(chemin: str) -> str | None:
    normalise = chemin.replace("\\", "/")
    pos = normalise.find("data/raw/")
    return normalise[pos:] if pos >= 0 else None


def main() -> None:
    lignes = [r for r in manifeste_reference() if r["source"] in SOURCES]
    ajoutes = deja = ignores = 0
    for r in lignes:
        rel = chemin_relatif(r["chemin"])
        if not rel:
            ignores += 1
            continue
        chemin = ROOT / rel
        if not chemin.is_file():
            ignores += 1
            continue
        fiche = register(
            r["medicament"], r["source"], r["url"], r["langue"], chemin,
            date_collecte=r["date_collecte"] or None,
        )
        if fiche is None:
            deja += 1
        else:
            ajoutes += 1
    print(f"Lignes AFMPS dans {REF} : {len(lignes)}")
    print(f"Ajoutées : {ajoutes} | déjà présentes (sha256) : {deja} | ignorées : {ignores}")


if __name__ == "__main__":
    main()
