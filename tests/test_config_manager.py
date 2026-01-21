import pytest
from pathlib import Path
from src.config_manager import ConfigManager, ScraperConfig


def test_load_valid_config(tmp_path):
    """Test loading a valid config file"""
    config_file = tmp_path / "config.json"
    config_file.write_text("""{
        "scan_interval_seconds": 30,
        "hard_filters": {
            "min_liquidity_usd": 5000,
            "min_maker_count": 20
        },
        "scoring": {
            "min_score": 5,
            "age_weight": 1.0,
            "volume_weight": 1.0,
            "momentum_weight": 0.5
        }
    }""")

    config = ConfigManager.load(config_file)

    assert config.scan_interval_seconds == 30
    assert config.hard_filters.min_liquidity_usd == 5000
    assert config.hard_filters.min_maker_count == 20
    assert config.scoring.min_score == 5


def test_load_missing_config_uses_defaults():
    """Test that missing config uses sensible defaults"""
    config = ConfigManager.load(Path("nonexistent.json"))

    assert config.scan_interval_seconds == 30
    assert config.hard_filters.min_liquidity_usd == 5000


def test_invalid_config_raises_error(tmp_path):
    """Test that invalid config raises validation error"""
    config_file = tmp_path / "bad_config.json"
    config_file.write_text('{"scan_interval_seconds": -10}')

    with pytest.raises(ValueError):
        ConfigManager.load(config_file)
