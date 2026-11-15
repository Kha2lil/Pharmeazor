"""Test : la recherche ANPP fonctionne-t-elle avec une DCI (majuscules, accents) ?"""
import json
import sys
import time
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://rcp.anpp.dz"


def chercher(requete):
    s = requests.Session()
    s.headers["User-Agent"] = "PharmeazorStudentProject"
    home = BeautifulSoup(s.get(BASE + "/", timeout=20).text, "lxml")
    token = home.find("meta", attrs={"name": "csrf-token"})["content"]
    snapshot = next(el["wire:snapshot"] for el in home.find_all(attrs={"wire:snapshot": True})
                    if "browse-rcp" in el["wire:snapshot"])
    body = {"_token": token,
            "components": [{"snapshot": snapshot, "updates": {"query": requete},
                            "calls": [{"path": "", "method": "search", "params": []}]}]}
    r = s.post(BASE + "/livewire/update", data=json.dumps(body), timeout=30,
               headers={"Content-Type": "application/json", "X-Livewire": "",
                        "Accept": "*/*", "Referer": BASE + "/"})
    html = r.json()["components"][0]["effects"]["html"] or ""
    return BeautifulSoup(html, "lxml")


def resume(lien):
    """Texte de la plus petite carte de résultat qui contient 'Nom de Marque'."""
    bloc = lien.parent
    while bloc is not None:
        t = " ".join(bloc.get_text().split())
        if "Nom de Marque" in t:
            return t.replace("Voir le RCP", "").strip()
        bloc = bloc.parent
    return "?"


for q in sys.argv[1:] or ["PARAC\u00c9TAMOL"]:
    soup = chercher(q)
    liens = [a for a in soup.find_all("a", href=True) if ".pdf" in a["href"]]
    print(f"\nRequête '{q}' : {len(liens)} liens PDF")
    for i, a in enumerate(liens, 1):
        print(f" {i}. {resume(a)}")
    time.sleep(3)