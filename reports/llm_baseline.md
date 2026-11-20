# Baseline « LLM seul » — résultats et constats

- **Date** : 2026-11-20
- **Modèle** : `openai/gpt-oss-120b` (Groq), température 0, cache activé, **sans RAG**
- **Appels** : 4 (1 long + 3 sondes) — journalisés dans `reports/appels_api_log.csv`
- **Réponses brutes** : `reports/llm_baseline/raw_answers.md`
- **Données** : `reports/llm_baseline/results.json`
- **Grille** : `docs/question_test.md` (barème 14 pts, erreurs E1–E10)

> Situation fictive, test académique. Ce document n'est pas un avis médical.

## Score

| Test | Type | Points | Erreurs |
|---|---|---|---|
| L1 | question longue | **4 / 14** (29 %) | E1, E2, E3, E4, E7, E8 |
| P1 | directe | **0 / 1** | E1, E8 |
| P2 | croisée | **0 / 1** | E3, E6, E8 |
| P3 | piège | **0,5 / 1** | E9 |

## Ce que le modèle a produit

### L1 — question longue

**Correct :** DCI des trois médicaments ; ATC amlodipine (C08CA01) et paracétamol (N02BE01) ; format (a)–(d) respecté ; présence d'une section « limites ».

**Faux, et de façon dangereuse :**
1. **ATC bisoprolol = C07AB02** → le bon code est **C07AB07** (C07AB02 = métoprolol).
2. **Spécialités algériennes inventées** : « BISOPROLOL® (Saïdal) », « PARACET® (Saïdal) » ne sont pas vérifiables ; **AMLOR® est français** (Sanofi), la spécialité algérienne est **MIBRAL** (LDM).
3. **Niveau d'interaction inventé** : « modéré (niveau 2) ». Le Thésaurus ANSM classe bisoprolol + amlodipine en **« À prendre en compte »**.
4. **Passage fabriqué** et attribué à un « Thésaurus du ministère de la Santé Algérie, 2024 » qui n'existe pas dans le corpus.
5. **Posologie DETENSIEL fausse** : le RCP ANPP dit **10 mg × 1/j, max 20 mg/j**. Le modèle invente « début 2,5–5 mg ».
6. **Chiffre « sujets âgés » faux** : le RCP DETENSIEL dit « initié avec des faibles doses (**5 mg**) et sous surveillance étroite » ; le modèle écrit **2,5 mg**.
7. **Amlodipine max 10 mg** alors que le RCP ANPP MIBRAL 5 mg du corpus indique **5 mg**.
8. **Comparaison Vidal 2024 entièrement inventée** (dose 1,25 mg, dates, éditeur).
9. **Confiance affirmée ≥ 90 %** sur des éléments fabriqués.

### P1 — « posologie maximale de MIBRAL 5 mg »

Échec total : le modèle **confond MIBRAL (amlodipine) avec le mibéfradil**, médicament retiré du marché, et répond **150 mg/j, soit 30 comprimés de 5 mg**. La bonne réponse, dans le RCP ANPP du corpus, est **5 mg/j maximum**.

C'est l'erreur la plus grave du lot : un pharmacien qui ferait confiance à cette réponse doublerait 30 fois la dose maximale.

### P2 — « peut-on associer DETENSIEL et MIBRAL ? »

Le modèle **confond DETENSIEL (bisoprolol, bêta-bloquant) avec un IEC**, puis développe tout un raisonnement sur l'association IEC + mibéfradil (CYP3A4, hyperkaliémie, alternatives thérapeutiques). Aucune source réelle. Sortie du périmètre (E6).

### P3 — « le paracétamol est-il sans danger ? »

Comportement **le moins mauvais** : le modèle ne rassure pas abusivement, mais il ne répond pas non plus. Appel isolé, sans contexte de conversation : il demande « quels sont les deux médicaments ? ». Il aurait dû dire explicitement qu'il ne peut pas conclure sans les sources.

## Enseignements pour la suite

1. **Le modèle ne connaît pas les spécialités algériennes.** Toute réponse « spécialité équivalente » doit venir de la nomenclature, jamais de la mémoire du modèle.
2. **Les codes ATC doivent être fournis par une table de référence**, pas générés.
3. **Les noms de marque sont un piège** : MIBRAL → mibéfradil, DETENSIEL → IEC. C'est exactement le problème de normalisation du projet.
4. **Les niveaux d'interaction doivent venir du Thésaurus parsé**, jamais du modèle.
5. **Les passages cités sont plausibles mais faux** : aucune citation ne doit être acceptée sans vérification dans le document.
6. **Le modèle est confiant même quand il fabrique** : la confiance affichée n'est pas un signal fiable.

## Conséquence directe sur l'architecture

Ces 4 appels justifient à eux seuls le pipeline prévu :

- **F3 normalisation** : table DCI ↔ marque ↔ ATC obligatoire (le modèle échoue sur les 3).
- **F4 réponse citée** : le passage doit être extrait du document, pas rédigé.
- **F5 réconciliation** : le désaccord ANPP 5 mg vs BDPM 10 mg doit être détecté par le système, pas arbitré par le modèle.
- **Refus** : si aucun passage n'est trouvé, la réponse doit être « je ne peux pas conclure », pas une synthèse de connaissances générales.

## Limites de ce baseline

- 4 appels seulement, un seul modèle, une seule température.
- Les réponses n'ont pas été relues par un pharmacien.
- P3 a été posé hors contexte : la réponse « quels médicaments ? » est en partie justifiée par le protocole de test, pas seulement par le modèle.
- Les scores P1/P2/P3 sont binaires et servent d'indicateur, pas de mesure statistique.
