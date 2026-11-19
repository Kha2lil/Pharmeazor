"""Fonctions et chemins communs au projet BDPM (ANSM)."""
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://base-donnees-publique.medicaments.gouv.fr"
HEADERS = {"User-Agent": "PharmeazorStudentProject"}
DOSSIER = ROOT / "data" / "raw" / "bdpm"
COMPO = DOSSIER / "CIS_COMPO_bdpm.txt"
CATALOGUE = DOSSIER / "catalogue_index.json"
LISTE = ROOT / "data" / "reference" / "liste_40_medicaments.xlsx"
COLONNES = ["cis", "designation", "code_substance", "nom_substance",
            "dosage", "ref_dosage", "nature", "liaison"]


def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", norm(s).lower()).strip("_")


def lire_compo():
    return pd.read_csv(COMPO, sep="\t", header=None, names=COLONNES, usecols=range(8),
                       encoding="latin-1", dtype=str, keep_default_na=False)


def charger_catalogue():
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


def url_extrait(cis):
    return f"{BASE}/medicament/{cis}/extrait"


def telecharger_page(cis):
    r = requests.get(url_extrait(cis), headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text


def extraire_rcp(html):
    """Retourne {'titre': ..., 'sections': {'4.1': 'texte', ...}} ou None si pas de RCP."""
    soup = BeautifulSoup(html, "lxml")
    h = soup.find("h3")
    texte = soup.get_text("\n")
    debut = texte.find("Résumé des Caractéristiques du Produit")
    if debut == -1:
        return None
    fin = texte.find("Notice patient", debut)
    rcp = texte[debut: fin if fin != -1 else None]

    sections, cle, buf = {}, "intro", []
    for ligne in rcp.splitlines():
        l = ligne.strip()
        if not l:
            continue
        m = re.match(r"^(\d{1,2}(?:\.\d{1,2})?)\.?\s+([A-ZÉÈÀ].{2,})$", l)
        if m:
            sections[cle] = "\n".join(buf).strip()
            cle, buf = m.group(1), [l]
        else:
            buf.append(l)
    sections[cle] = "\n".join(buf).strip()
    return {"titre": h.get_text(" ", strip=True) if h else "", "sections": sections}

# Associations : tous les composants doivent être présents dans le même CIS
ASSOCIATIONS = {
    "paracétamol + codéine": ["PARACETAMOL", "CODEINE"],
    "amoxicilline + acide clavulanique": ["AMOXICILLINE", "CLAVULAN"],
    "cotrimoxazole (sulfaméthoxazole + triméthoprime)": ["SULFAMETHOXAZOLE", "TRIMETHOPRIME"],
}


def cis_correspondants(dci, catalogue):
    """CIS correspondant à la DCI.
    - DCI simple : le CIS contient UNE SEULE substance distincte (mono-composant)
    - association : le CIS contient exactement les composants demandés (substances distinctes)
    """
    cle = dci.strip().lower()
    if cle in ASSOCIATIONS:
        mots = ASSOCIATIONS[cle]
        return [m for m in catalogue
                if len(set(m["substances_norm"])) == len(mots)
                and all(any(mot in s for s in m["substances_norm"]) for mot in mots)]
    mot = norm(dci)
    return [m for m in catalogue
            if len(set(m["substances_norm"])) == 1 and mot in m["substances_norm"][0]]

NOTICES = ROOT / "data" / "raw" / "notices_ansm"
INDEX_NOTICES = NOTICES / "_index.csv"


def extraire_notice(html):
    """Retourne {'titre', 'texte', 'sections'} de la notice patient, ou None si absente."""
    soup = BeautifulSoup(html, "lxml")
    panel = soup.find(id="tabpanel-notice-panel")
    if panel is None:
        return None
    texte = panel.get_text("\n", strip=True)
    if len(texte) < 200:
        return None
    h = soup.find("h3")
    sections, cle, buf = {}, "intro", []
    for ligne in texte.splitlines():
        m = re.match(r"^(\d{1,2})\.\s+(.{5,})$", ligne)
        if m:
            sections[cle] = "\n".join(buf).strip()
            cle, buf = m.group(1), [ligne]
        else:
            buf.append(ligne)
    sections[cle] = "\n".join(buf).strip()
    return {"titre": h.get_text(" ", strip=True) if h else "",
            "texte": texte, "sections": sections}