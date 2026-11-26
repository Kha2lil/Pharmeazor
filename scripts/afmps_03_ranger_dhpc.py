"""AFMPS (Belgique) : range les DHPC (communications aux professionnels de santé) téléchargées à la main
dans un dossier par DCI de la liste, puis les enregistre dans documents.csv (source « afmps_dhpc »).
Classement sur tout le texte : une DCI est retenue si elle apparaît au moins SEUIL fois (nom de fichier compris).
Une DHPC qui concerne plusieurs DCI de la liste va dans _multi_dci/ (enregistrée une seule fois).
Rejouable, sans doublons."""
import hashlib
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import pymupdf as fitz

from src.collecte.provenance import register

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DOSSIER_RCP = ROOT / "data" / "raw" / "afmps"
DOSSIER = DOSSIER_RCP / "afmps_dhpc"
VRAC = DOSSIER / "_vrac"
A_VERIFIER = DOSSIER / "_a_verifier"
MULTI = DOSSIER / "_multi_dci"
BASE_URL = "https://medicinesdatabase.be"
SOURCE = "afmps_dhpc"
SEUIL = 3       # occurrences minimales pour dire qu'une DCI est le sujet de la DHPC
TETE = 3000     # début du texte utilisé pour reconnaître la langue et le type de document

COMBOS = {
    "PARACETAMOL + CODEINE": ["PARACETAMOL", "CODEINE"],
    "AMOXICILLINE + ACIDE CLAVULANIQUE": ["AMOXICILLINE", "CLAVULAN"],
    "COTRIMOXAZOLE (SULFAMETHOXAZOLE + TRIMETHOPRIME)": ["SULFAMETHOXAZOLE", "TRIMETHOPRIM"],
}
RACINES = {"ACIDE ACETYLSALICYLIQUE": "ACETYLSALICYLIQUE"}

# DHPC qui citent seulement une classe : terme -> DCI de la liste concernées (à compléter si besoin)
CLASSES = {
    "FLUOROQUINOLON": ["CIPROFLOXACINE", "LEVOFLOXACINE"],
    "MACROLIDE": ["AZITHROMYCINE", "CLARITHROMYCINE"],
}


def norm(s):
    s = unicodedata.normalize("NFD", str(s).replace("’", "'"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", norm(s).lower()).strip("_")


def raccourcir_noms():
    """Windows limite les chemins à ~260 caractères : on raccourcit les noms trop longs dans _vrac."""
    for f in list(VRAC.glob("*.pdf")):
        if len(str(f)) < 200:
            continue
        base = re.sub(r"[^\w\-]+", "_", f.stem)
        court = f"{base[:40].strip('_')}_{base[-40:].strip('_')}_{hashlib.sha1(f.name.encode()).hexdigest()[:6]}.pdf"
        src, dst = str(f), str(f.with_name(court))
        if os.name == "nt":                      # préfixe « chemin long » de Windows
            src, dst = "\\\\?\\" + src, "\\\\?\\" + dst
        os.rename(src, dst)
        print(f"~   nom raccourci : {f.name[:50]}... -> {court}")


def lire(pdf):
    """Retourne (texte complet normalisé, type de document, néerlandais ?, n° AMM éventuel)."""
    with fitz.open(pdf) as doc:
        brut = " ".join(page.get_text() for page in doc)
    t = norm(re.sub(r"\s+", " ", brut))
    amm = re.search(r"\bBE\d{6,7}\b", t)
    if "RESUME DES CARACTERISTIQUES DU PRODUIT" in t[:800]:
        type_doc = "RCP"
    elif t[:400].lstrip().startswith("NOTICE") or "NOTICE : INFORMATION" in t[:600]:
        type_doc = "NOTICE"
    else:
        type_doc = "AUTRE"
    neerlandais = any(m in t[:TETE] for m in ("GEZONDHEIDSZORG", "GENEESMIDDEL", "GESCHATTE", "BELANGRIJKE"))
    return t, type_doc, neerlandais, (amm.group(0) if amm else "")


liste = pd.read_excel(ROOT / "data" / "reference" / "liste_40_medicaments.xlsx", sheet_name="Médicaments")
DCIS = list(liste["DCI (nom de la substance)"])
SLUGS = {slug(d): d for d in DCIS}
NORM2DCI = {norm(d): d for d in DCIS}
SIMPLES = {d: RACINES.get(norm(d), norm(d)) for d in DCIS if norm(d) not in COMBOS}
ASSOCS = {d: COMBOS[norm(d)] for d in DCIS if norm(d) in COMBOS}


def dcis_du_document(t, nom):
    """Retourne {DCI de la liste: nombre d'occurrences}, en ignorant les mentions isolées."""
    compte = {}
    for d, r in SIMPLES.items():
        c = t.count(r) + (SEUIL if r in nom else 0)
        if c >= SEUIL:
            compte[d] = c
    for d, racines in ASSOCS.items():
        cs = [t.count(x) + (SEUIL if x in nom else 0) for x in racines]
        if min(cs) >= SEUIL:
            compte[d] = min(cs)
            for s, r in SIMPLES.items():         # les composants de l'association ne comptent pas à part
                if any(r in x or x in r for x in racines):
                    compte.pop(s, None)
    if not compte:                               # aucune DCI nommée : on regarde les termes de classe
        for terme, noms in CLASSES.items():
            if terme in t or terme in nom:
                for n in noms:
                    d = NORM2DCI.get(n)
                    if d:
                        compte[d] = t.count(terme)
    return compte


def classer(t, nom, type_doc, neerlandais):
    """Retourne (compte, raison). compte = None si la DHPC est à vérifier."""
    if type_doc == "RCP":
        return None, "c'est un RCP (à ranger avec le script RCP)"
    if type_doc == "NOTICE":
        return None, "c'est une notice (à ranger avec le script notices)"
    if neerlandais:
        return None, "document en néerlandais"
    if len(t) < 200:
        return None, "peu de texte (PDF scanné ?)"
    compte = dcis_du_document(t, nom)
    if not compte:
        return None, "aucune DCI de la liste (ni terme de classe)"
    return compte, ""


VRAC.mkdir(parents=True, exist_ok=True)
A_VERIFIER.mkdir(parents=True, exist_ok=True)
MULTI.mkdir(parents=True, exist_ok=True)

raccourcir_noms()
ranges = refuses = multi = nouveaux = doublons = 0

# 1) fichiers en vrac : classement puis déplacement
for f in sorted(VRAC.glob("*.pdf")):
    try:
        t, type_doc, neerlandais, amm = lire(f)
        compte, raison = classer(t, norm(f.stem), type_doc, neerlandais)
    except Exception as e:
        print(f"ERR {f.name[:80]} : {e}")
        continue
    if compte is None:
        shutil.move(str(f), str(A_VERIFIER / f.name))
        print(f"?   {f.name[:80]} -> _a_verifier ({raison})")
        refuses += 1
        continue
    detail = ", ".join(f"{d} ({n})" for d, n in sorted(compte.items(), key=lambda x: -x[1]))
    if len(compte) == 1:
        dci = next(iter(compte))
        dest = DOSSIER / slug(dci) / f.name
        cible = slug(dci)
    else:
        dest = MULTI / f.name
        cible = "_multi_dci"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"=   {f.name[:80]} existe déjà dans {cible}, ignoré")
        continue
    shutil.move(str(f), str(dest))
    ranges += 1
    multi += cible == "_multi_dci"
    print(f"->  {f.name[:80]} -> {cible} | {detail}")

# 2) enregistrement de toutes les DHPC rangées (rejouable : register ignore les doublons)
for dossier in sorted(p for p in DOSSIER.iterdir() if p.is_dir() and not p.name.startswith("_")):
    dci = SLUGS.get(dossier.name)
    if dci is None:
        print(f"Dossier inconnu (pas dans la liste) : {dossier.name}")
        continue
    for pdf in sorted(dossier.glob("*.pdf")):
        try:
            amm = lire(pdf)[3]
        except Exception:
            amm = ""
        url = BASE_URL + (f"#AMM={amm}" if amm else "")
        if register(dci, SOURCE, url, "fr", pdf):
            nouveaux += 1
            print(f"OK  {dci} | {pdf.name[:80]}")
        else:
            doublons += 1

# 3) DHPC multi-DCI : enregistrées une seule fois, médicament = DCI séparées par « ; »
for pdf in sorted(MULTI.glob("*.pdf")):
    try:
        t, _, _, amm = lire(pdf)
        noms = " ; ".join(sorted(dcis_du_document(t, norm(pdf.stem)))) or "multi_dci"
    except Exception:
        noms, amm = "multi_dci", ""
    url = BASE_URL + (f"#AMM={amm}" if amm else "")
    if register(noms, SOURCE, url, "fr", pdf):
        nouveaux += 1
        print(f"OK  [{noms}] | {pdf.name[:80]}")
    else:
        doublons += 1

print(f"\nRangés : {ranges} (dont multi-DCI : {multi}) | enregistrés : {nouveaux} "
      f"| déjà enregistrés/doublons : {doublons} | à vérifier : {refuses}")

avec = [d for d in DCIS if list((DOSSIER / slug(d)).glob("*.pdf"))]
print(f"\nDCI avec au moins une DHPC dédiée : {len(avec)}/{len(DCIS)} "
      f"(normal qu'il y en ait peu ; voir aussi _multi_dci)")
for d in avec:
    print(" -", d)