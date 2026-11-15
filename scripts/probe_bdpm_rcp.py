"""Test : extraire le RCP d'UNE page BDPM et l'enregistrer en .txt lisible."""
import sys

sys.stdout.reconfigure(encoding="utf-8")
from src.collecte.bdpm_outils import DOSSIER, telecharger_page, extraire_rcp

cis = sys.argv[1] if len(sys.argv) > 1 else "61293112"
doc = extraire_rcp(telecharger_page(cis))
if doc is None:
    print("Pas de RCP trouvé sur cette page.")
    raise SystemExit

print("Titre :", doc["titre"])
print("Sections :", list(doc["sections"].keys()))

dest = DOSSIER / f"test_{cis}.txt"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text("\n".join(f"===== {k} =====\n{v}\n" for k, v in doc["sections"].items()), encoding="utf-8")
print("Enregistré :", dest)