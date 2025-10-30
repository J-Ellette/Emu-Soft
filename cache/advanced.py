"""Advanced caching features including cache invalidation, warming, and monitoring."""

from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import re
import time
from mycms.cache.backend import CacheBackend


@dataclass
class CachePolicy:
    """Cache policy configuration for different content types."""

    timeout: int  # Cache timeout in seconds
    tags: Optional[Set[str]] = None  # Cache tags for invalidation
    vary_on: Optional[List[str]] = None  # Headers to vary cache on
    stale_while_revalidate: Optional[int] = None  # Serve stale for X seconds
    cache_control: Optional[str] = None  # Cache-Control header


class CacheTag:
    """Cache tagging system for smart invalidation."""

    def __init__(self, cache_backend: CacheBackend) -> None:
        """Initialize cache tag manager.

        Args:
            cache_backend: Cache backend instance
        """
        self.cache_backend = cache_backend
        self._tag_prefix = "cache_tag:"
        self._key_prefix = "cache_keys:"

    def _tag_key(self, tag: str) -> str:
        """Generate key for tag version.

        Args:
            tag: Tag name

        Returns:
            Tag version key
        """
        return f"{self._tag_prefix}{tag}"

    def _keys_key(self, tag: str) -> str:
        """Generate key for tag's cache keys set.

        Args:
            tag: Tag name

        Returns:
            Tag keys set key
        """
        return f"{self._key_prefix}{tag}"

    def get_tag_version(self, tag: str) -> int:
        """Get current version for a tag.

        Args:
            tag: Tag name

        Returns:
            Tag version number
        """
        tag_key = self._tag_key(tag)
        version = self.cache_backend.get(tag_key)
        if version is None:
            version = int(time.time())
            self.cache_backend.set(tag_key, version, timeout=None)
        return version

    def invalidate_tag(self, tag: str) -> None:
        """Invalidate all cache entries with a tag.

        Args:
            tag: Tag name to invalidate
        """
        # Increment tag version - all keys with old version become invalid
        tag_key = self._tag_key(tag)
        new_version = int(time.time())
        self.cache_backend.set(tag_key, new_version, timeout=None)

        # Also clear the keys set for cleanup
        keys_key = self._keys_key(tag)
        keys = self.cache_backend.get(keys_key) or set()
        for key in keys:
            self.cache_backend.delete(key)

        self.cache_backend.delete(keys_key)

    def tag_cache_key(self, cache_key: str, tags: Set[str]) -> str:
        """Create a versioned cache key with tags.

        Args:
            cache_key: Original cache key
            tags: Set of tags

        Returns:
            Versioned cache key
        """
        if not tags:
            return cache_key

        # Get versions for all tags
        versions = [str(self.get_tag_version(tag)) for tag in sorted(tags)]
        version_hash = hashlib.md5(":".join(versions).encode()).hexdigest()[:8]

        # Store key in each tag's set
        for tag in tags:
            keys_key = self._keys_key(tag)
            keys = self.cache_backend.get(keys_key) or set()
            keys.add(cache_key)
            self.cache_backend.set(keys_key, keys, timeout=3600)

        return f"{cache_key}:v{version_hash}"


class CacheInvalidator:
    """Smart cache invalidation with pattern matching."""

    def __init__(self, cache_backend: CacheBackend) -> None:
        """Initialize cache invalidator.

        Args:
            cache_backend: Cache backend instance
        """
        self.cache_backend = cache_backend
        self._key_registry: Dict[str, datetime] = {}

    def register_key(self, key: str) -> None:
        """Register a cache key for tracking.

        Args:
            key: Cache key to register
        """
        self._key_registry[key] = datetime.now(timezone.utc)

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.

        Args:
            pattern: Regex pattern to match keys

        Returns:
            Number of keys invalidated
        """
        regex = re.compile(pattern)
        count = 0

        for key in list(self._key_registry.keys()):
            if regex.match(key):
                self.cache_backend.delete(key)
                del self._key_registry[key]
                count += 1

        return count

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all keys with a prefix.

        Args:
            prefix: Key prefix

        Returns:
            Number of keys invalidated
        """
        count = 0
        for key in list(self._key_registry.keys()):
            if key.startswith(prefix):
                self.cache_backend.delete(key)
                del self._key_registry[key]
                count += 1

        return count

    def cleanup_old_keys(self, max_age_hours: int = 24) -> int:
        """Clean up old keys from registry.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of keys cleaned up
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        count = 0

        for key, timestamp in list(self._key_registry.items()):
            if timestamp < cutoff:
                del self._key_registry[key]
                count += 1

        return count


class CacheWarmer:
    """Cache warming to pre-populate cache with frequently accessed data."""

    def __init__(self, cache_backend: CacheBackend) -> None:
        """Initialize cache warmer.

        Args:
            cache_backend: Cache backend instance
        """
        self.cache_backend = cache_backend
        self._warming_tasks: List[Dict[str, Any]] = []

    def register_warming_task(
        self,
        key: str,
        generator: Callable,
        timeout: int = 300,
        schedule: Optional[str] = None,
    ) -> None:
        """Register a cache warming task.

        Args:
            key: Cache key to warm
            generator: Function that generates the cached value
            timeout: Cache timeout in seconds
            schedule: Optional cron-like schedule (not implemented in basic version)
        """
        self._warming_tasks.append(
            {
                "key": key,
                "generator": generator,
                "timeout": timeout,
                "schedule": schedule,
                "last_run": None,
            }
        )

    async def warm_cache(self, key: Optional[str] = None) -> int:
        """Warm the cache by running warming tasks.

        Args:
            key: Optional specific key to warm (None = all tasks)

        Returns:
            Number of tasks executed
        """
        count = 0

        for task in self._warming_tasks:
            if key and task["key"] != key:
                continue

            try:
                # Generate value
                generator = task["generator"]
                if callable(generator):
                    value = await generator() if hasattr(generator, "__await__") else generator()

                    # Store in cache
                    self.cache_backend.set(task["key"], value, task["timeout"])
                    task["last_run"] = datetime.now(timezone.utc)
                    count += 1
            except Exception:
                # Log error but continue with other tasks
                print(f"Error warming cache for key {task['key']}")

        return count

    def get_warming_status(self) -> List[Dict[str, Any]]:
        """Get status of all warming tasks.

        Returns:
            List of task status dictionaries
        """
        return [
            {
                "key": task["key"],
                "last_run": task["last_run"],
                "schedule": task["schedule"],
            }
            for task in self._warming_tasks
        ]


class ContentTypeCacheManager:
    """Manage cache policies for different content types."""

    def __init__(self, cache_backend: CacheBackend) -> None:
        """Initialize content type cache manager.

        Args:
            cache_backend: Cache backend instance
        """
        self.cache_backend = cache_backend
        self._policies: Dict[str, CachePolicy] = {}
        self._default_policy = CachePolicy(timeout=300)

    def register_policy(self, content_type: str, policy: CachePolicy) -> None:
        """Register a cache policy for a content type.

        Args:
            content_type: Content type (e.g., 'page', 'post', 'image')
            policy: Cache policy configuration
        """
        self._policies[content_type] = policy

    def get_policy(self, content_type: str) -> CachePolicy:
        """Get cache policy for a content type.

        Args:
            content_type: Content type

        Returns:
            Cache policy
        """
        return self._policies.get(content_type, self._default_policy)

    def cache_content(
        self,
        content_type: str,
        content_id: str,
        content: Any,
        extra_tags: Optional[Set[str]] = None,
    ) -> str:
        """Cache content with appropriate policy.

        Args:
            content_type: Content type
            content_id: Unique content identifier
            content: Content to cache
            extra_tags: Optional additional cache tags

        Returns:
            Cache key used
        """
        policy = self.get_policy(content_type)

        # Generate cache key
        cache_key = f"content:{content_type}:{content_id}"

        # Apply tags if configured
        tags = set(policy.tags or [])
        if extra_tags:
            tags.update(extra_tags)

        # Add content type tag
        tags.add(f"type:{content_type}")

        # Store in cache
        self.cache_backend.set(cache_key, content, policy.timeout)

        return cache_key

    def get_cached_content(
        self,
        content_type: str,
        content_id: str,
    ) -> Optional[Any]:
        """Retrieve cached content.

        Args:
            content_type: Content type
            content_id: Unique content identifier

        Returns:
            Cached content or None
        """
        cache_key = f"content:{content_type}:{content_id}"
        return self.cache_backend.get(cache_key)

    def invalidate_content_type(self, content_type: str) -> None:
        """Invalidate all content of a type.

        Args:
            content_type: Content type to invalidate
        """
        # This would use CacheTag to invalidate by tag
        # For now, we'll need to track keys to invalidate
        pass


class CacheStatistics:
    """Track and report cache statistics."""

    def __init__(self) -> None:
        """Initialize cache statistics tracker."""
        self._hits: int = 0
        self._misses: int = 0
        self._sets: int = 0
        self._deletes: int = 0
        self._hit_times: List[float] = []
        self._miss_times: List[float] = []
        self._start_time = time.time()

    def record_hit(self, duration: float = 0) -> None:
        """Record a cache hit.

        Args:
            duration: Time taken for the hit in seconds
        """
        self._hits += 1
        if duration > 0:
            self._hit_times.append(duration)

    def record_miss(self, duration: float = 0) -> None:
        """Record a cache miss.

        Args:
            duration: Time taken for the miss in seconds
        """
        self._misses += 1
        if duration > 0:
            self._miss_times.append(duration)

    def record_set(self) -> None:
        """Record a cache set operation."""
        self._sets += 1

    def record_delete(self) -> None:
        """Record a cache delete operation."""
        self._deletes += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        uptime = time.time() - self._start_time

        avg_hit_time = sum(self._hit_times) / len(self._hit_times) if self._hit_times else 0
        avg_miss_time = sum(self._miss_times) / len(self._miss_times) if self._miss_times else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "sets": self._sets,
            "deletes": self._deletes,
            "uptime_seconds": round(uptime, 2),
            "requests_per_second": round(total_requests / uptime, 2) if uptime > 0 else 0,
            "avg_hit_time_ms": round(avg_hit_time * 1000, 2),
            "avg_miss_time_ms": round(avg_miss_time * 1000, 2),
        }

    def reset(self) -> None:
        """Reset all statistics."""
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        self._hit_times.clear()
        self._miss_times.clear()
        self._start_time = time.time()


class StaleWhileRevalidateCache:
    """Cache with stale-while-revalidate support."""

    def __init__(self, cache_backend: CacheBackend) -> None:
        """Initialize SWR cache.

        Args:
            cache_backend: Cache backend instance
        """
        self.cache_backend = cache_backend

    def get_with_swr(
        self,
        key: str,
        generator: Callable,
        timeout: int = 300,
        stale_timeout: int = 60,
    ) -> tuple[Any, bool]:
        """Get value with stale-while-revalidate support.

        Args:
            key: Cache key
            generator: Function to generate fresh value
            timeout: Fresh cache timeout
            stale_timeout: How long to serve stale content

        Returns:
            Tuple of (value, is_stale)
        """
        # Try to get cached value
        cached = self.cache_backend.get(key)

        if cached is not None:
            # Check if stale
            stale_key = f"{key}:stale_at"
            stale_at = self.cache_backend.get(stale_key)

            if stale_at and time.time() > stale_at:
                # Serve stale while revalidating
                # In production, you'd trigger async revalidation here
                return cached, True
            return cached, False

        # Generate fresh value
        value = generator() if callable(generator) else generator

        # Cache with timestamps
        self.cache_backend.set(key, value, timeout + stale_timeout)
        self.cache_backend.set(f"{key}:stale_at", time.time() + timeout, timeout + stale_timeout)

        return value, False
