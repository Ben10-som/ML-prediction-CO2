"""
Module : Feature Engineering Pipeline 

Ce script intègre le module de feature engineering dans le pipeline Hydra.
Il prépare les paramètres à partir de la configuration Hydra, exécute la
fonction `feature_engineering_seattle`, et journalise les étapes clés.

Fonctionnalités :
- Chargement des paramètres depuis la config Hydra (year_ref, eps, etc.)
- Application du feature engineering sur le DataFrame nettoyé
- Export du jeu de données enrichi vers le répertoire processed
- Logging du démarrage et de la fin du processus avec la shape finale

"""



import logging
import pandas as pd
from omegaconf import DictConfig

from feature_engineering.feature_engineering import feature_engineering_seattle
from utils.config_loader import PROJECT_ROOT

logger = logging.getLogger(__name__)

def run_feature_engineering_pipeline(df: pd.DataFrame, cfg: DictConfig) -> pd.DataFrame:
    """
    Wrapper pour intégrer le script du collègue dans le pipeline Hydra.
    """
    logger.info("--- Démarrage : Feature Engineering ---")

    # Préparation des arguments depuis la config Hydra
    output_dir = (PROJECT_ROOT / cfg.feature_engineering.output_dir).resolve()

    #filename = cfg.feature_engineering.filename
    filename=None
    if filename is None:
        filename = f"{getattr(df, 'name', 'features')}.csv"

    df_fe = feature_engineering_seattle(
        df=df,
        # On ajoute .params 
        year_ref=cfg.feature_engineering.params.year_ref,
        eps=cfg.feature_engineering.params.eps,
        # On ajoute .selection 
        drop_leaky_cols=cfg.feature_engineering.selection.drop_leaky,
        keep_raw_energy_cols=cfg.feature_engineering.selection.keep_raw_energy,
        output_dir=output_dir,
        filename=filename,
        metadata={"source": "hydra_pipeline", "run_type": "script"},
        fe_cfg=cfg.feature_engineering 
    )

    logger.info(f"✓ Feature Engineering terminé. Shape: {df_fe.shape}")
    return df_fe