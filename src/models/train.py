import sys
import copy
import logging
import numpy as np
import os
from pathlib import Path

import hydra
from omegaconf import DictConfig
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# Ajout du chemin SRC pour les imports
current_file = Path(__file__).resolve()
SRC_PATH = current_file.parent.parent

from data.load_data import load_data_raw
from data.clean_data import run_cleaning_pipeline
from feature_engineering.build_features import run_feature_engineering_pipeline
from models.transformer import make_preprocessor
from models.eval_utils import evaluate_model, detect_column_types

import logging
import sys

# Forcer l'encodage UTF-8 pour le stream de sortie 
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# CONSTANTES HARDCODÉES
TARGET = "TotalGHGEmissions"
GROUP_COL = "PrimaryPropertyType"

logger = logging.getLogger(__name__)

import warnings
warnings.filterwarnings("ignore")
logging.getLogger("mlflow").setLevel(logging.ERROR)
logging.getLogger("alembic").setLevel(logging.ERROR)

def prepare_data(cfg):
    """Charge, nettoie et split les données."""
    df_raw = load_data_raw(cfg)
    
    cfg_ml = copy.deepcopy(cfg)
    cfg_ml.cleaning.section_1.enable_imputation = False
    
    df_cleaned = run_cleaning_pipeline(df_raw, cfg_ml)
    df_fe = run_feature_engineering_pipeline(df_cleaned, cfg)

    X = df_fe.drop(columns=[TARGET])
    y = np.log1p(df_fe[TARGET])
    
    return train_test_split(
        X, y, 
        test_size=0.2, 
        random_state=cfg["global"]["random_seed"],
        stratify=df_fe[GROUP_COL]
    )

@hydra.main(config_path="../../configs", config_name="config", version_base="1.2")
def train(cfg: DictConfig):
    # 1. Préparation
    X_train, X_test, y_train, y_test = prepare_data(cfg)
    num_cols, cat_cols, binary_cols = detect_column_types(X_train)

    # Nettoyage des listes pour éviter les doublons dans le ColumnTransformer
    num_cols = [c for c in num_cols if c != GROUP_COL]
    cat_cols = [c for c in cat_cols if c != GROUP_COL]
    binary_cols = [c for c in binary_cols if c != GROUP_COL]

    # 2. MLflow Setup
    mlflow.set_experiment(cfg.project.name)
    run_name = cfg.model.name

    with mlflow.start_run(run_name=run_name) as run:
        # Création du preprocessor
        preprocessor = make_preprocessor(
            num_cols=num_cols,
            cat_cols=cat_cols,
            binary_cols=binary_cols,
            numeric_scaler=cfg.model.get("scaler")
        )

        from hydra.utils import instantiate
        model = instantiate(cfg.model.params)

        full_pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", model)
        ])
        
        # 3. Fit & Eval
        logger.info(f"Entrainement de : {run_name}")
        full_pipeline.fit(X_train, y_train)

        #  Passage des 4 arguments pour le Dashboard 
        metrics, plot_path = evaluate_model(full_pipeline, X_test, y_test, run_name)

        # 4. Préparation des métadonnées MLflow
        y_pred = full_pipeline.predict(X_test)
        signature = infer_signature(X_test, y_pred)
        
        # Sauvegarde temporaire du dataset de test pour log
        test_data_path = "test_features.csv"
        X_test.to_csv(test_data_path, index=False)

        # 5. Logs MLflow
        mlflow.log_params(cfg.model.params)
        mlflow.log_metrics(metrics)
        
        # Log du graphique d'évaluation
        if plot_path and os.path.exists(plot_path):
            mlflow.log_artifact(plot_path)
        
        # Log du dataset de test
        mlflow.log_artifact(test_data_path, artifact_path="data")
        
        # Log de la config Hydra
        if os.path.exists(".hydra"):
            mlflow.log_artifacts(".hydra", artifact_path="config")

        # Log du Pipeline COMPLET (Preprocessor + Model)
        mlflow.sklearn.log_model(
            sk_model=full_pipeline, 
            artifact_path="pipeline",
            signature=signature
        )
        
        # Nettoyage
        if os.path.exists(test_data_path):
            os.remove(test_data_path)

        logger.info(f"Termine. R2: {metrics['R2']:.4f}")

if __name__ == "__main__":
    train()