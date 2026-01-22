"""Main orchestrator for Solana token scraper"""
import sys
import time
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime
from rich.live import Live
from src.config_manager import ConfigManager
from src.dexscreener_client import DexScreenerClient
from src.token_filter import TokenFilter
from src.token_cache import TokenCache
from src.dashboard import Dashboard, MatchedToken


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class SolanaScraperOrchestrator:
    """Main orchestrator for the scraper"""

    def __init__(self, config_path: Path):
        self.config = ConfigManager.load(config_path)
        self.client = DexScreenerClient()
        self.token_filter = TokenFilter(self.config)
        self.cache = TokenCache()
        self.dashboard = Dashboard()
        self.running = True

        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def run(self) -> None:
        """Run the main scan loop with live dashboard"""
        logger.info("Starting Solana Token Scraper")

        with Live(self.dashboard.render(0), refresh_per_second=1) as live:
            while self.running:
                # Perform scan
                self._scan_once()

                # Wait for next scan
                for remaining in range(self.config.scan_interval_seconds, 0, -1):
                    if not self.running:
                        break
                    live.update(self.dashboard.render(remaining))
                    time.sleep(1)

        logger.info("Scraper stopped")
        self._print_summary()

    def _scan_once(self) -> None:
        """Perform single scan cycle"""
        try:
            # Fetch tokens from API
            tokens = self.client.fetch_solana_tokens()

            scanned_count = len(tokens)
            duplicate_count = 0

            # Process each token
            for token in tokens:
                # Check if already seen
                if self.cache.has_seen(token.address):
                    duplicate_count += 1
                    continue

                # Score token
                score = self.token_filter.score_token(token)

                if score and score.passed:
                    # Add to dashboard
                    matched = MatchedToken(token=token, score=score)
                    self.dashboard.add_match(matched)
                    self.cache.mark_seen(token.address)
                    logger.info(f"Match found: {token.symbol} - Score: {score.total_score}")

            # Update stats
            self.dashboard.update_stats(scanned_count, duplicate_count)

        except Exception as e:
            logger.error(f"Scan failed: {e}")

    def _handle_shutdown(self, signum, frame) -> None:
        """Handle graceful shutdown"""
        logger.info("Shutdown signal received")
        self.running = False

    def _print_summary(self) -> None:
        """Print session summary"""
        print("\n" + "="*60)
        print("Session Summary")
        print("="*60)
        print(f"Total tokens scanned: {self.dashboard.total_scanned}")
        print(f"Total matches found: {self.dashboard.total_matches}")
        print(f"Total duplicates filtered: {self.dashboard.total_duplicates}")
        print("="*60)

    def verify_token(self, address: str) -> None:
        """Verify a specific token against filters"""
        print(f"\nVerifying token: {address}\n")

        tokens = self.client.fetch_solana_tokens()

        for token in tokens:
            if token.address == address:
                print(f"Token found: {token.name} ({token.symbol})")
                print(f"Liquidity: ${token.liquidity_usd:,.2f}")
                print(f"Maker count: {token.maker_count}")
                print(f"Age: {datetime.now() - token.created_at}")

                score = self.token_filter.score_token(token)

                if score:
                    print(f"\nScore Breakdown:")
                    print(f"  Age score: {score.age_score}")
                    print(f"  Volume score: {score.volume_score}")
                    print(f"  Momentum score: {score.momentum_score}")
                    print(f"  Total: {score.total_score}")
                    print(f"\nResult: {'✅ PASS' if score.passed else '❌ FAIL'}")
                else:
                    print("\nResult: ❌ FAIL (hard filter)")

                return

        print("Token not found in current DexScreener data")


def main():
    """Entry point for CLI"""
    parser = argparse.ArgumentParser(description="Solana Token Scraper")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="Path to config file (default: config.json)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run once and show stats only (no dashboard)"
    )
    parser.add_argument(
        "--verify-token",
        type=str,
        help="Verify specific token address against filters"
    )

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check config exists
    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)

    orchestrator = SolanaScraperOrchestrator(args.config)

    # Handle special modes
    if args.verify_token:
        orchestrator.verify_token(args.verify_token)
        return

    if args.dry_run:
        orchestrator._scan_once()
        orchestrator._print_summary()
        return

    # Normal run
    orchestrator.run()


if __name__ == "__main__":
    main()
