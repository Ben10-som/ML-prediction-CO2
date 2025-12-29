"""
eda_logger : Module de gestion centralisée des logs EDA via Hydra
"""

import logging
from omegaconf import DictConfig

def setup_eda_logger(cfg: DictConfig) -> None:
    """
    Configure le logger global en utilisant la section logging de la config Hydra.
    
    Args:
        cfg (DictConfig): configuration Hydra contenant la section `logging`
    """
    logging.basicConfig(
        level=getattr(logging, cfg.logging.level),
        format=cfg.logging.format
    )
