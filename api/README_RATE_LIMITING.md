# API Rate Limiting

Advanced API rate limiting implementation with token bucket algorithm, multiple strategies, and analytics.

## Features

- **Token Bucket Algorithm**: Allows burst traffic while maintaining average rate limits
- **Flexible Configuration**: Per-endpoint, per-user-tier, or global rate limiting
- **Analytics & Monitoring**: Track violations, top violators, and usage patterns
- **Easy Integration**: Simple decorator for endpoint protection

## Basic Usage

### Using the Decorator

```python
from mycms.api.rate_limiting import rate_limit

@rate_limit(requests=100, window=60)  # 100 requests per minute
async def my_api_endpoint(request):
    return {"data": "response"}
```

### Configuring Endpoint-Specific Limits

```python
from mycms.api.rate_limiting import get_rate_limiter, RateLimitConfig

limiter = get_rate_limiter()

# Configure different limits for different endpoints
limiter.configure_endpoint(
    "/api/public",
    RateLimitConfig(requests=100, window=60)
)

limiter.configure_endpoint(
    "/api/admin",
    RateLimitConfig(requests=10, window=60)
)
```

### User Tier-Based Limiting

```python
from mycms.api.rate_limiting import get_rate_limiter, RateLimitConfig

limiter = get_rate_limiter()

# Configure tiers
limiter.configure_user_tier(
    "free",
    RateLimitConfig(requests=10, window=60)
)

limiter.configure_user_tier(
    "premium",
    RateLimitConfig(requests=100, window=60, burst=150)
)

limiter.configure_user_tier(
    "enterprise",
    RateLimitConfig(requests=1000, window=60, burst=2000)
)
```

### Manual Rate Limit Check

```python
from mycms.api.rate_limiting import get_rate_limiter

limiter = get_rate_limiter()

# Check rate limit
allowed, info = limiter.check_limit(
    identifier="user_id_123",
    endpoint="/api/data",
    user_tier="premium"
)

if not allowed:
    # Rate limit exceeded
    print(f"Retry after {info['retry_after']} seconds")
else:
    # Process request
    print(f"Remaining: {info['remaining']}")
```

## Rate Limit Analytics

Track and analyze rate limiting patterns:

```python
from mycms.api.rate_limiting import RateLimitAnalytics

analytics = RateLimitAnalytics()

# Record a violation
analytics.record_violation("user_123", "/api/endpoint")

# Get violations
violations = analytics.get_violations(identifier="user_123")

# Get top violators
top_violators = analytics.get_top_violators(limit=10)

# Clear old data
analytics.clear_old_data(max_age_hours=24)
```

## Token Bucket Algorithm

The token bucket algorithm provides a balance between strict rate limiting and allowing burst traffic:

```python
from mycms.api.rate_limiting import TokenBucket

# 10 tokens per second, max capacity of 100
bucket = TokenBucket(rate=10.0, capacity=100)

# Consume tokens
if bucket.consume(5):
    # Tokens consumed successfully
    print("Request allowed")
else:
    # Not enough tokens
    wait_time = bucket.get_wait_time(5)
    print(f"Wait {wait_time} seconds")
```

## Configuration

### Rate Limit Config

```python
from mycms.api.rate_limiting import RateLimitConfig

config = RateLimitConfig(
    requests=100,     # Number of requests allowed
    window=60,        # Time window in seconds
    burst=150         # Optional: burst capacity (defaults to requests)
)
```

### Response Headers

When rate limiting is active, responses include informative headers:

- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait before retrying (when rate limited)

## Best Practices

1. **Set Appropriate Limits**: Balance protection with user experience
2. **Use Burst Capacity**: Allow occasional spikes in traffic
3. **Tier-Based Limits**: Offer different limits for different user tiers
4. **Monitor Analytics**: Track violations to identify abuse patterns
5. **Cleanup Expired Data**: Regularly clean up old bucket and analytics data

```python
from mycms.api.rate_limiting import get_rate_limiter

limiter = get_rate_limiter()

# Cleanup old buckets (run periodically)
removed = limiter.cleanup_expired(max_age_seconds=3600)
print(f"Cleaned up {removed} expired buckets")
```

## Error Handling

When rate limit is exceeded, a 429 status code is returned:

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 30
}
```

## Integration with Middleware

For application-wide rate limiting, use the existing `RateLimitMiddleware` in conjunction with this advanced system:

```python
from mycms.security.middleware import RateLimitMiddleware
from mycms.api.rate_limiting import get_rate_limiter, RateLimitConfig

# Configure global rate limiter
limiter = get_rate_limiter()
limiter.configure_endpoint(
    "/api/*",
    RateLimitConfig(requests=1000, window=60, burst=1500)
)

# Add middleware
middleware = RateLimitMiddleware(
    max_requests=1000,
    window_seconds=60
)
```
