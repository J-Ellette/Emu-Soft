"""Edge caching strategies for optimal performance at edge locations.

This module provides sophisticated caching strategies optimized for edge computing,
including geographic distribution and intelligent cache invalidation.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
import time
import hashlib
from collections import defaultdict


class CacheStrategy(Enum):
    """Edge caching strategies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    GEO = "geo"  # Geographic-based
    ADAPTIVE = "adaptive"  # Adaptive based on usage patterns


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: float
    ttl: int
    region: Optional[str] = None
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)
    etag: Optional[str] = None


class EdgeCache:
    """Edge-optimized cache with multiple strategies."""

    def __init__(
        self,
        strategy: CacheStrategy = CacheStrategy.TTL,
        max_size: int = 1000,
        default_ttl: int = 3600,
    ) -> None:
        """Initialize edge cache.

        Args:
            strategy: Caching strategy
            max_size: Maximum cache size
            default_ttl: Default TTL in seconds
        """
        self.strategy = strategy
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU
        self._frequency: Dict[str, int] = defaultdict(int)  # For LFU
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)  # Tag to keys mapping

    def get(self, key: str, region: Optional[str] = None) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key
            region: Optional region for geo-based caching

        Returns:
            Cached value or None if not found/expired
        """
        # Generate region-specific key if needed
        cache_key = self._get_region_key(key, region)

        if cache_key not in self._cache:
            return None

        entry = self._cache[cache_key]

        # Check TTL expiration
        if self._is_expired(entry):
            self.delete(cache_key)
            return None

        # Update access metadata
        entry.access_count += 1
        entry.last_access = time.time()
        self._frequency[cache_key] += 1

        # Update LRU order
        if self.strategy == CacheStrategy.LRU:
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self._access_order.append(cache_key)

        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        region: Optional[str] = None,
        tags: Optional[Set[str]] = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
            region: Optional region for geo-based caching
            tags: Optional tags for cache invalidation
        """
        # Generate region-specific key if needed
        cache_key = self._get_region_key(key, region)

        # Evict if cache is full
        if len(self._cache) >= self.max_size and cache_key not in self._cache:
            self._evict()

        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            value=value,
            created_at=time.time(),
            ttl=ttl or self.default_ttl,
            region=region,
            tags=tags or set(),
            etag=self._compute_etag(value),
        )

        self._cache[cache_key] = entry

        # Update indexes
        if tags:
            for tag in tags:
                self._tags_index[tag].add(cache_key)

        if self.strategy == CacheStrategy.LRU:
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self._access_order.append(cache_key)

    def delete(self, key: str, region: Optional[str] = None) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key
            region: Optional region

        Returns:
            True if deleted, False if not found
        """
        cache_key = self._get_region_key(key, region)

        if cache_key not in self._cache:
            return False

        entry = self._cache.pop(cache_key)

        # Clean up indexes
        for tag in entry.tags:
            self._tags_index[tag].discard(cache_key)

        if cache_key in self._access_order:
            self._access_order.remove(cache_key)

        if cache_key in self._frequency:
            del self._frequency[cache_key]

        return True

    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with a specific tag.

        Args:
            tag: Tag to invalidate

        Returns:
            Number of entries invalidated
        """
        if tag not in self._tags_index:
            return 0

        keys_to_delete = list(self._tags_index[tag])
        count = 0

        for key in keys_to_delete:
            if self.delete(key):
                count += 1

        return count

    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern.

        Args:
            pattern: Key pattern (supports * wildcard)

        Returns:
            Number of entries invalidated
        """
        import re

        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace("*", ".*")
        regex = re.compile(f"^{regex_pattern}$")

        keys_to_delete = [key for key in self._cache.keys() if regex.match(key)]

        count = 0
        for key in keys_to_delete:
            if self.delete(key):
                count += 1

        return count

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        self._frequency.clear()
        self._tags_index.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        total_size = len(self._cache)
        expired_count = sum(1 for entry in self._cache.values() if self._is_expired(entry))

        return {
            "strategy": self.strategy.value,
            "total_entries": total_size,
            "max_size": self.max_size,
            "expired_entries": expired_count,
            "hit_rate": self._calculate_hit_rate(),
            "avg_ttl": self._calculate_avg_ttl(),
            "regions": self._get_regions(),
        }

    def _evict(self) -> None:
        """Evict entries based on strategy."""
        if self.strategy == CacheStrategy.LRU:
            self._evict_lru()
        elif self.strategy == CacheStrategy.LFU:
            self._evict_lfu()
        elif self.strategy == CacheStrategy.TTL:
            self._evict_expired()
        elif self.strategy == CacheStrategy.ADAPTIVE:
            self._evict_adaptive()
        else:
            # Default to LRU
            self._evict_lru()

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._access_order:
            # Fallback: remove first entry
            if self._cache:
                key = next(iter(self._cache))
                self.delete(key)
            return

        # Remove least recently used
        lru_key = self._access_order[0]
        self.delete(lru_key)

    def _evict_lfu(self) -> None:
        """Evict least frequently used entry."""
        if not self._frequency:
            # Fallback to LRU
            self._evict_lru()
            return

        # Find least frequently used
        lfu_key = min(self._frequency, key=self._frequency.get)
        self.delete(lfu_key)

    def _evict_expired(self) -> None:
        """Evict expired entries."""
        expired_keys = [key for key, entry in self._cache.items() if self._is_expired(entry)]

        if expired_keys:
            self.delete(expired_keys[0])
        else:
            # Fallback to LRU if no expired entries
            self._evict_lru()

    def _evict_adaptive(self) -> None:
        """Adaptive eviction based on multiple factors."""
        # Score each entry based on age, access frequency, and TTL
        scores = {}

        for key, entry in self._cache.items():
            age = time.time() - entry.created_at
            frequency = self._frequency.get(key, 0)
            ttl_ratio = age / entry.ttl if entry.ttl > 0 else 1

            # Lower score = higher priority for eviction
            score = frequency * 10 - age * 0.1 - ttl_ratio * 100
            scores[key] = score

        if scores:
            # Evict entry with lowest score
            key_to_evict = min(scores, key=scores.get)
            self.delete(key_to_evict)

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired.

        Args:
            entry: Cache entry

        Returns:
            True if expired
        """
        age = time.time() - entry.created_at
        return age > entry.ttl

    def _get_region_key(self, key: str, region: Optional[str]) -> str:
        """Get region-specific cache key.

        Args:
            key: Base cache key
            region: Optional region

        Returns:
            Region-specific key
        """
        if region and self.strategy == CacheStrategy.GEO:
            return f"{region}:{key}"
        return key

    def _compute_etag(self, value: Any) -> str:
        """Compute ETag for value.

        Args:
            value: Value to hash

        Returns:
            ETag
        """
        content = str(value).encode()
        return hashlib.sha256(content).hexdigest()[:16]

    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate.

        Returns:
            Hit rate (0.0 to 1.0)
        """
        if not self._cache:
            return 0.0

        total_accesses = sum(entry.access_count for entry in self._cache.values())
        if total_accesses == 0:
            return 0.0

        # Simplified hit rate calculation
        return min(1.0, total_accesses / (len(self._cache) * 10))

    def _calculate_avg_ttl(self) -> float:
        """Calculate average TTL of cache entries.

        Returns:
            Average TTL in seconds
        """
        if not self._cache:
            return 0.0

        return sum(entry.ttl for entry in self._cache.values()) / len(self._cache)

    def _get_regions(self) -> List[str]:
        """Get list of regions in cache.

        Returns:
            List of regions
        """
        regions = set()
        for entry in self._cache.values():
            if entry.region:
                regions.add(entry.region)
        return sorted(list(regions))


class GeoCache:
    """Geographic-aware cache for edge locations."""

    def __init__(self, regions: Optional[List[str]] = None) -> None:
        """Initialize geo-aware cache.

        Args:
            regions: List of supported regions
        """
        self.regions = regions or ["us-east", "us-west", "eu-west", "ap-southeast"]
        self._caches: Dict[str, EdgeCache] = {
            region: EdgeCache(strategy=CacheStrategy.GEO) for region in self.regions
        }

    def get(self, key: str, region: str) -> Optional[Any]:
        """Get value from region-specific cache.

        Args:
            key: Cache key
            region: Region identifier

        Returns:
            Cached value or None
        """
        cache = self._get_cache_for_region(region)
        return cache.get(key, region)

    def set(
        self, key: str, value: Any, ttl: Optional[int] = None, regions: Optional[List[str]] = None
    ) -> None:
        """Set value in one or more region caches.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL
            regions: Optional list of regions (default: all)
        """
        target_regions = regions or self.regions

        for region in target_regions:
            if region in self._caches:
                self._caches[region].set(key, value, ttl, region)

    def invalidate(self, key: str, regions: Optional[List[str]] = None) -> int:
        """Invalidate key across regions.

        Args:
            key: Cache key
            regions: Optional list of regions (default: all)

        Returns:
            Number of entries invalidated
        """
        target_regions = regions or self.regions
        count = 0

        for region in target_regions:
            if region in self._caches:
                if self._caches[region].delete(key, region):
                    count += 1

        return count

    def _get_cache_for_region(self, region: str) -> EdgeCache:
        """Get cache instance for region.

        Args:
            region: Region identifier

        Returns:
            Cache instance
        """
        # Find closest region if exact match not found
        if region in self._caches:
            return self._caches[region]

        # Default to first region
        return self._caches[self.regions[0]]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all regional caches.

        Returns:
            Statistics per region
        """
        return {region: cache.get_stats() for region, cache in self._caches.items()}
