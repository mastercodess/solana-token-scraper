import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
from src.main import SolanaScraperOrchestrator
from src.dexscreener_client import TokenData
from src.token_filter import TokenScore


@patch('src.main.DexScreenerClient')
@patch('src.main.TokenFilter')
@patch('src.main.TokenCache')
@patch('src.main.Dashboard')
def test_orchestrator_initialization(mock_dash, mock_cache, mock_filter, mock_client):
    """Test orchestrator initializes all components"""
    config_path = Path("config.json")

    orchestrator = SolanaScraperOrchestrator(config_path)

    assert orchestrator.client is not None
    assert orchestrator.token_filter is not None
    assert orchestrator.cache is not None
    assert orchestrator.dashboard is not None


@patch('src.main.DexScreenerClient')
@patch('src.main.TokenFilter')
@patch('src.main.TokenCache')
@patch('src.main.Dashboard')
def test_orchestrator_single_scan_cycle(mock_dash, mock_cache, mock_filter, mock_client):
    """Test single scan cycle processes tokens correctly"""
    # Setup real token data
    mock_tokens = [
        TokenData(
            address="TOKEN1", name="Test1", symbol="T1",
            price_usd=0.001, liquidity_usd=10000, volume_24h=20000,
            maker_count=50, created_at=datetime.now() - timedelta(minutes=20)
        ),
        TokenData(
            address="TOKEN2", name="Test2", symbol="T2",
            price_usd=0.002, liquidity_usd=15000, volume_24h=30000,
            maker_count=60, created_at=datetime.now() - timedelta(minutes=25)
        )
    ]
    mock_client.return_value.fetch_solana_tokens.return_value = mock_tokens

    # Setup score with proper model
    mock_score = TokenScore(passed=True, total_score=7, age_score=3, volume_score=2, momentum_score=2)
    mock_filter.return_value.score_token.return_value = mock_score

    mock_cache_instance = mock_cache.return_value
    mock_cache_instance.has_seen.return_value = False

    orchestrator = SolanaScraperOrchestrator(Path("config.json"))

    # Run single scan
    orchestrator._scan_once()

    # Verify flow
    mock_client.return_value.fetch_solana_tokens.assert_called_once()
    assert mock_filter.return_value.score_token.call_count == 2
    assert mock_cache_instance.mark_seen.call_count == 2
