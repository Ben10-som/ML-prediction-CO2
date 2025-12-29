import pytest
from omegaconf import OmegaConf
from src.utils.config_loader import load_config, create_directories

@pytest.fixture
def mock_cfg():
    """Crée une configuration factice pour tester la création de dossiers."""
    return OmegaConf.create({
        "data": {
            "raw": {"data_dir": "tests/tmp/raw"},
            "interim": {"data_dir": "tests/tmp/interim"},
            "processed": {"data_dir": "tests/tmp/processed"},
            "figures": {"root_dir": "tests/tmp/figures"},
            "reports": {"root_dir": "tests/tmp/reports"}
        }
    })

def test_load_config_returns_dictconfig():
    """Vérifie que le chargement Hydra fonctionne et retourne le bon type."""
    try:
        cfg = load_config()
        assert cfg is not None
        assert OmegaConf.is_config(cfg)
    except Exception as e:
        pytest.fail(f"Le chargement de la config a échoué : {e}")

def test_create_directories(mock_cfg, tmp_path):
    """Vérifie que les dossiers sont créés physiquement."""
    # On remplace les chemins par un dossier temporaire géré par pytest
    mock_cfg.data.raw.data_dir = str(tmp_path / "raw")
    mock_cfg.data.reports.root_dir = str(tmp_path / "reports")
    
    create_directories(mock_cfg)
    
    assert (tmp_path / "raw").exists()
    assert (tmp_path / "reports").exists()
    assert (tmp_path / "raw").is_dir()

def test_load_config_with_overrides():
    """Vérifie que les surcharges (overrides) fonctionnent."""
    # on teste juste que l'appel ne crash pas avec des overrides
    cfg = load_config(overrides=["+test_key=123"])
    assert cfg.test_key == 123

def test_create_directories_missing_key():
    """Vérifie que la fonction ne crash pas si une clé est manquante (AttributeError)."""
    bad_cfg = OmegaConf.create({"data": {}}) # Structure incomplète
    try:
        create_directories(bad_cfg)
    except Exception as e:
        pytest.fail(f"La fonction a levé une exception au lieu de logger un warning : {e}")