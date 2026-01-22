import pytest
from datetime import datetime, timedelta
from src.dashboard import Dashboard, MatchedToken
from src.dexscreener_client import TokenData
from src.token_filter import TokenScore


@pytest.fixture
def matched_token():
    """Sample matched token"""
    token = TokenData(
        address="ABC123XYZ",
        name="TestToken",
        symbol="TEST",
        price_usd=0.00234,
        liquidity_usd=12500,
        volume_24h=45000,
        maker_count=67,
        price_change_5m=12.5,
        price_change_1h=45.2,
        created_at=datetime.now() - timedelta(minutes=25)
    )

    score = TokenScore(
        age_score=3,
        volume_score=2,
        momentum_score=2,
        total_score=7,
        passed=True
    )

    return MatchedToken(token=token, score=score)


def test_dashboard_initialization():
    """Test dashboard can be initialized"""
    dashboard = Dashboard()

    assert dashboard.total_scanned == 0
    assert dashboard.total_matches == 0
    assert dashboard.total_duplicates == 0


def test_dashboard_add_match(matched_token):
    """Test adding a matched token"""
    dashboard = Dashboard()

    dashboard.add_match(matched_token)

    assert dashboard.total_matches == 1
    assert len(dashboard.matches) == 1


def test_dashboard_update_stats():
    """Test updating scan statistics"""
    dashboard = Dashboard()

    dashboard.update_stats(scanned=150, duplicates=12)

    assert dashboard.total_scanned == 150
    assert dashboard.total_duplicates == 12


def test_dashboard_format_token_age():
    """Test age formatting for display"""
    dashboard = Dashboard()

    # Test minutes
    age_25min = datetime.now() - timedelta(minutes=25)
    assert dashboard._format_age(age_25min) == "25 minutes"

    # Test hours
    age_90min = datetime.now() - timedelta(minutes=90)
    assert dashboard._format_age(age_90min) == "1.5 hours"


def test_dashboard_format_currency():
    """Test currency formatting"""
    dashboard = Dashboard()

    assert dashboard._format_currency(12500) == "$12.5K"
    assert dashboard._format_currency(1500000) == "$1.5M"
    assert dashboard._format_currency(500) == "$500"
