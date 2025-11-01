# TracAgg - Distributed Tracing Aggregator

A pure Python implementation of a distributed tracing aggregator for microservices without external dependencies.

## What This Provides

**Purpose:** Collect, correlate, and analyze distributed traces from multiple microservices in a system
**Use Case:** Observability and performance analysis for microservice architectures

## Features

- **Trace Collection** from multiple services
- **Span Correlation** and trace reconstruction
- **Service Dependency Mapping** with call graphs
- **Latency Analysis** with percentile calculations
- **Bottleneck Detection** identifying slow operations
- **Error Tracking** across distributed traces
- **Query Capabilities** with multiple filter options
- **Critical Path Analysis** for trace optimization
- **Statistics Collection** per service and operation
- **Trace Export** in JSON format
- **Thread-safe** operations for concurrent ingestion

## Core Components

- **TracAgg.py**: Main implementation
  - `Span`: Individual span in a trace with timing and metadata
  - `Trace`: Complete trace with multiple spans
  - `TracAgg`: Main aggregator for collecting and analyzing traces
  - `ServiceDependency`: Tracks dependencies between services
  - `SpanKind`: Enumeration of span types (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
  - `TraceStatus`: Trace completion status (COMPLETE, INCOMPLETE, ERROR)

## Usage

### Basic Trace Ingestion

```python
from TracAgg import TracAgg, create_span_data

# Initialize aggregator
agg = TracAgg(retention_seconds=3600)  # Keep traces for 1 hour

# Create a span
span_data = create_span_data(
    trace_id='trace-123',
    span_id='span-1',
    service_name='api-gateway',
    operation_name='GET /users',
    duration_ms=150.0,
    status_code=200
)

# Ingest the span
trace_id = agg.ingest_span(span_data)
```

### Multi-Service Trace

```python
from TracAgg import TracAgg, create_span_data

agg = TracAgg()

# Root span - API Gateway
root_span = create_span_data(
    trace_id='trace-456',
    span_id='span-1',
    service_name='api-gateway',
    operation_name='GET /orders',
    duration_ms=300.0
)
agg.ingest_span(root_span)

# Child span - Order Service
order_span = create_span_data(
    trace_id='trace-456',
    span_id='span-2',
    parent_span_id='span-1',
    service_name='order-service',
    operation_name='fetch_orders',
    duration_ms=200.0,
    kind='client',
    tags={'peer.service': 'database'}
)
agg.ingest_span(order_span)

# Grandchild span - Database
db_span = create_span_data(
    trace_id='trace-456',
    span_id='span-3',
    parent_span_id='span-2',
    service_name='database',
    operation_name='SELECT orders',
    duration_ms=150.0
)
agg.ingest_span(db_span)
```

### Retrieving Traces

```python
from TracAgg import TracAgg

agg = TracAgg()

# Get specific trace
trace = agg.get_trace('trace-456')
print(f"Trace duration: {trace.duration_ms}ms")
print(f"Services involved: {trace.services}")
print(f"Total spans: {len(trace.spans)}")

# Check trace completion
if trace.is_complete():
    print(f"Trace status: {trace.status.value}")
```

### Querying Traces

```python
from TracAgg import TracAgg

agg = TracAgg()

# Query by service
traces = agg.query_traces(service_name='user-service', limit=10)

# Query by operation
traces = agg.query_traces(operation_name='database_query')

# Query by duration
slow_traces = agg.query_traces(min_duration_ms=500.0)

# Query traces with errors
error_traces = agg.query_traces(has_error=True)

# Combined filters
traces = agg.query_traces(
    service_name='api-gateway',
    min_duration_ms=100.0,
    max_duration_ms=500.0,
    has_error=False,
    limit=50
)
```

### Service Dependencies

```python
from TracAgg import TracAgg, create_span_data

agg = TracAgg()

# Ingest span with service dependency
span = create_span_data(
    trace_id='trace-789',
    span_id='span-1',
    service_name='api-gateway',
    operation_name='call_user_service',
    duration_ms=100.0,
    kind='client',
    tags={'peer.service': 'user-service'}
)
agg.ingest_span(span)

# Get all dependencies
dependencies = agg.get_service_dependencies()
for dep in dependencies:
    print(f"{dep.from_service} -> {dep.to_service}")
    print(f"  Calls: {dep.call_count}")
    print(f"  Avg Latency: {dep.average_latency_ms():.2f}ms")
    print(f"  Error Rate: {dep.error_rate():.2%}")

# Get dependency graph
graph = agg.get_service_graph()
for service, downstream in graph.items():
    print(f"{service} calls: {', '.join(downstream)}")
```

### Service Statistics

```python
from TracAgg import TracAgg

agg = TracAgg()

# Get statistics for specific service
stats = agg.get_service_stats('user-service')
print(f"Span Count: {stats['span_count']}")
print(f"Avg Duration: {stats.get('avg_duration_ms', 0):.2f}ms")
print(f"Error Rate: {stats.get('error_rate', 0):.2%}")

# Get statistics for all services
all_stats = agg.get_service_stats()
for service, stats in all_stats.items():
    print(f"\n{service}:")
    print(f"  Spans: {stats['span_count']}")
    print(f"  Avg Duration: {stats.get('avg_duration_ms', 0):.2f}ms")
```

### Bottleneck Detection

```python
from TracAgg import TracAgg

agg = TracAgg()

# Find bottlenecks (95th percentile)
bottlenecks = agg.find_bottlenecks(percentile=0.95)

print("Performance Bottlenecks:")
for bottleneck in bottlenecks[:10]:  # Top 10
    print(f"\n{bottleneck['service']}.{bottleneck['operation']}")
    print(f"  Avg: {bottleneck['avg_duration_ms']:.2f}ms")
    print(f"  P95: {bottleneck['p95_duration_ms']:.2f}ms")
    print(f"  Samples: {bottleneck['sample_count']}")
```

### Critical Path Analysis

```python
from TracAgg import TracAgg

agg = TracAgg()

# Get trace
trace = agg.get_trace('trace-123')

# Get critical path (longest sequential chain)
critical_path = trace.get_critical_path()

print("Critical Path:")
total_duration = 0
for span in critical_path:
    print(f"  {span.service_name}.{span.operation_name}: {span.duration_ms}ms")
    total_duration += span.duration_ms or 0

print(f"Total Critical Path Duration: {total_duration:.2f}ms")
```

### Trace Export

```python
from TracAgg import TracAgg
import json

agg = TracAgg()

# Export trace
trace_data = agg.export_trace('trace-123')

if trace_data:
    # Save to file
    with open('trace-123.json', 'w') as f:
        json.dump(trace_data, f, indent=2)
    
    # Or process the data
    print(f"Trace: {trace_data['trace_id']}")
    print(f"Duration: {trace_data['duration_ms']}ms")
    print(f"Services: {', '.join(trace_data['services'])}")
    print(f"Spans: {len(trace_data['spans'])}")
```

### Cleanup and Maintenance

```python
from TracAgg import TracAgg

# Initialize with retention period
agg = TracAgg(retention_seconds=3600)  # 1 hour retention

# Periodically cleanup old traces
removed = agg.cleanup_old_traces()
print(f"Removed {removed} old traces")

# Get current trace count
count = agg.get_trace_count()
print(f"Currently storing {count} traces")

# Clear all data
agg.clear()
```

## Testing

Run the test suite:

```bash
cd python/TracAgg
python test_TracAgg.py
```

Or run specific test classes:

```bash
python test_TracAgg.py TestTracAggBasic
python test_TracAgg.py TestServiceDependencies
python test_TracAgg.py TestQueryCapabilities
```

## Implementation Notes

- **Thread-safe**: All operations use locks for concurrent access
- **In-memory storage**: Traces stored locally for fast access
- **Retention management**: Automatic cleanup of old traces
- **Span correlation**: Automatic parent-child relationship tracking
- **Dependency tracking**: Tracks client-server relationships via tags
- **No external dependencies**: Pure Python implementation

## API Reference

### TracAgg Class

**Constructor:**
```python
TracAgg(retention_seconds: int = 3600)
```

**Methods:**
- `ingest_span(span_data: Dict) -> str`: Ingest a span and return trace ID
- `get_trace(trace_id: str) -> Optional[Trace]`: Retrieve a trace by ID
- `query_traces(**filters) -> List[Trace]`: Query traces with filters
- `get_service_dependencies() -> List[ServiceDependency]`: Get all service dependencies
- `get_service_graph() -> Dict[str, List[str]]`: Get dependency graph
- `get_service_stats(service_name: Optional[str]) -> Dict`: Get service statistics
- `find_bottlenecks(percentile: float) -> List[Dict]`: Find performance bottlenecks
- `cleanup_old_traces() -> int`: Remove old traces and return count
- `get_trace_count() -> int`: Get total number of traces
- `export_trace(trace_id: str) -> Optional[Dict]`: Export trace as JSON
- `clear()`: Clear all traces and statistics

### Helper Functions

**create_span_data:**
```python
create_span_data(
    trace_id: str,
    span_id: str,
    service_name: str,
    operation_name: str,
    parent_span_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    status_code: int = 200,
    kind: str = "internal",
    tags: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

## Example Use Cases

### Microservice Request Tracing

```python
from TracAgg import TracAgg, create_span_data
import time

agg = TracAgg()

def handle_user_request(user_id: str):
    """Simulate handling a user request across services"""
    trace_id = f"trace-{int(time.time())}"
    
    # API Gateway receives request
    gateway_span = create_span_data(
        trace_id=trace_id,
        span_id='gateway-1',
        service_name='api-gateway',
        operation_name='GET /user/profile',
        duration_ms=250.0,
        kind='server',
        tags={'http.method': 'GET', 'user_id': user_id}
    )
    agg.ingest_span(gateway_span)
    
    # Call to Auth Service
    auth_span = create_span_data(
        trace_id=trace_id,
        span_id='auth-1',
        parent_span_id='gateway-1',
        service_name='auth-service',
        operation_name='verify_token',
        duration_ms=50.0,
        kind='client',
        tags={'peer.service': 'auth-service'}
    )
    agg.ingest_span(auth_span)
    
    # Call to User Service
    user_span = create_span_data(
        trace_id=trace_id,
        span_id='user-1',
        parent_span_id='gateway-1',
        service_name='user-service',
        operation_name='get_profile',
        duration_ms=150.0,
        kind='client',
        tags={'peer.service': 'user-service', 'user_id': user_id}
    )
    agg.ingest_span(user_span)
    
    # Database query
    db_span = create_span_data(
        trace_id=trace_id,
        span_id='db-1',
        parent_span_id='user-1',
        service_name='postgres',
        operation_name='SELECT FROM users',
        duration_ms=80.0,
        tags={'db.system': 'postgresql', 'db.statement': 'SELECT * FROM users WHERE id = $1'}
    )
    agg.ingest_span(db_span)
    
    return trace_id

# Handle request
trace_id = handle_user_request('user-123')

# Analyze the trace
trace = agg.get_trace(trace_id)
print(f"Total duration: {trace.duration_ms}ms")
print(f"Services: {trace.services}")
print(f"Critical path: {len(trace.get_critical_path())} spans")
```

### Real-Time Monitoring Dashboard

```python
from TracAgg import TracAgg
import time

agg = TracAgg()

def generate_dashboard():
    """Generate real-time monitoring dashboard"""
    print("=== Distributed Tracing Dashboard ===\n")
    
    # Overall stats
    print(f"Total Traces: {agg.get_trace_count()}")
    
    # Service statistics
    print("\n--- Service Statistics ---")
    stats = agg.get_service_stats()
    for service, data in stats.items():
        print(f"\n{service}:")
        print(f"  Requests: {data['span_count']}")
        if data.get('avg_duration_ms'):
            print(f"  Avg Latency: {data['avg_duration_ms']:.2f}ms")
        if data.get('error_rate'):
            print(f"  Error Rate: {data['error_rate']:.2%}")
    
    # Top bottlenecks
    print("\n--- Top Bottlenecks (P95) ---")
    bottlenecks = agg.find_bottlenecks(percentile=0.95)
    for i, bottleneck in enumerate(bottlenecks[:5], 1):
        print(f"{i}. {bottleneck['service']}.{bottleneck['operation']}")
        print(f"   P95: {bottleneck['p95_duration_ms']:.2f}ms")
    
    # Service dependencies
    print("\n--- Service Dependencies ---")
    graph = agg.get_service_graph()
    for service, downstream in graph.items():
        print(f"{service} -> {', '.join(downstream)}")

# Run dashboard
generate_dashboard()
```

### Error Analysis

```python
from TracAgg import TracAgg

agg = TracAgg()

def analyze_errors():
    """Analyze error patterns in traces"""
    error_traces = agg.query_traces(has_error=True)
    
    print(f"Found {len(error_traces)} traces with errors\n")
    
    # Group errors by service
    service_errors = {}
    for trace in error_traces:
        for span in trace.spans:
            if span.status_code >= 400:
                service = span.service_name
                if service not in service_errors:
                    service_errors[service] = []
                service_errors[service].append({
                    'trace_id': trace.trace_id,
                    'operation': span.operation_name,
                    'status': span.status_code
                })
    
    # Print error summary
    for service, errors in service_errors.items():
        print(f"{service}: {len(errors)} errors")
        for error in errors[:5]:  # Show first 5
            print(f"  - {error['operation']}: {error['status']}")

analyze_errors()
```

## Performance Considerations

- **Memory**: Traces stored in-memory; configure retention_seconds appropriately
- **Cleanup**: Call cleanup_old_traces() periodically to manage memory
- **Concurrency**: Thread-safe operations, suitable for concurrent ingestion
- **Indexing**: Queries scan all traces; consider external storage for large volumes
- **Sampling**: Consider implementing sampling at the span creation level

## Best Practices

1. **Use consistent trace IDs**: Propagate trace IDs across service boundaries
2. **Set appropriate retention**: Balance memory usage with analysis needs
3. **Tag client spans**: Use 'peer.service' tag for dependency tracking
4. **Include metadata**: Add relevant tags for better analysis
5. **Set status codes**: Use standard HTTP codes for errors
6. **Regular cleanup**: Schedule periodic cleanup_old_traces() calls
7. **Export important traces**: Export and store critical traces externally
8. **Monitor bottlenecks**: Regular bottleneck analysis for optimization

## License

This implementation is part of the Emu-Soft project and is original code written from scratch.
