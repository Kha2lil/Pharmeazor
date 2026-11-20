from pathlib import Path

from src.normalisation.matcher import charger, resoudre

ROOT = Path(__file__).resolve().parent.parent
DICO = ROOT / "data" / "processed" / "dictionnaire_medicaments.csv"


def test_dictionnaire_charge():
    dico = charger(DICO)
    assert len(dico) >= 1000
    assert any(r["type"] == "dci" for r in dico)
    assert any(r["type"] == "marque" for r in dico)


def test_marque_vers_dci():
    dico = charger(DICO)
    assert resoudre("MIBRAL", dico)["statut"] == "ok"
    assert resoudre("MIBRAL", dico)["candidats"][0]["dci"] == "amlodipine"
    assert resoudre("DETENSIEL", dico)["statut"] == "ok"
    assert resoudre("DETENSIEL", dico)["candidats"][0]["dci"] == "bisoprolol"


def test_typo():
    dico = charger(DICO)
    assert resoudre("paracetmol", dico)["candidats"][0]["dci"] == "paracétamol"
    assert resoudre("amlodipin", dico)["candidats"][0]["dci"] == "amlodipine"


def test_ambigu_signale():
    dico = charger(DICO)
    r = resoudre("PARACET", dico)
    assert r["statut"] == "ambigu"


def test_classe_thesaurus():
    dico = charger(DICO)
    m = resoudre("MIBRAL", dico)["candidats"][0]
    assert "DIHYDROPYRIDINES" in m["classe_thesaurus"]
    b = resoudre("DETENSIEL", dico)["candidats"][0]
    assert "BETA-BLOQUANTS" in b["classe_thesaurus"]
