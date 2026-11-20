# Baseline BM25 — résultats (Week 2)

- **Date** : 2026-11-20
- **Index** : `data/index/bm25_chunks.pkl` (gitignored, recalculable)
- **Corpus** : 1 527 documents → **45 694 chunks** (BDPM par section, PDF par page)
- **Tokenizer** : lowercasing + suppression des accents + mots alphanumériques
- **Questions** : mêmes sondes que `docs/question_test.md` (P1, P2, P3) + requête courte L1

## Résultats

| Sondes | Cible | Rang | Top-3 ? |
|---|---|---|---|
| P1 — posologie max de MIBRAL 5 mg | chunk `32c42dd29237` contenant « maximale de 5 mg » | **2** | ✅ oui |
| P2 — association DETENSIEL + MIBRAL | chunk `0db64c85e805` contenant « À prendre en compte » | **239** | ❌ non |
| P3 — paracétamol sans danger ? | aucun passage unique (absence à signaler) | n/a | n/a |
| L1 — requête courte | top-3 = BDPM bisoprolol (4.2) | — | partiel |

## Constats

1. **P1 passe** : BM25 trouve la bonne page en rang 2, car le titre contient « MIBRAL » et la page 1 contient toute la posologie.
2. **P2 échoue** : le Thésaurus est indexé par **classe DCI** (« bêta-bloquants », « dihydropyridines »), pas par marque. La requête contient « DETENSIEL » et « MIBRAL » → aucune correspondance. C'est le **problème de normalisation (F3)** prédit par le baseline LLM.
3. **P3** : BM25 renvoie des RCP de paracétamol ; il ne peut pas "trouver une absence". Le système devra répondre « aucune interaction répertoriée dans le tableau consulté » sans conclure à l'absence de risque.

## Ce que cela valide

- Le nettoyage (metadata, authority, paths) a rendu le corpus **recherchable**.
- BM25 fonctionne pour les requêtes **marque + mot-clé présent dans le document**.
- BM25 échoue pour les requêtes **marque → classe DCI** (normalisation requise) et pour les **absences**.

## Prochaines étapes (Week 2)

- [ ] Normalisation DCI ↔ marque ↔ ATC (`data/processed/dictionnaire_medicaments.csv`) pour que la requête "MIBRAL" se traduise en "amlodipine / dihydropyridines".
- [ ] Embeddings (sentence-transformers) + comparaison BM25 vs sémantique sur la même grille (P1, P2, P3).
- [ ] Améliorer le chunking PDF (par section 4.x plutôt que par page) pour réduire le bruit des en-têtes.

## Livrables produits

- `data/index/bm25_chunks.pkl` (index, gitignored)
- `reports/bm25_baseline.md` (ce fichier)
