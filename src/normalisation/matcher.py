"""F3 - Normalisation des noms : nom commercial / DCI / ATC / fautes de frappe.
Dictionnaire attendu : data/processed/dictionnaire_medicaments.csv (colonnes : alias, dci, atc, type)."""
import csv
import unicodedata
from pathlib import Path
from rapidfuzz import fuzz, process

SEUIL_OK = 90        # correspondance sûre
SEUIL_AMBIGU = 8     # écart minimal entre 1er et 2e candidat (DCI différentes)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower().strip())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def charger(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def resoudre(saisie: str, dico: list[dict]) -> dict:
    """Renvoie {statut: ok|ambigu|inconnu, candidats: [...]}. Les cas ambigus sont SIGNALÉS, jamais tranchés en silence."""
    alias = {norm(r["alias"]): r for r in dico}
    res = process.extract(norm(saisie), list(alias), scorer=fuzz.WRatio, limit=3)
    if not res or res[0][1] < 70:
        return {"statut": "inconnu", "candidats": []}
    cands = [{"alias": a, "dci": alias[a]["dci"], "atc": alias[a]["atc"], "score": s} for a, s, _ in res]
    dcis = {c["dci"] for c in cands if res[0][1] - c["score"] < SEUIL_AMBIGU}
    if len(dcis) > 1 or res[0][1] < SEUIL_OK:
        return {"statut": "ambigu", "candidats": cands}
    return {"statut": "ok", "candidats": cands[:1]}
