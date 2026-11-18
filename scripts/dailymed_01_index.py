"""Catalogue DailyMed : recherche par DCI, arrêt dès que GARDER fiches valides (substance unique).
Cache par page, reprise possible. Le filtre est sur le titre (approximatif) : voir ecartes_a_verifier.json."""
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DOSSIER = ROOT / "data" / "raw" / "dailymed"
SORTIE = DOSSIER / "catalogue_index.json"
ECARTES = DOSSIER / "ecartes_a_verifier.json"
BRUT = DOSSIER / "brut"
API = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
HEADERS = {"User-Agent": "PharmeazorStudentProject"}

TEST = None       # nombre de médicaments pour un test ; None = tous
GARDER = 10     # fiches valides à garder par DCI (le téléchargement en prendra MAX_PAR_DCI)
MAX_PAGES = 10  # sécurité : pages max parcourues par DCI

ALIAS = {
    "PARACETAMOL": "ACETAMINOPHEN",
    "IBUPROFENE": "IBUPROFEN",
    "KETOPROFENE": "KETOPROFEN",
    "NAPROXENE": "NAPROXEN",
    "ACIDE ACETYLSALICYLIQUE": "ASPIRIN",
    "PARACETAMOL + CODEINE": "ACETAMINOPHEN AND CODEINE",
    "AMOXICILLINE": "AMOXICILLIN",
    "AMOXICILLINE + ACIDE CLAVULANIQUE": "AMOXICILLIN AND CLAVULANATE",
    "AZITHROMYCINE": "AZITHROMYCIN",
    "CLARITHROMYCINE": "CLARITHROMYCIN",
    "CIPROFLOXACINE": "CIPROFLOXACIN",
    "LEVOFLOXACINE": "LEVOFLOXACIN",
    "COTRIMOXAZOLE (SULFAMETHOXAZOLE + TRIMETHOPRIME)": "SULFAMETHOXAZOLE AND TRIMETHOPRIM",
    "GENTAMICINE": "GENTAMICIN",
    "CLINDAMYCINE": "CLINDAMYCIN",
    "PERINDOPRIL": "PERINDOPRIL ERBUMINE",
    "BISOPROLOL": "BISOPROLOL FUMARATE",
    "NEFOPAM": "NEFOPAM",
}

# DCI de la liste qui sont elles-mêmes des associations : on accepte alors plusieurs substances
ASSOCIATIONS_LISTE = {"PARACETAMOL + CODEINE",
                      "AMOXICILLINE + ACIDE CLAVULANIQUE",
                      "COTRIMOXAZOLE (SULFAMETHOXAZOLE + TRIMETHOPRIME)"}

# mots du titre qui ne sont PAS une autre substance (forme, voie, sel, emballage, etc.)
MOTS_NEUTRES = set("""
TABLET TABLETS CAPSULE CAPSULES FILM COATED EXTENDED RELEASE DELAYED ORALLY DISINTEGRATING CHEWABLE
INJECTION INJECTABLE SOLUTION ORAL SUSPENSION POWDER FOR GEL CREAM OINTMENT PATCH SPRAY LIQUID FILLED
SYRUP TOPICAL OPHTHALMIC OTIC INTRAVENOUS IN DEXTROSE SODIUM CHLORIDE WATER VIAL BAG USP MG ML MCG G
HYDROCHLORIDE HCL HCI POTASSIUM CALCIUM MALEATE FUMARATE ERBUMINE AXETIL HYCLATE
MONOHYDRATE TRIHYDRATE ANHYDROUS SUCCINATE TARTRATE BESYLATE MESYLATE SULFATE PHOSPHATE ACETATE
CITRATE EPOLAMINE DIETHYLAMINE EXTRA STRENGTH REGULAR PAIN RELIEVER RELIEF FEVER REDUCER ADULT
CHILDRENS CHILDREN INFANTS JUNIOR CAPLETS GELCAPS CAPLET GELCAP GELS SOFTGELS SOFTGEL
THE OF AND ER SR XR CR DR ODT PLUS
""".split())

# distributeurs / reconditionneurs / marques de magasin (fiches OTC répétées, peu utiles)
DISTRIBUTEURS = re.compile(
    r"WALGREEN|CVS|WALMART|EQUATE|KROGER|TARGET|RITE AID|MEIJER|PUBLIX|SAFEWAY|MCKESSON|"
    r"MAJOR PHARM|GOOD NEIGHBOR|LEADER|SUNMARK|QUALITY CHOICE|BRYANT RANCH|PROFICIENT RX|"
    r"A-S MEDICATION|NUCARE|DIRECT[ _]?RX|REMEDYREPACK|PREFERRED PHARMACEUTICALS|QPHARMA|"
    r"PD-RX|RPK|ASCEND|ALTURA|MEDSOURCE|LAKE ERIE|ST\. MARY|H\.J\. HARKINS|NORTHWIND|"
    r"ASPEN|AIDAREX|COUPLER|UNIT DOSE SERVICES|AMERICAN HEALTH PACKAGING|CARDINAL|"
    r"MEDVANTX|CLINICAL SOLUTIONS|HENRY SCHEIN|DISPENSING SOLUTIONS|BLENHEIM|"
    r"NATIONAL VITAMIN|TOP CARE|TOPCARE|H[ -]?E[ -]?B\b|UP & UP|UP AND UP|MEDLINE|BLUE POINT|"
    r"DISCOUNT DRUG|HARRIS TEETER|DEMOULAS|MARC GLASSMAN|CHAIN DRUG|AMAZON|"
    r"AAA PHARMACEUTICAL|TOPCO|CABINET HEALTH|PERRIGO|GOOD ?SENSE|GOODMEDS|ASCLEMED|"
    r"PLD ACQUISITIONS|AVEMA|AV&EACUTE;MA")


def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", norm(s).lower()).strip("_")


def get_json(params, essais=4):
    for i in range(1, essais + 1):
        try:
            r = requests.get(API, params=params, headers=HEADERS, timeout=(15, 60))
            r.raise_for_status()
            return r.json()
        except (requests.Timeout, requests.ConnectionError):
            if i == essais:
                raise
            print(f"   timeout, nouvel essai dans {5 * i}s", flush=True)
            time.sleep(5 * i)


def page_cachee(nom, page):
    """Une page de résultats, mise en cache sur disque."""
    f = BRUT / slug(nom) / f"p{page:03d}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    j = get_json({"drug_name": nom, "pagesize": 100, "page": page})
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    time.sleep(1)
    return j


def titre_valide(titre, nom, est_association):
    """Titre DailyMed : 'NOM (SUBSTANCE) FORME [FABRICANT]'. Retourne (ok, raison).
    On juge sur la substance entre parenthèses, et on écarte les distributeurs."""
    m_fab = re.search(r"\[(.*?)\]\s*$", titre)
    fabricant = norm(m_fab.group(1)) if m_fab else ""
    avant_crochet = norm(titre.split("[")[0])
    if DISTRIBUTEURS.search(fabricant) or DISTRIBUTEURS.search(avant_crochet):
        return False, "distributeur"

    t = norm(re.sub(r"\[.*?\]", " ", titre))
    base = norm(nom)

    # --- DCI qui est elle-même une association : toutes les substances doivent apparaître ---
    if est_association:
        parties = [p.split()[0] for p in base.split(" AND ")]
        manquantes = [p for p in parties if p not in t]
        if manquantes:
            return False, "substance absente : " + " ".join(manquantes)
        return True, ""

    base_mots = set(base.split())

    # --- cas courant : 'NOM (SUBSTANCE) FORME' ---
    m = re.search(r"\((.*?)\)", t)
    if m:
        subst = m.group(1)
        if not base_mots & set(re.sub(r"[^A-Z0-9 ]", " ", subst).split()):
            return False, "substance absente"
        if re.search(r"\bAND\b|,|/|\+|&", subst):
            return False, "association : " + subst[:40]
        autres = set(re.sub(r"[^A-Z0-9 ]", " ", subst).split()) - MOTS_NEUTRES - base_mots
        autres = {w for w in autres if not re.fullmatch(r"\d+[A-Z]*", w)}
        if autres:
            return False, "autre substance : " + " ".join(sorted(autres))[:40]
        return True, ""

    # --- pas de parenthèses : le titre EST le nom générique, règle stricte ---
    mots = re.sub(r"[^A-Z0-9 ]", " ", t).split()
    if not base_mots & set(mots):
        return False, "substance absente"
    restes = [w for w in mots if w not in base_mots and w not in MOTS_NEUTRES and not re.fullmatch(r"\d+[A-Z]*", w)]
    if restes:
        return False, "mots en plus : " + " ".join(restes[:4])
    return True, ""


liste = pd.read_excel(ROOT / "data" / "reference" / "liste_40_medicaments.xlsx", sheet_name="Médicaments")
if TEST:
    liste = liste.head(TEST)

catalogue, ecartes = {}, []
for _, row in liste.iterrows():
    dci_fr = row["DCI (nom de la substance)"]
    cle = norm(dci_fr)
    nom = norm(ALIAS.get(cle, dci_fr))
    est_assoc = cle in ASSOCIATIONS_LISTE
    print(f"{dci_fr} ({nom})", flush=True)

    gardes, vus = 0, 0
    page, total = 1, 1
    try:
        while page <= min(total, MAX_PAGES) and gardes < GARDER:
            j = page_cachee(nom, page)
            total = j.get("metadata", {}).get("total_pages", 1)
            data = sorted(j.get("data", []), key=lambda p: p.get("published_date") or "", reverse=True)
            for p in data:
                vus += 1
                if p["setid"] in catalogue:
                    continue
                ok, raison = titre_valide(p["title"], nom, est_assoc)
                if ok and gardes < GARDER:
                    catalogue[p["setid"]] = {
                        "dci_liste": dci_fr, "dci_en": nom, "setid": p["setid"],
                        "titre": p["title"], "version": p.get("spl_version"),
                        "date": p.get("published_date"),
                        "url_pdf": f"https://dailymed.nlm.nih.gov/dailymed/downloadpdffile.cfm?setId={p['setid']}",
                        "url_xml": f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{p['setid']}.xml",
                    }
                    gardes += 1
                elif not ok:
                    ecartes.append({"dci_liste": dci_fr, "setid": p["setid"], "titre": p["title"], "raison": raison})
            print(f"   page {page}/{total} | gardés {gardes}/{GARDER}", flush=True)
            page += 1
    except Exception as e:
        print(f"ERR {dci_fr} : {e}")
    print(f"   => {gardes} gardées sur {vus} vues", flush=True)

DOSSIER.mkdir(parents=True, exist_ok=True)
SORTIE.write_text(json.dumps(list(catalogue.values()), ensure_ascii=False, indent=1), encoding="utf-8")
ECARTES.write_text(json.dumps(ecartes, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nTotal : {len(catalogue)} fiches dans {SORTIE}")
print(f"Écartés : {len(ecartes)} dans {ECARTES}")