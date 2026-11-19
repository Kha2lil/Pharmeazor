"""Test : repérer la notice patient dans la page BDPM d'un CIS (aucun fichier écrit)."""
import re
import sys

from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.bdpm_outils import telecharger_page

cis = sys.argv[1] if len(sys.argv) > 1 else "61293112"
soup = BeautifulSoup(telecharger_page(cis), "lxml")

print("Titres (h2/h3/h4) :")
for h in soup.find_all(["h2", "h3", "h4"]):
    t = h.get_text(" ", strip=True)
    if t:
        print("  ", h.name, "|", t[:90])

print("\nBlocs dont l'id contient 'notice' :")
for tag in soup.find_all(id=re.compile("notice", re.I)):
    print("  ", tag.name, tag.get("id"), "| longueur texte:", len(tag.get_text()))

print("\nOccurrences de 'Notice' dans le texte :",
      len(re.findall(r"Notice", soup.get_text())))