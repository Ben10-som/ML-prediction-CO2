"""
Module de chargement des données (Download -> Load -> Validate)
"""

import json
import logging
from pathlib import Path
import requests
import pandas as pd
from omegaconf import DictConfig

# Configuration du logger
logger = logging.getLogger(__name__)

def download_file(url: str, dest_path: Path) -> None:
    """Télécharge un fichier depuis une URL si nécessaire."""
    if not url:
        raise ValueError("URL de téléchargement manquante dans la configuration.")
    
    logger.info(f"Téléchargement en cours depuis : {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status() # Lève une erreur si code HTTP != 200
        
        # Création du dossier parent si inexistant
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        dest_path.write_bytes(response.content)
        logger.info("✓ Téléchargement terminé avec succès.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Échec du téléchargement : {e}")
        raise

def load_data_raw(cfg: DictConfig) -> pd.DataFrame:
    """
    Orchestre le chargement des données :
    1. Vérifie si le fichier existe localement.
    2. Si non, le télécharge.
    3. Charge le CSV en DataFrame.
    """
    # Construction du chemin complet
    raw_path = Path(cfg.data.raw.dir) / cfg.data.raw.file
    
    # 1. Gestion du fichier physique
    if not raw_path.exists():
        logger.warning(f"Fichier local introuvable : {raw_path}")
        download_file(url=cfg.data.raw.url, dest_path=raw_path)
    else:
        logger.info(f"Fichier local détecté : {raw_path}")

    # 2. Préparation des paramètres de lecture (depuis eda.yaml)
    load_params = {
        'encoding': cfg.eda.loading.encoding,
        'low_memory': cfg.eda.loading.low_memory,
        'na_values': cfg.eda.loading.na_values
    }

    # 3. Chargement Pandas
    try:
        df = pd.read_csv(raw_path, **load_params)
        logger.info(f"✓ DataFrame chargé : {df.shape[0]} lignes, {df.shape[1]} colonnes")
        return df
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du CSV : {e}")
        raise

def save_metadata(df: pd.DataFrame, cfg: DictConfig) -> None:
    #TODO: Logger ces metadata avec mlflow et l'inclure dans load_data_****() pour interim/ et processed/
    # Pour les fichiers raw,cette fonction ne sert à rien car tous le monde a systematiquement le bon csv (normalement)
    """Génère et sauvegarde des métadonnées techniques légères."""
    meta_path = Path(cfg.data.metadata.file)
    
    metadata = {
        "dataset": cfg.project.name,
        "source_file": cfg.data.raw.file,
        "n_rows": int(df.shape[0]),
        "n_columns": int(df.shape[1]),
        "columns": df.columns.tolist(),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024**2), 2),
        "dtypes": {k: str(v) for k, v in df.dtypes.items()}
    }

    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Métadonnées sauvegardées : {meta_path}")
