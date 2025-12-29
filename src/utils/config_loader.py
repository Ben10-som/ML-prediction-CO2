"""
Module de gestion de la configuration avec Hydra.
"""

import logging
from pathlib import Path
from typing import List, Optional

from hydra import compose, initialize
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig, OmegaConf

from .eda_logger import setup_eda_logger

logger = logging.getLogger(__name__)

# racine projet (depuis src/utils/config_loader.py -> remontée de 2 niveaux)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OmegaConf.register_new_resolver(
    "project_root",
    lambda: str(PROJECT_ROOT),
    replace=True
)

def load_config(config_name: str = "config", overrides: Optional[List[str]] = None) -> DictConfig:
    """
    Charge la configuration Hydra.
    Garantit la présence de cfg.project.root via OmegaConf.merge (évite affectation d'attribut).
    """
    GlobalHydra.instance().clear()

    with initialize(version_base="1.3", config_path="../../configs"):
        cfg = compose(config_name=config_name, overrides=overrides or [])

    # Injecter project.root sans faire d'affectation d'attribut direct (évite Pylance warnings)
    try:
        OmegaConf.set_struct(cfg, False)
        cfg = OmegaConf.merge(cfg, {"project": {"root": str(PROJECT_ROOT)}})
        OmegaConf.set_struct(cfg, True)
    except Exception:
        logger.exception("Impossible de garantir project.root dans la config")

    logger.info(f"Configuration '{config_name}' chargée (project_root={cfg.project.root})")
    return cfg



def create_directories(cfg: DictConfig) -> None:
    """
    Crée les dossiers dont la config indique le chemin.
    Les chemins relatifs sont résolus par rapport à PROJECT_ROOT.
    """
    try:
        sections = [
            cfg.data.raw,
            cfg.data.interim,
            cfg.data.processed,
            cfg.data.figures,
            cfg.data.reports
        ]
    except AttributeError as e:
        logger.warning(f"Clé de configuration manquante pour la création de dossiers : {e}")
        return

    for section in sections:
        try:
            path_str = section.get("dir") or section.get("data_dir")
        except Exception:
            logger.warning("Section de configuration malformée, ignorée.")
            continue

        if not path_str:
            logger.debug("Chemin absent pour une section, ignoré.")
            continue

        if isinstance(path_str, str) and (path_str.strip().lower() == "none" or path_str.strip() == ""):
            logger.warning(f"Chemin invalide résolu: '{path_str}'. Ignoré.")
            continue

        p = Path(path_str)
        if not p.is_absolute():
            p = (PROJECT_ROOT / p).resolve()

        try:
            p.mkdir(parents=True, exist_ok=True)
            logger.info(f"Répertoire prêt : {p}")
        except Exception:
            logger.exception(f"Échec création répertoire : {p}")


if __name__ == "__main__":

    # Test du chargement
    config = load_config()
    # Configurer le logger via eda_logger
    setup_eda_logger(config)
    logger = logging.getLogger(__name__)
    create_directories(config)
    # Affichage pour vérification
    print(OmegaConf.to_yaml(config))
