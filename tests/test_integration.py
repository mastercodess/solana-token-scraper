import pytest
import json
from pathlib import Path
from unittest.mock import patch, Mock
from src.main import SolanaScraperOrchestrator


@pytest.fixture
def mock_api_response():
    """Load mock DexScreener response"""
    fixture_path = Path(__file__).parent / "fixtures" / "mock_dexscreener_response.json"
    with open(fixture_path) as f:
        return json.load(f)


def test_end_to_end_scan_filters_correctly(mock_api_response, tmp_path):
    """Test complete scan cycle with real data flow"""
    # Setup config
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
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
    }))

    # Mock API to return fixture data
    mock_response = Mock()
    mock_response.json.return_value = mock_api_response
    mock_response.status_code = 200

    with patch('requests.get', return_value=mock_response):
        # Create orchestrator
        orchestrator = SolanaScraperOrchestrator(config_path)

        # Run single scan
        orchestrator._scan_once()

        # Verify results
        # Should have 1 match (FRESH_TOKEN) and 1 filtered (LOW_LIQ)
        assert orchestrator.dashboard.total_matches == 1
        assert len(orchestrator.dashboard.matches) == 1

        # Verify the match is the correct token
        matched = orchestrator.dashboard.matches[0]
        assert matched.token.address == "FRESH_TOKEN_123"
        assert matched.score.passed is True


def test_config_validation_integration(tmp_path):
    """Test that invalid config fails gracefully"""
    bad_config = tmp_path / "bad_config.json"
    bad_config.write_text('{"scan_interval_seconds": -10}')

    with pytest.raises(ValueError):
        orchestrator = SolanaScraperOrchestrator(bad_config)
