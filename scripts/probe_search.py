"""Test : une recherche sur rcp.anpp.dz depuis Python (une seule requête de recherche)."""
import json
import requests
from bs4 import BeautifulSoup

BASE = "https://rcp.anpp.dz"
s = requests.Session()
s.headers["User-Agent"] = "PharmeazorStudentProject"

# 1) page d'accueil : jeton + snapshot
home = BeautifulSoup(s.get(BASE + "/", timeout=20).text, "lxml")
token = home.find("meta", attrs={"name": "csrf-token"})["content"]
snapshot = None
for el in home.find_all(attrs={"wire:snapshot": True}):
    if "browse-rcp" in el["wire:snapshot"]:
        snapshot = el["wire:snapshot"]
print("Snapshot de la page de recherche trouvé :", snapshot is not None)

# 2) la recherche
body = {"_token": token,
        "components": [{"snapshot": snapshot,
                        "updates": {"query": "doliprane"},
                        "calls": [{"path": "", "method": "search", "params": []}]}]}
r = s.post(BASE + "/livewire/update", data=json.dumps(body), timeout=30,
           headers={"Content-Type": "application/json", "X-Livewire": "",
                    "Accept": "*/*", "Referer": BASE + "/"})
print("Code :", r.status_code)

# 3) lecture de la réponse
try:
    html = r.json()["components"][0]["effects"]["html"] or ""
except Exception as e:
    print("Réponse inattendue :", e)
    print(r.text[:200])
    raise SystemExit
liens = [a["href"] for a in BeautifulSoup(html, "lxml").find_all("a", href=True)
         if ".pdf" in a["href"]]
print("Liens PDF trouvés :", len(liens))
for l in liens[:3]:
    print(" -", l)