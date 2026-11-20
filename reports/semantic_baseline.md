# Baseline Sémantique (Embeddings) — résultats (Week 2)

- **Date** : 2026-11-20
- **Modèle** : `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dim, ONNX via fastembed)
- **Base vectorielle** : Chroma (persistent, cosine similarity) — `data/index/chroma/`
- **Corpus** : 1 527 documents → **45 694 chunks** (mêmes chunks que BM25)
- **Questions** : P1, P2, P3, L1 (identiques au baseline BM25)

## Résultats

| Sondes | Cible (chunk) | Rang BM25 | Rang Sémantique | Top-3 ? |
|---|---|---|---|---|
| P1 — posologie max de MIBRAL 5 mg | `32c42dd29237` ("maximale de 5 mg") | **2** | **>50** | ❌ (sémantique pire) |
| P2 — association DETENSIEL + MIBRAL | `0db64c85e805` ("À prendre en compte") | **239** | **>50** | ❌ |
| P3 — paracétamol sans danger ? | absence à signaler | n/a | n/a | n/a |
| L1 — requête courte | top-3 = amlodipine (4.3/4.5) | partiel | partiel | — |

## Observations

1. **La recherche sémantique naïve performe MOINS bien que BM25** sur ce corpus.
   - P1 : BM25 rang 2, sémantique rang >50 (la cible n'apparaît même pas dans le top 50).
   - P2 : BM25 rang 239, sémantique rang >50.

2. **Causes probables** :
   - **Boilerplate des en-têtes** : les chunks de page 1 ("Résumé des Caractéristiques du Produit ANSM - Mis à jour le...") sont courts et génériques → ils dominent la similarité cosinus pour toute requête médicamenteuse.
   - **Modèle généraliste** : `paraphrase-multilingual-MiniLM-L12-v2` n'est pas spécialisé pour le domaine médical/pharmaceutique.
   - **Pas de filtrage par metadata** : la recherche sémantique renvoie des diclofénac/ibuprofène pour une requête MIBRAL, car le modèle ne distingue pas les médicaments.

3. **Ce que cela valide** :
   - Les embeddings "bruts" ne sont pas suffisants : le **prétraitement du corpus** (chunking par section, suppression du boilerplate, filtrage par metadata) compte plus que le choix du modèle.
   - BM25 reste un **baseline solide** pour ce corpus (mots-clés exacts, marques).
   - La **normalisation (F3)** est indispensable pour P2, quelle que soit la méthode de recherche.

## Recommandations (Week 2+)

- [ ] **Chunking par section** (4.2, 4.3, 4.4...) au lieu de par page, en excluant les en-têtes boilerplate.
- [ ] **Filtrage par metadata** : si le DCI est identifié (via F3), restreindre la recherche aux documents de ce DCI avant la recherche sémantique.
- [ ] **Hybrid search** : combiner BM25 (mots-clés exacts) + sémantique (synonymes) avec un score fusionné (RRF).
- [ ] **Modèle spécialisé** : tester un modèle médical (ex. `camembert-bio` ou `sentence-transformers/all-MiniLM-L6-v2` fine-tuné) si disponible.
- [ ] **Re-évaluer** après ces améliorations et comparer avec BM25.

## Livrables produits

- `data/index/chroma/` (base vectorielle, gitignored)
- `data/index/embeddings.npy` (45 694 × 384, gitignored)
- `reports/semantic_baseline.md` (ce fichier)
- `reports/bm25_baseline.md` (baseline BM25 pour comparaison)
