
# python src/models/hparams_search.py --multirun model=ridge,lasso,rf_baseline,xgb



import sys
import logging
import io
import os
import mlflow
import mlflow.sklearn
from pathlib import Path
import hydra
from omegaconf import DictConfig
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from hydra.utils import instantiate

# Ajout du chemin SRC pour les imports
current_file = Path(__file__).resolve()
SRC_PATH = current_file.parent.parent
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from models.train import prepare_data
from models.transformer import make_preprocessor
from models.eval_utils import evaluate_model, detect_column_types


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constante pour le groupement
GROUP_COL = "PrimaryPropertyType"

@hydra.main(config_path="../../configs", config_name="config", version_base="1.2")
def optimize(cfg: DictConfig):
    # 1. Préparation des données 
    X_train, X_test, y_train, y_test = prepare_data(cfg)
    num_cols, cat_cols, binary_cols = detect_column_types(X_train)

    # --- CORRECTION 1 : Éviter les doublons de colonnes ---
    num_cols = [c for c in num_cols if c != GROUP_COL]
    cat_cols = [c for c in cat_cols if c != GROUP_COL]
    binary_cols = [c for c in binary_cols if c != GROUP_COL]

    # 2. MLflow Setup
    mlflow.set_experiment(f"{cfg.project.name}_Optimization")
    
    with mlflow.start_run(run_name=f"GridSearch_{cfg.model.name}"):
        # Construction du pipeline de base
        preprocessor = make_preprocessor(
            num_cols=num_cols,
            cat_cols=cat_cols,
            binary_cols=binary_cols,
            numeric_scaler=cfg.model.get("scaler", "robust")
        )
        
        model = instantiate(cfg.model.params)
        
        base_pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", model)
        ])

        # --- CORRECTION 2 : Adapter la param_grid au Pipeline ---
        # Dans un Pipeline, on doit préfixer les paramètres par "nomDuStep__"
        raw_grid = dict(cfg.model.search_space)
        param_grid = {f"model__{k}": v for k, v in raw_grid.items()}
        
        logger.info(f"Démarrage de la Grid Search pour {cfg.model.name}...")
        grid_search = GridSearchCV(
            estimator=base_pipeline,
            param_grid=param_grid,
            cv=3,
            scoring='r2',
            n_jobs=-1,
            verbose=2
        )

        grid_search.fit(X_train, y_train)

        # 3. Logs des résultats
        logger.info(f"Meilleurs paramètres : {grid_search.best_params_}")
        logger.info(f"Meilleur score CV (R2) : {grid_search.best_score_:.4f}")

        # Évaluation sur le set de test avec le meilleur estimateur
        best_model = grid_search.best_estimator_
        
        # --- CORRECTION 3 : Signature de evaluate_model ---
        metrics, plot_path = evaluate_model(best_model, X_test, y_test, f"Best_{cfg.model.name}")

        # Enregistrement dans MLflow
        mlflow.log_params(grid_search.best_params_)
        mlflow.log_metrics(metrics)
        
        if plot_path and os.path.exists(plot_path):
            mlflow.log_artifact(plot_path)
            
        mlflow.sklearn.log_model(best_model, "optimized_model")
        
        logger.info(f"Optimisation terminée pour {cfg.model.name}. R2 Test: {metrics['R2']:.4f}")

if __name__ == "__main__":
    optimize()