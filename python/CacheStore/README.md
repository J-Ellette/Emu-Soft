# Redis Emulator - In-Memory Data Store

This module emulates the **redis-py** library, which is the Python client for Redis, an in-memory data structure store used as a database, cache, and message broker.

## What is Redis?

Redis (REmote DIctionary Server) is an open-source, in-memory data structure store that can be used as:
- **Database**: Persistent key-value store
- **Cache**: High-performance caching layer
- **Message Broker**: Pub/Sub messaging system
- **Session Store**: Web session management
- **Queue**: Task queue implementation

The redis-py library provides a Python interface to Redis servers with support for all Redis data types and commands.

## Features

This emulator implements core Redis functionality:

### Data Structures
- **Strings**: Basic key-value operations (GET, SET, INCR, DECR)
- **Hashes**: Field-value pairs (HGET, HSET, HGETALL, HDEL)
- **Lists**: Ordered collections (LPUSH, RPUSH, LPOP, RPOP, LRANGE)
- **Sets**: Unordered unique collections (SADD, SREM, SMEMBERS, SISMEMBER)
- **Sorted Sets**: Ordered sets with scores (ZADD, ZRANGE, ZSCORE, ZREM)

### Key Management
- Key existence checking (EXISTS)
- Key deletion (DELETE)
- Key expiration (EXPIRE, PEXPIRE, TTL, PERSIST)
- Pattern matching (KEYS)
- Database flushing (FLUSHDB, FLUSHALL)

### Advanced Features
- **Pipeline**: Batch multiple commands for efficiency
- **Pub/Sub**: Publish/subscribe messaging
- **Connection Pool**: Connection management
- **Sentinel**: High availability support
- **Transactions**: MULTI/EXEC support via pipeline

## Usage Examples

### Basic String Operations

```python
from redis_emulator import Redis

# Create Redis client
redis = Redis(host='localhost', port=6379, db=0)

# Set and get values
redis.set('username', 'john_doe')
username = redis.get('username')  # Returns b'john_doe'

# With decode_responses=True
redis = Redis(decode_responses=True)
redis.set('username', 'john_doe')
username = redis.get('username')  # Returns 'john_doe'

# Conditional set
redis.set('key1', 'value1', nx=True)  # Only if key doesn't exist
redis.set('key2', 'value2', xx=True)  # Only if key exists

# Set with expiration
redis.set('session_token', 'abc123', ex=3600)  # Expires in 1 hour
redis.set('temp_key', 'data', px=5000)  # Expires in 5 seconds

# Increment/decrement
redis.set('counter', 0)
redis.incr('counter')  # Returns 1
redis.incr('counter', 5)  # Returns 6
redis.decr('counter')  # Returns 5

# Delete keys
redis.delete('key1', 'key2', 'key3')

# Check existence
if redis.exists('username'):
    print("User exists")
```

### Hash Operations

```python
from redis_emulator import Redis

redis = Redis(decode_responses=True)

# Set hash fields
redis.hset('user:1000', 'username', 'john_doe')
redis.hset('user:1000', 'email', 'john@example.com')

# Set multiple fields at once
redis.hset('user:1001', mapping={
    'username': 'jane_doe',
    'email': 'jane@example.com',
    'age': '28'
})

# Get single field
username = redis.hget('user:1000', 'username')

# Get all fields
user_data = redis.hgetall('user:1000')
# Returns: {'username': 'john_doe', 'email': 'john@example.com'}

# Check field existence
if redis.hexists('user:1000', 'email'):
    print("Email field exists")

# Delete fields
redis.hdel('user:1000', 'age', 'phone')

# Use case: Storing user sessions
redis.hset('session:abc123', mapping={
    'user_id': '1000',
    'login_time': '2024-01-01T12:00:00Z',
    'ip_address': '192.168.1.1'
})
redis.expire('session:abc123', 3600)  # Session expires in 1 hour
```

### List Operations

```python
from redis_emulator import Redis

redis = Redis(decode_responses=True)

# Push to list (queue behavior)
redis.rpush('tasks', 'task1', 'task2', 'task3')  # Add to tail
redis.lpush('priority_tasks', 'urgent_task')  # Add to head

# Pop from list
task = redis.lpop('tasks')  # Remove from head (FIFO)
task = redis.rpop('tasks')  # Remove from tail (LIFO)

# Get range of elements
all_tasks = redis.lrange('tasks', 0, -1)  # Get all
first_three = redis.lrange('tasks', 0, 2)  # Get first 3

# Get list length
length = redis.llen('tasks')

# Use case: Job queue
redis.lpush('job_queue', 'process_image', 'send_email', 'generate_report')
while redis.llen('job_queue') > 0:
    job = redis.rpop('job_queue')
    # Process job...

# Use case: Activity feed
redis.lpush('user:1000:feed', 'Posted a photo')
redis.lpush('user:1000:feed', 'Liked a post')
recent_activities = redis.lrange('user:1000:feed', 0, 9)  # Last 10 activities
```

### Set Operations

```python
from redis_emulator import Redis

redis = Redis(decode_responses=True)

# Add members to set
redis.sadd('tags', 'python', 'redis', 'database')
redis.sadd('user:1000:skills', 'python', 'javascript', 'docker')

# Check membership
if redis.sismember('tags', 'python'):
    print("Python tag exists")

# Get all members
all_tags = redis.smembers('tags')

# Remove members
redis.srem('tags', 'database')

# Get set size
count = redis.scard('tags')

# Use case: Unique visitors tracking
redis.sadd('visitors:2024-01-01', 'user123', 'user456', 'user789')
daily_visitors = redis.scard('visitors:2024-01-01')

# Use case: User followers
redis.sadd('user:1000:followers', 'user100', 'user200', 'user300')
redis.sadd('user:1000:following', 'user400', 'user500')
follower_count = redis.scard('user:1000:followers')
```

### Sorted Set Operations

```python
from redis_emulator import Redis

redis = Redis(decode_responses=True)

# Add members with scores
redis.zadd('leaderboard', {
    'player1': 1000,
    'player2': 1500,
    'player3': 2000,
    'player4': 1200
})

# Get range by rank (lowest to highest score)
bottom_three = redis.zrange('leaderboard', 0, 2)
# Returns: ['player1', 'player4', 'player2']

# Get range with scores
top_players = redis.zrange('leaderboard', 0, 2, withscores=True)
# Returns: [('player1', 1000.0), ('player4', 1200.0), ('player2', 1500.0)]

# Get score of specific member
score = redis.zscore('leaderboard', 'player3')  # Returns 2000.0

# Remove members
redis.zrem('leaderboard', 'player1')

# Use case: Real-time leaderboard
redis.zadd('game:scores', {'player_a': 10500, 'player_b': 9800})
top_10 = redis.zrange('game:scores', -10, -1, withscores=True)  # Top 10

# Use case: Time-based ranking
import time
redis.zadd('recent_posts', {
    'post123': time.time(),
    'post456': time.time() - 3600
})
latest_posts = redis.zrange('recent_posts', -20, -1)  # 20 most recent
```

### Key Expiration

```python
from redis_emulator import Redis

redis = Redis(decode_responses=True)

# Set expiration in seconds
redis.set('verification_code', '123456')
redis.expire('verification_code', 300)  # Expires in 5 minutes

# Set expiration in milliseconds
redis.set('rate_limit', '100')
redis.pexpire('rate_limit', 60000)  # Expires in 60 seconds

# Check time to live
ttl = redis.ttl('verification_code')  # Returns remaining seconds
if ttl > 0:
    print(f"Key expires in {ttl} seconds")

# Remove expiration
redis.persist('verification_code')  # Key no longer expires

# Set key with expiration in one command
redis.set('temp_token', 'xyz789', ex=3600)  # Expires in 1 hour

# Use case: Session management
redis.hset('session:abc123', mapping={'user_id': '1000'})
redis.expire('session:abc123', 1800)  # 30 minute session

# Use case: Rate limiting
user_id = '1000'
key = f'rate_limit:{user_id}'
if redis.exists(key):
    requests = redis.incr(key)
    if requests > 100:
        print("Rate limit exceeded")
else:
    redis.set(key, 1, ex=60)  # 100 requests per minute
```

### Pipeline Operations

```python
from redis_emulator import Redis

redis = Redis(decode_responses=True)

# Basic pipeline usage
pipe = redis.pipeline()
pipe.set('key1', 'value1')
pipe.set('key2', 'value2')
pipe.incr('counter')
pipe.get('key1')
results = pipe.execute()
# Returns: [True, True, 1, 'value1']

# Pipeline with context manager
with redis.pipeline() as pipe:
    pipe.set('user:1000:name', 'John')
    pipe.set('user:1000:email', 'john@example.com')
    pipe.incr('user_count')
    results = pipe.execute()

# Use case: Atomic operations
def transfer_points(from_user, to_user, amount):
    pipe = redis.pipeline()
    pipe.hincrby(f'user:{from_user}', 'points', -amount)
    pipe.hincrby(f'user:{to_user}', 'points', amount)
    pipe.execute()

# Use case: Batch data loading
pipe = redis.pipeline()
for i in range(1000):
    pipe.set(f'key:{i}', f'value:{i}')
pipe.execute()  # Executes all 1000 commands at once
```

### Pub/Sub Messaging

```python
from redis_emulator import Redis

redis = Redis(decode_responses=True)

# Publishing messages
subscribers = redis.publish('news', 'Breaking news!')
print(f"Message sent to {subscribers} subscribers")

# Subscribing to channels
pubsub = redis.pubsub()
pubsub.subscribe('news', 'updates', 'alerts')

# Pattern-based subscription
pubsub.psubscribe('user:*:notifications')

# Listening for messages (simplified)
for message in pubsub.listen():
    if message['type'] == 'message':
        print(f"Channel: {message['channel']}")
        print(f"Message: {message['data']}")

# Unsubscribe
pubsub.unsubscribe('news')
pubsub.punsubscribe('user:*:notifications')

# Use case: Real-time notifications
def send_notification(user_id, message):
    redis.publish(f'user:{user_id}:notifications', message)

# Use case: Chat application
redis.publish('chat:room1', '{"user": "john", "message": "Hello!"}')
```

### Connection Management

```python
from redis_emulator import Redis, ConnectionPool, from_url

# Basic connection
redis = Redis(host='localhost', port=6379, db=0)

# With authentication
redis = Redis(
    host='localhost',
    port=6379,
    password='secret',
    socket_timeout=5.0
)

# Using connection pool
pool = ConnectionPool(host='localhost', port=6379, db=0, max_connections=10)
redis = Redis(connection_pool=pool)

# From URL
redis = from_url('redis://localhost:6379/0')
redis = from_url('redis://:password@localhost:6379/0')

# Multiple databases
redis_cache = Redis(db=0)  # Cache database
redis_sessions = Redis(db=1)  # Sessions database
redis_tasks = Redis(db=2)  # Task queue database
```

### Pattern Matching and Bulk Operations

```python
from redis_emulator import Redis

redis = Redis(decode_responses=True)

# Find keys by pattern
redis.set('user:1000:profile', 'data1')
redis.set('user:1001:profile', 'data2')
redis.set('user:1002:profile', 'data3')
redis.set('post:100', 'post_data')

user_keys = redis.keys('user:*:profile')  # Returns all user profiles
all_users = redis.keys('user:*')  # Returns all user-related keys

# Delete multiple keys matching pattern
for key in redis.keys('temp:*'):
    redis.delete(key)

# Flush database
redis.flushdb()  # Delete all keys in current database
redis.flushall()  # Delete all keys in all databases

# Use case: Clean up expired sessions
session_keys = redis.keys('session:*')
for key in session_keys:
    if redis.ttl(key) == -1:  # No expiration set
        redis.expire(key, 3600)  # Set default expiration
```

### Complete Application Examples

#### Caching Layer

```python
from redis_emulator import Redis
import json

redis = Redis(decode_responses=True)

def get_user_from_cache(user_id):
    """Get user data from cache."""
    key = f'cache:user:{user_id}'
    data = redis.get(key)
    if data:
        return json.loads(data)
    return None

def cache_user_data(user_id, user_data, ttl=3600):
    """Cache user data for specified TTL."""
    key = f'cache:user:{user_id}'
    redis.set(key, json.dumps(user_data), ex=ttl)

def invalidate_user_cache(user_id):
    """Remove user data from cache."""
    key = f'cache:user:{user_id}'
    redis.delete(key)

# Usage
user_data = get_user_from_cache('1000')
if not user_data:
    user_data = fetch_from_database('1000')
    cache_user_data('1000', user_data)
```

#### Session Management

```python
from redis_emulator import Redis
import uuid
import time

redis = Redis(decode_responses=True)

def create_session(user_id, user_data):
    """Create a new user session."""
    session_id = str(uuid.uuid4())
    session_key = f'session:{session_id}'
    
    redis.hset(session_key, mapping={
        'user_id': user_id,
        'created_at': str(time.time()),
        **user_data
    })
    redis.expire(session_key, 3600)  # 1 hour session
    
    return session_id

def get_session(session_id):
    """Retrieve session data."""
    session_key = f'session:{session_id}'
    return redis.hgetall(session_key)

def refresh_session(session_id):
    """Extend session expiration."""
    session_key = f'session:{session_id}'
    if redis.exists(session_key):
        redis.expire(session_key, 3600)
        return True
    return False

def destroy_session(session_id):
    """Delete session."""
    session_key = f'session:{session_id}'
    redis.delete(session_key)
```

#### Rate Limiting

```python
from redis_emulator import Redis
import time

redis = Redis(decode_responses=True)

def check_rate_limit(user_id, max_requests=100, window=60):
    """Check if user is within rate limit."""
    key = f'rate_limit:{user_id}'
    
    # Get current request count
    count = redis.get(key)
    
    if count is None:
        # First request in window
        redis.set(key, 1, ex=window)
        return True, 1, max_requests
    
    count = int(count)
    if count >= max_requests:
        ttl = redis.ttl(key)
        return False, count, ttl
    
    # Increment and allow
    new_count = redis.incr(key)
    return True, new_count, max_requests

# Usage
allowed, current, limit = check_rate_limit('user123', max_requests=10, window=60)
if not allowed:
    print(f"Rate limit exceeded. Try again in {limit} seconds.")
else:
    print(f"Request allowed. {current}/{limit} requests used.")
```

#### Leaderboard System

```python
from redis_emulator import Redis

redis = Redis(decode_responses=True)

def update_score(leaderboard, player_id, score):
    """Update player score in leaderboard."""
    redis.zadd(leaderboard, {player_id: score})

def increment_score(leaderboard, player_id, points):
    """Increment player score."""
    current_score = redis.zscore(leaderboard, player_id) or 0
    new_score = current_score + points
    redis.zadd(leaderboard, {player_id: new_score})
    return new_score

def get_top_players(leaderboard, count=10):
    """Get top N players with scores."""
    # Get highest scores (reverse order)
    return redis.zrange(leaderboard, -count, -1, withscores=True)

def get_player_rank(leaderboard, player_id):
    """Get player's rank (1-based)."""
    all_players = redis.zrange(leaderboard, 0, -1)
    try:
        rank = all_players.index(player_id) + 1
        return rank
    except ValueError:
        return None

# Usage
update_score('game:weekly', 'player123', 5000)
increment_score('game:weekly', 'player123', 100)
top_10 = get_top_players('game:weekly', 10)
rank = get_player_rank('game:weekly', 'player123')
```

## Testing

Run the comprehensive test suite:

```bash
python test_redis_emulator.py
```

Tests cover:
- String operations (GET, SET, INCR, DECR)
- Hash operations (HGET, HSET, HGETALL, HDEL)
- List operations (LPUSH, RPUSH, LPOP, RPOP, LRANGE)
- Set operations (SADD, SREM, SMEMBERS, SISMEMBER)
- Sorted set operations (ZADD, ZRANGE, ZSCORE, ZREM)
- Key operations (EXPIRE, TTL, PERSIST, DELETE, EXISTS, KEYS)
- Pipeline operations
- Pub/Sub messaging
- Connection pooling
- Sentinel support
- Integration scenarios

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for redis-py:

```python
# Instead of:
# import redis

# Use:
import redis_emulator as redis

# The rest of your code remains unchanged
r = redis.Redis(host='localhost', port=6379, db=0)
r.set('key', 'value')
value = r.get('key')
```

## Use Cases

Perfect for:
- **Local Development**: Develop Redis-based applications without Redis server
- **Testing**: Test Redis integrations without external dependencies
- **CI/CD**: Run tests in CI pipelines without Redis installation
- **Learning**: Learn Redis concepts and patterns
- **Prototyping**: Quickly prototype Redis-based features
- **Offline Development**: Work on Redis applications without network access

## Common Patterns

### Cache-Aside Pattern

```python
def get_data(key):
    # Try cache first
    data = redis.get(f'cache:{key}')
    if data:
        return json.loads(data)
    
    # Cache miss - fetch from source
    data = fetch_from_database(key)
    redis.set(f'cache:{key}', json.dumps(data), ex=3600)
    return data
```

### Distributed Lock

```python
def acquire_lock(lock_key, timeout=10):
    """Acquire distributed lock."""
    identifier = str(uuid.uuid4())
    if redis.set(lock_key, identifier, nx=True, ex=timeout):
        return identifier
    return None

def release_lock(lock_key, identifier):
    """Release distributed lock."""
    if redis.get(lock_key) == identifier:
        redis.delete(lock_key)
        return True
    return False
```

### Message Queue

```python
def enqueue_task(queue_name, task_data):
    """Add task to queue."""
    redis.lpush(queue_name, json.dumps(task_data))

def dequeue_task(queue_name, timeout=1):
    """Get task from queue."""
    task = redis.rpop(queue_name)
    if task:
        return json.loads(task)
    return None
```

## Limitations

This is an emulator for development and testing purposes:
- In-memory storage only (data is lost when process ends)
- Simplified Pub/Sub (no blocking operations)
- No clustering or sharding support
- No persistence (RDB/AOF)
- No Lua scripting support
- Limited pattern matching (basic wildcard support)
- Simplified transaction support

## Supported Operations

### String Operations
- ✅ GET, SET, DELETE
- ✅ INCR, DECR, INCRBY, DECRBY
- ✅ SET with EX, PX, NX, XX flags
- ✅ EXISTS

### Hash Operations
- ✅ HGET, HSET, HGETALL, HDEL
- ✅ HEXISTS
- ✅ HSET with mapping

### List Operations
- ✅ LPUSH, RPUSH, LPOP, RPOP
- ✅ LRANGE, LLEN

### Set Operations
- ✅ SADD, SREM, SMEMBERS
- ✅ SISMEMBER, SCARD

### Sorted Set Operations
- ✅ ZADD, ZREM, ZRANGE
- ✅ ZSCORE, ZRANGE with scores

### Key Operations
- ✅ EXPIRE, PEXPIRE, TTL, PERSIST
- ✅ KEYS (with pattern matching)
- ✅ FLUSHDB, FLUSHALL

### Advanced Features
- ✅ Pipeline
- ✅ Pub/Sub (basic)
- ✅ Connection Pool
- ✅ Sentinel (basic)

## Compatibility

Emulates core features of:
- redis-py 4.x API
- Redis 6.x command set
- Common Redis patterns and idioms

## License

Part of the Emu-Soft project. See main repository LICENSE.
