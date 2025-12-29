"""
Module de gestion de la configuration avec Hydra.
"""

import logging
from pathlib import Path
from typing import List, Optional

from hydra import compose, initialize
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig, OmegaConf

from eda_logger import setup_eda_logger # Config des log depuis eda_loger

logger = logging.getLogger(__name__)

def load_config(config_name: str = "config", overrides: Optional[List[str]] = None) -> DictConfig:
    """
    Charge la configuration Hydra
    """
    GlobalHydra.instance().clear()

    # Le chemin config_path est relatif au dossier contenant ce script
    # Utiliser Hydra 1.3
    with initialize(version_base="1.3", config_path="../../configs"):
        cfg = compose(config_name=config_name, overrides=overrides)
        logger.info(f"Configuration '{config_name}' chargée avec succès.")
        return cfg

def create_directories(cfg: DictConfig) -> None:
    """
    Crée les répertoires de données et de résultats définis dans la config.
    """
    try:
        # Liste directe des chemins à créer (basée sur la structure de ton YAML)
        directories = [
            cfg.data.raw.data_dir,
            cfg.data.interim.data_dir,
            cfg.data.processed.data_dir,
            cfg.data.figures.root_dir,
            cfg.data.reports.root_dir
        ]

        for path in directories:
            p = Path(path)
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                logger.info(f"Répertoire créé : {p}")
                
    except AttributeError as e:
        logger.warning(f"Impossible de créer certains dossiers (clé manquante) : {e}")

if __name__ == "__main__":

    # Test du chargement
    config = load_config()
    # Configurer le logger via eda_logger 
    setup_eda_logger(config) 
    logger = logging.getLogger(__name__)
    create_directories(config)
    # Affichage pour vérification
    print(OmegaConf.to_yaml(config))