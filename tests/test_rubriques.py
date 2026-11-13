from src.extraction.rubriques import decouper


def test_decoupe():
    t = "Indications\nDouleur\nContre-indications\nAllergie\nPosologie\nX"
    assert set(decouper(t)) >= {"indications", "contre_indications", "posologie"}
