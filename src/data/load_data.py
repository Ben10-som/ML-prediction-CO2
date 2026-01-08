"""
Module de chargement des données (Download -> Load -> Validate -> Audit)
"""

import json
import logging
import hashlib
import getpass
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd
from omegaconf import DictConfig

from utils.config_loader import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _resolve_path(path_str: str) -> Path:
    """Résout un chemin de manière défensive."""
    if not path_str or str(path_str).strip().lower() == "none":
        raise ValueError("Chemin invalide dans la configuration")

    p = Path(path_str)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return p


def _get_file_hash(filepath: Path) -> str:
    """Calcule l'empreinte MD5 d'un fichier pour vérifier son intégrité."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        # Lecture par blocs pour ne pas saturer la RAM
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


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


def save_metadata(df: pd.DataFrame, cfg: DictConfig, file_path: Path) -> None:
    """
    Audit Log : Sauvegarde les métadonnées uniquement si les données ont changé.
    Gère un historique (liste) au lieu d'écraser le fichier.
    """
    meta_path = _resolve_path(cfg.data.metadata.file)
    
    # 1. Calcul de l'empreinte actuelle
    current_hash = _get_file_hash(file_path)
    
    # 2. Construction de la nouvelle entrée
    new_record = {
        "timestamp": datetime.now().isoformat(),
        "user": getpass.getuser(),  # Qui a lancé le script ?
        "file_name": file_path.name,
        "file_hash": current_hash,
        "n_rows": int(df.shape[0]),
        "n_columns": int(df.shape[1]),
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024**2), 2),
        "status": "unchanged" # Par défaut
    }

    # 3. Chargement de l'historique existant
    history = []
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                # Si c'est l'ancien format (dict), on le convertit en liste
                if isinstance(content, dict):
                    history = [content]
                else:
                    history = content
        except json.JSONDecodeError:
            logger.warning("Fichier métadonnées corrompu, réinitialisation.")
            history = []

    # 4. Logique de détection de changement
    last_record = history[-1] if history else None
    data_has_changed = False
    
    if last_record is None:
        new_record["status"] = "created"
        data_has_changed = True
    elif last_record.get("file_hash") != current_hash:
        new_record["status"] = "modified"
        data_has_changed = True
        # On ne loggue l'alerte QUE si le fichier n'est pas celui qu'on vient de produire
        # Pour l'instant, on reste informatif :
        logger.info(f" Nouvelle version détectée pour {file_path.name} (MàJ de l'historique).")
    else:
        logger.info(f"✔️ {file_path.name} : Identique à la version précédente.")
        return

    #  Sauvegarde si changement
    if data_has_changed:
        history.append(new_record)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Historique mis à jour : {meta_path}")


def load_data_raw(cfg: DictConfig) -> pd.DataFrame:
    """Chargement robuste avec audit automatique."""
    raw_dir = _resolve_path(cfg.data.raw.dir)
    raw_file = cfg.data.raw.file
    raw_path = raw_dir / raw_file

    if not raw_path.exists():
        logger.warning(f"Fichier local introuvable : {raw_path}")
        download_file(url=cfg.data.raw.url, dest_path=raw_path)

    load_params = {
        "encoding": cfg.eda.loading.encoding,
        "low_memory": cfg.eda.loading.low_memory,
        "na_values": cfg.eda.loading.na_values,
    }

    try:
        df = pd.read_csv(raw_path, **load_params)
        logger.info(f"DataFrame chargé : {df.shape[0]} lignes, {df.shape[1]} colonnes")
        
        # APPEL AUTOMATIQUE DE L'AUDIT ICI
        # On passe raw_path pour calculer le hash du fichier source
        save_metadata(df, cfg, raw_path) 
        
        return df
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du CSV : {e}")
        raise