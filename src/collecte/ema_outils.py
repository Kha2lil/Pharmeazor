"""Fonctions et chemins communs au projet EMA."""
import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DOSSIER = ROOT / "data" / "raw" / "ema"
FICHIER = DOSSIER / "medicines.xlsx"
LISTE = ROOT / "data" / "reference" / "liste_40_medicaments.xlsx"
HEADERS = {"User-Agent": "PharmeazorStudentProject"}

# Traduction des DCI de la liste (français -> anglais, comme dans EMA)
TRADUCTION = {
    "paracétamol": "paracetamol",
    "ibuprofène": "ibuprofen",
    "diclofénac": "diclofenac",
    "kétoprofène": "ketoprofen",
    "naproxène": "naproxen",
    "acide acétylsalicylique": "acetylsalicylic acid",
    "méloxicam": "meloxicam",
    "piroxicam": "piroxicam",
    "célécoxib": "celecoxib",
    "tramadol": "tramadol",
    "néfopam": "nefopam",
    "amoxicilline": "amoxicillin",
    "céfixime": "cefixime",
    "céfuroxime": "cefuroxime",
    "ceftriaxone": "ceftriaxone",
    "azithromycine": "azithromycin",
    "clarithromycine": "clarithromycin",
    "ciprofloxacine": "ciprofloxacin",
    "lévofloxacine": "levofloxacin",
    "doxycycline": "doxycycline",
    "métronidazole": "metronidazole",
    "gentamicine": "gentamicin",
    "clindamycine": "clindamycin",
    "amlodipine": "amlodipine",
    "nifédipine": "nifedipine",
    "périndopril": "perindopril",
    "ramipril": "ramipril",
    "énalapril": "enalapril",
    "losartan": "losartan",
    "valsartan": "valsartan",
    "bisoprolol": "bisoprolol",
    "aténolol": "atenolol",
    "nébivolol": "nebivolol",
    "hydrochlorothiazide": "hydrochlorothiazide",
    "indapamide": "indapamide",
    "spironolactone": "spironolactone",
    "méthyldopa": "methyldopa",
}

# Associations : liste des composants en anglais
ASSOCIATIONS = {
    "paracétamol + codéine": ["paracetamol", "codeine"],
    "amoxicilline + acide clavulanique": ["amoxicillin", "clavulanic acid"],
    "cotrimoxazole (sulfaméthoxazole + triméthoprime)": ["sulfamethoxazole", "trimethoprim"],
}


def slug(s):
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def composants(dci):
    cle = dci.strip().lower()
    if cle in ASSOCIATIONS:
        return ASSOCIATIONS[cle]
    return [TRADUCTION[cle]]


def charger_medicaments():
    """Lit le fichier EMA (en-tête à la ligne 9) : seulement humains et autorisés."""
    df = pd.read_excel(FICHIER, sheet_name="Medicine", header=8)
    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]
    return df[(df["Category"] == "Human") & (df["Medicine status"] == "Authorised")]


def correspond(dci, df):
    """Lignes dont les substances actives correspondent exactement aux composants de la DCI.
    Les sels (ex. 'amoxicillin trihydrate') sont acceptés grâce à startswith."""
    mots = composants(dci)

    def ok(sub):
        parts = [p.strip().lower() for p in str(sub).split(";") if p.strip()]
        if len(parts) != len(mots):
            return False
        return all(any(p.startswith(m) for p in parts) for m in mots)

    return df[df["Active substance"].apply(ok)]


def liens_pdf(url):
    """Retourne la liste (texte, adresse) des liens PDF d'une fiche EMA."""
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    liens = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower():
            if href.startswith("/"):
                href = "https://www.ema.europa.eu" + href
            liens.append((a.get_text(" ", strip=True), href))
    return liens


def lien_notice(url):
    """Choisit le PDF 'Product information' en anglais (_en.pdf) parmi les liens de la fiche."""
    liens = liens_pdf(url)
    for _, href in liens:
        h = href.lower()
        if "product-information" in h and h.endswith("_en.pdf"):
            return href
    for _, href in liens:
        if "product-information" in href.lower():
            return href
    return None