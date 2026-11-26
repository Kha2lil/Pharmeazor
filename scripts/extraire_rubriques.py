"""F2 - Écrit la fiche de rubriques de chaque document : data/processed/rubriques/{doc_id}.json."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from src.config import ROOT
from src.extraction.rubriques import OBLIGATOIRES, RUBRIQUES, extraire_rubriques

TEXTE_INDEX = ROOT / "data" / "processed" / "textes_index.csv"
DOSSIER = ROOT / "data" / "processed" / "rubriques"
INDEX = ROOT / "data" / "processed" / "rubriques_index.csv"
CHAMPS = [
    "doc_id", "medicament", "source", "langue", "autorite", "url",
    "date_collecte", "chemin_texte", "nb_trouvees", "manquantes",
    *RUBRIQUES,
]
# Référentiel d'interactions et courriers DHPC : pas des notices/RCP,
# donc pas de rubrique « indication / posologie » à retrouver.
SANS_RUBRIQUES = {"thesaurus", "afmps_dhpc"}


def rubriques_vides(raison: str) -> dict:
    return {
        r: {
            "trouve": False, "raison": raison, "titre": "", "methode": "",
            "debut": None, "fin": None, "passage": "",
        }
        for r in RUBRIQUES
    }


def afficher_stats(lignes: list[dict]) -> None:
    par_source: dict[str, Counter] = {}
    for l in lignes:
        c = par_source.setdefault(l["source"], Counter())
        c["docs"] += 1
        c["nb"] += int(l["nb_trouvees"])
        for r in OBLIGATOIRES:
            c[r] += int(l[r])
        if int(l["nb_trouvees"]) >= 3:
            c["au_moins_3"] += 1
    print(f"Documents : {len(lignes)}")
    print("Rubriques obligatoires trouvées :", dict(Counter({
        r: sum(int(l[r]) for l in lignes) for r in OBLIGATOIRES
    })))
    print(f"Documents avec >= 3 rubriques obligatoires : "
          f"{sum(int(l['nb_trouvees']) >= 3 for l in lignes)}")
    print(f"Moyenne par document : "
          f"{statistics.mean(int(l['nb_trouvees']) for l in lignes):.2f} / 4")
    print(f"{'source':14} {'docs':>6} {'>=3':>6} {'moy':>6}")
    for source, c in sorted(par_source.items()):
        print(f"{source:14} {c['docs']:6} {c['au_moins_3']:6} "
              f"{c['nb'] / c['docs']:6.2f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if INDEX.is_file() and not args.rebuild and not args.limit:
        with open(INDEX, encoding="utf-8", newline="") as f:
            lignes = list(csv.DictReader(f))
        print(f"Index existant : {INDEX.relative_to(ROOT)} ({len(lignes)} lignes)")
        if args.stats:
            afficher_stats(lignes)
        return

    with open(TEXTE_INDEX, encoding="utf-8", newline="") as f:
        textes = list(csv.DictReader(f))
    if args.limit:
        textes = textes[: args.limit]

    DOSSIER.mkdir(parents=True, exist_ok=True)
    aujourd_hui = date.today().isoformat()
    lignes: list[dict] = []

    for t in textes:
        chemin_texte = ROOT / t["chemin_texte"]
        if not chemin_texte.is_file():
            sys.exit(f"Texte manquant : {chemin_texte}")
        texte = chemin_texte.read_text(encoding="utf-8")
        if t["source"] in SANS_RUBRIQUES:
            rubriques = rubriques_vides("document de référence, pas une notice/RCP")
        else:
            rubriques = extraire_rubriques(texte)

        fiche = {
            "doc_id": t["doc_id"],
            "medicament": t["medicament"],
            "source": t["source"],
            "langue": t["langue"],
            "url": t["url"],
            "date_collecte": t["date_collecte"],
            "date_extraction": aujourd_hui,
            "chemin_texte": t["chemin_texte"],
            "rubriques": rubriques,
        }
        (DOSSIER / f"{t['doc_id']}.json").write_text(
            json.dumps(fiche, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        nb = sum(bool(rubriques[r]["trouve"]) for r in OBLIGATOIRES)
        manquantes = "|".join(r for r in OBLIGATOIRES if not rubriques[r]["trouve"])
        lignes.append({
            "doc_id": t["doc_id"],
            "medicament": t["medicament"],
            "source": t["source"],
            "langue": t["langue"],
            "autorite": t["autorite"],
            "url": t["url"],
            "date_collecte": t["date_collecte"],
            "chemin_texte": t["chemin_texte"],
            "nb_trouvees": nb,
            "manquantes": manquantes,
            **{r: int(bool(rubriques[r]["trouve"])) for r in RUBRIQUES},
        })

    with open(INDEX, "w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=CHAMPS)
        ecrivain.writeheader()
        ecrivain.writerows(lignes)

    print(f"Écrit : {INDEX.relative_to(ROOT)}")
    print(f"Écrit : {DOSSIER.relative_to(ROOT)}/ ({len(lignes)} fichiers)")
    afficher_stats(lignes)


if __name__ == "__main__":
    main()
