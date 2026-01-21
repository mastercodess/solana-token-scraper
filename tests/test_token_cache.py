import pytest
from src.token_cache import TokenCache


def test_cache_starts_empty():
    """Test that new cache is empty"""
    cache = TokenCache()

    assert not cache.has_seen("TOKEN123")
    assert cache.size() == 0


def test_cache_marks_tokens_as_seen():
    """Test that cache remembers seen tokens"""
    cache = TokenCache()

    cache.mark_seen("TOKEN123")

    assert cache.has_seen("TOKEN123")
    assert cache.size() == 1


def test_cache_deduplicates_same_token():
    """Test that marking same token twice doesn't duplicate"""
    cache = TokenCache()

    cache.mark_seen("TOKEN123")
    cache.mark_seen("TOKEN123")

    assert cache.size() == 1


def test_cache_tracks_multiple_tokens():
    """Test that cache handles multiple tokens"""
    cache = TokenCache()

    cache.mark_seen("TOKEN1")
    cache.mark_seen("TOKEN2")
    cache.mark_seen("TOKEN3")

    assert cache.has_seen("TOKEN1")
    assert cache.has_seen("TOKEN2")
    assert cache.has_seen("TOKEN3")
    assert cache.size() == 3


def test_cache_clear_resets():
    """Test that clear removes all tokens"""
    cache = TokenCache()
    cache.mark_seen("TOKEN1")
    cache.mark_seen("TOKEN2")

    cache.clear()

    assert cache.size() == 0
    assert not cache.has_seen("TOKEN1")
