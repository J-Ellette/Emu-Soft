"""
Developed by PowerShield, as an alternative to Django Cache
"""

"""Cache middleware for HTTP caching."""

from typing import Any, Callable, Dict, Optional
from cache.backend import CacheBackend
import hashlib


class CacheMiddleware:
    """Middleware for HTTP response caching.

    This middleware caches HTTP responses based on the request path
    and query string, with support for cache headers and TTL.
    """

    def __init__(
        self,
        cache_backend: Optional[CacheBackend] = None,
        default_timeout: int = 300,
        cache_anonymous_only: bool = True,
    ) -> None:
        """Initialize the cache middleware.

        Args:
            cache_backend: Cache backend to use (None to create InMemoryCache)
            default_timeout: Default cache timeout in seconds (default: 300)
            cache_anonymous_only: Only cache requests without authentication
        """
        from cache.backend import InMemoryCache

        self.cache_backend = cache_backend or InMemoryCache(default_timeout)
        self.default_timeout = default_timeout
        self.cache_anonymous_only = cache_anonymous_only

    async def __call__(self, request: Any, call_next: Callable, scope: Dict[str, Any]) -> Any:
        """Process a request through the cache middleware.

        Args:
            request: Request object
            call_next: Next middleware or handler
            scope: ASGI scope dictionary

        Returns:
            Response object
        """
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        # Skip caching for authenticated users if configured
        if self.cache_anonymous_only and hasattr(request, "user") and request.user:
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get cached response
        cached_response = self.cache_backend.get(cache_key)
        if cached_response is not None:
            # Add cache hit header
            if hasattr(cached_response, "headers"):
                cached_response.headers["x-cache"] = "HIT"
            return cached_response

        # Get response from next handler
        response = await call_next(request)

        # Cache the response if it's successful
        if response.status_code == 200:
            timeout = self._get_timeout_from_response(response)
            self.cache_backend.set(cache_key, response, timeout)

            # Add cache miss header
            if hasattr(response, "headers"):
                response.headers["x-cache"] = "MISS"

        return response

    def _generate_cache_key(self, request: Any) -> str:
        """Generate a cache key for a request.

        Args:
            request: Request object

        Returns:
            Cache key string
        """
        # Include path and query string in cache key
        key_parts = [request.path]

        if hasattr(request, "query_string") and request.query_string:
            key_parts.append(request.query_string)

        # Include accept header for content negotiation
        if hasattr(request, "headers"):
            accept = request.headers.get("accept", "")
            if accept:
                key_parts.append(accept)

        key_string = "_".join(key_parts)
        return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"

    def _get_timeout_from_response(self, response: Any) -> int:
        """Extract cache timeout from response headers.

        Args:
            response: Response object

        Returns:
            Timeout in seconds
        """
        # Check for Cache-Control header
        if hasattr(response, "headers"):
            cache_control = response.headers.get("cache-control", "")
            if "max-age=" in cache_control:
                try:
                    max_age = cache_control.split("max-age=")[1].split(",")[0].strip()
                    return int(max_age)
                except (ValueError, IndexError):
                    pass

        return self.default_timeout

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        self.cache_backend.clear()

    def invalidate_path(self, path: str) -> bool:
        """Invalidate cache for a specific path.

        Args:
            path: Request path to invalidate

        Returns:
            True if cache was invalidated, False otherwise
        """
        # Create a simple key from the path
        cache_key = f"cache:{hashlib.md5(path.encode()).hexdigest()}"
        return self.cache_backend.delete(cache_key)

    def __repr__(self) -> str:
        """Return string representation of the middleware."""
        return f"<CacheMiddleware timeout={self.default_timeout}>"
