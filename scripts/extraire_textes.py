"""F1 - Extraction du texte exploitable de chaque document brut.

Un document brut (PDF, JSON ou TXT) devient un fichier texte simple :
    data/processed/textes/{doc_id}.txt
et une ligne dans :
    data/processed/textes_index.csv

Les phrases d'origine sont conservées ; seule la mise en forme est normalisée.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

import pymupdf

sys.stdout.reconfigure(encoding="utf-8")

from src.config import ROOT

MANIFEST = ROOT / "data" / "metadata" / "documents.csv"
DOSSIER_TEXTES = ROOT / "data" / "processed" / "textes"
INDEX = ROOT / "data" / "processed" / "textes_index.csv"
CHAMPS = [
    "doc_id", "medicament", "source", "langue", "autorite", "url",
    "date_collecte", "chemin_source", "chemin_texte", "methode",
    "nb_caracteres", "sha256_source", "statut", "extrait_le",
]


def nettoyer(texte: str) -> str:
    t = unicodedata.normalize("NFC", texte or "")
    for c in ("\xa0", "\u202f", "\u2009", "\u2007"):
        t = t.replace(c, " ")
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = "".join(c for c in t if c in "\n\t" or ord(c) >= 32)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def lire_json(chemin: Path) -> str:
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    morceaux = [str(donnees.get("titre") or "")]
    for valeur in (donnees.get("sections") or {}).values():
        if str(valeur).strip():
            morceaux.append(str(valeur).strip())
    return "\n\n".join(m for m in morceaux if m.strip())


def lire_pdf(chemin: Path) -> str:
    with pymupdf.open(chemin) as doc:
        return "\n".join(page.get_text() for page in doc)


def extraire(chemin: Path) -> tuple[str, str]:
    suffixe = chemin.suffix.lower()
    if suffixe == ".json":
        return lire_json(chemin), "json"
    if suffixe == ".pdf":
        return lire_pdf(chemin), "pdf"
    if suffixe == ".txt":
        return chemin.read_text(encoding="utf-8", errors="replace"), "txt"
    raise ValueError(f"Format non pris en charge : {chemin.name}")


def afficher_stats(lignes: list[dict]) -> None:
    par_source = Counter(l["source"] for l in lignes)
    par_methode = Counter(l["methode"] for l in lignes)
    statuts = Counter(l["statut"] for l in lignes)
    tailles = [int(l["nb_caracteres"]) for l in lignes]
    print(f"Documents : {len(lignes)}")
    print(f"Textes écrits : {len(lignes) - statuts['vide']} | vides : {statuts['vide']}")
    print("Par source :", dict(sorted(par_source.items())))
    print("Par méthode :", dict(sorted(par_methode.items())))
    if tailles:
        print(
            "Caractères min / médian / max : "
            f"{min(tailles)} / {int(statistics.median(tailles))} / {max(tailles)}"
        )
    print("Total caractères :", sum(tailles))
    print("doc_id uniques :", len({l["doc_id"] for l in lignes}) == len(lignes))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true", help="réécrire tous les textes")
    ap.add_argument("--stats", action="store_true", help="afficher les statistiques")
    ap.add_argument("--limit", type=int, default=0, help="traiter seulement les N premiers documents")
    args = ap.parse_args()

    if INDEX.is_file() and not args.rebuild and not args.limit:
        with open(INDEX, encoding="utf-8", newline="") as f:
            lignes = list(csv.DictReader(f))
        print(f"Index existant : {INDEX.relative_to(ROOT)} ({len(lignes)} lignes)")
        manquants = [l for l in lignes if not (ROOT / l["chemin_texte"]).is_file()]
        print("Fichiers texte manquants :", len(manquants))
        if args.stats:
            afficher_stats(lignes)
        return

    with open(MANIFEST, encoding="utf-8", newline="") as f:
        documents = list(csv.DictReader(f))
    if args.limit:
        documents = documents[: args.limit]

    DOSSIER_TEXTES.mkdir(parents=True, exist_ok=True)
    aujourd_hui = date.today().isoformat()
    lignes: list[dict] = []
    erreurs: list[str] = []

    for d in documents:
        chemin = ROOT / d["chemin"].replace("\\", "/")
        if not chemin.is_file():
            erreurs.append(f"Fichier manquant : {chemin}")
            continue
        digest = hashlib.sha256(chemin.read_bytes()).hexdigest()
        if digest != d["sha256"]:
            erreurs.append(f"sha256 différent : {chemin}")
            continue
        try:
            brut, methode = extraire(chemin)
        except Exception as exc:  # lecture défaillante -> document signalé
            erreurs.append(f"Lecture impossible : {chemin} ({exc})")
            continue

        texte = nettoyer(brut)
        statut = "ok" if len(texte) >= 40 else "vide"
        destination = DOSSIER_TEXTES / f"{d['doc_id']}.txt"
        destination.write_text(texte, encoding="utf-8")

        lignes.append({
            "doc_id": d["doc_id"],
            "medicament": d["medicament"],
            "source": d["source"],
            "langue": d["langue"],
            "autorite": d["autorite"],
            "url": d["url"],
            "date_collecte": d["date_collecte"],
            "chemin_source": d["chemin"].replace("\\", "/"),
            "chemin_texte": destination.relative_to(ROOT).as_posix(),
            "methode": methode,
            "nb_caracteres": len(texte),
            "sha256_source": digest,
            "statut": statut,
            "extrait_le": aujourd_hui,
        })

    if erreurs:
        print(f"ERREURS ({len(erreurs)}) :")
        for e in erreurs[:10]:
            print("  ", e)
        if len(erreurs) > 10:
            print(f"  ... et {len(erreurs) - 10} autres")
        sys.exit("Extraction interrompue : index non écrit.")

    with open(INDEX, "w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=CHAMPS)
        ecrivain.writeheader()
        ecrivain.writerows(lignes)

    print(f"Écrit : {INDEX.relative_to(ROOT)}")
    print(f"Écrit : {DOSSIER_TEXTES.relative_to(ROOT)}/ ({len(lignes)} fichiers)")
    afficher_stats(lignes)


if __name__ == "__main__":
    main()
