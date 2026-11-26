# Pharmeazor — Assistant de sécurité médicamenteuse

> Base de connaissances médicamenteuses multi-sources + plateforme de raisonnement (RAG) pour des réponses **fiables et justifiées**.
> Module RCR | M1-IA | Université Constantine 2 – Abdelhamid Mehri (FNTIC / IFA)

**Principe fondamental : une information médicale n'a de valeur que si elle cite sa source, et tout chiffre affiché doit se retrouver mot pour mot dans le passage cité.**

---

## 1. Présentation

Pharmeazor lit des documents sur les médicaments (RCP, notices, tableaux d'interactions), les croise, détecte leurs désaccords et répond aux questions d'un pharmacien en **citant la source exacte** de chaque information.

- **Utilisateur cible** : pharmacien d'officine ou étudiant en santé. La décision reste la sienne.
- **Corpus cœur** : 40 médicaments (12 antalgiques/anti-inflammatoires, 14 antibiotiques, 14 antihypertenseurs).

## 2. Périmètre et règles

**Inclus** : identification et noms, indications, contre-indications, posologie, interactions, effets indésirables, équivalents enregistrés en Algérie.
**Exclu** : diagnostic, choix de traitement, ordonnance, conseil personnalisé, compléments alimentaires, dispositifs médicaux.

Règles non négociables :
1. Le système **ne prescrit ni ne diagnostique**.
2. **Aucune information sans source** n'est affichée ; « aucune interaction trouvée » n'est **jamais** présenté comme « sans risque ».
3. Les ordonnances de test sont **fictives** ; aucune donnée de vrai patient.
4. **Règle d'or** : en cas de contradiction, la source de rang supérieur l'emporte, et le système dit pourquoi.
5. Une source étrangère est un **complément, jamais un substitut** à la source algérienne.
6. `robots.txt` et conditions d'utilisation respectés : si une source l'interdit, usage **manuel** ou écartée, **jamais contournée**.

### Hiérarchie des sources (du plus au moins fiable)
| Rang | Source                                                                  |
| ---- | ----------------------------------------------------------------------- |
| 1    | RCP et notices officiels (ANPP, Algérie)                                |
| 2    | Nomenclature officielle (Ministère de l'Industrie pharmaceutique)       |
| 3    | Références institutionnelles étrangères (Thésaurus ANSM, DailyMed, EMA) |
| 4    | Sites professionnels algériens (Pharm'Net, MEDAlgérie, dzair-pharma)    |
| 5    | Forums, blogs, réseaux sociaux → **écartés**                            |

### Niveaux d'interaction (ANSM)
Contre-indication > Association déconseillée > Précaution d'emploi > À prendre en compte.

## 3. Architecture

```
Collecte → Extraction des rubriques → Normalisation des noms → Recherche (BM25 / embeddings)
        → Réponse avec citations (LLM) → Vérification (contrôle des chiffres) → Réconciliation des sources
                                                   ↓
                                      Interface web + jeu de test (≥ 30 questions)
```

| Fonctionnalité              | Module                                            | Critère de réussite                                               |
| --------------------------- | ------------------------------------------------- | ----------------------------------------------------------------- |
| F1 Collecte + provenance    | `src/collecte/`                                   | Rejouable sans doublons, CGU/robots.txt consignés                 |
| F2 Extraction des rubriques | `src/extraction/`                                 | Taux mesuré sur ~20 notices vérifiées à la main                   |
| F3 Normalisation des noms   | `src/normalisation/`                              | Évaluation sur ≥ 40 saisies, cas ambigus signalés                 |
| F4 Réponse avec preuves     | `src/retrieval/`, `src/rag/`, `src/verification/` | Citations correctes, ≥ 2 méthodes comparées, refus hors périmètre |
| F5 Réconciliation           | `src/reconciliation/`                             | ≥ 10 désaccords réels annotés retrouvés                           |
| F6 Interface + jeu de test  | `src/ui/`, `tests/`                               | ≥ 30 questions, relançable d'un clic                              |

**Format de réponse imposé** : (a) réponse courte, (b) explication simple, (c) sources citées avec niveau d'autorité et date de collecte, (d) niveau de confiance et limites.


## 4. Installation

### Linux / macOS

```bash
git clone <url-du-depot> Pharmeazor
cd Pharmeazor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
git clone <url-du-depot> Pharmeazor
cd Pharmeazor

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

Copy-Item .env.example .env
```


## 5. Configuration de la clé API

Une clé gratuite **par personne** : https://console.groq.com/keys (elle commence par `gsk_`).

```bash
cp .env.example .env               # puis renseigner GROQ_API_KEY dans .env
```

- **Colab** : icône clé (Secrets) → secret `GROQ_API_KEY` → activer l'accès au notebook.
- **Interdit** : clé dans le code, dans Git, dans le rapport, dans une capture d'écran.
- Si la clé a fuité : la supprimer sur la console Groq, en créer une autre, **prévenir l'enseignant**.
- **Aucun moyen de paiement**, pas de comptes supplémentaires.

## 6. Modèle de langage imposé

- Modèle commun : `openai/gpt-oss-120b` via l'API Groq (plan gratuit). Secours (sur annonce de l'enseignant uniquement) : `openai/gpt-oss-20b`.
- Limites (par compte) : 30 requêtes/min, 1 000/jour, ~8 000 jetons/min, 200 000 jetons/jour.
- Chaque appel **< ~4 000 jetons** ; pause entre appels ; sur erreur 429, 2 à 3 réessais maximum.
- **Cache obligatoire** des réponses du modèle (`data/cache/`) : le jeu de test doit être rejouable depuis le cache.
- Le nombre d'appels est journalisé dans `reports/appels_api_log.csv`.
- Textes **publics uniquement** envoyés au modèle.

## 7. Utilisation

> À compléter au fil du développement.

```bash
python -m src.collecte.run            # F1 : collecte + fiches de provenance
python -m src.extraction.run          # F2 : extraction des rubriques
python -m src.normalisation.build     # F3 : dictionnaire DCI / nom commercial / ATC
streamlit run src/ui/app.py           # F6 : interface
python -m tests.run_eval              # jeu de test (relançable d'un clic)
```

## 8. Sources et conditions d'utilisation

Voir `data/metadata/sources.csv` et `data/metadata/robots_cgu_log.md`.

| Source                              | Rang | robots.txt / CGU                        | Mode de collecte          | Statut |
| ----------------------------------- | ---- | --------------------------------------- | ------------------------- | ------ |
| ANPP (RCP/notices)                  | 1    | à vérifier                              | à vérifier                | ☐      |
| Nomenclature officielle             | 2    | robots.txt interdit l'accès automatique | **téléchargement manuel** | ☐      |
| Thésaurus ANSM                      | 3    | à vérifier                              | à vérifier                | ☐      |
| DailyMed / EMA                      | 3    | à vérifier                              | à vérifier                | ☐      |
| Pharm'Net, MEDAlgérie, dzair-pharma | 4    | à lire avant collecte                   | à vérifier                | ☐      |

Chaque document collecté a une fiche : source, URL, **date de collecte**, langue, niveau d'autorité.

## 9. Évaluation

Résultats chiffrés dans `reports/evaluation/` :
`extraction` · `normalisation` · `retrieval` (BM25 vs embeddings, bon passage dans le top-3 ?) · `reconciliation` · `jeu_de_test`.

## 10. Équipe et contributions

| Membre | Rôle          | Contribution |
| ------ | ------------- | ------------ |
| …      | Chef d'équipe | …            |
| …      | …             | …            |

Rapport d'avancement : à déposer chaque **vendredi 10h00 → samedi 10h00** (chef d'équipe, plateforme de suivi). Les copies sont rangées dans `reports/hebdo/`.

## 11. Déclaration d'usage de l'IA

Outils d'IA utilisés et finalité : voir `docs/usage_ia.md` (mis à jour chaque semaine). L'équipe reste responsable de tout ce qu'elle rend.

## 12. Limites connues

> À compléter : couverture ANPP, notices scannées/arabes (qualité OCR), médicaments absents de la nomenclature, etc.

---
*Un système qui dit « je ne sais pas » vaut mieux qu'un système qui invente.*
