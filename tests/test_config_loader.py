import pytest
from omegaconf import OmegaConf
from src.utils.config_loader import load_config, create_directories

@pytest.fixture
def mock_cfg():
    """Crée une configuration factice alignée sur la nouvelle structure (.dir)."""
    return OmegaConf.create({
        "data": {
            "raw": {"dir": "tests/tmp/raw"},
            "interim": {"dir": "tests/tmp/interim"},
            "processed": {"dir": "tests/tmp/processed"},
            "figures": {"dir": "tests/tmp/figures"},
            "reports": {"dir": "tests/tmp/reports"}
        }
    })

def test_load_config_returns_dictconfig():
    """Vérifie que le chargement Hydra fonctionne."""
    cfg = load_config()
    assert cfg is not None
    assert OmegaConf.is_config(cfg)

def test_create_directories(mock_cfg, tmp_path):
    """Vérifie que les dossiers sont créés physiquement avec la clé .dir."""
    # On écrase les chemins de la fixture par le dossier temporaire de pytest
    mock_cfg.data.raw.dir = str(tmp_path / "raw")
    mock_cfg.data.reports.dir = str(tmp_path / "reports")
    
    create_directories(mock_cfg)
    
    assert (tmp_path / "raw").exists()
    assert (tmp_path / "reports").exists()

def test_load_config_with_overrides():
    """Vérifie que les surcharges (overrides) fonctionnent."""
    cfg = load_config(overrides=["+test_key=123"])
    assert cfg.test_key == 123

def test_create_directories_missing_key():
    """Vérifie la robustesse si une section data est vide."""
    bad_cfg = OmegaConf.create({"data": {"raw": {}}}) 
    # Ne doit pas lever d'exception, juste passer à la suite
    create_directories(bad_cfg)