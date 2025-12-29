import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.data.load_data import load_data_raw,save_metadata
import json

@pytest.fixture
def mock_cfg():
    """Fixture pour simuler la configuration Hydra"""
    from omegaconf import OmegaConf
    return OmegaConf.create({
        "data": {
            "raw": {
                "dir": "tests/tmp_raw",
                "file": "test_data.csv",
                "url": "http://fake-url.com/data.csv"
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
def test_load_data_raw_downloads_if_missing(mock_get, mock_cfg, tmp_path):
    """Teste si le téléchargement est déclenché quand le fichier est absent."""
    # Configurer le dossier temporaire
    mock_cfg.data.raw.dir = str(tmp_path)
    file_path = tmp_path / mock_cfg.data.raw.file
    
    # Simuler une réponse HTTP 200 avec un contenu CSV valide
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"OSEBuildingID,Data\n1,100"
    mock_get.return_value = mock_response

    # Exécuter
    df = load_data_raw(mock_cfg)

    # Vérifications
    assert mock_get.called
    assert file_path.exists()
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 2)

def test_load_data_raw_local_exists(mock_cfg, tmp_path):
    """Teste le chargement direct si le fichier existe déjà localement."""
    mock_cfg.data.raw.dir = str(tmp_path)
    file_path = tmp_path / mock_cfg.data.raw.file
    
    # Créer manuellement le fichier
    file_path.write_text("OSEBuildingID,Data\n1,100")

    with patch("src.data.load_data.requests.get") as mock_get:
        df = load_data_raw(mock_cfg)
        # requests.get ne doit PAS être appelé
        assert not mock_get.called
        assert len(df) == 1


def test_save_metadata_creates_file_and_content(tmp_path):
    """Teste que save_metadata génère un fichier JSON correct."""
    # DataFrame factice
    df = pd.DataFrame({
        "OSEBuildingID": [1, 2],
        "Data": [100, 200]
    })

    # Config factice
    from omegaconf import OmegaConf
    cfg = OmegaConf.create({
        "project": {"name": "seattle_energy_2016_ml"},
        "data": {
            "raw": {"file": "test_data.csv"},
            "metadata": {"file": str(tmp_path / "metadata.json")}
        }
    })

    # Exécuter la fonction
    save_metadata(df, cfg)

    # Vérifier que le fichier existe
    meta_path = Path(cfg.data.metadata.file)
    assert meta_path.exists()

    # Charger le contenu JSON
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Vérifications clés
    assert metadata["dataset"] == "seattle_energy_2016_ml"
    assert metadata["source_file"] == "test_data.csv"
    assert metadata["n_rows"] == 2
    assert metadata["n_columns"] == 2
    assert "OSEBuildingID" in metadata["columns"]
    assert "Data" in metadata["columns"]
    assert isinstance(metadata["memory_usage_mb"], float)
    assert metadata["dtypes"]["OSEBuildingID"] == "int64"
