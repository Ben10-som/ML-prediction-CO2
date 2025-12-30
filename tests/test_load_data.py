import sys
from pathlib import Path

# =============================================================================
# 1. CORRECTION DES IMPORTS (CRITIQUE)
# =============================================================================
# On configure sys.path AVANT d'importer les modules du projet.
# Cela permet à Python de trouver "utils" comme s'il était à la racine, 
# =============================================================================

# Récupère la racine du projet (remonte de 'tests/' vers la racine)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"

# Ajoute 'src' au PYTHONPATH pour que 'from utils...' fonctionne dans load_data.py
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Ajoute la racine du projet au PYTHONPATH pour les imports absolus (ex: src.data...)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# 2. IMPORTS DES LIBRARIES & MODULES
# =============================================================================
import pytest
import json
import pandas as pd
from unittest.mock import patch, MagicMock
from omegaconf import OmegaConf

# Maintenant, l'import fonctionnera sans erreur "ModuleNotFoundError"
from src.data.load_data import load_data_raw, save_metadata

# =============================================================================
# 3. FIXTURES & TESTS
# =============================================================================

@pytest.fixture
def mock_cfg(tmp_path):
    """
    Fixture robuste simulant une configuration Hydra complète.
    Utilise tmp_path pour que les dossiers de test soient isolés.
    """
    return OmegaConf.create({
        "project": {
            "name": "test_project_co2",
            "root": str(tmp_path)  # Important pour _resolve_path
        },
        "data": {
            "raw": {
                "dir": str(tmp_path / "raw"),
                "file": "test_data.csv",
                "url": "http://fake-url.com/data.csv"
            },
            "metadata": {
                "file": str(tmp_path / "metadata" / "metadata.json")
            }
        },
        "eda": {
            "loading": {
                "encoding": "utf-8",
                "low_memory": False,
                "na_values": ["NA"]
            }
        }
    })

@patch("src.data.load_data.requests.get")
def test_load_data_raw_downloads_if_missing(mock_get, mock_cfg):
    """
    Teste le scénario "Cold Start" : Fichier absent -> Téléchargement -> Chargement.
    """
    # 1. Setup : Le fichier n'existe pas physiquement au début
    # Simulation de la réponse HTTP
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"OSEBuildingID,Data\n1,100\n2,200"
    mock_get.return_value = mock_response

    # 2. Action
    df = load_data_raw(mock_cfg)

    # 3. Assertions
    # Vérifie que requests.get a bien été appelé (car fichier absent)
    mock_get.assert_called_once_with("http://fake-url.com/data.csv", timeout=30)
    
    # Vérifie que le DataFrame est correct
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)
    assert df.iloc[0]["OSEBuildingID"] == 1

def test_load_data_raw_local_exists(mock_cfg):
    """
    Teste le scénario "Cache" : Fichier présent -> Pas de téléchargement -> Chargement direct.
    """
    # 1. Setup : On crée le fichier manuellement avant d'appeler la fonction
    raw_dir = Path(mock_cfg.data.raw.dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    file_path = raw_dir / mock_cfg.data.raw.file
    
    csv_content = "OSEBuildingID,Data\n99,999"
    file_path.write_text(csv_content, encoding="utf-8")

    # 2. Action : On patch requests pour s'assurer qu'il n'est PAS appelé
    with patch("src.data.load_data.requests.get") as mock_get:
        df = load_data_raw(mock_cfg)
        
        # 3. Assertions
        mock_get.assert_not_called() # Le point crucial : pas de téléchargement
        assert len(df) == 1
        assert df.iloc[0]["OSEBuildingID"] == 99

def test_save_metadata_structure(mock_cfg):
    """
    Teste que save_metadata produit un JSON valide avec les bonnes clés.
    """
    # 1. Setup : DataFrame factice
    df = pd.DataFrame({
        "OSEBuildingID": [1, 2, 3],
        "Price": [10.5, 20.0, 15.5],
        "Category": ["A", "B", "A"]
    })
    
    # Conversion explicite des types pour correspondre à ce que pandas fait souvent
    df["Category"] = df["Category"].astype("category")

    # 2. Action
    save_metadata(df, mock_cfg)

    # 3. Vérifications
    meta_path = Path(mock_cfg.data.metadata.file)
    assert meta_path.exists(), "Le fichier metadata.json n'a pas été créé"

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Vérification du contenu
    expected_keys = ["dataset", "source_file", "n_rows", "n_columns", "columns", "dtypes", "memory_usage_mb"]
    for key in expected_keys:
        assert key in metadata, f"Clé manquante dans metadata : {key}"

    assert metadata["n_rows"] == 3
    assert metadata["n_columns"] == 3
    assert "Category" in metadata["dtypes"]

# =============================================================================
# FIN DU TEST
# =============================================================================