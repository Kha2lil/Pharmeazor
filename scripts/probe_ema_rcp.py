"""Test : lister les PDF d'UNE fiche EMA et vérifier le lien 'Product information'."""
import sys

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.ema_outils import charger_medicaments, correspond, liens_pdf, lien_notice

df = correspond("ibuprofène", charger_medicaments())
print("Médicaments trouvés :", len(df))
if df.empty:
    raise SystemExit

ligne = df.iloc[0]
print("Nom :", ligne["Name of medicine"])
print("Fiche :", ligne["Medicine URL"])
for texte, href in liens_pdf(ligne["Medicine URL"]):
    print(" -", texte[:60], "|", href)
print("\nLien retenu :", lien_notice(ligne["Medicine URL"]))