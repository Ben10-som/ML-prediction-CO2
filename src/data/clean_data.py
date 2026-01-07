import logging
import pandas as pd
from omegaconf import DictConfig
from utils.config_loader import PROJECT_ROOT
from pathlib import Path
from .load_data import save_metadata 


# Import des étapes
from cleaning_steps.section_0 import Section0
from cleaning_steps.section_1 import Section1
from cleaning_steps.section_2 import Section2
from cleaning_steps.section_3 import Section3

logger = logging.getLogger(__name__)

def run_cleaning_pipeline(df: pd.DataFrame, cfg: DictConfig):
    # Résolution dynamique du chemin interim via PROJECT_ROOT
    interim_dir = (PROJECT_ROOT / cfg.data.interim.dir).resolve()
    interim_dir.mkdir(parents=True, exist_ok=True)

    steps_mapping = {
        "section_0": Section0,
        "section_1": Section1,
        "section_2": Section2,
        "section_3": Section3
    }

    current_df = df
    
    # Accès à cfg.cleaning.pipeline (chargé via config.yaml defaults)
    for step_name in cfg.cleaning.pipeline:
        if step_name in steps_mapping:
            logger.info(f"--- Exécution : {step_name} ---")
            processor = steps_mapping[step_name](step_name, cfg)
            current_df = processor.run(current_df)
            
            # Utilise ta logique de sauvegarde par étape
            processor.save_step(current_df, interim_dir)
            
    # Sauvegarde finale "Silver"
    final_path = interim_dir / cfg.data.interim.file
    current_df.to_csv(final_path, index=False)
    logger.info(f"✓ Données sauvegardées dans : {final_path}")
    
    return current_df


def export_and_audit_clean_data(df: pd.DataFrame, cfg: DictConfig):
    """
    Sauvegarde le fichier nettoyé et met à jour l'empreinte MD5 
    dans le JSON partagé pour l'équipe.
    """
    # 1. Résolution du chemin de sortie (via ta config)
    processed_dir = Path(cfg.data.processed.dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    file_path = processed_dir / cfg.data.processed.file

    # 2. Sauvegarde physique
    df.to_csv(file_path, index=False)
    logger.info(f"💾 Fichier nettoyé sauvegardé sous : {file_path}")

    # 3. Signature MD5
    # Cette fonction va comparer le hash actuel avec celui du JSON
    # et logger un WARNING si un collègue a une version différente.
    save_metadata(df, cfg, file_path)