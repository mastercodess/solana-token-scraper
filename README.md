# Solana Token Scraper

Real-time discovery tool for newly listed Solana tokens on DexScreener.

## Features

- **Live Dashboard** - Real-time terminal UI showing matched tokens
- **Balanced Filtering** - Combines age, volume, liquidity, and momentum scoring
- **Session Deduplication** - Never see the same token twice in a session
- **Robust Error Handling** - Automatic retry on network failures
- **Configurable** - Adjust all thresholds via `config.json`

## Installation

```bash
# Clone repository
git clone <repo-url>
cd SOL_scraper

# Install dependencies
pip install -e ".[dev]"
```

## Configuration

Edit `config.json` to customize filtering:

```json
{
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
}
```

## Usage

### Basic Usage

```bash
solana-scraper
```

### CLI Options

```bash
# Use custom config file
solana-scraper --config my_config.json

# Enable debug logging
solana-scraper --debug

# Dry run (stats only, no dashboard)
solana-scraper --dry-run

# Verify specific token
solana-scraper --verify-token TOKEN_ADDRESS
```

## How It Works

1. **Scan** - Fetches latest Solana tokens from DexScreener every 30s
2. **Filter** - Applies hard gates (liquidity, makers) and scoring (age, volume, momentum)
3. **Deduplicate** - Skips tokens already shown this session
4. **Display** - Shows matches in live terminal dashboard

## Scoring System

**Hard Filters (must pass all):**
- Liquidity ≥ $5,000
- Maker count ≥ 20
- Valid price data

**Scoring (need ≥ 5 points):**
- Age: < 30min (3pts), < 1hr (2pts), < 2hr (1pt)
- Volume/Liquidity ratio: > 5x (3pts), > 2x (2pts), > 1x (1pt)
- Momentum: +1pt each for positive 5m/1h price change

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_filter.py::test_age_scoring_tiers -v
```

## Troubleshooting

**No matches appearing:**
- Lower `min_score` in config
- Reduce `min_liquidity_usd` threshold
- Check logs in `logs/scraper.log`

**Rate limited:**
- Increase `scan_interval_seconds` to 60+
- Wait a few minutes and retry

**Dashboard not updating:**
- Check terminal supports Rich library
- Try updating `rich` package: `pip install --upgrade rich`

## License

MIT
