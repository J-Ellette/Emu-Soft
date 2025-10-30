"""Cache decorators for views and functions."""

from functools import wraps
from typing import Any, Callable, Optional
import hashlib
import json


def cache_result(
    cache_backend: Any, key_prefix: str = "", timeout: Optional[int] = None
) -> Callable:
    """Decorator to cache function results.

    Args:
        cache_backend: Cache backend instance
        key_prefix: Prefix for cache keys
        timeout: Cache timeout in seconds

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]

            # Add arguments to key
            if args:
                key_parts.append(str(args))
            if kwargs:
                key_parts.append(str(sorted(kwargs.items())))

            cache_key = hashlib.md5("_".join(key_parts).encode()).hexdigest()

            # Try to get from cache
            cached_value = cache_backend.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache_backend.set(cache_key, result, timeout)
            return result

        return wrapper

    return decorator


def cache_view(
    cache_backend: Any, key_prefix: str = "view", timeout: Optional[int] = 300
) -> Callable:
    """Decorator to cache view responses.

    Args:
        cache_backend: Cache backend instance
        key_prefix: Prefix for cache keys (default: "view")
        timeout: Cache timeout in seconds (default: 300)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            # Generate cache key from request path and query string
            cache_key = _generate_view_cache_key(
                key_prefix, request.path, request.query_string, args, kwargs
            )

            # Try to get from cache
            cached_response = cache_backend.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Call view and cache response
            response = await func(request, *args, **kwargs)
            cache_backend.set(cache_key, response, timeout)
            return response

        @wraps(func)
        def sync_wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            # Generate cache key from request path and query string
            cache_key = _generate_view_cache_key(
                key_prefix, request.path, request.query_string, args, kwargs
            )

            # Try to get from cache
            cached_response = cache_backend.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Call view and cache response
            response = func(request, *args, **kwargs)
            cache_backend.set(cache_key, response, timeout)
            return response

        # Return appropriate wrapper based on whether function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _generate_view_cache_key(
    prefix: str, path: str, query_string: str, args: tuple, kwargs: dict
) -> str:
    """Generate a cache key for a view.

    Args:
        prefix: Key prefix
        path: Request path
        query_string: Query string
        args: View args
        kwargs: View kwargs

    Returns:
        Cache key string
    """
    key_parts = [prefix, path]

    if query_string:
        key_parts.append(query_string)

    if args:
        key_parts.append(str(args))

    if kwargs:
        key_parts.append(json.dumps(sorted(kwargs.items())))

    return hashlib.md5("_".join(key_parts).encode()).hexdigest()


def invalidate_cache(cache_backend: Any, pattern: Optional[str] = None) -> int:
    """Invalidate cache entries matching a pattern.

    Args:
        cache_backend: Cache backend instance
        pattern: Pattern to match (None to clear all)

    Returns:
        Number of entries invalidated
    """
    if pattern is None:
        cache_backend.clear()
        return -1  # Unknown count for full clear

    # For simple backends without pattern matching, we can't efficiently
    # implement pattern-based invalidation
    return 0
