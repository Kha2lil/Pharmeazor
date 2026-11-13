#!/usr/bin/env bash
# Crée l'arborescence du dépôt Pharmeazor (à lancer à la racine du dépôt)
set -e

dirs=(
  config
  data/reference
  data/raw/anpp data/raw/nomenclature data/raw/ansm data/raw/dailymed data/raw/sites_pro
  data/processed data/metadata data/annotations data/cache data/index
  notebooks
  src/collecte src/extraction src/normalisation src/retrieval src/rag
  src/verification src/reconciliation src/llm src/ui
  tests
  reports/hebdo reports/evaluation
  docs
)
for d in "${dirs[@]}"; do mkdir -p "$d"; touch "$d/.gitkeep"; done

touch src/__init__.py
for m in collecte extraction normalisation retrieval rag verification reconciliation llm ui; do
  touch "src/$m/__init__.py"
done

echo "Téléchargement MANUEL uniquement (robots.txt interdit l'accès automatique). Noter la date et l'URL de téléchargement." > data/raw/nomenclature/README.md

cat > data/metadata/sources.csv << 'CSV'
source,rang,url,robots_txt,cgu,mode_collecte,date_verification,remarques
ANPP,1,,,,,,
Nomenclature officielle,2,,interdit (auto),,manuel,,
Thesaurus ANSM,3,,,,,,
DailyMed,3,,,,,,
EMA,3,,,,,,
Pharm'Net,4,,,,,,
MEDAlgerie,4,,,,,,
dzair-pharma,4,,,,,,
CSV

cat > data/metadata/robots_cgu_log.md << 'MD'
# Journal robots.txt et conditions d'utilisation
(à remplir AVANT toute collecte automatique ; une entrée par source : date, URL, ce qui est autorisé/interdit, décision)
MD

echo "document,source,type_desaccord,valeur_source_haute,valeur_source_basse,source_retenue" > data/annotations/desaccords.csv
echo "date,membre,appels,objet" > reports/appels_api_log.csv

cat > docs/usage_ia.md << 'MD'
# Déclaration d'usage de l'IA
| Semaine | Membre | Outil | Usage |
|---|---|---|---|
MD

echo "[]" > tests/jeu_de_test.json
echo "Structure créée."
