"""Caching system for the CMS."""

from mycms.cache.backend import CacheBackend, InMemoryCache
from mycms.cache.decorators import cache_view, cache_result
from mycms.cache.middleware import CacheMiddleware

__all__ = ["CacheBackend", "InMemoryCache", "cache_view", "cache_result", "CacheMiddleware"]
