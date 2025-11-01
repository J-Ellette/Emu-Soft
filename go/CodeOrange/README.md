# Redis Emulator - Go Client for Redis

**Developed by PowerShield, as an alternative to Redis (Go client)**


This module emulates the **Redis Go client**, which provides a Go interface to Redis, the popular in-memory data structure store. Redis is used as a database, cache, message broker, and queue.

## What is Redis?

Redis (Remote Dictionary Server) is an open-source, in-memory data structure store that can be used as:
- A database
- A cache
- A message broker
- A streaming engine

Key features:
- In-memory storage with optional persistence
- Support for various data structures (strings, lists, sets, sorted sets, hashes)
- Atomic operations
- Pub/Sub messaging
- Transactions
- Lua scripting
- Replication and high availability

## Features

This emulator implements core Redis functionality:

### Data Types
- **Strings**: Simple key-value storage
- **Lists**: Ordered collections of strings
- **Sets**: Unordered collections of unique strings
- **Sorted Sets**: Sets ordered by score
- **Hashes**: Maps of field-value pairs

### Operations
- **Key Operations**: Set, Get, Delete, Exists, Expire, TTL
- **String Operations**: Increment, Decrement
- **List Operations**: LPush, RPush, LPop, RPop, LRange, LLen
- **Set Operations**: SAdd, SMembers, SIsMember, SRem, SCard
- **Hash Operations**: HSet, HGet, HGetAll, HDel, HExists, HLen
- **Sorted Set Operations**: ZAdd, ZRange, ZScore, ZRem, ZCard
- **Utility Operations**: Keys, FlushDB, Ping

## Usage Examples

### Client Connection

```go
package main

import "redis_emulator"

func main() {
    // Create a new Redis client
    client := NewClient(&Options{
        Addr:     "localhost:6379",
        Password: "", // no password set
        DB:       0,  // use default DB
    })
}
```

### String Operations

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    client := NewClient(&Options{Addr: "localhost:6379"})

    // Set a value
    client.Set("name", "Alice", 0)

    // Get a value
    value, err := client.Get("name")
    if err == nil {
        fmt.Println("Name:", value)
    }

    // Set with expiration
    client.Set("session", "abc123", 5*time.Minute)

    // Increment/Decrement
    client.Set("counter", "0", 0)
    client.Incr("counter")          // counter = 1
    client.IncrBy("counter", 10)    // counter = 11
    client.Decr("counter")          // counter = 10
    client.DecrBy("counter", 5)     // counter = 5
}
```

### Key Operations

```go
package main

func main() {
    client := NewClient(&Options{Addr: "localhost:6379"})

    // Check if keys exist
    count, _ := client.Exists("key1", "key2")
    fmt.Printf("%d keys exist\n", count)

    // Delete keys
    deleted, _ := client.Del("key1", "key2")
    fmt.Printf("Deleted %d keys\n", deleted)

    // Set expiration
    client.Set("temp", "data", 0)
    client.Expire("temp", 10*time.Second)

    // Get time to live
    ttl, _ := client.TTL("temp")
    fmt.Printf("TTL: %v\n", ttl)
}
```

### List Operations

```go
package main

func main() {
    client := NewClient(&Options{Addr: "localhost:6379"})

    // Push elements
    client.RPush("tasks", "task1", "task2", "task3")
    client.LPush("tasks", "urgent")

    // Pop elements
    first, _ := client.LPop("tasks")  // "urgent"
    last, _ := client.RPop("tasks")   // "task3"

    // Get range
    tasks, _ := client.LRange("tasks", 0, -1)
    fmt.Println("Tasks:", tasks)

    // Get length
    length, _ := client.LLen("tasks")
    fmt.Printf("List has %d items\n", length)
}
```

### Set Operations

```go
package main

func main() {
    client := NewClient(&Options{Addr: "localhost:6379"})

    // Add members to a set
    client.SAdd("tags", "go", "redis", "database")
    client.SAdd("tags", "go") // duplicate ignored

    // Check membership
    isMember, _ := client.SIsMember("tags", "redis")
    if isMember {
        fmt.Println("redis is in the set")
    }

    // Get all members
    members, _ := client.SMembers("tags")
    fmt.Println("Tags:", members)

    // Remove members
    client.SRem("tags", "database")

    // Get set size
    size, _ := client.SCard("tags")
    fmt.Printf("Set has %d members\n", size)
}
```

### Hash Operations

```go
package main

func main() {
    client := NewClient(&Options{Addr: "localhost:6379"})

    // Set hash fields
    client.HSet("user:1", "name", "Alice")
    client.HSet("user:1", "email", "alice@example.com")
    client.HSet("user:1", "age", "25")

    // Get a field
    name, _ := client.HGet("user:1", "name")
    fmt.Println("Name:", name)

    // Get all fields
    user, _ := client.HGetAll("user:1")
    fmt.Println("User:", user)

    // Check if field exists
    exists, _ := client.HExists("user:1", "name")
    if exists {
        fmt.Println("Name field exists")
    }

    // Get hash length
    length, _ := client.HLen("user:1")
    fmt.Printf("Hash has %d fields\n", length)

    // Delete fields
    client.HDel("user:1", "age")
}
```

### Sorted Set Operations

```go
package main

func main() {
    client := NewClient(&Options{Addr: "localhost:6379"})

    // Add members with scores
    client.ZAdd("leaderboard",
        100, "Alice",
        85, "Bob",
        120, "Charlie",
    )

    // Get range (sorted by score)
    top3, _ := client.ZRange("leaderboard", 0, 2)
    fmt.Println("Top 3:", top3) // [Bob, Alice, Charlie]

    // Get score of a member
    score, _ := client.ZScore("leaderboard", "Alice")
    fmt.Printf("Alice's score: %.0f\n", score)

    // Remove members
    client.ZRem("leaderboard", "Bob")

    // Get sorted set size
    size, _ := client.ZCard("leaderboard")
    fmt.Printf("Leaderboard has %d members\n", size)
}
```

### Pattern Matching

```go
package main

func main() {
    client := NewClient(&Options{Addr: "localhost:6379"})

    // Set multiple keys
    client.Set("user:1:name", "Alice", 0)
    client.Set("user:2:name", "Bob", 0)
    client.Set("user:3:name", "Charlie", 0)
    client.Set("product:1", "Laptop", 0)

    // Find keys matching pattern
    userKeys, _ := client.Keys("user:*")
    fmt.Println("User keys:", userKeys)

    // Get all keys
    allKeys, _ := client.Keys("*")
    fmt.Println("All keys:", allKeys)
}
```

### Cache Example

```go
package main

import (
    "fmt"
    "time"
)

type UserCache struct {
    client *Client
}

func NewUserCache() *UserCache {
    return &UserCache{
        client: NewClient(&Options{Addr: "localhost:6379"}),
    }
}

func (uc *UserCache) GetUser(id string) (string, error) {
    // Try to get from cache
    key := fmt.Sprintf("user:%s", id)
    value, err := uc.client.Get(key)
    if err == nil {
        fmt.Println("Cache hit")
        return value, nil
    }

    // Cache miss - fetch from database (simulated)
    fmt.Println("Cache miss - fetching from DB")
    userData := fmt.Sprintf("User data for %s", id)

    // Store in cache with 5 minute expiration
    uc.client.Set(key, userData, 5*time.Minute)

    return userData, nil
}

func main() {
    cache := NewUserCache()

    // First call - cache miss
    cache.GetUser("123")

    // Second call - cache hit
    cache.GetUser("123")
}
```

### Session Management

```go
package main

import (
    "fmt"
    "time"
)

type SessionStore struct {
    client *Client
}

func NewSessionStore() *SessionStore {
    return &SessionStore{
        client: NewClient(&Options{Addr: "localhost:6379"}),
    }
}

func (ss *SessionStore) CreateSession(sessionID, userID string) error {
    key := fmt.Sprintf("session:%s", sessionID)
    ss.client.HSet(key, "user_id", userID)
    ss.client.HSet(key, "created_at", time.Now().String())
    ss.client.Expire(key, 30*time.Minute)
    return nil
}

func (ss *SessionStore) GetSession(sessionID string) (map[string]string, error) {
    key := fmt.Sprintf("session:%s", sessionID)
    return ss.client.HGetAll(key)
}

func (ss *SessionStore) DeleteSession(sessionID string) error {
    key := fmt.Sprintf("session:%s", sessionID)
    ss.client.Del(key)
    return nil
}

func main() {
    store := NewSessionStore()

    // Create session
    store.CreateSession("abc123", "user456")

    // Get session
    session, _ := store.GetSession("abc123")
    fmt.Println("Session:", session)

    // Delete session
    store.DeleteSession("abc123")
}
```

### Rate Limiting

```go
package main

import (
    "fmt"
    "time"
)

type RateLimiter struct {
    client *Client
}

func NewRateLimiter() *RateLimiter {
    return &RateLimiter{
        client: NewClient(&Options{Addr: "localhost:6379"}),
    }
}

func (rl *RateLimiter) Allow(userID string, limit int64) bool {
    key := fmt.Sprintf("rate:%s", userID)

    // Get current count
    count, err := rl.client.Get(key)
    if err != nil {
        // First request
        rl.client.Set(key, "1", 60*time.Second)
        return true
    }

    // Parse count
    currentCount := int64(0)
    fmt.Sscanf(count, "%d", &currentCount)

    if currentCount >= limit {
        return false
    }

    // Increment count
    rl.client.Incr(key)
    return true
}

func main() {
    limiter := NewRateLimiter()

    // Allow 5 requests per minute
    for i := 0; i < 7; i++ {
        allowed := limiter.Allow("user123", 5)
        fmt.Printf("Request %d: %v\n", i+1, allowed)
    }
}
```

### Queue Implementation

```go
package main

import "fmt"

type Queue struct {
    client *Client
    name   string
}

func NewQueue(name string) *Queue {
    return &Queue{
        client: NewClient(&Options{Addr: "localhost:6379"}),
        name:   name,
    }
}

func (q *Queue) Enqueue(item string) error {
    _, err := q.client.RPush(q.name, item)
    return err
}

func (q *Queue) Dequeue() (string, error) {
    return q.client.LPop(q.name)
}

func (q *Queue) Size() int {
    size, _ := q.client.LLen(q.name)
    return size
}

func main() {
    queue := NewQueue("tasks")

    // Add tasks
    queue.Enqueue("task1")
    queue.Enqueue("task2")
    queue.Enqueue("task3")

    fmt.Printf("Queue size: %d\n", queue.Size())

    // Process tasks
    for queue.Size() > 0 {
        task, _ := queue.Dequeue()
        fmt.Printf("Processing: %s\n", task)
    }
}
```

## Testing

Run the comprehensive test suite:

```bash
go run test_redis_emulator.go
```

Tests cover:
- Client creation and connection
- Ping command
- String operations (Set, Get)
- Expiration and TTL
- Delete and Exists operations
- Increment and Decrement
- List operations (Push, Pop, Range, Length)
- Set operations (Add, Members, Membership, Remove, Cardinality)
- Hash operations (Set, Get, GetAll, Length, Exists)
- Sorted set operations (Add, Range, Score, Remove, Cardinality)
- Pattern matching with Keys
- FlushDB

Total: 24 tests, all passing

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for go-redis in development and testing:

```go
// Instead of:
// import "github.com/go-redis/redis/v8"

// Use:
// import "redis_emulator"

// Most of your Redis code will work with minimal changes
func main() {
    client := NewClient(&Options{
        Addr: "localhost:6379",
    })

    client.Set("key", "value", 0)
    value, _ := client.Get("key")
}
```

## Use Cases

Perfect for:
- **Local Development**: Develop Redis-dependent applications without running Redis
- **Testing**: Test caching and data structure operations in memory
- **Learning**: Understand Redis commands and data structures
- **Prototyping**: Quickly prototype applications using Redis patterns
- **Education**: Teach caching and NoSQL concepts
- **CI/CD**: Run Redis-dependent tests without Redis infrastructure

## Limitations

This is an emulator for development and testing purposes:
- No actual network communication (in-memory storage)
- No persistence (data is lost when program exits)
- No replication or clustering
- No Pub/Sub messaging
- No transactions (MULTI/EXEC)
- No Lua scripting
- No pipelining
- Simplified pattern matching (only * wildcard)
- No connection pooling
- Single-threaded (no concurrent access handling)

## Supported Features

### String Commands
- ✅ SET - Set key to hold string value
- ✅ GET - Get value of key
- ✅ INCR - Increment integer value
- ✅ INCRBY - Increment by amount
- ✅ DECR - Decrement integer value
- ✅ DECRBY - Decrement by amount

### Key Commands
- ✅ DEL - Delete keys
- ✅ EXISTS - Check if keys exist
- ✅ EXPIRE - Set key expiration
- ✅ TTL - Get time to live
- ✅ KEYS - Find keys matching pattern

### List Commands
- ✅ LPUSH - Push to list head
- ✅ RPUSH - Push to list tail
- ✅ LPOP - Pop from list head
- ✅ RPOP - Pop from list tail
- ✅ LRANGE - Get list range
- ✅ LLEN - Get list length

### Set Commands
- ✅ SADD - Add members to set
- ✅ SMEMBERS - Get all set members
- ✅ SISMEMBER - Check set membership
- ✅ SREM - Remove set members
- ✅ SCARD - Get set cardinality

### Hash Commands
- ✅ HSET - Set hash field
- ✅ HGET - Get hash field
- ✅ HGETALL - Get all hash fields
- ✅ HDEL - Delete hash fields
- ✅ HEXISTS - Check if hash field exists
- ✅ HLEN - Get hash length

### Sorted Set Commands
- ✅ ZADD - Add members with scores
- ✅ ZRANGE - Get range by index
- ✅ ZSCORE - Get member score
- ✅ ZREM - Remove members
- ✅ ZCARD - Get sorted set cardinality

### Connection Commands
- ✅ PING - Test connection

### Server Commands
- ✅ FLUSHDB - Remove all keys

## Real-World Redis Concepts

This emulator teaches the following concepts:

1. **Key-Value Storage**: Basic Redis data model
2. **Data Structures**: Lists, Sets, Hashes, Sorted Sets
3. **Expiration**: Time-to-live for keys
4. **Atomic Operations**: Increment/Decrement operations
5. **Caching Patterns**: Cache-aside, write-through
6. **Session Management**: Storing user sessions
7. **Rate Limiting**: Request throttling
8. **Queues**: FIFO data structures
9. **Leaderboards**: Using sorted sets for ranking
10. **Pattern Matching**: Finding keys by pattern

## Compatibility

Emulates core features of:
- go-redis/redis (github.com/go-redis/redis)
- Redis 6.x/7.x command set
- Standard Redis data structure semantics

## License

Part of the Emu-Soft project. See main repository LICENSE.
