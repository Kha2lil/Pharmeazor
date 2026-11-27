"""Tests et evaluation chiffre (40+ saisies) pour la normalisation des medicaments (F3)."""

from __future__ import annotations

import csv
from pathlib import Path

from src.normalisation.build import COLONNES, build_dictionary
from src.normalisation.matcher import charger, resoudre, trouver_equivalents


def _sample_dico() -> list[dict[str, str]]:
    return [
        {
            "alias": "paracétamol",
            "dci": "paracétamol",
            "atc": "N02BE01",
            "type": "dci",
            "classe": "Antalgiques et anti-inflammatoires",
            "classe_thesaurus": "",
            "statut": "oui",
            "forme": "",
            "dosage": "",
            "marque": "",
        },
        {
            "alias": "DOLIPRANE",
            "dci": "paracétamol",
            "atc": "N02BE01",
            "type": "marque",
            "classe": "Antalgiques et anti-inflammatoires",
            "classe_thesaurus": "",
            "statut": "active",
            "forme": "COMPRIME",
            "dosage": "500MG",
            "marque": "DOLIPRANE",
        },
        {
            "alias": "EFFERALGAN",
            "dci": "paracétamol",
            "atc": "N02BE01",
            "type": "marque",
            "classe": "Antalgiques et anti-inflammatoires",
            "classe_thesaurus": "",
            "statut": "active",
            "forme": "COMPRIME",
            "dosage": "500MG",
            "marque": "EFFERALGAN",
        },
        {
            "alias": "amlodipine",
            "dci": "amlodipine",
            "atc": "C08CA01",
            "type": "dci",
            "classe": "Antihypertenseurs",
            "classe_thesaurus": "",
            "statut": "oui",
            "forme": "",
            "dosage": "",
            "marque": "",
        },
        {
            "alias": "AMLODIPINE ALMUS",
            "dci": "amlodipine",
            "atc": "C08CA01",
            "type": "marque",
            "classe": "Antihypertenseurs",
            "classe_thesaurus": "",
            "statut": "active",
            "forme": "GELULE",
            "dosage": "5MG",
            "marque": "AMLODIPINE ALMUS",
        },
        {
            "alias": "bisoprolol",
            "dci": "bisoprolol",
            "atc": "C07AB07",
            "type": "dci",
            "classe": "Antihypertenseurs",
            "classe_thesaurus": "",
            "statut": "oui",
            "forme": "",
            "dosage": "",
            "marque": "",
        },
        {
            "alias": "BISOPROLOL SANDOZ",
            "dci": "bisoprolol",
            "atc": "C07AB07",
            "type": "marque",
            "classe": "Antihypertenseurs",
            "classe_thesaurus": "",
            "statut": "active",
            "forme": "COMPRIME",
            "dosage": "5MG",
            "marque": "BISOPROLOL SANDOZ",
        },
        {
            "alias": "ibuprofène",
            "dci": "ibuprofène",
            "atc": "M01AE01",
            "type": "dci",
            "classe": "Antalgiques et anti-inflammatoires",
            "classe_thesaurus": "ANTI-INFLAMMATOIRES NON STEROIDIENS",
            "statut": "oui",
            "forme": "",
            "dosage": "",
            "marque": "",
        },
        {
            "alias": "amoxicilline",
            "dci": "amoxicilline",
            "atc": "J01CA04",
            "type": "dci",
            "classe": "Antibiotiques",
            "classe_thesaurus": "",
            "statut": "oui",
            "forme": "",
            "dosage": "",
            "marque": "",
        },
        {
            "alias": "tramadol",
            "dci": "tramadol",
            "atc": "N02AX02",
            "type": "dci",
            "classe": "Antalgiques et anti-inflammatoires",
            "classe_thesaurus": "ANALGESIQUES MORPHINIQUES AGONISTES",
            "statut": "oui",
            "forme": "",
            "dosage": "",
            "marque": "",
        },
    ]


def test_build_intègre_marques_documents_csv(tmp_path: Path) -> None:
    base_csv = tmp_path / "base.csv"
    docs_csv = tmp_path / "documents.csv"
    out_csv = tmp_path / "dico_out.csv"

    with open(base_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        w.writerows(_sample_dico())

    with open(docs_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["doc_id", "medicament", "marque_brute", "dci_present_algerie"],
        )
        w.writeheader()
        w.writerow(
            {
                "doc_id": "d1",
                "medicament": "paracétamol",
                "marque_brute": "DOLIPRANE 1000 mg comprimé",
                "dci_present_algerie": "oui",
            }
        )
        w.writerow(
            {
                "doc_id": "d2",
                "medicament": "interactions (référentiel)",
                "marque_brute": "IGNORER",
                "dci_present_algerie": "",
            }
        )

    built = build_dictionary(base_dico_path=base_csv, documents_csv_path=docs_csv, output_path=out_csv)
    loaded = charger(built)
    aliases = [r["alias"] for r in loaded]
    assert "DOLIPRANE 1000 mg comprimé" in aliases
    assert "IGNORER" not in aliases


def test_equivalents_et_ambiguite() -> None:
    dico = _sample_dico()
    eqs = trouver_equivalents("paracétamol", "COMPRIME", "500MG", dico, exclure_marque="DOLIPRANE")
    assert len(eqs) == 1
    assert eqs[0]["marque"] == "EFFERALGAN"

    res_amb = resoudre("moliprane", dico)
    assert res_amb["statut"] in {"ambigu", "ok"}
    assert len(res_amb["candidats"]) >= 1


def test_evaluation_chiffree_40_saisies_et_plus() -> None:
    dico = _sample_dico()
    # 44 saisies couvrant DCI, marques, ATC, variantes et fautes de frappe
    cas_test: list[tuple[str, str | None]] = [
        ("paracetamol", "paracétamol"),
        ("PARACETAMOL", "paracétamol"),
        ("paracétamol", "paracétamol"),
        ("doliprane", "paracétamol"),
        ("DOLIPRANE", "paracétamol"),
        ("efferalgan", "paracétamol"),
        ("N02BE01", "paracétamol"),
        ("n02be01", "paracétamol"),
        ("amlodipine", "amlodipine"),
        ("AMLODIPINE", "amlodipine"),
        ("amlodipine almus", "amlodipine"),
        ("C08CA01", "amlodipine"),
        ("bisoprolol", "bisoprolol"),
        ("bisoprolol sandoz", "bisoprolol"),
        ("C07AB07", "bisoprolol"),
        ("ibuprofene", "ibuprofène"),
        ("ibuprofène", "ibuprofène"),
        ("amoxicilline", "amoxicilline"),
        ("tramadol", "tramadol"),
        ("dolipran", "paracétamol"),
        ("efferalgan", "paracétamol"),
        ("amlodipn", "amlodipine"),
        ("bisoprolo", "bisoprolol"),
        ("ibuprofen", "ibuprofène"),
        ("amoxicillin", "amoxicilline"),
        ("tramadole", "tramadol"),
        ("  Doliprane  ", "paracétamol"),
        ("  Amlodipine Almus ", "amlodipine"),
        ("  Bisoprolol Sandoz ", "bisoprolol"),
        ("c08ca01", "amlodipine"),
        ("c07ab07", "bisoprolol"),
        ("paracetamole", "paracétamol"),
        ("dolipranne", "paracétamol"),
        ("efferalgane", "paracétamol"),
        ("amlodipine 5mg", "amlodipine"),
        ("bisoprolol 5mg", "bisoprolol"),
        ("amoxiciline", "amoxicilline"),
        ("ibuprufene", "ibuprofène"),
        ("tramadol 50", "tramadol"),
        ("doliprane gelule", "paracétamol"),
        ("amlodipine comprimé", "amlodipine"),
        ("bisoprolol comprimé", "bisoprolol"),
        ("xyz_inconnu_999", None),
        ("zzzz_non_existant", None),
    ]
    assert len(cas_test) >= 40

    correct = 0
    for saisie, attendu_dci in cas_test:
        out = resoudre(saisie, dico)
        if attendu_dci is None:
            if out["statut"] == "inconnu":
                correct += 1
        else:
            if out["statut"] == "ok" and out["candidats"] and out["candidats"][0]["dci"] == attendu_dci:
                correct += 1

    precision = correct / len(cas_test)
    assert precision >= 0.80, f"Taux trop bas : {correct}/{len(cas_test)} ({precision:.2%})"
