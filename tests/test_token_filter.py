import pytest
from datetime import datetime, timedelta
from src.token_filter import TokenFilter, TokenScore
from src.dexscreener_client import TokenData
from src.config_manager import ScraperConfig


@pytest.fixture
def config():
    """Default config for testing"""
    return ScraperConfig()


@pytest.fixture
def fresh_token():
    """Token created 20 minutes ago"""
    return TokenData(
        address="FRESH123",
        name="FreshToken",
        symbol="FRESH",
        price_usd=0.001,
        liquidity_usd=10000,
        volume_24h=50000,
        maker_count=80,
        price_change_5m=15.0,
        price_change_1h=50.0,
        created_at=datetime.now() - timedelta(minutes=20)
    )


def test_score_fresh_token_passes(config, fresh_token):
    """Test that a fresh quality token passes all filters"""
    filter = TokenFilter(config)

    score = filter.score_token(fresh_token)

    assert score is not None
    assert score.total_score >= config.scoring.min_score
    assert score.age_score == 3  # < 30 min
    assert score.passed


def test_filter_by_liquidity_threshold(config):
    """Test that low liquidity tokens are filtered out"""
    token = TokenData(
        address="LOW_LIQ",
        name="LowLiq",
        symbol="LL",
        price_usd=0.001,
        liquidity_usd=1000,  # Below 5000 threshold
        volume_24h=10000,
        maker_count=50,
        created_at=datetime.now() - timedelta(minutes=10)
    )

    filter = TokenFilter(config)
    score = filter.score_token(token)

    assert score is None  # Filtered out


def test_filter_by_maker_count(config):
    """Test that tokens with low maker count are filtered"""
    token = TokenData(
        address="LOW_MAKERS",
        name="LowMakers",
        symbol="LM",
        price_usd=0.001,
        liquidity_usd=10000,
        volume_24h=20000,
        maker_count=10,  # Below 20 threshold
        created_at=datetime.now() - timedelta(minutes=10)
    )

    filter = TokenFilter(config)
    score = filter.score_token(token)

    assert score is None


def test_age_scoring_tiers():
    """Test age scoring at different time intervals"""
    config = ScraperConfig()
    filter = TokenFilter(config)

    # < 30 min = 3 points
    token_20min = TokenData(
        address="T1", name="T1", symbol="T1",
        price_usd=0.001, liquidity_usd=10000,
        volume_24h=20000, maker_count=50,
        created_at=datetime.now() - timedelta(minutes=20)
    )

    # < 1 hour = 2 points
    token_45min = TokenData(
        address="T2", name="T2", symbol="T2",
        price_usd=0.001, liquidity_usd=10000,
        volume_24h=20000, maker_count=50,
        created_at=datetime.now() - timedelta(minutes=45)
    )

    # < 2 hours = 1 point
    token_90min = TokenData(
        address="T3", name="T3", symbol="T3",
        price_usd=0.001, liquidity_usd=10000,
        volume_24h=20000, maker_count=50,
        created_at=datetime.now() - timedelta(minutes=90)
    )

    score1 = filter.score_token(token_20min)
    score2 = filter.score_token(token_45min)
    score3 = filter.score_token(token_90min)

    assert score1.age_score == 3
    assert score2.age_score == 2
    assert score3.age_score == 1


def test_volume_ratio_scoring():
    """Test volume/liquidity ratio scoring"""
    config = ScraperConfig()
    filter = TokenFilter(config)

    # High volume relative to liquidity
    high_vol_token = TokenData(
        address="HV", name="HV", symbol="HV",
        price_usd=0.001,
        liquidity_usd=5000,
        volume_24h=50000,  # 10x ratio
        maker_count=50,
        created_at=datetime.now() - timedelta(minutes=30)
    )

    # Low volume relative to liquidity
    low_vol_token = TokenData(
        address="LV", name="LV", symbol="LV",
        price_usd=0.001,
        liquidity_usd=20000,
        volume_24h=10000,  # 0.5x ratio
        maker_count=50,
        created_at=datetime.now() - timedelta(minutes=30)
    )

    score_high = filter.score_token(high_vol_token)
    score_low = filter.score_token(low_vol_token)

    assert score_high.volume_score > score_low.volume_score
