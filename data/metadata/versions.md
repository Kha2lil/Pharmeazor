# Versions des sources — Pharmeazor

Document de traçabilité. Chaque source ci-dessous est versionnée par sa date de collecte (colonne `date_collecte` / `source_version` de `documents.csv`).

## Nomenclature algérienne (MIPH)

- **Fichier** : `Projet2_Liste_40_medicaments_verifie (1).xlsx` (feuille `Détail nomenclature`)
- **Version** : Nomenclature nationale des produits pharmaceutiques, usage médecine humaine, au **31/08/2026**
- **Source officielle** : Ministère de l'Industrie pharmaceutique (MIPH)
- **Feuilles** : `Active (31/08/2026)` (718 présentations), `Retraits` (657), `Non renouvelés` (304)
- **Médicaments** : 38/40 présents (oui), 2 à vérifier (nifédipine, hydrochlorothiazide)
- **Marques actives** : 470 distinctes sur 38 DCI

## BDPM (RCP français)

- **Version des RCP** : "Mis à jour le 01/09/2026" (mentionnée dans les documents)
- **Collecte** : 2026-11-15
- **Documents** : 1 291 RCP (1 par spécialité)
- **Autorité** : 3 (source étrangère)

## ANPP (RCP algériens)

- **Collecte** : 2026-11-15
- **Documents** : 41 RCP pour 13 médicaments sur 40
- **Autorité** : 1 (source nationale officielle)
- **Lacune** : 27 médicaments sans RCP ANPP → à compléter ou remplacer par la nomenclature

## Thésaurus des interactions (ANSM)

- **Version** : Thésaurus des interactions médicamenteuses, édition septembre 2023 (PDF publié 2024-06-07)
- **Collecte** : 2026-11-15
- **Documents** : 3 (référentiel + index substances + index classes)
- **Autorité** : 3

## DailyMed (RCP américains)

- **Collecte** : 2026-11-15
- **Documents** : 190 RCP
- **Autorité** : 3

## EMA

- **Collecte** : 2026-11-15
- **Documents** : 2
- **Autorité** : 3

## Règle de versioning

- `date_collecte` = date à laquelle le document a été téléchargé (version disponible localement).
- `source_version` = identifiant de version de la source (date de publication officielle si connue, sinon date de collecte).
- En cas de re-collecte, le `sha256` change → le document est considéré comme une **nouvelle version**, l'ancienne est conservée (collecte rejouable, pas d'écrasement).
- Les désaccords entre versions sont tracés dans `data/annotations/desaccords.csv`.
