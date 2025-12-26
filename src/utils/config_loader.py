"""
Module de gestion de la configuration avec Hydra.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from hydra import compose, initialize
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig, OmegaConf

# Configuration du logger
logger = logging.getLogger(__name__)


def load_config(
    config_name: str = "config", 
    overrides: Optional[List[str]] = None
) -> DictConfig:
    """
    Charge la configuration Hydra de manière robuste.

    Args:
        config_name: Nom du fichier de configuration (sans l'extension .yaml).
        overrides: Liste d'arguments de surcharge (ex: ["db.port=5432"]).

    Returns:
        DictConfig: Objet de configuration OmegaConf.
    """
    # Nettoyage de l'instance Hydra globale (essentiel pour les Notebooks)
    GlobalHydra.instance().clear()

    # Le chemin doit être relatif au fichier actuel ou au point d'entrée
    # Si ce fichier est dans src/utils, on remonte vers ../../configs
    try:
        with initialize(version_base="1.3", config_path="../../configs"):
            cfg = compose(config_name=config_name, overrides=overrides or [])
            logger.info("Configuration chargée avec succès.")
            return cfg
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        raise


def get_paths(cfg: DictConfig) -> Dict[str, str]:
    """
    Extrait et centralise les chemins définis dans la configuration.
    """
    try:
        return {
            # Données
            "raw_dir": cfg.data.raw.data_dir,
            "raw_data": cfg.data.raw.main_file,
            "interim_dir": cfg.data.interim.data_dir,
            "processed_dir": cfg.data.processed.data_dir,
            
            # Sorties
            "figures_dir": cfg.data.figures.root_dir,
            "reports_dir": cfg.data.reports.root_dir,
            
            # Métadonnées
            "metadata": cfg.data.metadata.file,
        }
    except AttributeError as e:
        logger.error(f"Clé manquante dans le fichier de configuration : {e}")
        raise


def create_directories(cfg: DictConfig) -> None:
    """
    Crée récursivement tous les répertoires nécessaires au projet.
    """
    paths = get_paths(cfg)
    
    # On filtre pour ne garder que les entrées finissant par '_dir' 
    # ou on sélectionne manuellement les dossiers à créer
    dirs_to_create = {
        paths[k] for k in paths if k.endswith("_dir") or "root" in k
    }

    for directory in dirs_to_create:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Répertoire créé : {dir_path}")
        else:
            logger.debug(f"Le répertoire existe déjà : {dir_path}")


def get_random_seed(cfg: DictConfig, default: int = 42) -> int:
    """
    Récupère la seed de reproductibilité. 
    Note: 'global' étant un mot-clé Python, il est préférable d'utiliser 
    une clé nommée 'settings' ou 'params' dans votre YAML.
    """
    # Utilisation de .get pour éviter un crash si la clé n'existe pas
    return cfg.get("random_seed", default)


if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    print(OmegaConf.to_yaml(config))