# Solana Token Scraper - Design Document

**Date:** 2026-01-21
**Purpose:** Real-time discovery tool for newly listed Solana tokens on DexScreener

## Overview

A Python CLI tool that continuously monitors DexScreener for Solana tokens matching quality criteria, presenting matches in a live terminal dashboard. The user manually reviews matches and uses their own sniper tool for trading.

## High-Level Architecture

### Core Components

1. **Config Manager** - Loads and validates `config.json` with filtering thresholds
2. **DexScreener Client** - Handles API calls with rate limiting and retry logic
3. **Token Filter** - Applies balanced scoring to filter quality tokens
4. **Token Cache** - In-memory deduplication (session-based)
5. **Dashboard Renderer** - Live terminal UI using `rich` library
6. **Main Orchestrator** - Runs scan loop every 30 seconds (configurable)

### Data Flow

```
Config File → Config Manager
                    ↓
Main Loop: DexScreener API → Token Filter → Token Cache → Dashboard
          (every 30s)         (scoring)     (dedup)       (display)
```

## Filtering Strategy

### Hybrid Approach: Hard Gates + Scoring

**Hard Requirements (Safety Gates):**
- Liquidity > $5,000 USD
- Maker count > 20
- Valid price data exists

**Scoring Criteria (Quality Signals):**
- **Age score**: Newer = higher score
  - < 30 min: 3 points
  - < 1 hour: 2 points
  - < 2 hours: 1 point
- **Volume score**: Based on Volume/Liquidity ratio
  - High ratio indicates strong interest
- **Liquidity growth**: +2 points if trending upward
- **Price momentum**: +1 point each for positive 5m/1h changes

**Threshold:** Minimum score of 5 points to display (configurable)

### Configuration Structure

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

## Dashboard Interface

### Terminal UI Layout

```
╔═══════════════════════════════════════════════════════════════╗
║ 🔍 Solana Token Scraper - Live Feed                          ║
║ Last scan: 2026-01-21 15:23:45 | Next: 12s | Matches: 3     ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║ ✨ NEW MATCH - Score: 7/10                                    ║
║ Token: PumpXYZ...abc123                                       ║
║ Age: 25 minutes | Liquidity: $12.5K | Volume: $45K          ║
║ Makers: 67 | Price: $0.00234 (↑ 5m: +12%, 1h: +45%)        ║
║ [Copy Address]                                                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
Stats: 156 tokens scanned | 3 matches shown | 12 duplicates filtered
Press Ctrl+C to exit
```

### Features

- Newest matches at top
- All filtering criteria visible at a glance
- Color coding: Green (positive momentum), Yellow (caution)
- Full token address displayed for copy/paste
- Session statistics
- Auto-scrolling

## Error Handling & Reliability

### API Rate Limit Management

- DexScreener free tier: ~300 requests/5 minutes
- Our usage: ~10 requests/5 minutes (safe margin)
- Exponential backoff if rate limited: 30s → 60s → 120s
- Display rate limit status in dashboard

### Error Recovery

1. **Network failures** - Retry up to 3 times with 5s delays, keep running
2. **Invalid responses** - Skip malformed tokens, log warning, continue
3. **Missing data** - Use safe defaults, filter out if critical fields missing
4. **API downtime** - Continue retry with backoff, show "Waiting..." status

### Logging

- Errors written to `logs/scraper.log` (daily rotation)
- Console shows only critical errors
- `--debug` flag for verbose output

### Graceful Shutdown

- Ctrl+C stops cleanly
- Saves session stats
- No hanging processes

## Testing & Verification

### Development Testing

1. **Mock API Mode** - Test with sample JSON responses (`--mock` flag)
   - `test_data/new_token.json`
   - `test_data/high_volume_spike.json`
   - `test_data/should_filter_out.json`

2. **Unit Tests**
   - Config validation
   - Filter scoring logic
   - Token deduplication
   - Age calculation

3. **Integration Test**
   - Single end-to-end API call
   - Data parsing verification
   - Dashboard rendering
   - Log file creation

### Manual Verification Checklist

- [ ] Config file loads and validates
- [ ] API connection successful
- [ ] Dashboard renders correctly
- [ ] Token addresses accurate (spot-check on DexScreener)
- [ ] Filtering matches expected behavior
- [ ] No duplicate tokens in session
- [ ] Graceful shutdown works

### Built-in Verification Features

- `--dry-run`: Fetch and filter without displaying, show stats only
- `--verify-token <address>`: Check specific token against filters

## Technology Stack

- **Language:** Python 3.10+
- **Key Libraries:**
  - `requests` - API calls
  - `rich` - Terminal UI
  - `pydantic` - Config validation
  - `pytest` - Testing
- **API:** DexScreener public API

## Project Structure

```
SOL_scraper/
├── config.json                 # User configuration
├── src/
│   ├── main.py                # Entry point, orchestrator
│   ├── config_manager.py      # Config loading/validation
│   ├── dexscreener_client.py  # API interactions
│   ├── token_filter.py        # Filtering and scoring logic
│   ├── token_cache.py         # Session deduplication
│   └── dashboard.py           # Terminal UI rendering
├── tests/
│   ├── test_config.py
│   ├── test_filter.py
│   └── test_data/             # Mock API responses
├── logs/                      # Auto-generated logs
└── docs/
    └── plans/                 # This document
```

## Success Criteria

1. Scraper runs continuously without crashes
2. Displays only tokens matching balanced criteria
3. No duplicate tokens shown in same session
4. Dashboard updates smoothly every 30 seconds
5. Token addresses are accurate and copyable
6. Recovers automatically from API hiccups
7. User can easily tune thresholds via config file

## Future Enhancements (Out of Scope)

- Historical database of tokens
- Top trader tracking
- Multi-chain support
- Web dashboard
- Automated trading integration
