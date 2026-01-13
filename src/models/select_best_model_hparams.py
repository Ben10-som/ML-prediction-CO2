import sys
from pathlib import Path
import mlflow
import joblib
import pandas as pd
import hydra
from omegaconf import DictConfig

import sys
from pathlib import Path

# ===== FIX CRITIQUE POUR CLOUDPICKLE =====
CURRENT_FILE = Path(__file__).resolve()
SRC_PATH = CURRENT_FILE.parent.parent  # src/
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@hydra.main(config_path="../../configs", config_name="config", version_base="1.2")
def select_best(cfg: DictConfig):

    EXPERIMENT_NAME = f"{cfg.project.name}_Optimization"
    MODEL_ARTIFACT_PATH = "optimized_model"

    mlflow.set_tracking_uri("http://localhost:5000")

    # Racine projet
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    best_model_dir = project_root / "best_model"/ cfg.project.name
    best_model_dir.mkdir(exist_ok=True)

    # Récupération de l’expérience
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        raise ValueError(
            f"Expérience MLflow introuvable : {EXPERIMENT_NAME}\n"
            f"Vérifie cfg.project.name"
        )

    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        output_format="pandas"
    )

    # Sécurité
    for m in ["metrics.R2", "metrics.MAE", "metrics.RMSE"]:
        if m not in runs.columns:
            raise ValueError(f"Métrique absente : {m}")

    # Règle métier
    runs["R2_cmp"] = runs["metrics.R2"].round(2)
    runs["MAE_cmp"] = runs["metrics.MAE"].round(3)
    runs["RMSE_cmp"] = runs["metrics.RMSE"].round(3)

    runs = runs.sort_values(
        by=["R2_cmp", "MAE_cmp", "RMSE_cmp"],
        ascending=[False, True, True]
    )

    best = runs.iloc[0]

    # =============================
    # RÉCUPÉRATION DU NOM DU MODÈLE
    # =============================
    run_name = best.get("tags.mlflow.runName", "unknown_model")

    # Exemple : GridSearch_ridge → ridge
    model_name = run_name.replace("GridSearch_", "").lower()

    # Sécurisation nom de fichier
    model_name = model_name.replace(" ", "_").replace("/", "_")


    best_run_id = best.run_id

    model_uri = f"runs:/{best_run_id}/{MODEL_ARTIFACT_PATH}"
    best_model = mlflow.sklearn.load_model(model_uri)

    model_filename = f"best_model_{model_name}.joblib"
    joblib.dump(best_model, best_model_dir / model_filename)


    pd.Series({
    "run_id": best_run_id,
    "model_name": model_name,
    "R2": best["metrics.R2"],
    "MAE": best["metrics.MAE"],
    "RMSE": best["metrics.RMSE"],
    "experiment": EXPERIMENT_NAME,
    "artifact": model_filename
    }).to_csv(best_model_dir / "best_model_metrics.csv")


    print("Meilleur modèle sélectionné et sauvegardé")
    print(best[["metrics.R2", "metrics.MAE", "metrics.RMSE"]])

if __name__ == "__main__":
    select_best()
