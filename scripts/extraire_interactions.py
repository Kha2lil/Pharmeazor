"""Extrait du Thésaurus ANSM les interactions entre les 40 DCI (classes incluses, sans doublons)."""
import csv
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
TEXTE = ROOT / "data" / "raw" / "thesaurus" / "referentiel.txt"
SORTIE = ROOT / "data" / "processed" / "interactions_40.csv"

# Nos 40 DCI (mono-substance), écrites comme dans le Thésaurus, sans accents
MES_DCI = [
    "PARACETAMOL", "IBUPROFENE", "DICLOFENAC", "KETOPROFENE", "NAPROXENE",
    "ACIDE ACETYLSALICYLIQUE", "MELOXICAM", "PIROXICAM", "CELECOXIB", "TRAMADOL",
    "NEFOPAM", "AMOXICILLINE", "CEFIXIME", "CEFUROXIME", "CEFTRIAXONE",
    "AZITHROMYCINE", "CLARITHROMYCINE", "CIPROFLOXACINE", "LEVOFLOXACINE",
    "DOXYCYCLINE", "SULFAMETHOXAZOLE", "TRIMETHOPRIME", "METRONIDAZOLE",
    "GENTAMICINE", "CLINDAMYCINE", "AMLODIPINE", "NIFEDIPINE", "PERINDOPRIL",
    "RAMIPRIL", "ENALAPRIL", "LOSARTAN", "VALSARTAN", "BISOPROLOL", "ATENOLOL",
    "NEBIVOLOL", "HYDROCHLOROTHIAZIDE", "INDAPAMIDE", "SPIRONOLACTONE",
    "METHYLDOPA", "CODEINE",
]

# Lignes de niveau de contrainte (CI, ASDEC, PE, APEC, texte complet...)
NIVEAU_RE = re.compile(
    r"^(CI|ASDEC|APEC|PE|CONTRE-INDICATION|ASSOCIATION DECONSEILLEE|"
    r"PRECAUTION D'EMPLOI|A PRENDRE EN COMPTE)\b"
)


def norm(s):
    """Majuscules, sans accents, apostrophes droites, espaces simples."""
    s = s.replace("\u2019", "'")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).upper().strip()


def est_niveau(ligne):
    return NIVEAU_RE.match(norm(ligne)) is not None


def est_entete(ligne):
    """Titre de section : tout en majuscules, contient des lettres, pas un niveau ni une liste."""
    if ligne.startswith(("+", "(", "Voir")) or est_niveau(ligne):
        return False
    return any(c.isalpha() for c in ligne) and ligne == ligne.upper()


def lire(chemin):
    """Retourne (membres des classes, paires brutes (entete_a, entete_b, niveau))."""
    lignes = [l.strip() for l in chemin.read_text(encoding="utf-8").splitlines()]
    membres = {}
    paires = []
    entete = None
    n = len(lignes)
    i = 0
    while i < n:
        l = lignes[i]
        # lignes vides, numéros de page, renvois
        if not l or l.startswith("Voir") or re.fullmatch(r"\d+", l):
            i += 1
            continue
        if l.startswith("+ "):
            b = norm(l[2:])
            j = i + 1
            while j < n and not lignes[j]:
                j += 1
            if entete and j < n and est_niveau(lignes[j]):
                paires.append((entete, b, lignes[j]))
            i += 1
            continue
        if l.startswith("(") and entete:
            bloc = l
            while ")" not in bloc and i + 1 < n:
                i += 1
                bloc += " " + lignes[i]
            fin = bloc.find(")")
            contenu = bloc[1:fin] if fin != -1 else bloc[1:]
            membres[entete] = [norm(x) for x in contenu.split(",") if x.strip()]
            i += 1
            continue
        if est_entete(l):
            entete = norm(l)
        i += 1
    return membres, paires


def membres_de(nom, membres):
    """Si le titre est une classe avec liste de membres, retourne la liste ; sinon le nom seul."""
    return membres.get(nom, [nom])


def dci_de(nom):
    """Notre DCI si le nom est exactement elle, ou elle suivie d'un sel (ex. PERINDOPRIL TERT-BUTYLAMINE).
    Refuse les associations (/, +, ,) et les mots qui la contiennent (DIHYDROCODEINE)."""
    if any(c in nom for c in "/+,"):
        return None
    for d in MES_DCI:
        if nom == d or nom.startswith(d + " "):
            return d
    return None


def nos_dci(liste):
    return {x for x in (dci_de(m) for m in liste) if x}


def main():
    membres, paires = lire(TEXTE)
    # أعضاء AINS المأخوذين من الـThésaurus (قائمة الفئة كما هي في النص)
    # الكود ما قدرش يقرأها تلقائياً، فكنزيدوها يدوياً (أدويتنا فقط)
    membres["ANTI-INFLAMMATOIRES NON STEROIDIENS"] = [
        "IBUPROFENE", "DICLOFENAC", "CELECOXIB", "NAPROXENE",
        "MELOXICAM", "PIROXICAM", "KETOPROFENE",
    ]
    print(f"{len(membres)} classes avec liste de membres, {len(paires)} paires brutes lues")

    vus = set()
    sortie = []
    for a, b, niv in paires:
        ga = nos_dci(membres_de(a, membres))
        gb = nos_dci(membres_de(b, membres))
        for x in ga:
            for y in gb:
                if x == y:
                    continue
                cle = (tuple(sorted((x, y))), norm(niv))
                if cle in vus:
                    continue
                vus.add(cle)
                sortie.append((x, y, niv, a, b))

    sortie.sort(key=lambda r: (r[0], r[1]))
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with open(SORTIE, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dci_a", "dci_b", "niveau", "entete_a", "entete_b"])
        w.writerows(sortie)
    print(f"{len(sortie)} interactions uniques entre vos 40 DCI -> {SORTIE}")


if __name__ == "__main__":
    main()