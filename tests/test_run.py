"""F1 : conducteur de collecte — garde-fou CGU et ordre des scripts.

Tous les lancements sont simulés : aucun test ne télécharge ni n'écrit de donnée.
"""
from __future__ import annotations

import builtins
import csv

import pytest

from src.collecte import run

CHAMPS = [
    "source", "rang", "url", "robots_txt", "cgu",
    "mode_collecte", "date_verification", "remarques",
]


def ecrire_registre(tmp_path, date_par_source: dict[str, str]):
    chemin = tmp_path / "sources.csv"
    noms = {s.ligne_csv for s in run.REGLES.values()}
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=CHAMPS)
        ecrivain.writeheader()
        for nom in sorted(noms):
            ecrivain.writerow({
                "source": nom,
                "rang": "3",
                "url": "https://exemple.test",
                "robots_txt": "aucune restriction",
                "cgu": "autorisé",
                "mode_collecte": "automatique",
                "date_verification": date_par_source.get(nom, "2026-11-15"),
                "remarques": "",
            })
    return chemin


@pytest.fixture
def registre(tmp_path, monkeypatch):
    chemin = ecrire_registre(tmp_path, {})
    monkeypatch.setattr(run, "SOURCES_CSV", chemin)
    return chemin


@pytest.fixture
def appels(monkeypatch):
    enregistres: list[str] = []

    def faux_lancement(etape):
        enregistres.append(etape.script)
        return 0

    monkeypatch.setattr(run, "lancer_script", faux_lancement)
    return enregistres


def test_dry_run_all_ne_lance_rien(registre, appels, capsys):
    assert run.main(["--all", "--dry-run"]) == 0
    sortie = capsys.readouterr().out
    assert appels == []
    assert "aucun script lancé" in sortie
    for cle in run.ORDRE:
        assert f"[{cle}]" in sortie or f" {cle} " in sortie


def test_dry_run_source_seule(registre, appels, capsys):
    assert run.main(["--source", "dailymed", "--dry-run"]) == 0
    sortie = capsys.readouterr().out
    assert "dailymed_01_index.py" in sortie
    assert "dailymed_03_telecharger.py" in sortie
    assert "telecharger_bdpm.py" not in sortie
    assert appels == []


def test_date_cgu_vide_refusee(tmp_path, monkeypatch, capsys):
    chemin = ecrire_registre(tmp_path, {"Thesaurus ANSM": ""})
    monkeypatch.setattr(run, "SOURCES_CSV", chemin)
    assert run.main(["--source", "thesaurus", "--dry-run"]) == 2
    erreur = capsys.readouterr().err
    assert "CGU absente" in erreur
    assert "thesaurus" in erreur


def test_date_au_format_invalide_refusee(tmp_path, monkeypatch, capsys):
    chemin = ecrire_registre(tmp_path, {"EMA": "15/11/2026"})
    monkeypatch.setattr(run, "SOURCES_CSV", chemin)
    assert run.main(["--source", "ema", "--dry-run"]) == 2
    assert "date de vérification invalide" in capsys.readouterr().err


def test_source_inconnue_refusee(registre, capsys):
    assert run.main(["--source", "inconnu", "--dry-run"]) == 2
    assert "source inconnue" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [
    [],
    ["--all", "--source", "bdpm"],
])
def test_flags_mutuellement_exclusifs(argv):
    with pytest.raises(SystemExit) as exc:
        run.main(argv)
    assert exc.value.code == 2


def test_lancement_reel_sans_confirmation_ne_rien_faire(registre, appels, monkeypatch, capsys):
    monkeypatch.setattr(builtins, "input", lambda _: "non")
    assert run.main(["--source", "bdpm"]) == 0
    assert appels == []
    assert "aucune collecte effectuée" in capsys.readouterr().out


def test_lancement_reel_ordre_des_scripts(registre, appels, monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "oui")
    assert run.main(["--source", "afmps"]) == 0
    assert appels == [
        "fagg_01_ranger.py",
        "afmps_02_ranger_notices.py",
        "afmps_03_ranger_dhpc.py",
    ]
