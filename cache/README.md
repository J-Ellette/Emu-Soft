# Cache System

In-memory caching backend emulating Redis functionality.

## What This Emulates

**Emulates:** Django Cache Framework, Redis-py, Memcached
**Purpose:** High-performance caching without external cache servers

## Features

- In-memory key-value storage
- TTL (time-to-live) support
- Cache decorators for functions and views
- Cache middleware for HTTP responses
- Advanced caching patterns
- Cache warming and invalidation

## Components

### Cache Backend
- **backend.py** - Core cache implementation
  - In-memory storage with TTL
  - Key-value operations (get, set, delete)
  - Atomic operations
  - Cache statistics

### Cache Decorators
- **decorators.py** - Caching decorators
  - Function result caching
  - View response caching
  - Cache key generation
  - Conditional caching
  - Cache invalidation

### Cache Middleware
- **middleware.py** - HTTP caching middleware
  - Automatic response caching
  - Cache-Control header handling
  - ETag generation
  - Conditional requests (304 Not Modified)

### Advanced Features
- **advanced.py** - Advanced caching patterns
  - Cache warming (pre-populating cache)
  - Cache sharding (distributed caching)
  - Cache hierarchies
  - Write-through caching
  - Cache stampede prevention

## Usage Examples

### Basic Caching
```python
from cache.backend import CacheBackend

cache = CacheBackend()

# Set value with TTL
cache.set("user:123", {"name": "John"}, ttl=3600)

# Get value
user = cache.get("user:123")

# Delete value
cache.delete("user:123")

# Check existence
if cache.exists("user:123"):
    pass
```

### Function Caching
```python
from cache.decorators import cache_result

@cache_result(ttl=300)
def expensive_calculation(x, y):
    # Result will be cached for 5 minutes
    return x * y + complex_operation()
```

### View Caching
```python
from cache.decorators import cache_view

@cache_view(ttl=600)
async def homepage(request):
    # Response will be cached for 10 minutes
    return Response(generate_homepage())
```

### Cache Middleware
```python
from cache.middleware import CacheMiddleware
from framework.application import Application

app = Application()
app.add_middleware(CacheMiddleware(ttl=300))
```

### Advanced Patterns
```python
from cache.advanced import CacheWarmer, ShardedCache

# Cache warming
warmer = CacheWarmer(cache)
warmer.warm("popular_items", lambda: fetch_popular_items())

# Sharded cache
sharded = ShardedCache(num_shards=4)
sharded.set("key", "value")
```

## Cache Strategies

### Time-based Expiration
- Automatic expiration after TTL
- Sliding window expiration
- Absolute expiration

### Size-based Eviction
- LRU (Least Recently Used)
- LFU (Least Frequently Used)
- FIFO (First In, First Out)

### Invalidation Patterns
- Manual invalidation
- Tag-based invalidation
- Pattern-based invalidation
- Event-driven invalidation

## Performance Considerations

- **Memory Usage**: In-memory storage, monitor size
- **TTL Management**: Clean up expired entries regularly
- **Lock Contention**: Thread-safe operations
- **Serialization**: Automatic for complex objects

## Configuration Options

- `default_ttl`: Default time-to-live for cache entries
- `max_entries`: Maximum number of cache entries
- `eviction_policy`: LRU, LFU, or FIFO
- `serializer`: JSON, pickle, or custom

## Integration

Works with:
- Web framework (framework/ module)
- API framework (api/ module)
- Database layer (database/ module)
- Any Python application

## Why This Was Created

Part of the CIV-ARCOS project to provide caching capabilities without external cache servers, improving performance while maintaining self-containment.
