"""Télécharge les PDF du Thésaurus des interactions (ANSM) et enregistre la provenance."""
import sys
from pathlib import Path

import pymupdf as fitz
import requests

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.collecte.provenance import register

DOSSIER = Path(__file__).resolve().parent.parent / "data" / "raw" / "thesaurus"
HEADERS = {"User-Agent": "PharmeazorStudentProject"}
DOCS = {
    "referentiel": "https://ansm.sante.fr/uploads/2024/06/07/20230915-thesaurus-interactions-medicamenteuses-septembre-2023.pdf",
    "index_substances": "https://ansm.sante.fr/uploads/2023/09/15/20230915-thesaurus-index-des-substances-septembre-2023.pdf",
    "index_classes": "https://ansm.sante.fr/uploads/2023/09/15/20230915-thesaurus-index-des-classes-septembre-2023.pdf",
}

DOSSIER.mkdir(parents=True, exist_ok=True)
for nom, url in DOCS.items():
    pdf = DOSSIER / f"{nom}.pdf"
    if pdf.exists():
        print("Déjà présent :", nom)
        continue
    r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()
    pdf.write_bytes(r.content)
    with fitz.open(pdf) as doc:
        texte = "\n".join(page.get_text() for page in doc)
    (DOSSIER / f"{nom}.txt").write_text(texte, encoding="utf-8")
    register("interactions (référentiel)", "thesaurus", url, "fr", pdf)
    print(f"OK {nom} | {len(texte)} caractères")