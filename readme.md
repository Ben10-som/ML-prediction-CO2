<table>
  <tr>
    <td><img src="https://res.cloudinary.com/dsiban6wc/image/upload/v1768303944/images_cwini1.jpg" alt="Seattle logo" height="48" /></td>
    <td><h1>ML-prediction-CO2 — Seattle Energy Benchmarking 2016</h1></td>
  </tr>
</table>

![GitHub last commit](https://img.shields.io/github/last-commit/Ben10-som/ML-prediction-CO2?style=flat-square)
![GitHub repo size](https://img.shields.io/github/repo-size/Ben10-som/ML-prediction-CO2?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/Ben10-som/ML-prediction-CO2?style=flat-square)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Ben10-som/ML-prediction-CO2?style=flat-square)
![GitHub stars](https://img.shields.io/github/stars/Ben10-som/ML-prediction-CO2?style=flat-square)
![GitHub forks](https://img.shields.io/github/forks/Ben10-som/ML-prediction-CO2?style=flat-square)

## Résumé exécutif
Ce projet couvre l’ensemble de la chaîne data science pour prédire les émissions de CO2 des bâtiments non résidentiels de Seattle (2016). Il combine ingestion contrôlée, audit de qualité, nettoyage par règles métier, feature engineering structuré, modélisation et mise à disposition via API + dashboard.

## Objectifs et périmètre
- Prédire `TotalGHGEmissions` pour des bâtiments non résidentiels.
- Garantir la traçabilité (audit automatique, fichiers intermédiaires, métadonnées).
- Produire des livrables data science exploitables : notebooks, rapports, modèle, API.

## Données
- Source : Seattle 2016 Building Energy Benchmarking (CSV accessible via URL de `configs/data/paths.yaml`).
- Volumétrie initiale observée : ~3 376 lignes, 46 colonnes (voir `reports/notebook_0/`).
- Dictionnaire de données automatique : `reports/notebook_0/data_dictionary_auto.md`.
- Audit et historisation : `data/metadata.json` (empreinte MD5, horodatage, utilisateur).

## Pipeline analytique
### 1) Ingestion & audit
- Chargement robuste + téléchargement si absent : `src/data/load_data.py`.
- Audit automatique à chaque chargement (hash et historique).

### 2) Nettoyage structuré (Sections 0 → 2 → 3 → 1)
- Section 0 : filtrage du périmètre (types de bâtiments), normalisation des labels.
- Section 2 : cohérence physique (GFA, énergie, EUI, ratios).
- Section 3 : outliers statistiques par usage (Z-score + IQR).
- Section 1 : imputation en cascade, suppression des colonnes trop lacunaires.

Le choix d’ordre est documenté dans `reports/notebook_1/compte_rendu.md`.

### 3) Feature engineering
- Variables morphologiques (log GFA, surfaces par étage/bâtiment).
- Variables spatiales (distance à un centre proxy, flag Downtown).
- Flags énergétiques (steam/gaz/energystar, ratios, intensités).
- Pipeline paramétré via `configs/feature_engineering/default.yaml`.

### 4) Modélisation
- Notebooks de modélisation : `notebooks/06_modeling_pipeline.ipynb` et variantes.
- Modèle final référencé : `best_model/best_model_ridge.joblib`.

## Résultats modèle (snapshot)
D’après `best_model/best_model_metrics.csv` (ridge) :

| Metric | Test |
| --- | --- |
| R2 | 0.8082 |
| MAE | 0.4977 |
| RMSE | 0.6305 |

## API & Dashboard
- API FastAPI : `dashboard/backend/api.py`.
- Modèle utilisé par l’API : `dashboard/models/co2_model.joblib`.
- Frontend React : `dashboard/frontend/`.

Endpoints principaux :
- `GET /health` : statut du modèle.
- `POST /predict` : prédiction CO2.
- `POST /retrain` : réentraînement depuis `dashboard/data/*.csv`.
- `GET /data` : historique des prédictions.
- `GET /metrics` : statistiques agrégées.

## Déploiements
- Dashboard (Vercel) : https://co2-prediction-seattle.vercel.app/
- API (AWS ECS) : https://co-e0d0ef8ded0e469293ef4e043ef80593.ecs.eu-west-3.on.aws/

## Structure du dépôt
```
best_model/            # Artefacts du meilleur modèle + métriques
configs/               # Configs Hydra (chemins, nettoyage, FE, modèles)
data/                  # Raw, interim, processed + metadata
figures/               # Graphiques de diagnostics
mlflow.db              # Tracking local MLflow
notebooks/             # Notebooks d’analyse & modélisation
reports/               # Synthèses et rapports exportés
src/                   # Pipeline Python (ingestion, cleaning, FE, modèles)
dashboard/             # API FastAPI + frontend React
tests/                 # Tests unitaires
```

## Démarrage rapide
### 1) Pipeline data (exemple Python)
```python
from src.utils.config_loader import load_config
from src.data.load_data import load_data_raw
from src.data.clean_data import run_cleaning_pipeline
from src.feature_engineering.build_features import run_feature_engineering_pipeline

cfg = load_config()
raw_df = load_data_raw(cfg)
clean_df = run_cleaning_pipeline(raw_df, cfg)
fe_df = run_feature_engineering_pipeline(clean_df, cfg)
```

### 2) Lancer l’API
```bash
cd dashboard/backend
python -m uvicorn api:app --reload --port 8000
```

### 3) Tester une prédiction
```bash
python test_prediction.py
```

### 4) Lancer le dashboard
```bash
cd dashboard/frontend
npm install
npm start
```

## Configuration
- Config principale : `configs/config.yaml` (inclut `data`, `eda`, `cleaning`, `feature_engineering`).
- Exemple de surcharge : `load_config(overrides=["data.raw.file=..."])`.
- Chemins relatifs résolus depuis la racine projet via `PROJECT_ROOT`.

## Qualité & tests
- Tests disponibles : `tests/test_load_data.py`, `tests/test_config_loader.py`.
- Exécution : `pytest`.

## Livrables clés
- Dictionnaire de données : `reports/notebook_0/data_dictionary_auto.md`.
- Rapports de synthèse : `reports/notebook_0/`, `reports/notebook_1/`, `reports/notebook_5/`.
- Modèle et métriques : `best_model/`.
- API + dashboard fonctionnels : `dashboard/`.

## Contributeurs
<div align="center">
  <table>
    <tr>
      <td align="center">
        <a href="https://github.com/Mafieuu">
          <img src="https://avatars.githubusercontent.com/Mafieuu?v=4" width="80" alt="Moussa DIEME" />
        </a>
        <br />
        Moussa DIEME
      </td>
      <td align="center">
        <a href="https://github.com/Ben10-som">
          <img src="https://avatars.githubusercontent.com/Ben10-som?v=4" width="80" alt="Ben Idriss SOMA" />
        </a>
        <br />
        Ben Idriss SOMA
      </td>
      <td align="center">
        <a href="https://github.com/PapaAmad">
          <img src="https://avatars.githubusercontent.com/PapaAmad?v=4" width="80" alt="Papa Amadou NIANG" />
        </a>
        <br />
        Papa Amadou NIANG
      </td>
      <td align="center">
        <a href="https://github.com/proslawa">
          <img src="https://avatars.githubusercontent.com/proslawa?v=4" width="80" alt="Lawa Foumsou PROSPERE" />
        </a>
        <br />
        Lawa Foumsou PROSPERE
      </td>
      <td align="center">
        <a href="https://github.com/tamsir03">
          <img src="https://avatars.githubusercontent.com/tamsir03?v=4" width="80" alt="Tamsir NDONG" />
        </a>
        <br />
        Tamsir NDONG
      </td>
    </tr>
  </table>
</div>
