"""
Module de chargement des données (Download -> Load -> Validate)
"""

import json
import logging
from pathlib import Path

import requests
import pandas as pd
from omegaconf import DictConfig

from utils.config_loader import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _resolve_path(path_str: str) -> Path:
    """
    Résout un chemin de manière défensive :
    - refuse None / "None" / ""
    - ancre les chemins relatifs au PROJECT_ROOT
    """
    if not path_str or str(path_str).strip().lower() == "none":
        raise ValueError("Chemin invalide dans la configuration")

    p = Path(path_str)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return p


def download_file(url: str, dest_path: Path) -> None:
    """Télécharge un fichier depuis une URL si nécessaire."""
    if not url:
        raise ValueError("URL de téléchargement manquante dans la configuration.")

    logger.info(f"Téléchargement en cours depuis : {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(response.content)

        logger.info("✓ Téléchargement terminé avec succès.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Échec du téléchargement : {e}")
        raise


def load_data_raw(cfg: DictConfig) -> pd.DataFrame:
    """
    Chargement robuste des données raw :
    - résolution stricte des chemins
    - aucun dossier 'None' possible
    """

    raw_dir = _resolve_path(cfg.data.raw.dir)
    raw_file = cfg.data.raw.file
    raw_path = raw_dir / raw_file

    if not raw_path.exists():
        logger.warning(f"Fichier local introuvable : {raw_path}")
        download_file(url=cfg.data.raw.url, dest_path=raw_path)
    else:
        logger.info(f"Fichier local détecté : {raw_path}")

    load_params = {
        "encoding": cfg.eda.loading.encoding,
        "low_memory": cfg.eda.loading.low_memory,
        "na_values": cfg.eda.loading.na_values,
    }

    try:
        df = pd.read_csv(raw_path, **load_params)
        logger.info(f"✓ DataFrame chargé : {df.shape[0]} lignes, {df.shape[1]} colonnes")
        return df
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du CSV : {e}")
        raise


def save_metadata(df: pd.DataFrame, cfg: DictConfig) -> None:
    """Sauvegarde des métadonnées techniques."""
    meta_path = _resolve_path(cfg.data.metadata.file)

    metadata = {
        "dataset": cfg.project.name,
        "source_file": cfg.data.raw.file,
        "n_rows": int(df.shape[0]),
        "n_columns": int(df.shape[1]),
        "columns": df.columns.tolist(),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024**2), 2),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
    }

    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Métadonnées sauvegardées : {meta_path}")
