"""F2 - Mesure du taux de réussite de l'extraction des rubriques.

Compare les 80 passages annotés à la main dans
`data/annotations/echantillon_20/fiche_annotation.csv` aux passages retrouvés
par le détecteur `src/extraction/rubriques.py`.

Les annotateurs notent des NUMÉROS DE LIGNE ; le programme travaille en
POSITIONS CARACTÈRES. La conversion est mécanique : la ligne `n` commence à
`offsets[n-1]` dans le texte original.

Un cas est CORRECT si le passage du programme recouvre au moins 80 % du
passage humain (rappel >= 0,80). Le rappel et la précision sont reportés
séparément pour distinguer « a-t-on trouvé le bon endroit ? » de « le passage
renvoyé est-il propre ? ».

Sorties :
    data/annotations/rubriques_20.csv    clé de correction (offsets caractères)
    data/annotations/evaluation_20.csv   résultat par cas (80 lignes)
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import ROOT
from src.extraction.rubriques import extraire_rubriques

FICHE = ROOT / "data" / "annotations" / "echantillon_20" / "fiche_annotation.csv"
TEXTES = ROOT / "data" / "processed" / "textes"
CLE = ROOT / "data" / "annotations" / "rubriques_20.csv"
EVAL = ROOT / "data" / "annotations" / "evaluation_20.csv"

RUBRIQUES = ("Indications", "Contre-indications", "Posologie", "Interactions")
VERS_DETECTEUR = {
    "Indications": "indications",
    "Contre-indications": "contre_indications",
    "Posologie": "posologie",
    "Interactions": "interactions",
}
SEUIL = 0.80

CHAMPS_CLE = [
    "ordre", "doc_id", "medicament", "source", "rubrique",
    "ligne_debut", "ligne_fin", "debut", "fin", "longueur",
]
CHAMPS_EVAL = [
    "ordre", "doc_id", "medicament", "source", "rubrique",
    "main_debut", "main_fin", "main_longueur",
    "prog_debut", "prog_fin", "prog_longueur", "prog_trouve",
    "intersection", "rappel", "precision", "correct", "prog_titre",
]


def offsets_lignes(texte: str) -> list[int]:
    """Position du premier caractère de chaque ligne (0-indexé)."""
    resultat, pos = [], 0
    for ligne in texte.split("\n"):
        resultat.append(pos)
        pos += len(ligne) + 1
    return resultat


def charger_fiche() -> list[dict]:
    with FICHE.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 80:
        raise SystemExit(f"attendu 80 lignes d'annotation, trouvé {len(rows)}")
    return rows


def mesurer() -> tuple[list[dict], list[dict]]:
    cle: list[dict] = []
    evaluation: list[dict] = []
    for row in charger_fiche():
        ordre = int(row["ordre"])
        doc_id = row["doc_id"]
        rubrique = row["rubrique"]
        if rubrique not in VERS_DETECTEUR:
            raise SystemExit(f"rubrique inconnue : {rubrique!r}")

        texte = (TEXTES / f"{doc_id}.txt").read_text(encoding="utf-8")
        offsets = offsets_lignes(texte)
        nb_lignes = len(offsets)

        ligne_debut = int(row["ligne_debut"])
        ligne_fin = int(row["ligne_fin"])
        if not (1 <= ligne_debut <= ligne_fin <= nb_lignes):
            raise SystemExit(
                f"bornes invalides ordre {ordre} {rubrique}: "
                f"{ligne_debut}-{ligne_fin} (fichier: {nb_lignes} lignes)"
            )

        main_debut = offsets[ligne_debut - 1]
        main_fin = offsets[ligne_fin] if ligne_fin < nb_lignes else len(texte)

        passage = extraire_rubriques(texte)[VERS_DETECTEUR[rubrique]]
        prog_trouve = bool(passage["trouve"])
        prog_debut = passage["debut"] if prog_trouve else None
        prog_fin = passage["fin"] if prog_trouve else None

        if prog_trouve:
            intersection = max(
                0, min(main_fin, prog_fin) - max(main_debut, prog_debut)
            )
            rappel = intersection / (main_fin - main_debut)
            precision = intersection / (prog_fin - prog_debut)
        else:
            intersection = 0
            rappel = 0.0
            precision = 0.0

        correct = rappel >= SEUIL

        cle.append({
            "ordre": ordre,
            "doc_id": doc_id,
            "medicament": row["medicament"],
            "source": row["source"],
            "rubrique": rubrique,
            "ligne_debut": ligne_debut,
            "ligne_fin": ligne_fin,
            "debut": main_debut,
            "fin": main_fin,
            "longueur": main_fin - main_debut,
        })
        evaluation.append({
            "ordre": ordre,
            "doc_id": doc_id,
            "medicament": row["medicament"],
            "source": row["source"],
            "rubrique": rubrique,
            "main_debut": main_debut,
            "main_fin": main_fin,
            "main_longueur": main_fin - main_debut,
            "prog_debut": prog_debut,
            "prog_fin": prog_fin,
            "prog_longueur": (prog_fin - prog_debut) if prog_trouve else 0,
            "prog_trouve": "oui" if prog_trouve else "non",
            "intersection": intersection,
            "rappel": f"{rappel:.4f}",
            "precision": f"{precision:.4f}",
            "correct": "oui" if correct else "non",
            "prog_titre": passage["titre"],
        })
    return cle, evaluation


def ecrire(chemin: Path, champs: list[str], rows: list[dict]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=champs, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def resume(evaluation: list[dict]) -> None:
    def moyennes(sous: list[dict]) -> tuple[float, float]:
        return (
            statistics.mean(float(x["rappel"]) for x in sous),
            statistics.mean(float(x["precision"]) for x in sous),
        )

    total = len(evaluation)
    corrects = sum(1 for x in evaluation if x["correct"] == "oui")
    rappel, precision = moyennes(evaluation)
    print(f"Global : {corrects}/{total} corrects "
          f"({100 * corrects / total:.1f} %) | "
          f"rappel moyen {100 * rappel:.1f} % | "
          f"précision moyenne {100 * precision:.1f} %")
    print()
    print(f"{'Rubrique':20} {'Correct':>9} {'Trouvé':>8} "
          f"{'Rappel':>8} {'Précision':>10}")
    for rubrique in RUBRIQUES:
        sous = [x for x in evaluation if x["rubrique"] == rubrique]
        ok = sum(1 for x in sous if x["correct"] == "oui")
        trouves = sum(1 for x in sous if x["prog_trouve"] == "oui")
        r, p = moyennes(sous)
        print(f"{rubrique:20} {ok:>4}/{len(sous):<4} {trouves:>4}/{len(sous):<3} "
              f"{100 * r:>7.1f}% {100 * p:>9.1f}%")
    print()
    print("Échecs (rappel < 80 %) :")
    for x in evaluation:
        if x["correct"] == "non":
            print(
                f"  ordre {x['ordre']:>2} {x['rubrique']:18} "
                f"{x['medicament'][:20]:20} "
                f"main={x['main_debut']}-{x['main_fin']} "
                f"prog={x['prog_debut']}-{x['prog_fin']} "
                f"rappel={float(x['rappel']):.3f} "
                f"titre={x['prog_titre'][:60]!r}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true",
                        help="afficher seulement le résumé")
    args = parser.parse_args()

    cle, evaluation = mesurer()
    ecrire(CLE, CHAMPS_CLE, cle)
    ecrire(EVAL, CHAMPS_EVAL, evaluation)
    print(f"clé écrite     : {CLE.relative_to(ROOT)} ({len(cle)} lignes)")
    print(f"résultats      : {EVAL.relative_to(ROOT)} ({len(evaluation)} lignes)")
    print()
    resume(evaluation)


if __name__ == "__main__":
    main()
