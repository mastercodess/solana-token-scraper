"""Token filtering with balanced scoring logic"""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from src.dexscreener_client import TokenData
from src.config_manager import ScraperConfig


class TokenScore(BaseModel):
    """Score breakdown for a token"""
    age_score: int = 0
    volume_score: int = 0
    momentum_score: int = 0
    total_score: int = 0
    passed: bool = False


class TokenFilter:
    """Filters and scores tokens based on config criteria"""

    def __init__(self, config: ScraperConfig):
        self.config = config

    def score_token(self, token: TokenData) -> Optional[TokenScore]:
        """Score a token, return None if it fails hard filters"""
        # Hard filters (safety gates)
        if not self._passes_hard_filters(token):
            return None

        # Calculate scores
        age_score = self._calculate_age_score(token)
        volume_score = self._calculate_volume_score(token)
        momentum_score = self._calculate_momentum_score(token)

        # Apply weights
        weighted_age = int(age_score * self.config.scoring.age_weight)
        weighted_volume = int(volume_score * self.config.scoring.volume_weight)
        weighted_momentum = int(momentum_score * self.config.scoring.momentum_weight)

        total = weighted_age + weighted_volume + weighted_momentum

        return TokenScore(
            age_score=age_score,
            volume_score=volume_score,
            momentum_score=momentum_score,
            total_score=total,
            passed=total >= self.config.scoring.min_score
        )

    def _passes_hard_filters(self, token: TokenData) -> bool:
        """Check if token passes safety gates"""
        if token.liquidity_usd < self.config.hard_filters.min_liquidity_usd:
            return False
        if token.maker_count < self.config.hard_filters.min_maker_count:
            return False
        if token.price_usd <= 0:
            return False
        return True

    def _calculate_age_score(self, token: TokenData) -> int:
        """Score based on token age"""
        age = datetime.now() - token.created_at

        if age < timedelta(minutes=30):
            return 3
        elif age < timedelta(hours=1):
            return 2
        elif age < timedelta(hours=2):
            return 1
        return 0

    def _calculate_volume_score(self, token: TokenData) -> int:
        """Score based on volume/liquidity ratio"""
        if token.liquidity_usd == 0:
            return 0

        ratio = token.volume_24h / token.liquidity_usd

        if ratio > 5:
            return 3
        elif ratio > 2:
            return 2
        elif ratio > 1:
            return 1
        return 0

    def _calculate_momentum_score(self, token: TokenData) -> int:
        """Score based on price momentum"""
        score = 0

        if token.price_change_5m and token.price_change_5m > 0:
            score += 1

        if token.price_change_1h and token.price_change_1h > 0:
            score += 1

        return score
