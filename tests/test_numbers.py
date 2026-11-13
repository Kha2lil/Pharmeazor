from src.verification.numbers import verifier


def test_chiffre_present():
    assert verifier("Dose max : 3 g par jour", ["Ne pas dépasser 3 g par jour."])["ok"]


def test_chiffre_invente_bloque():
    r = verifier("Dose max : 4 g par jour", ["Ne pas dépasser 3 g par jour."])
    assert not r["ok"] and "4" in r["introuvables"]
