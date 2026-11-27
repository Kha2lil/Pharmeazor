"""F1 - Conducteur de collecte : un seul point d'entrée pour les scripts de collecte.

Le programme ne télécharge rien par lui-même : il appelle les scripts existants
dans le bon ordre, et refuse toute source dont la date de vérification CGU est
absente de data/metadata/sources.csv.

    python -m src.collecte.run --all --dry-run
    python -m src.collecte.run --source bdpm
    python -m src.collecte.run --all --yes

Le mode --dry-run n'appelle aucun script et n'écrit aucun fichier.
Sans --yes, un lancement réel demande une confirmation manuelle.
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from src.config import ROOT

SOURCES_CSV = ROOT / "data" / "metadata" / "sources.csv"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ErreurCollecte(Exception):
    """Collecte refusée (source inconnue, CGU non vérifiée, script absent)."""


@dataclass(frozen=True)
class Etape:
    script: str
    role: str  # "téléchargement" ou "rangement"


@dataclass(frozen=True)
class Source:
    cle: str
    ligne_csv: str
    etapes: tuple[Etape, ...]


BDPM_CSV = "Base de Données Publique des Médicaments"
REGLES: dict[str, Source] = {
    "anpp": Source(
        "anpp", "ANPP_RCP",
        (Etape("telecharger_anpp.py", "téléchargement"),),
    ),
    "bdpm": Source(
        "bdpm", BDPM_CSV,
        (Etape("telecharger_bdpm.py", "téléchargement"),),
    ),
    "ansm_notice": Source(
        "ansm_notice", BDPM_CSV,
        (Etape("telecharger_notices_ansm.py", "téléchargement"),),
    ),
    "ema": Source(
        "ema", "EMA",
        (Etape("telecharger_ema.py", "téléchargement"),),
    ),
    "thesaurus": Source(
        "thesaurus", "Thesaurus ANSM",
        (Etape("telecharger_thesaurus.py", "téléchargement"),),
    ),
    "dailymed": Source(
        "dailymed", "DailyMed",
        (
            Etape("dailymed_01_index.py", "téléchargement"),
            Etape("dailymed_03_telecharger.py", "téléchargement"),
        ),
    ),
    "afmps": Source(
        "afmps", "AFMPS",
        (
            Etape("fagg_01_ranger.py", "rangement"),
            Etape("afmps_02_ranger_notices.py", "rangement"),
            Etape("afmps_03_ranger_dhpc.py", "rangement"),
        ),
    ),
}
ORDRE = ("anpp", "bdpm", "ansm_notice", "ema", "thesaurus", "dailymed", "afmps")


def robots_autorise(base_url: str, chemin: str) -> bool:
    """Utilitaire de lecture seule : vérifie robots.txt pour une URL."""
    from urllib.robotparser import RobotFileParser

    rp = RobotFileParser(base_url.rstrip("/") + "/robots.txt")
    rp.read()
    return rp.can_fetch("*", base_url.rstrip("/") + chemin)


def lire_sources(chemin: Path | None = None) -> dict[str, dict[str, str]]:
    chemin = chemin if chemin is not None else SOURCES_CSV
    with open(chemin, encoding="utf-8", newline="") as f:
        return {r["source"]: r for r in csv.DictReader(f)}


def verifier_cgu(registre: dict[str, dict[str, str]], source: Source) -> str:
    """Renvoie la date de vérification, ou refuse la collecte."""
    ligne = registre.get(source.ligne_csv)
    if ligne is None:
        raise ErreurCollecte(
            f'ligne « {source.ligne_csv} » absente de sources.csv '
            f'(requise pour la source « {source.cle} »).'
        )
    date = (ligne.get("date_verification") or "").strip()
    if not date:
        raise ErreurCollecte(
            f'CGU absente pour « {source.cle} » : date de vérification vide '
            f'dans sources.csv (ligne « {source.ligne_csv} »).'
        )
    if not DATE_RE.match(date):
        raise ErreurCollecte(
            f'date de vérification invalide pour « {source.cle} » : {date!r} '
            '(attendu AAAA-MM-JJ).'
        )
    return date


def planifier(
    cles: list[str], registre: dict[str, dict[str, str]]
) -> list[tuple[Source, str]]:
    for cle in cles:
        if cle not in REGLES:
            raise ErreurCollecte(
                f'source inconnue « {cle} ». Sources possibles : '
                + ", ".join(ORDRE)
            )
    plan: list[tuple[Source, str]] = []
    for cle in cles:
        source = REGLES[cle]
        date = verifier_cgu(registre, source)
        for etape in source.etapes:
            if not (ROOT / "scripts" / etape.script).is_file():
                raise ErreurCollecte(f'script introuvable : scripts/{etape.script}')
        plan.append((source, date))
    return plan


def afficher_plan(plan: list[tuple[Source, str]], dry_run: bool) -> None:
    etiquette = "DRY-RUN" if dry_run else "COLLECTE"
    print("Plan de collecte :")
    for source, date in plan:
        for etape in source.etapes:
            print(
                f"[{etiquette}] {source.cle:12} | {etape.role:14} | "
                f"scripts/{etape.script} | CGU {date}"
            )


def lancer_script(etape: Etape) -> int:
    """Appelle un script avec l'interpréteur courant. Seul point de lancement."""
    commande = [sys.executable, str(ROOT / "scripts" / etape.script)]
    return subprocess.run(commande, cwd=ROOT, check=False).returncode


def executer(plan: list[tuple[Source, str]], dry_run: bool, yes: bool) -> int:
    afficher_plan(plan, dry_run)
    if dry_run:
        print("Mode dry-run : aucun script lancé, aucun fichier modifié.")
        return 0

    if not yes:
        reponse = input("Tapez OUI pour continuer : ").strip().casefold()
        if reponse != "oui":
            print("Annulé : aucune collecte effectuée.")
            return 0

    for source, _ in plan:
        for etape in source.etapes:
            print(f"→ {source.cle} : {etape.script} ...")
            code = lancer_script(etape)
            if code != 0:
                print(f"ÉCHEC ({code}) : {etape.script}")
                return 1
            print("   OK")
    print("Collecte terminée.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Collecte reproductible : un point d'entrée, une garde-fou CGU."
    )
    ap.add_argument("--source", help="une seule source (ex. bdpm, afmps)")
    ap.add_argument("--all", action="store_true", help="toutes les sources")
    ap.add_argument("--dry-run", action="store_true", help="afficher sans exécuter")
    ap.add_argument("--yes", action="store_true", help="passer la confirmation")
    args = ap.parse_args(argv)

    if bool(args.source) == args.all:
        ap.error("indiquez soit --source NOM, soit --all (pas les deux, pas aucun)")

    cles = list(ORDRE) if args.all else [args.source]
    try:
        plan = planifier(cles, lire_sources())
    except ErreurCollecte as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERREUR : lecture de sources.csv impossible ({exc})", file=sys.stderr)
        return 2
    return executer(plan, args.dry_run, args.yes)


if __name__ == "__main__":
    sys.exit(main())
