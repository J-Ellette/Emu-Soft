# Database Optimization

Tools for query tracking, performance monitoring, index management, and database optimization.

## Features

- **Query Tracking**: Track all queries with execution time
- **Slow Query Detection**: Automatically identify slow queries
- **Index Management**: List indexes and get recommendations
- **Query Plan Analysis**: Analyze EXPLAIN output for optimization
- **Connection Pool Monitoring**: Track connection pool health
- **Statistics**: Detailed query performance statistics

## Query Tracking

Track and analyze database queries:

```python
from mycms.core.database.optimization import QueryTracker, QueryMetrics
from datetime import datetime, timezone

tracker = QueryTracker(slow_query_threshold=1.0)  # 1 second

# Track a query
metrics = QueryMetrics(
    query="SELECT * FROM users WHERE id = $1",
    execution_time=0.05,
    timestamp=datetime.now(timezone.utc),
    rows_affected=1,
    table="users",
    operation="SELECT"
)

tracker.track_query(metrics)
```

### Using the Decorator

```python
from mycms.core.database.optimization import track_query, get_query_tracker

tracker = get_query_tracker()

@track_query(tracker)
async def execute_query(query: str):
    result = await db.execute(query)
    return result

# Query will be automatically tracked
await execute_query("SELECT * FROM users WHERE id = $1")
```

## Slow Query Detection

Automatically identify and analyze slow queries:

```python
from mycms.core.database.optimization import get_query_tracker

tracker = get_query_tracker()

# Get slow queries
slow_queries = tracker.get_slow_queries(limit=10)

for query in slow_queries:
    print(f"Query: {query.query}")
    print(f"Time: {query.execution_time}s")
    print(f"Table: {query.table}")
```

## Query Statistics

Get detailed statistics about query performance:

```python
# Get overall statistics
stats = tracker.get_query_stats()

print(f"Total queries: {stats['total_queries']}")
print(f"Slow queries: {stats['slow_queries']}")
print(f"Unique patterns: {stats['unique_patterns']}")

# Most frequent queries
for query in stats['most_frequent']:
    print(f"{query['count']} executions, avg {query['avg_time']}s")

# Slowest queries
for query in stats['slowest']:
    print(f"Avg time: {query['avg_time']}s")
```

### Query Pattern Analysis

```python
# Get statistics for specific pattern
pattern = tracker._normalize_query("SELECT * FROM users WHERE id = $1")
stats = tracker.get_query_stats(query_pattern=pattern)

print(f"Executions: {stats['count']}")
print(f"Average time: {stats['avg_time']}s")
print(f"Min time: {stats['min_time']}s")
print(f"Max time: {stats['max_time']}s")
```

## Index Management

Manage and optimize database indexes:

```python
from mycms.core.database.optimization import IndexManager

manager = IndexManager(db_connection)

# List all indexes
indexes = await manager.list_indexes()
for idx in indexes:
    print(f"{idx['table']}.{idx['name']}: {idx['definition']}")

# List indexes for specific table
user_indexes = await manager.list_indexes(table="users")

# Analyze missing indexes
recommendations = await manager.analyze_missing_indexes(tracker)
for rec in recommendations:
    print(f"Table: {rec['table']}")
    print(f"Column: {rec['column']}")
    print(f"Reason: {rec['reason']}")
    print(f"SQL: {rec['recommendation']}")
```

## Query Optimization

Analyze query execution plans:

```python
from mycms.core.database.optimization import QueryOptimizer

optimizer = QueryOptimizer(db_connection)

# Get query execution plan
plan = await optimizer.explain_query(
    "SELECT * FROM users WHERE email = 'test@example.com'",
    analyze=True  # Actually execute the query
)

# Analyze the plan for optimization opportunities
analysis = optimizer.analyze_query_plan(plan)

for suggestion in analysis['suggestions']:
    print(f"Type: {suggestion['type']}")
    print(f"Message: {suggestion['message']}")
    
    if suggestion['type'] == 'index_missing':
        print(f"Table: {suggestion['table']}")
    elif suggestion['type'] == 'high_cost':
        print(f"Cost: {suggestion['cost']}")
```

## Connection Pool Monitoring

Track connection pool performance:

```python
from mycms.core.database.optimization import get_connection_monitor

monitor = get_connection_monitor()

# Record connection events
monitor.record_connection_created()
monitor.record_connection_closed()
monitor.record_wait_time(0.1)  # 100ms wait

# Get statistics
stats = monitor.get_stats()

print(f"Connections created: {stats['connections_created']}")
print(f"Connections in use: {stats['connections_in_use']}")
print(f"Max connections: {stats['max_connections_used']}")
print(f"Avg wait time: {stats['avg_wait_time_ms']}ms")
print(f"Max wait time: {stats['max_wait_time_ms']}ms")
print(f"Uptime: {stats['uptime_seconds']}s")
```

## Complete Integration Example

```python
from mycms.core.database.optimization import (
    QueryTracker,
    IndexManager,
    QueryOptimizer,
    ConnectionPoolMonitor,
    track_query,
    get_query_tracker,
    get_connection_monitor
)

# Setup
tracker = get_query_tracker()
monitor = get_connection_monitor()

# Wrap database connection class
class OptimizedConnection:
    def __init__(self, db_connection):
        self.db = db_connection
        self.monitor = get_connection_monitor()
    
    async def __aenter__(self):
        self.monitor.record_connection_created()
        return self
    
    async def __aexit__(self, *args):
        self.monitor.record_connection_closed()
    
    @track_query(get_query_tracker())
    async def execute(self, query: str, *params):
        return await self.db.execute(query, *params)

# Use optimized connection
async with OptimizedConnection(db) as conn:
    result = await conn.execute("SELECT * FROM users WHERE id = $1", user_id)

# Analyze performance
stats = tracker.get_query_stats()
print(f"Total queries: {stats['total_queries']}")
print(f"Slow queries: {stats['slow_queries']}")

# Check for missing indexes
index_manager = IndexManager(db)
recommendations = await index_manager.analyze_missing_indexes(tracker)

if recommendations:
    print("Missing index recommendations:")
    for rec in recommendations:
        print(f"  {rec['recommendation']}")

# Monitor connection pool
pool_stats = monitor.get_stats()
print(f"Connection pool health: {pool_stats}")
```

## Query Metrics Data Class

```python
from mycms.core.database.optimization import QueryMetrics
from datetime import datetime, timezone

metrics = QueryMetrics(
    query="SELECT * FROM users WHERE id = $1",
    execution_time=0.05,        # Seconds
    timestamp=datetime.now(timezone.utc),
    rows_affected=1,
    table="users",
    operation="SELECT",
    parameters=[123]
)
```

## Best Practices

### 1. Set Appropriate Thresholds

```python
# Production: stricter threshold
tracker = QueryTracker(slow_query_threshold=0.5)  # 500ms

# Development: looser threshold
tracker = QueryTracker(slow_query_threshold=2.0)  # 2 seconds
```

### 2. Regular Analysis

```python
import asyncio

async def analyze_performance():
    """Run periodic performance analysis"""
    tracker = get_query_tracker()
    
    # Get slow queries
    slow = tracker.get_slow_queries(limit=10)
    
    if slow:
        print(f"Found {len(slow)} slow queries")
        
        # Analyze for missing indexes
        manager = IndexManager(db)
        recommendations = await manager.analyze_missing_indexes(tracker)
        
        # Apply recommendations or alert
        for rec in recommendations:
            print(f"Consider: {rec['recommendation']}")
    
    # Reset stats periodically
    tracker.clear_stats()

# Run every hour
while True:
    await analyze_performance()
    await asyncio.sleep(3600)
```

### 3. Monitor Connection Pool

```python
def check_connection_pool():
    """Alert on connection pool issues"""
    monitor = get_connection_monitor()
    stats = monitor.get_stats()
    
    # Alert if wait times are high
    if stats['avg_wait_time_ms'] > 100:
        print(f"Warning: High connection wait time: {stats['avg_wait_time_ms']}ms")
    
    # Alert if using too many connections
    if stats['connections_in_use'] > 80:  # 80% of pool
        print(f"Warning: High connection usage: {stats['connections_in_use']}")
```

### 4. Index Optimization

```python
async def optimize_indexes():
    """Analyze and optimize indexes"""
    manager = IndexManager(db)
    tracker = get_query_tracker()
    
    # Get current indexes
    indexes = await manager.list_indexes()
    print(f"Current indexes: {len(indexes)}")
    
    # Get recommendations
    recommendations = await manager.analyze_missing_indexes(tracker)
    
    # Create missing indexes
    for rec in recommendations:
        print(f"Creating index: {rec['recommendation']}")
        await db.execute(rec['recommendation'])
```

### 5. Query Plan Analysis

```python
async def analyze_slow_query(query: str):
    """Analyze a specific slow query"""
    optimizer = QueryOptimizer(db)
    
    # Get execution plan
    plan = await optimizer.explain_query(query, analyze=False)
    
    # Analyze
    analysis = optimizer.analyze_query_plan(plan)
    
    print(f"Query: {query}")
    print(f"Suggestions: {len(analysis['suggestions'])}")
    
    for suggestion in analysis['suggestions']:
        print(f"  - {suggestion['message']}")
    
    return analysis
```

## Performance Tips

1. **Use Connection Pooling**: Reuse connections to reduce overhead
2. **Create Indexes**: Add indexes for frequently queried columns
3. **Avoid N+1 Queries**: Use JOINs or batch loading
4. **Limit Result Sets**: Use LIMIT and OFFSET for pagination
5. **Monitor Regularly**: Track performance over time

## Monitoring Dashboard Example

```python
def get_performance_dashboard():
    """Get comprehensive performance metrics"""
    tracker = get_query_tracker()
    monitor = get_connection_monitor()
    
    return {
        'query_stats': tracker.get_query_stats(),
        'slow_queries': [
            {
                'query': q.query[:100],
                'time': q.execution_time,
                'timestamp': q.timestamp
            }
            for q in tracker.get_slow_queries(limit=5)
        ],
        'connection_pool': monitor.get_stats(),
        'most_frequent': tracker.get_most_frequent_queries(limit=10),
        'slowest': tracker.get_slowest_queries(limit=10)
    }
```

## Cleanup

Regular cleanup prevents memory growth:

```python
# Clear query statistics
tracker.clear_stats()

# Reset connection monitor
monitor.reset()
```
