# Documentation – Collecte manuelle des RCP depuis l'ANPP

## 1. Objectif

Cette documentation décrit la collecte des Résumés des Caractéristiques du Produit (RCP) depuis le portail de l'ANPP. Conformément aux nouvelles consignes du projet, cette collecte est désormais effectuée **manuellement**.

## 2. Arrêt de la collecte automatique

- La collecte automatique des documents RCP depuis l'ANPP est **définitivement abandonnée**.
- Le script dédié à cette collecte a été **supprimé du projet**.
- Aucune nouvelle collecte automatique ne sera effectuée depuis cette source.
- Les documents déjà collectés depuis l'ANPP (41 documents) et leurs métadonnées sont **conservés**.

## 3. Procédure de collecte manuelle

1. Accéder au portail officiel de l'ANPP.
2. Rechercher le médicament par sa DCI.
3. Vérifier la disponibilité du document RCP.
4. Télécharger manuellement le document lorsqu'il est disponible.
5. Enregistrer le document dans le répertoire du projet prévu pour la source ANPP (`data/raw/anpp/<médicament>/`).
6. Enregistrer ses métadonnées et sa provenance dans le fichier de métadonnées du projet.

## 4. Traçabilité

Chaque document collecté est décrit par une ligne du fichier de métadonnées, qui conserve notamment :

- la **source** (`source`) ;
- l'**URL** d'origine (`url`) ;
- la **date de collecte** (`date_collecte`) ;
- la langue (`langue`), le chemin du fichier (`chemin`) et son empreinte (`sha256`).

## 5. Gestion des documents absents

Pour **27 médicaments**, aucun RCP n'est disponible sur le portail de l'ANPP.

- **Date de vérification :** 2026-11-15.
- **Recherche effectuée :** recherche par la DCI sur le portail de l'ANPP ; le médicament n'y a pas été trouvé.
- **Statut enregistré**, avec cette orthographe exacte :

```
RCP ANPP absent
```

- Ces documents ne sont **ni inventés, ni remplacés** par des documents provenant d'autres sources sous l'identité de l'ANPP.

| # | Médicament | Statut | Date de vérification |
|---|------------|--------|----------------------|
| 1 | amoxicilline | RCP ANPP absent | 2026-11-15 |
| 2 | amoxicilline + acide clavulanique | RCP ANPP absent | 2026-11-15 |
| 3 | aténolol | RCP ANPP absent | 2026-11-15 |
| 4 | azithromycine | RCP ANPP absent | 2026-11-15 |
| 5 | ceftriaxone | RCP ANPP absent | 2026-11-15 |
| 6 | clarithromycine | RCP ANPP absent | 2026-11-15 |
| 7 | clindamycine | RCP ANPP absent | 2026-11-15 |
| 8 | cotrimoxazole (sulfaméthoxazole + triméthoprime) | RCP ANPP absent | 2026-11-15 |
| 9 | céfixime | RCP ANPP absent | 2026-11-15 |
| 10 | céfuroxime | RCP ANPP absent | 2026-11-15 |
| 11 | doxycycline | RCP ANPP absent | 2026-11-15 |
| 12 | gentamicine | RCP ANPP absent | 2026-11-15 |
| 13 | indapamide | RCP ANPP absent | 2026-11-15 |
| 14 | lévofloxacine | RCP ANPP absent | 2026-11-15 |
| 15 | méloxicam | RCP ANPP absent | 2026-11-15 |
| 16 | méthyldopa | RCP ANPP absent | 2026-11-15 |
| 17 | naproxène | RCP ANPP absent | 2026-11-15 |
| 18 | nifédipine | RCP ANPP absent | 2026-11-15 |
| 19 | nébivolol | RCP ANPP absent | 2026-11-15 |
| 20 | néfopam | RCP ANPP absent | 2026-11-15 |
| 21 | paracétamol + codéine | RCP ANPP absent | 2026-11-15 |
| 22 | périndopril | RCP ANPP absent | 2026-11-15 |
| 23 | ramipril | RCP ANPP absent | 2026-11-15 |
| 24 | spironolactone | RCP ANPP absent | 2026-11-15 |
| 25 | tramadol | RCP ANPP absent | 2026-11-15 |
| 26 | valsartan | RCP ANPP absent | 2026-11-15 |
| 27 | énalapril | RCP ANPP absent | 2026-11-15 |

## 6. Sources alternatives

Pour ces 27 médicaments, la collecte est complétée par deux **sources étrangères**, signalées comme telles :

| Source | Origine | Langue | Date de collecte |
|--------|---------|--------|------------------|
| `bdpm` | Base de données publique des médicaments (France) | fr | 2026-11-15 |
| `dailymed` | DailyMed (États-Unis) | en | 2026-11-16 |

- Tout document provenant de ces sources **conserve sa provenance réelle** (source, URL, date de collecte).
- Il n'est **jamais présenté comme un RCP de l'ANPP** : le champ `source` ne prend jamais la valeur `anpp` pour ces documents.
- Le statut `RCP ANPP absent` est conservé pour le médicament : le document étranger complète la collecte, il ne remplace pas le RCP ANPP.
- Pour le néfopam, seule la source BDPM est disponible (aucun document DailyMed).

## 7. Conclusion

La collecte des RCP depuis l'ANPP repose désormais exclusivement sur une procédure manuelle. Les 27 médicaments sans RCP ANPP sont explicitement identifiés par le statut `RCP ANPP absent`, avec la date de vérification et la recherche effectuée. Les documents de substitution proviennent de sources étrangères clairement identifiées et conservent leur provenance réelle, afin de garantir la transparence et la traçabilité des données.