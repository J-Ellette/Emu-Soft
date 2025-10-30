"""Cache backend implementations."""

from abc import ABC, abstractmethod
from typing import Any, Optional
import time
import threading


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value, or None if not found or expired
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            timeout: Timeout in seconds (None for no expiration)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        pass

    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired, False otherwise
        """
        pass


class InMemoryCache(CacheBackend):
    """Simple in-memory cache implementation with TTL support.

    This cache stores values in memory and is suitable for single-process
    applications. For distributed systems, use a Redis-based backend.
    """

    def __init__(self, default_timeout: int = 300) -> None:
        """Initialize the in-memory cache.

        Args:
            default_timeout: Default timeout in seconds (default: 300)
        """
        self.default_timeout = default_timeout
        self._cache: dict[str, tuple[Any, Optional[float]]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value, or None if not found or expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check if expired
            if expiry is not None and time.time() > expiry:
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            timeout: Timeout in seconds (None for default, 0 for no expiration)
        """
        with self._lock:
            if timeout is None:
                timeout = self.default_timeout

            expiry = None if timeout == 0 else time.time() + timeout
            self._cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()

    def has(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired, False otherwise
        """
        return self.get(key) is not None

    def cleanup_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for key, (_, expiry) in self._cache.items()
                if expiry is not None and current_time > expiry
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)

    def size(self) -> int:
        """Get the number of items in the cache.

        Returns:
            Number of cached items
        """
        with self._lock:
            return len(self._cache)

    def __repr__(self) -> str:
        """Return string representation of the cache."""
        return f"<InMemoryCache size={self.size()}>"
