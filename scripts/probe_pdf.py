"""Test : télécharger UN RCP de l'ANPP et vérifier s'il contient du vrai texte."""
from pathlib import Path
import requests
import pymupdf as fitz

URL = "https://rcp.anpp.dz/storage/rcp-pdfs/propharmal-spa/40ae6726-c6c3-46b1-a9b9-79ca7fa473a5.pdf"
ROOT = Path(__file__).resolve().parent.parent
dest = ROOT / "data" / "raw" / "anpp" / "test_doliprane.pdf"

r = requests.get(URL, timeout=60, headers={"User-Agent": "PharmeazorStudentProject"})
print("Code :", r.status_code, "| Type :", r.headers.get("Content-Type"), "| Taille :", len(r.content), "octets")
dest.write_bytes(r.content)

doc = fitz.open(dest)
print("Nombre de pages :", len(doc))
texte = "".join(page.get_text() for page in doc)
print("Caractères de texte extraits :", len(texte))
print("--- Début du texte ---")
print(texte[:500])

import re
print("--- Titres de rubriques trouvés ---")
for ligne in texte.splitlines():
    if re.match(r"^\s*\d+(\.\d+)*\.?\s+[A-ZÉÈÀ]", ligne):
        print(ligne.strip())