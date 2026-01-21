import pytest
from unittest.mock import Mock, patch
from src.dexscreener_client import DexScreenerClient, TokenData


@pytest.fixture
def mock_response():
    """Mock DexScreener API response"""
    return {
        "pairs": [
            {
                "chainId": "solana",
                "pairAddress": "ABC123",
                "baseToken": {
                    "address": "TOKEN_ABC",
                    "name": "TestToken",
                    "symbol": "TEST"
                },
                "priceUsd": "0.00123",
                "liquidity": {"usd": 15000},
                "volume": {"h24": 50000},
                "txns": {
                    "h24": {"buys": 45, "sells": 22}
                },
                "priceChange": {
                    "m5": 12.5,
                    "h1": 45.2
                },
                "pairCreatedAt": 1705850000000
            }
        ]
    }


def test_fetch_solana_tokens_success(mock_response):
    """Test successful API call returns parsed tokens"""
    client = DexScreenerClient()

    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        tokens = client.fetch_solana_tokens()

        assert len(tokens) == 1
        assert tokens[0].address == "TOKEN_ABC"
        assert tokens[0].liquidity_usd == 15000
        assert tokens[0].maker_count == 67


def test_fetch_with_network_error_retries():
    """Test that network errors trigger retry logic"""
    client = DexScreenerClient(max_retries=2)

    with patch('requests.get') as mock_get:
        mock_get.side_effect = [
            Exception("Network error"),
            Mock(json=lambda: {"pairs": []}, status_code=200)
        ]

        tokens = client.fetch_solana_tokens()

        assert mock_get.call_count == 2
        assert tokens == []


def test_fetch_with_rate_limit_returns_empty():
    """Test that rate limit (429) returns empty list"""
    client = DexScreenerClient()

    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 429

        tokens = client.fetch_solana_tokens()

        assert tokens == []
