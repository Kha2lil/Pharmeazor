"""Diagnostic : vérifier que les classes AINS / AAS et leurs interactions sont bien lues."""
import sys
from scripts.extraire_interactions import TEXTE, lire, norm, nos_dci, membres_de

sys.stdout.reconfigure(encoding="utf-8")
membres, paires = lire(TEXTE)

print("== 1) Classes contenant ibuprofène / AAS / IEC ==")
for cle, liste in membres.items():
    if any("IBUPROFENE" in m or "PERINDOPRIL" in m for m in liste):
        print(f"  {cle!r} -> dci de nous: {sorted(nos_dci(liste))}")

print("\n== 2) Paires dont un côté est AINS ou AAS ==")
for a, b, n in paires:
    if "NON STEROIDIENS" in a or "ACETYLSALICYLIQUE" in a or "NON STEROIDIENS" in b or "ACETYLSALICYLIQUE" in b:
        print(f"  {a!r} | {b!r} | {n!r}")

print("\n== 3) Titres bruts qui ressemblent à AINS (pour vérifier l'écriture) ==")
for cle in membres:
    if "STEROIDIEN" in cle or "STÉROÏDIEN" in cle:
        print("  ", repr(cle))