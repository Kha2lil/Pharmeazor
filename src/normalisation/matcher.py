"""F3 - Normalisation des noms : nom commercial / DCI / ATC / classe / equivalents / ambiguite.

Dictionnaire attendu : data/processed/dictionnaire_medicaments.csv
(colonnes : alias, dci, atc, type, classe, classe_thesaurus, statut, forme, dosage, marque).
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz, process

SEUIL_OK = 90        # score >= 90 => ok
SEUIL_AMBIGU = 8     # ecart < 8 => ambigu (DCI differentes)


def norm(s: str | None) -> str:
    """Normalise une chaine : minuscules, sans accents, espaces unifies."""
    if s is None:
        return ""
    text = unicodedata.normalize("NFD", str(s).lower().strip())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def norm_compact(s: str | None) -> str:
    """Normalisation compacte utile pour codes ATC ou marques colles."""
    base = norm(s)
    return re.sub(r"[^a-z0-9]+", "", base)


def charger(path: Path) -> list[dict[str, str]]:
    """Charge le dictionnaire de normalisation depuis un fichier CSV."""
    with open(path, encoding="utf-8", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def trouver_equivalents(
    dci: str,
    forme: str,
    dosage: str,
    dico: list[dict[str, str]],
    exclure_marque: str | None = None,
) -> list[dict[str, str]]:
    """Retourne les produits equivalents : meme DCI, meme forme et meme dosage."""
    target_dci = norm(dci)
    target_forme = norm_compact(forme)
    target_dosage = norm_compact(dosage)
    excluded_brand = norm_compact(exclure_marque) if exclure_marque else ""

    if not target_dci or not target_forme or not target_dosage:
        return []

    equivalents: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str, str, str]] = set()

    for row in dico:
        if row.get("type") != "marque":
            continue
        if norm(row.get("dci")) != target_dci:
            continue
        if norm_compact(row.get("forme")) != target_forme:
            continue
        if norm_compact(row.get("dosage")) != target_dosage:
            continue

        marque_val = row.get("marque") or row.get("alias") or ""
        if excluded_brand and norm_compact(marque_val) == excluded_brand:
            continue

        key = (
            norm(row.get("dci")),
            norm_compact(marque_val),
            norm_compact(row.get("forme")),
            norm_compact(row.get("dosage")),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        equivalents.append(dict(row))

    return equivalents


def resoudre(saisie: str, dico: list[dict[str, str]]) -> dict[str, Any]:
    """Resout une saisie vers {statut: ok|ambigu|inconnu, candidats: [...], equivalents: [...]}.

    Les cas ambigus sont SIGNALES, jamais tranches en silence.
    """
    query = norm(saisie)
    if not query or not dico:
        return {"statut": "inconnu", "candidats": [], "equivalents": []}

    # Correspondance exacte sur code ATC (ex. C08CA01)
    query_compact = norm_compact(saisie)
    if re.fullmatch(r"[a-z]\d{2}[a-z]{2}\d{2}", query_compact):
        atc_matches = [r for r in dico if norm_compact(r.get("atc")) == query_compact]
        if atc_matches:
            dcis_atc = {r.get("dci") for r in atc_matches if r.get("dci")}
            cands = [
                {
                    "alias": r.get("alias", ""),
                    "dci": r.get("dci", ""),
                    "atc": r.get("atc", ""),
                    "classe": r.get("classe", ""),
                    "classe_thesaurus": r.get("classe_thesaurus", ""),
                    "statut": r.get("statut", ""),
                    "forme": r.get("forme", ""),
                    "dosage": r.get("dosage", ""),
                    "score": 100.0,
                }
                for r in atc_matches[:5]
            ]
            if len(dcis_atc) > 1:
                return {"statut": "ambigu", "candidats": cands, "equivalents": []}
            top = cands[0]
            eqs = trouver_equivalents(
                top["dci"], top.get("forme", ""), top.get("dosage", ""), dico, exclure_marque=top.get("alias")
            )
            return {"statut": "ok", "candidats": [top], "equivalents": eqs}

    alias_map: dict[str, dict[str, str]] = {}
    for r in dico:
        key = norm(r.get("alias"))
        if key and key not in alias_map:
            alias_map[key] = r

    if not alias_map:
        return {"statut": "inconnu", "candidats": [], "equivalents": []}

    # Correspondance exacte prioritaire sur l'alias normalise
    if query in alias_map:
        best_row = alias_map[query]
        top = {
            "alias": query,
            "dci": best_row.get("dci", ""),
            "atc": best_row.get("atc", ""),
            "classe": best_row.get("classe", ""),
            "classe_thesaurus": best_row.get("classe_thesaurus", ""),
            "statut": best_row.get("statut", ""),
            "forme": best_row.get("forme", ""),
            "dosage": best_row.get("dosage", ""),
            "score": 100.0,
        }
        eqs = trouver_equivalents(
            top["dci"],
            top.get("forme", ""),
            top.get("dosage", ""),
            dico,
            exclure_marque=best_row.get("marque") or best_row.get("alias"),
        )
        return {"statut": "ok", "candidats": [top], "equivalents": eqs}

    res = process.extract(query, list(alias_map.keys()), scorer=fuzz.WRatio, limit=5)
    if not res or res[0][1] < 70:
        return {"statut": "inconnu", "candidats": [], "equivalents": []}

    cands: list[dict[str, Any]] = []
    for a, score, _ in res:
        row = alias_map[a]
        cands.append(
            {
                "alias": a,
                "dci": row.get("dci", ""),
                "atc": row.get("atc", ""),
                "classe": row.get("classe", ""),
                "classe_thesaurus": row.get("classe_thesaurus", ""),
                "statut": row.get("statut", ""),
                "forme": row.get("forme", ""),
                "dosage": row.get("dosage", ""),
                "score": float(score),
            }
        )

    top_score = cands[0]["score"]
    near_cands = [c for c in cands if (top_score - c["score"]) < SEUIL_AMBIGU]
    dcis = {c["dci"] for c in near_cands if c["dci"]}

    if len(dcis) > 1 or top_score < SEUIL_OK:
        return {"statut": "ambigu", "candidats": cands[:3], "equivalents": []}

    best = cands[0]
    eqs = trouver_equivalents(
        best["dci"],
        best.get("forme", ""),
        best.get("dosage", ""),
        dico,
        exclure_marque=best.get("alias"),
    )
    return {"statut": "ok", "candidats": [best], "equivalents": eqs}