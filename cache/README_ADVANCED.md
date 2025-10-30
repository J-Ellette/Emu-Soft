# Advanced Caching

Advanced caching features including smart invalidation, cache warming, content-type optimization, and monitoring.

## Features

- **Cache Tagging**: Tag-based invalidation for related content
- **Smart Invalidation**: Pattern matching and prefix-based invalidation
- **Cache Warming**: Pre-populate cache with frequently accessed data
- **Content-Type Policies**: Different caching strategies for different content types
- **Statistics**: Real-time cache performance monitoring
- **Stale-While-Revalidate**: Serve stale content while updating in background

## Cache Tagging

Invalidate related content together using tags:

```python
from cache.backend import InMemoryCache
from cache.advanced import CacheTag

cache = InMemoryCache()
tag_manager = CacheTag(cache)

# Tag a cache entry
tags = {"user:123", "posts"}
versioned_key = tag_manager.tag_cache_key("post:456", tags)

# Store with versioned key
cache.set(versioned_key, post_data, timeout=300)

# Invalidate all entries with a tag
tag_manager.invalidate_tag("user:123")  # Invalidates all user's cached data
```

## Smart Cache Invalidation

### Pattern-Based Invalidation

```python
from cache.backend import InMemoryCache
from cache.advanced import CacheInvalidator

cache = InMemoryCache()
invalidator = CacheInvalidator(cache)

# Register keys
invalidator.register_key("user:1")
invalidator.register_key("user:2")
invalidator.register_key("post:1")

# Invalidate by pattern
count = invalidator.invalidate_pattern(r"^user:")  # Invalidates all user keys
print(f"Invalidated {count} keys")
```

### Prefix-Based Invalidation

```python
# Invalidate by prefix
count = invalidator.invalidate_prefix("page:")
print(f"Invalidated {count} page keys")
```

## Cache Warming

Pre-populate cache with frequently accessed data:

```python
from cache.backend import InMemoryCache
from cache.advanced import CacheWarmer

cache = InMemoryCache()
warmer = CacheWarmer(cache)

# Register warming tasks
def load_homepage():
    # Expensive operation to load homepage
    return generate_homepage()

warmer.register_warming_task(
    key="page:home",
    generator=load_homepage,
    timeout=600,
    schedule="0 * * * *"  # Every hour
)

# Warm the cache
await warmer.warm_cache()

# Warm specific key
await warmer.warm_cache(key="page:home")

# Check warming status
status = warmer.get_warming_status()
```

## Content-Type Cache Policies

Different caching strategies for different content types:

```python
from cache.backend import InMemoryCache
from cache.advanced import ContentTypeCacheManager, CachePolicy

cache = InMemoryCache()
manager = ContentTypeCacheManager(cache)

# Register policies
manager.register_policy(
    "page",
    CachePolicy(
        timeout=3600,
        tags={"page"},
        vary_on=["Accept-Language"],
        cache_control="public, max-age=3600"
    )
)

manager.register_policy(
    "api_response",
    CachePolicy(
        timeout=60,
        tags={"api"},
        stale_while_revalidate=30,
        cache_control="public, max-age=60, stale-while-revalidate=30"
    )
)

# Cache content
content = {"title": "Home", "body": "..."}
cache_key = manager.cache_content("page", "home", content)

# Retrieve cached content
cached = manager.get_cached_content("page", "home")
```

## Cache Statistics

Monitor cache performance in real-time:

```python
from cache.advanced import CacheStatistics

stats = CacheStatistics()

# Record operations
stats.record_hit(duration=0.001)
stats.record_miss(duration=0.01)
stats.record_set()
stats.record_delete()

# Get statistics
result = stats.get_stats()
print(f"Hit rate: {result['hit_rate']}%")
print(f"Average hit time: {result['avg_hit_time_ms']}ms")
print(f"Requests per second: {result['requests_per_second']}")

# Reset statistics
stats.reset()
```

## Stale-While-Revalidate

Serve stale content while updating in the background:

```python
from cache.backend import InMemoryCache
from cache.advanced import StaleWhileRevalidateCache

cache = InMemoryCache()
swr_cache = StaleWhileRevalidateCache(cache)

def generate_data():
    # Expensive operation
    return fetch_latest_data()

# Get with stale-while-revalidate
value, is_stale = swr_cache.get_with_swr(
    key="data:latest",
    generator=generate_data,
    timeout=60,        # Fresh for 60 seconds
    stale_timeout=30   # Serve stale for 30 more seconds
)

if is_stale:
    print("Serving stale content, revalidating in background")
```

## Cache Policy Configuration

```python
from cache.advanced import CachePolicy

policy = CachePolicy(
    timeout=600,                              # Cache for 10 minutes
    tags={"user", "content"},                 # Tags for invalidation
    vary_on=["Accept-Language", "Accept"],    # Vary cache on headers
    stale_while_revalidate=60,               # Serve stale for 1 minute
    cache_control="public, max-age=600"       # HTTP Cache-Control header
)
```

## Integration Example

Complete example integrating all features:

```python
from cache.backend import InMemoryCache
from cache.advanced import (
    CacheTag,
    CacheInvalidator,
    CacheWarmer,
    ContentTypeCacheManager,
    CacheStatistics,
    CachePolicy
)

# Setup
cache = InMemoryCache()
tag_manager = CacheTag(cache)
invalidator = CacheInvalidator(cache)
warmer = CacheWarmer(cache)
content_manager = ContentTypeCacheManager(cache)
stats = CacheStatistics()

# Configure content type policies
content_manager.register_policy(
    "page",
    CachePolicy(timeout=3600, tags={"page"})
)

content_manager.register_policy(
    "post",
    CachePolicy(timeout=600, tags={"post", "content"})
)

# Register warming tasks
async def load_popular_posts():
    return fetch_popular_posts()

warmer.register_warming_task(
    key="posts:popular",
    generator=load_popular_posts,
    timeout=600
)

# Cache content with tagging
post = {"id": 123, "title": "Example", "content": "..."}
cache_key = content_manager.cache_content(
    content_type="post",
    content_id="123",
    content=post,
    extra_tags={"author:456"}
)

# Record cache hit
stats.record_hit(duration=0.001)

# Invalidate by author
tag_manager.invalidate_tag("author:456")

# Warm cache
await warmer.warm_cache()

# Get statistics
cache_stats = stats.get_stats()
print(f"Cache hit rate: {cache_stats['hit_rate']}%")
```

## Best Practices

1. **Use Tags for Related Content**: Tag content that should be invalidated together
2. **Warm Critical Paths**: Pre-warm cache for frequently accessed content
3. **Monitor Performance**: Track cache statistics to optimize policies
4. **Set Appropriate TTLs**: Balance freshness with cache effectiveness
5. **Use SWR for Updates**: Serve stale content while revalidating for better UX

## Cleanup

Regular cleanup prevents memory growth:

```python
# Clean up old invalidator keys
invalidator.cleanup_old_keys(max_age_hours=24)

# The cache backend also has cleanup
cache.cleanup_expired()
```
