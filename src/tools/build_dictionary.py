"""
Module de génération de dictionnaire de données (Extraction -> Traduction -> Documentation)

Ce script automatise la création d'une documentation technique en français à partir 
des métadonnées officielles au format JSON. Il permet de maintenir un dictionnaire 
de données à jour sans saisie manuelle, en intégrant des statistiques.
"""

import json
import logging
import sys
from pathlib import Path

# On récupère le chemin absolu du dossier 'src'
# (On remonte de 1 niveau depuis src/tools)
current_file = Path(__file__).resolve()
src_path = current_file.parents[1] 

if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from deep_translator import GoogleTranslator
from tqdm import tqdm
from omegaconf import DictConfig

from utils.config_loader import load_config, PROJECT_ROOT

logger = logging.getLogger(__name__)

def _resolve_path(path_str: str) -> Path:
    """Résout un chemin de manière défensive (identique à load_data)."""
    if not path_str or str(path_str).strip().lower() == "none":
        raise ValueError("Chemin invalide dans la configuration")
    p = Path(path_str)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return p

def format_stats(cached_contents: dict) -> str:
    """
    Formatte les métadonnées Socrata pour le rendu Markdown.
    Motivation : Extraire les insights clés (NAs, Range, Top valeurs) sans calcul lourd.
    """
    if not cached_contents:
        return ""
    
    stats = []
    non_null = int(cached_contents.get('non_null', 0))
    null_val = int(cached_contents.get('null', 0))
    total = non_null + null_val
    
    if null_val > 0 and total > 0:
        stats.append(f"NAs: {null_val} ({null_val/total:.1%})")
    
    if 'smallest' in cached_contents and 'largest' in cached_contents:
        stats.append(f"Range: {cached_contents['smallest']} à {cached_contents['largest']}")
    
    if 'top' in cached_contents:
        top_items = [f"{t['item']} ({t['count']})" for t in cached_contents['top'][:3]]
        stats.append(f"Top: {', '.join(top_items)}")
        
    return "<br>".join(stats)

def build_dictionary():
    """Pipeline principal de génération du dictionnaire."""
    cfg = load_config()
    
    try:
        raw_dir = _resolve_path(cfg.data.raw.dir)
        source_path = raw_dir / cfg.data.metadata.source_file
        report_dir = _resolve_path(cfg.data.reports.dir)/ "notebook_0"
        output_path = report_dir / cfg.data.metadata.output_doc
    except Exception as e:
        logger.error(f"Erreur configuration chemins : {e}")
        return

    if not source_path.exists():
        logger.error(f"Source metadata introuvable : {source_path}")
        return

    with open(source_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    translator = GoogleTranslator(source='en', target='fr')
    columns = data.get('columns', [])
    
    md_content = [
        f"# Dictionnaire de données : {data.get('name', 'Seattle 2016')}",
        "\n> Document généré automatiquement via Socrata Metadata API.",
        "\n| Colonne | Type | Description (FR) | Statistiques |",
        "| :--- | :--- | :--- | :--- |"
    ]

    logger.info(f"Traitement de {len(columns)} colonnes...")

    for col in tqdm(columns, desc="Traduction"):
        name = col.get('name')
        dtype = col.get('dataTypeName', 'text')
        raw_desc = col.get('description', '')
        
        try:
            desc = translator.translate(raw_desc[:4999]) if raw_desc else "N/A"
        except Exception:
            desc = raw_desc # Fallback
            
        stats = format_stats(col.get('cachedContents', {}))
        md_content.append(f"| **{name}** | `{dtype}` | {desc} | {stats} |")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(md_content), encoding='utf-8')
    logger.info(f"✓ Rapport Markdown prêt : {output_path}")

if __name__ == "__main__":
    build_dictionary()