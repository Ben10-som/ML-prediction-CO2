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

    with initialize(version_base="1.3", config_path="../../configs"):
        cfg = compose(config_name=config_name, overrides=overrides or [])
        logger.info(f"Configuration '{config_name}' chargée avec succès.")
        return cfg

def create_directories(cfg: DictConfig) -> None:
    """
    Crée dynamiquement les répertoires définis dans la section data et outputs.
    """
    try:
        # On itère sur les sections de données (raw, interim, processed)
        # et les sorties (figures, reports)
        sections = [
            cfg.data.raw, 
            cfg.data.interim, 
            cfg.data.processed, 
            cfg.data.figures, 
            cfg.data.reports
        ]

        for section in sections:
            # On cherche la clé 'dir' ou 'data_dir' (pour compatibilité)
            path_str = section.get("dir") or section.get("data_dir")
            if path_str:
                p = Path(path_str)
                if not p.exists():
                    p.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Répertoire créé : {p}")
                
    except AttributeError as e:
        logger.warning(f"Clé de configuration manquante pour la création de dossiers : {e}")

if __name__ == "__main__":

    # Test du chargement
    config = load_config()
    # Configurer le logger via eda_logger 
    setup_eda_logger(config) 
    logger = logging.getLogger(__name__)
    create_directories(config)
    # Affichage pour vérification
    print(OmegaConf.to_yaml(config))