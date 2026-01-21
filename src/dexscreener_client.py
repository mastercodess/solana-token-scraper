"""DexScreener API client with retry logic"""
import time
import logging
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import requests


logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    """Parsed token data from DexScreener"""
    address: str
    name: str
    symbol: str
    price_usd: float
    liquidity_usd: float
    volume_24h: float
    maker_count: int
    price_change_5m: Optional[float] = None
    price_change_1h: Optional[float] = None
    created_at: datetime


class DexScreenerClient:
    """Client for DexScreener API with error handling"""

    BASE_URL = "https://api.dexscreener.com/latest/dex"

    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def fetch_solana_tokens(self) -> List[TokenData]:
        """Fetch latest Solana tokens from DexScreener"""
        url = f"{self.BASE_URL}/tokens/solana"

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=10)

                if response.status_code == 429:
                    logger.warning("Rate limited by DexScreener API")
                    return []

                if response.status_code != 200:
                    logger.error(f"API error: {response.status_code}")
                    return []

                data = response.json()
                return self._parse_tokens(data)

            except Exception as e:
                logger.error(f"API call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                continue

        return []

    def _parse_tokens(self, data: dict) -> List[TokenData]:
        """Parse API response into TokenData objects"""
        tokens = []

        for pair in data.get("pairs", []):
            if pair.get("chainId") != "solana":
                continue

            try:
                base_token = pair["baseToken"]
                txns = pair.get("txns", {}).get("h24", {})
                buys = txns.get("buys", 0)
                sells = txns.get("sells", 0)

                token = TokenData(
                    address=base_token["address"],
                    name=base_token.get("name", "Unknown"),
                    symbol=base_token.get("symbol", "???"),
                    price_usd=float(pair.get("priceUsd", 0)),
                    liquidity_usd=pair.get("liquidity", {}).get("usd", 0),
                    volume_24h=pair.get("volume", {}).get("h24", 0),
                    maker_count=buys + sells,
                    price_change_5m=pair.get("priceChange", {}).get("m5"),
                    price_change_1h=pair.get("priceChange", {}).get("h1"),
                    created_at=datetime.fromtimestamp(
                        pair.get("pairCreatedAt", 0) / 1000
                    )
                )
                tokens.append(token)

            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse token: {e}")
                continue

        return tokens
