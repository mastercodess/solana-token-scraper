"""Live terminal dashboard using Rich library"""
from datetime import datetime
from typing import List
from pydantic import BaseModel
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from src.dexscreener_client import TokenData
from src.token_filter import TokenScore


class MatchedToken(BaseModel):
    """Container for matched token with score"""
    token: TokenData
    score: TokenScore


class Dashboard:
    """Terminal UI for displaying matched tokens"""

    def __init__(self):
        self.console = Console()
        self.matches: List[MatchedToken] = []
        self.total_scanned = 0
        self.total_matches = 0
        self.total_duplicates = 0
        self.last_scan: datetime = datetime.now()

    def add_match(self, matched: MatchedToken) -> None:
        """Add a new matched token to display"""
        self.matches.insert(0, matched)  # Newest first
        self.total_matches += 1

        # Keep only last 10 matches displayed
        if len(self.matches) > 10:
            self.matches = self.matches[:10]

    def update_stats(self, scanned: int, duplicates: int) -> None:
        """Update scan statistics"""
        self.total_scanned += scanned
        self.total_duplicates += duplicates
        self.last_scan = datetime.now()

    def render(self, next_scan_in: int) -> Panel:
        """Render the dashboard as a Rich Panel"""
        # Header
        header = Text()
        header.append("🔍 Solana Token Scraper - Live Feed\n", style="bold cyan")
        header.append(f"Last scan: {self.last_scan.strftime('%Y-%m-%d %H:%M:%S')} | ", style="dim")
        header.append(f"Next: {next_scan_in}s | ", style="dim")
        header.append(f"Matches: {self.total_matches}", style="bold green")

        # Matches table
        table = Table(show_header=False, box=None, padding=(1, 2))

        for match in self.matches:
            token = match.token
            score = match.score

            # Match header
            match_text = Text()
            match_text.append("✨ NEW MATCH - ", style="bold yellow")
            match_text.append(f"Score: {score.total_score}/10\n", style="bold")

            # Token address
            match_text.append(f"Token: {token.address}\n", style="cyan")

            # Metrics line
            age_str = self._format_age(token.created_at)
            liq_str = self._format_currency(token.liquidity_usd)
            vol_str = self._format_currency(token.volume_24h)
            match_text.append(f"Age: {age_str} | Liquidity: {liq_str} | Volume: {vol_str}\n")

            # Price and momentum
            price_5m = f"{token.price_change_5m:+.1f}%" if token.price_change_5m is not None else "N/A"
            price_1h = f"{token.price_change_1h:+.1f}%" if token.price_change_1h is not None else "N/A"
            match_text.append(
                f"Makers: {token.maker_count} | "
                f"Price: ${token.price_usd:.6f} "
                f"(↑ 5m: {price_5m}, 1h: {price_1h})\n",
                style="green"
            )

            table.add_row(match_text)
            table.add_row(Text("─" * 60, style="dim"))

        # Stats footer
        footer = Text()
        footer.append(
            f"Stats: {self.total_scanned} tokens scanned | "
            f"{self.total_matches} matches shown | "
            f"{self.total_duplicates} duplicates filtered\n",
            style="dim"
        )
        footer.append("Press Ctrl+C to exit", style="dim italic")

        # Combine all
        content = Text()
        content.append(header)
        content.append("\n\n")
        if self.matches:
            content.append(table)
        else:
            content.append("Waiting for matches...\n", style="dim italic")
        content.append("\n")
        content.append(footer)

        return Panel(content, border_style="cyan", padding=(1, 2))

    def _format_age(self, created_at: datetime) -> str:
        """Format token age for display"""
        age = datetime.now() - created_at
        total_minutes = age.total_seconds() / 60

        if total_minutes < 60:
            return f"{int(total_minutes)} minutes"
        else:
            hours = total_minutes / 60
            return f"{hours:.1f} hours"

    def _format_currency(self, value: float) -> str:
        """Format currency with K/M suffixes"""
        if value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value / 1_000:.1f}K"
        else:
            return f"${value:.0f}"
