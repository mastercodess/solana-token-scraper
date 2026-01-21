"""Configuration management with validation"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import json


class HardFilters(BaseModel):
    """Hard filtering thresholds (safety gates)"""
    min_liquidity_usd: float = Field(default=5000, ge=0)
    min_maker_count: int = Field(default=20, ge=0)


class ScoringConfig(BaseModel):
    """Scoring weights and thresholds"""
    min_score: int = Field(default=5, ge=0, le=20)
    age_weight: float = Field(default=1.0, ge=0, le=5)
    volume_weight: float = Field(default=1.0, ge=0, le=5)
    momentum_weight: float = Field(default=0.5, ge=0, le=5)


class ScraperConfig(BaseModel):
    """Main configuration model"""
    scan_interval_seconds: int = Field(default=30, ge=10, le=300)
    hard_filters: HardFilters = Field(default_factory=HardFilters)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)


class ConfigManager:
    """Manages configuration loading and validation"""

    @staticmethod
    def load(config_path: Path) -> ScraperConfig:
        """Load and validate configuration from file"""
        if not config_path.exists():
            return ScraperConfig()

        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            return ScraperConfig(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid config file: {e}")
