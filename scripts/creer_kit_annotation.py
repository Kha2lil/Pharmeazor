"""F2 - Kit papier pour la vérification manuelle de 20 documents.

Tirage stratié reproductible (graine 20261126) : 5 ANSM, 5 AFMPS,
5 ANPP, 5 DailyMed, un document par DCI distincte.

Produit :
    data/annotations/echantillon_20/fiche_annotation.csv   (80 lignes vides)
    data/annotations/echantillon_20/textes_numerotes/{doc_id}.txt
    data/annotations/echantillon_20/guide.md

Les positions sont notées en NUMÉROS DE LIGNE par la personne qui vérifie :
c'est plus lisible que des positions en caractères. La conversion en
positions caractères se fait ensuite automatiquement à partir du texte original.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from src.config import ROOT

MANIFEST = ROOT / "data" / "metadata" / "documents.csv"
TEXTES = ROOT / "data" / "processed" / "textes"
KIT = ROOT / "data" / "annotations" / "echantillon_20"
NUMEROTES = KIT / "textes_numerotes"
FICHE = KIT / "fiche_annotation.csv"
GRAINE = 20261126
PLAN = (
    ("ansm_notice", "ANSM notice"),
    ("afmps_notice", "AFMPS leaflet"),
    ("anpp", "ANPP RCP"),
    ("dailymed", "DailyMed"),
)
PARTIES = ("Indications", "Contre-indications", "Posologie", "Interactions")
CHAMPS = [
    "ordre", "doc_id", "medicament", "source", "rubrique",
    "trouve", "ligne_debut", "ligne_fin",
]

GUIDE = """# Guide de vérification manuelle — 20 documents

## Ce qu'il faut faire

Pour chacun des 20 documents, trouver **4 parties** et noter **entre quelles
lignes** elles se trouvent. Ouvrez le fichier `textes_numerotes/<doc_id>.txt` :
chaque ligne commence par son numéro (`00012 | ...`).

| Partie | Question |
| --- | --- |
| Indications | À quoi sert le médicament ? |
| Contre-indications | Quand ne faut-il pas le prendre ? |
| Posologie | Combien, et combien de fois ? |
| Interactions | Avec quels autres médicaments est-ce dangereux ? |

## Ce qu'il faut écrire

Pour chaque partie, **deux nombres** :

- **ligne_debut** = la ligne du **titre** de la partie ;
- **ligne_fin** = la ligne **juste avant le titre suivant**.

Si la partie n'existe pas, écrivez **absent** dans `trouve` et laissez les
deux lignes vides.

### Exemple

```
00012 | 4.1. Indications thérapeutiques
00013 | Traitement symptomatique des douleurs légères à modérées...
00014 |
00015 | 4.2. Posologie et mode d'administration
```

→ `Indications` : ligne_debut = **12**, ligne_fin = **14**.

## Les 4 règles

1. Le **début** est toujours la ligne du **titre**, pas la phrase après.
2. La **fin** est la ligne juste avant le titre suivant, même si le sujet change.
3. **Ignorez le sommaire** au début des notices : les mêmes titres y sont
   répétés. Prenez la **vraie section**, plus loin dans le document.
4. **Ne devinez pas.** Si vous ne trouvez pas, écrivez `absent`.
   Ne recopiez pas le texte.

## Noms de titres selon la source

| Source | Titres à chercher |
| --- | --- |
| ANSM / AFMPS (fr) | `1. QU'EST-CE QUE ... ET DANS QUELS CAS ... ?`, `2. QUELLES SONT LES INFORMATIONS ... AVANT DE PRENDRE ... ?`, `3. COMMENT PRENDRE ... ?`, `Autres médicaments et ...` |
| ANPP (fr) | `4.1. Indications thérapeutiques`, `4.2. Posologie`, `4.3. Contre-indications`, `4.5. Interactions ...` |
| DailyMed (en) | `Indications and Usage`, `Contraindications`, `Dosage and Administration`, `Drug Interactions` |

## Ce qu'il faut rendre

Le fichier `fiche_annotation.csv` rempli (80 lignes), ou une feuille papier
avec les mêmes informations.

---

## بالعربية — تعليمات مختصرة

لكل وثيقة من 20، حدد **رقم السطر** الذي يبدأ فيه عنوان كل قسم، ورقم السطر
الذي يسبق العنوان التالي. الأقسام الأربعة: الدواعي، موانع الاستعمال،
الجرعة، التفاعلات. إذا لم يوجد القسم اكتب `absent`. تجاهل فهرس المحتوى
في بداية النشرة؛ خذ القسم الحقيقي في الداخل. لا تنسخ النص ولا تخمن.
"""


def selectionner(documents: list[dict]) -> list[dict]:
    rng = random.Random(GRAINE)
    resultat: list[dict] = []
    for source, _ in PLAN:
        par_dci: dict[str, list[dict]] = defaultdict(list)
        for d in documents:
            if d["source"] == source:
                par_dci[d["medicament"]].append(d)
        dci_choisies = rng.sample(sorted(par_dci), min(5, len(par_dci)))
        for dci in dci_choisies:
            resultat.append(sorted(par_dci[dci], key=lambda d: d["doc_id"])[0])
    return resultat


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="vérifier le kit sans l'écrire")
    args = ap.parse_args()

    with open(MANIFEST, encoding="utf-8", newline="") as f:
        documents = list(csv.DictReader(f))
    echantillon = selectionner(documents)

    if args.verify:
        print(f"Échantillon : {len(echantillon)} documents")
        for d in echantillon:
            p = TEXTES / f"{d['doc_id']}.txt"
            print(f"  {d['doc_id']} {d['source']:12} {d['medicament'][:22]:22} "
                  f"{'OK' if p.is_file() else 'MANQUANT'}")
        return

    NUMEROTES.mkdir(parents=True, exist_ok=True)
    for d in echantillon:
        texte = (TEXTES / f"{d['doc_id']}.txt").read_text(encoding="utf-8")
        lignes = [f"{i:05d} | {ligne}" for i, ligne in enumerate(texte.split("\n"), 1)]
        (NUMEROTES / f"{d['doc_id']}.txt").write_text(
            "\n".join(lignes), encoding="utf-8"
        )

    with open(FICHE, "w", encoding="utf-8-sig", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=CHAMPS)
        ecrivain.writeheader()
        for i, d in enumerate(echantillon, 1):
            for partie in PARTIES:
                ecrivain.writerow({
                    "ordre": i,
                    "doc_id": d["doc_id"],
                    "medicament": d["medicament"],
                    "source": d["source"],
                    "rubrique": partie,
                    "trouve": "",
                    "ligne_debut": "",
                    "ligne_fin": "",
                })

    (KIT / "guide.md").write_text(GUIDE, encoding="utf-8")
    print(f"Kit écrit : {KIT.relative_to(ROOT)}")
    print(f"  {len(echantillon)} textes numérotés, {len(echantillon) * len(PARTIES)} lignes à remplir")


if __name__ == "__main__":
    main()
