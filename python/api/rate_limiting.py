"""
Developed by PowerShield, as an alternative to Django REST Framework
"""

"""Advanced API rate limiting with multiple strategies and token bucket algorithm."""

from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from functools import wraps
import time


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting rules."""

    requests: int  # Number of requests allowed
    window: int  # Time window in seconds
    burst: Optional[int] = None  # Burst capacity (for token bucket)


class TokenBucket:
    """Token bucket algorithm for rate limiting.

    This allows for burst traffic while maintaining an average rate limit.
    """

    def __init__(self, rate: float, capacity: int) -> None:
        """Initialize token bucket.

        Args:
            rate: Token refill rate (tokens per second)
            capacity: Maximum bucket capacity (burst size)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Add tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

        # Try to consume tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Calculate time to wait before tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Wait time in seconds
        """
        tokens_needed = tokens - self.tokens
        if tokens_needed <= 0:
            return 0.0
        return tokens_needed / self.rate


class RateLimiter:
    """Advanced rate limiter with multiple strategies."""

    def __init__(
        self,
        default_config: Optional[RateLimitConfig] = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            default_config: Default rate limit configuration
        """
        self.default_config = default_config or RateLimitConfig(requests=100, window=60)
        self._buckets: Dict[str, TokenBucket] = {}
        self._endpoint_configs: Dict[str, RateLimitConfig] = {}
        self._user_tiers: Dict[str, RateLimitConfig] = {}

    def configure_endpoint(self, endpoint: str, config: RateLimitConfig) -> None:
        """Configure rate limit for a specific endpoint.

        Args:
            endpoint: Endpoint path or pattern
            config: Rate limit configuration
        """
        self._endpoint_configs[endpoint] = config

    def configure_user_tier(self, tier: str, config: RateLimitConfig) -> None:
        """Configure rate limit for a user tier.

        Args:
            tier: User tier name (e.g., 'free', 'premium', 'enterprise')
            config: Rate limit configuration
        """
        self._user_tiers[tier] = config

    def _get_bucket_key(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
    ) -> str:
        """Generate bucket key for identifier and endpoint.

        Args:
            identifier: Client identifier (IP, user ID, API key)
            endpoint: Optional endpoint path

        Returns:
            Bucket key string
        """
        if endpoint:
            return f"{identifier}:{endpoint}"
        return identifier

    def _get_config(
        self,
        endpoint: Optional[str] = None,
        user_tier: Optional[str] = None,
    ) -> RateLimitConfig:
        """Get rate limit config for endpoint or user tier.

        Args:
            endpoint: Optional endpoint path
            user_tier: Optional user tier

        Returns:
            Rate limit configuration
        """
        # User tier takes precedence
        if user_tier and user_tier in self._user_tiers:
            return self._user_tiers[user_tier]

        # Then endpoint-specific config
        if endpoint and endpoint in self._endpoint_configs:
            return self._endpoint_configs[endpoint]

        # Fall back to default
        return self.default_config

    def _get_or_create_bucket(self, key: str, config: RateLimitConfig) -> TokenBucket:
        """Get or create a token bucket for the key.

        Args:
            key: Bucket key
            config: Rate limit configuration

        Returns:
            Token bucket instance
        """
        if key not in self._buckets:
            # Calculate rate as requests per second
            rate = config.requests / config.window
            capacity = config.burst or config.requests
            self._buckets[key] = TokenBucket(rate=rate, capacity=capacity)
        return self._buckets[key]

    def check_limit(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
        user_tier: Optional[str] = None,
        tokens: int = 1,
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limit.

        Args:
            identifier: Client identifier
            endpoint: Optional endpoint path
            user_tier: Optional user tier
            tokens: Number of tokens to consume

        Returns:
            Tuple of (is_allowed, info_dict)
        """
        config = self._get_config(endpoint=endpoint, user_tier=user_tier)
        key = self._get_bucket_key(identifier, endpoint)
        bucket = self._get_or_create_bucket(key, config)

        allowed = bucket.consume(tokens)
        wait_time = bucket.get_wait_time(tokens) if not allowed else 0

        info = {
            "limit": config.requests,
            "remaining": int(bucket.tokens),
            "reset": int(time.time() + config.window),
            "retry_after": int(wait_time) if not allowed else None,
        }

        return allowed, info

    def reset(self, identifier: str, endpoint: Optional[str] = None) -> None:
        """Reset rate limit for an identifier.

        Args:
            identifier: Client identifier
            endpoint: Optional endpoint path
        """
        key = self._get_bucket_key(identifier, endpoint)
        if key in self._buckets:
            del self._buckets[key]

    def cleanup_expired(self, max_age_seconds: int = 3600) -> int:
        """Clean up old, unused buckets.

        Args:
            max_age_seconds: Maximum age for inactive buckets

        Returns:
            Number of buckets removed
        """
        now = time.time()
        to_remove = []

        for key, bucket in self._buckets.items():
            if now - bucket.last_update > max_age_seconds:
                to_remove.append(key)

        for key in to_remove:
            del self._buckets[key]

        return len(to_remove)


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance.

    Returns:
        Global rate limiter
    """
    return _rate_limiter


def rate_limit(
    requests: int = 60,
    window: int = 60,
    burst: Optional[int] = None,
    key_func: Optional[Callable] = None,
) -> Callable:
    """Decorator to apply rate limiting to an endpoint.

    Args:
        requests: Number of requests allowed per window
        window: Time window in seconds
        burst: Optional burst capacity
        key_func: Optional function to extract identifier from request

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        config = RateLimitConfig(requests=requests, window=window, burst=burst)

        @wraps(func)
        async def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            from framework.response import JSONResponse

            # Extract identifier
            if key_func:
                identifier = key_func(request)
            else:
                # Default: use IP address
                identifier = getattr(request, "client_ip", "unknown")

            # Extract endpoint path
            endpoint = getattr(request, "path", None)

            # Check rate limit
            limiter = get_rate_limiter()
            limiter.configure_endpoint(endpoint, config)

            # Extract user tier if available
            user_tier = None
            if hasattr(request, "user") and request.user:
                user_tier = getattr(request.user, "tier", None)

            allowed, info = limiter.check_limit(
                identifier=identifier,
                endpoint=endpoint,
                user_tier=user_tier,
            )

            if not allowed:
                return JSONResponse(
                    {"error": "Rate limit exceeded", "retry_after": info["retry_after"]},
                    status_code=429,
                    headers={
                        "X-RateLimit-Limit": str(info["limit"]),
                        "X-RateLimit-Remaining": str(info["remaining"]),
                        "X-RateLimit-Reset": str(info["reset"]),
                        "Retry-After": str(info["retry_after"]),
                    },
                )

            # Call the original function
            response = await func(request, *args, **kwargs)

            # Add rate limit headers to response
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(info["reset"])

            return response

        return wrapper

    return decorator


class RateLimitAnalytics:
    """Track and analyze rate limiting metrics."""

    def __init__(self) -> None:
        """Initialize analytics tracker."""
        self._violations: Dict[str, list] = {}
        self._total_requests: Dict[str, int] = {}

    def record_violation(
        self,
        identifier: str,
        endpoint: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record a rate limit violation.

        Args:
            identifier: Client identifier
            endpoint: Endpoint path
            timestamp: Optional timestamp (default: now)
        """
        timestamp = timestamp or datetime.now(timezone.utc)
        key = f"{identifier}:{endpoint}"

        if key not in self._violations:
            self._violations[key] = []

        self._violations[key].append(timestamp)

    def record_request(self, identifier: str, endpoint: str) -> None:
        """Record a successful request.

        Args:
            identifier: Client identifier
            endpoint: Endpoint path
        """
        key = f"{identifier}:{endpoint}"
        self._total_requests[key] = self._total_requests.get(key, 0) + 1

    def get_violations(
        self,
        identifier: Optional[str] = None,
        endpoint: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get rate limit violations.

        Args:
            identifier: Optional filter by identifier
            endpoint: Optional filter by endpoint
            since: Optional filter by timestamp

        Returns:
            Dictionary of violations
        """
        result = {}
        cutoff = since or datetime.now(timezone.utc) - timedelta(hours=24)

        for key, timestamps in self._violations.items():
            key_id, key_endpoint = key.split(":", 1)

            # Apply filters
            if identifier and key_id != identifier:
                continue
            if endpoint and key_endpoint != endpoint:
                continue

            # Filter by time
            recent = [ts for ts in timestamps if ts >= cutoff]
            if recent:
                result[key] = {
                    "identifier": key_id,
                    "endpoint": key_endpoint,
                    "violations": len(recent),
                    "last_violation": max(recent),
                }

        return result

    def get_top_violators(self, limit: int = 10) -> list:
        """Get top rate limit violators.

        Args:
            limit: Maximum number of results

        Returns:
            List of top violators
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        violator_counts = {}

        for key, timestamps in self._violations.items():
            key_id, key_endpoint = key.split(":", 1)
            recent = [ts for ts in timestamps if ts >= cutoff]

            if recent:
                if key_id not in violator_counts:
                    violator_counts[key_id] = 0
                violator_counts[key_id] += len(recent)

        # Sort by violation count
        sorted_violators = sorted(
            violator_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            {"identifier": identifier, "violations": count}
            for identifier, count in sorted_violators[:limit]
        ]

    def clear_old_data(self, max_age_hours: int = 24) -> None:
        """Clear old analytics data.

        Args:
            max_age_hours: Maximum age of data to keep
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

        for key in list(self._violations.keys()):
            self._violations[key] = [ts for ts in self._violations[key] if ts >= cutoff]
            if not self._violations[key]:
                del self._violations[key]
