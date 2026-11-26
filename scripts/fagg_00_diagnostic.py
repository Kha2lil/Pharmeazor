"""Diagnostic FAGG : pourquoi les PDF de _a_verifier ne sont pas lus ? (lecture seule)"""
import re
import sys
import unicodedata
from pathlib import Path

try:
    import pymupdf as fitz

    def pages(pdf):
        with fitz.open(pdf) as doc:
            return [p.get_text() for p in doc]
except ModuleNotFoundError:
    from pypdf import PdfReader

    def pages(pdf):
        return [(p.extract_text() or "") for p in PdfReader(pdf).pages]

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DOSSIER = ROOT / "data" / "raw" / "afmps" / "_a_verifier"


def norm(s):
    s = unicodedata.normalize("NFD", str(s).replace("’", "'"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper()


for f in sorted(DOSSIER.glob("*.pdf")):
    try:
        pp = pages(f)
    except Exception as e:
        print(f"{f.name:<14} ERR {e}")
        continue
    t = re.sub(r"\s+", " ", " ".join(pp)).strip()
    up = norm(t)
    if len(t) < 200:
        langue = "SANS TEXTE (scanné ?)"
    elif "GENEESMIDDEL" in up or "SAMENSTELLING" in up or "BIJSLUITER" in up:
        langue = "NEERLANDAIS"
    elif "DENOMINATION" in up or "CARACTERISTIQUES" in up or "NOTICE" in up:
        langue = "FRANCAIS"
    else:
        langue = "INCONNU"
    if "RESUME DES CARACTERISTIQUES" in up or "SAMENVATTING VAN DE KENMERKEN" in up:
        type_doc = "RCP/SPC"
    elif "NOTICE" in up[:400] or "BIJSLUITER" in up[:400]:
        type_doc = "NOTICE patient"
    else:
        type_doc = "?"
    r1 = bool(re.search(r"1\.? ?DENOMINATION DU MEDICAMENT", up))
    r2 = bool(re.search(r"2\.? ?COMPOSITION QUALITATIVE ET QUANTITATIVE", up))
    r3 = bool(re.search(r"3\.? ?FORME PHARMACEUTIQUE", up))
    print(f"{f.name:<14} p={len(pp):<3} car={len(t):<7} {langue:<22} {type_doc:<15} r1={r1} r2={r2} r3={r3} | {t[:90]}")