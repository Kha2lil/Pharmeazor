"""Parcourt la liste des résultats du site RCP de l'ANPP avec des lettres et chiffres.
Lecture de la liste seulement : aucun PDF n'est téléchargé."""
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://rcp.anpp.dz"
ROOT = Path(__file__).resolve().parent.parent
SORTIE = ROOT / "data" / "raw" / "anpp" / "catalogue_index.json"


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


def carte(lien):
    """Texte de la plus petite carte de résultat qui contient 'Nom de Marque'."""
    bloc = lien.parent
    while bloc is not None:
        t = " ".join(bloc.get_text().split())
        if "Nom de Marque" in t:
            return t.replace("Voir le RCP", "").strip()
        bloc = bloc.parent
    return ""


MOTIF = re.compile(r"Etablissement Pharmaceutique (.*?) Nom de Marque (.*?) DCI (.*)$")

catalogue = {}  # clé = adresse du PDF (évite les doublons)
for q in list("abcdefghijklmnopqrstuvwxyz") + list("0123456789"):
    try:
        soup = chercher(q)
    except Exception as e:
        print(f"{q}: erreur ({e})")
        continue
    liens = [a for a in soup.find_all("a", href=True) if ".pdf" in a["href"]]
    nouveaux = 0
    for a in liens:
        url = urljoin(BASE, a["href"])
        if url in catalogue:
            continue
        m = MOTIF.match(carte(a))
        catalogue[url] = {
            "etablissement": m.group(1) if m else "",
            "marque": m.group(2) if m else "",
            "dci": m.group(3) if m else "",
            "url": url,
        }
        nouveaux += 1
    print(f"{q}: {len(liens)} resultats, {nouveaux} nouveaux, total {len(catalogue)}")
    time.sleep(3)

SORTIE.parent.mkdir(parents=True, exist_ok=True)
SORTIE.write_text(json.dumps(list(catalogue.values()), ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nTotal : {len(catalogue)} RCP distincts, enregistrés dans {SORTIE}")