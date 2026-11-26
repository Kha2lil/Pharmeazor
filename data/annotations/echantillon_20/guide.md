# Guide de vérification manuelle — 20 documents

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
