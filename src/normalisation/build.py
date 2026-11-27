"""F3 - Construction du dictionnaire de normalisation a partir des references et documents.csv."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any

from src.normalisation.matcher import charger, norm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COLONNES: list[str] = [
    "alias",
    "dci",
    "atc",
    "type",
    "classe",
    "classe_thesaurus",
    "statut",
    "forme",
    "dosage",
    "marque",
]

_EXCLUDED_MED_VALUES = {
    "interactions (referentiel)",
}


def _find_base_dictionary() -> Path | None:
    candidates = [
        PROJECT_ROOT / "data" / "processed" / "dictionnaire_medicaments.csv",
        PROJECT_ROOT / "data" / "reference" / "dictionnaire_medicaments.csv",
        PROJECT_ROOT / "dictionnaire_medicaments.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _find_documents_csv() -> Path | None:
    candidates = [
        PROJECT_ROOT / "data" / "metadata" / "documents.csv",
        PROJECT_ROOT / "documents.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _clean_brand_name(raw_brand: str) -> str:
    """Nettoie un libelle de marque brut sans inventer d'information."""
    cleaned = re.sub(r"\s+", " ", str(raw_brand or "").strip())
    return cleaned


def _extract_dosage_hint(brand_text: str) -> str:
    """Extrait un dosage explicite present dans le libelle brut si visible."""
    m = re.search(r"\b(\d+(?:[.,]\d+)?\s*(?:mg|g|ml|µg|ug)(?:/\d+(?:[.,]\d+)?\s*(?:mg|g|ml))?)\b", brand_text, re.I)
    if not m:
        return ""
    return re.sub(r"\s+", "", m.group(1)).upper()


def build_dictionary(
    base_dico_path: Path | None = None,
    documents_csv_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    src_dico = base_dico_path or _find_base_dictionary()
    src_docs = documents_csv_path or _find_documents_csv()
    out_file = output_path or (PROJECT_ROOT / "data" / "processed" / "dictionnaire_medicaments.csv")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    dci_meta: dict[str, dict[str, str]] = {}
    seen_aliases: set[tuple[str, str]] = set()

    if src_dico and src_dico.exists():
        for raw in charger(src_dico):
            row = {col: (raw.get(col) or "").strip() for col in COLONNES}
            alias_norm = norm(row["alias"])
            dci_norm = norm(row["dci"])
            if not alias_norm or not dci_norm:
                continue
            dedup_key = (alias_norm, dci_norm)
            if dedup_key in seen_aliases:
                continue
            seen_aliases.add(dedup_key)
            rows.append(row)
            if row["type"] == "dci" or dci_norm not in dci_meta:
                dci_meta[dci_norm] = {
                    "dci": row["dci"],
                    "atc": row["atc"],
                    "classe": row["classe"],
                    "classe_thesaurus": row["classe_thesaurus"],
                }

    if src_docs and src_docs.exists():
        with open(src_docs, encoding="utf-8", newline="") as f:
            for doc_row in csv.DictReader(f):
                med_raw = (doc_row.get("medicament") or "").strip()
                med_norm = norm(med_raw)
                if not med_norm or med_norm in _EXCLUDED_MED_VALUES or ";" in med_norm:
                    continue
                if med_norm not in dci_meta:
                    continue

                meta = dci_meta[med_norm]
                brand_raw = _clean_brand_name(doc_row.get("marque_brute") or "")
                if not brand_raw:
                    continue

                brand_norm = norm(brand_raw)
                dedup_key = (brand_norm, med_norm)
                if dedup_key in seen_aliases:
                    continue

                seen_aliases.add(dedup_key)
                statut_algerie = (doc_row.get("dci_present_algerie") or "").strip()
                statut_val = f"algerie:{statut_algerie}" if statut_algerie else "observe_documents"
                rows.append(
                    {
                        "alias": brand_raw,
                        "dci": meta["dci"],
                        "atc": meta["atc"],
                        "type": "marque",
                        "classe": meta["classe"],
                        "classe_thesaurus": meta["classe_thesaurus"],
                        "statut": statut_val,
                        "forme": "",
                        "dosage": _extract_dosage_hint(brand_raw),
                        "marque": brand_raw,
                    }
                )

    with open(out_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLONNES)
        writer.writeheader()
        writer.writerows(rows)

    return out_file


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construit le dictionnaire normalise des medicaments (F3).")
    parser.add_argument("--base-dico", type=Path, default=None, help="Chemin du dictionnaire de base.")
    parser.add_argument("--documents-csv", type=Path, default=None, help="Chemin de documents.csv.")
    parser.add_argument("--output", type=Path, default=None, help="Chemin CSV de sortie.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    out = build_dictionary(
        base_dico_path=args.base_dico,
        documents_csv_path=args.documents_csv,
        output_path=args.output,
    )
    loaded = charger(out)
    print(f"Dictionnaire construit -> {out} | Entrees totales: {len(loaded)}")


if __name__ == "__main__":
    main()