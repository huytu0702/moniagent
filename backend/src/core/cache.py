"""
Caching utilities for performance optimization.
"""

import logging
from typing import Any, Callable, Optional, TypeVar, Dict
from functools import wraps
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheEntry:
    """Represents a cached entry with expiration."""

    def __init__(self, value: Any, ttl_seconds: int = 300):
        """
        Initialize a cache entry.

        Args:
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 5 minutes)
        """
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        """Initialize the cache."""
        self._store: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if key not in self._store:
            self._misses += 1
            return None

        entry = self._store[key]
        if entry.is_expired():
            del self._store[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        self._store[key] = CacheEntry(value, ttl_seconds)

    def delete(self, key: str) -> None:
        """Delete a cache entry."""
        if key in self._store:
            del self._store[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self._store.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total": total,
            "hit_rate": round(hit_rate, 2),
            "size": len(self._store),
        }


# Global cache instance
_cache = SimpleCache()


def cache_key(*parts) -> str:
    """Generate a cache key from parts."""
    return ":".join(str(p) for p in parts)


def get_cache_entry(key: str) -> Optional[Any]:
    """Get a value from global cache."""
    return _cache.get(key)


def set_cache_entry(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Set a value in global cache."""
    _cache.set(key, value, ttl_seconds)


def delete_cache_entry(key: str) -> None:
    """Delete a cache entry."""
    _cache.delete(key)


def clear_cache() -> None:
    """Clear all cache entries."""
    _cache.clear()


def cached(ttl_seconds: int = 300, key_builder: Optional[Callable] = None):
    """
    Decorator to cache function results.

    Args:
        ttl_seconds: Time to live for cached result
        key_builder: Optional function to build custom cache key

    Usage:
        @cached(ttl_seconds=600)
        def get_categories(user_id: str):
            # Expensive operation
            return categories

        # Or with custom key builder:
        @cached(ttl_seconds=600, key_builder=lambda user_id: f"user_cats:{user_id}")
        def get_categories(user_id: str):
            return categories
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Build cache key
            if key_builder:
                cache_k = key_builder(*args, **kwargs)
            else:
                # Generate key from function name and arguments
                arg_str = "_".join(str(a) for a in args)
                kwarg_str = "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
                cache_k = cache_key(func.__name__, arg_str, kwarg_str)

            # Try to get from cache
            cached_value = _cache.get(cache_k)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_k}")
                return cached_value

            # Not in cache, call function
            logger.debug(f"Cache miss for {cache_k}, computing...")
            result = func(*args, **kwargs)

            # Store in cache
            _cache.set(cache_k, result, ttl_seconds)
            return result

        # Add method to manually invalidate cache
        wrapper.invalidate = lambda *args, **kwargs: _cache.delete(
            key_builder(*args, **kwargs) if key_builder else cache_key(func.__name__)
        )

        return wrapper

    return decorator


def invalidate_user_cache(user_id: str) -> None:
    """Invalidate all cache entries for a user."""
    logger.debug(f"Invalidating cache for user {user_id}")
    # Clear entries matching user pattern
    keys_to_delete = [key for key in _cache._store if user_id in key]
    for key in keys_to_delete:
        _cache.delete(key)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return _cache.get_stats()
