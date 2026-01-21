"""In-memory cache for token deduplication"""


class TokenCache:
    """Session-based cache to track seen tokens"""

    def __init__(self):
        self._seen: set[str] = set()

    def has_seen(self, token_address: str) -> bool:
        """Check if token has been seen this session"""
        return token_address in self._seen

    def mark_seen(self, token_address: str) -> None:
        """Mark token as seen"""
        self._seen.add(token_address)

    def size(self) -> int:
        """Get number of cached tokens"""
        return len(self._seen)

    def clear(self) -> None:
        """Clear all cached tokens"""
        self._seen.clear()
