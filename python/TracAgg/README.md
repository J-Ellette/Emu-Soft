# TracAgg - Distributed Tracing Aggregator

A pure Python distributed tracing aggregator for microservices without external dependencies.

## What This Tool Does

**Purpose:** TracAgg aggregates and analyzes distributed traces from multiple microservices, helping identify performance bottlenecks, service dependencies, and system health issues.

## Features

- **Trace Aggregation** - Collect and organize spans into complete traces
- **Service Dependency Mapping** - Automatically build service dependency graphs
- **Performance Analysis** - Calculate latencies, percentiles, and identify slow operations
- **Error Tracking** - Track error rates across services and operations
- **Critical Path Analysis** - Identify the longest duration path through distributed traces
- **Trace Search** - Filter traces by service, operation, duration, errors, etc.
- **Service Metrics** - Compute per-service request counts, error rates, and latencies
- **Export/Import** - Save and load trace data in JSON format
- **Thread-safe** - All operations are thread-safe for concurrent usage

## Core Components

- **Span**: Represents a unit of work in a distributed trace
- **Trace**: Aggregates related spans into a complete request flow
- **TracAggregator**: Main class for ingesting and analyzing traces
- **ServiceMetrics**: Tracks performance and health metrics for each service
- **SpanKind**: Classifies span types (SERVER, CLIENT, PRODUCER, CONSUMER)
- **StatusCode**: Indicates success or error status

## Usage

### Basic Trace Aggregation

```python
from TracAgg import TracAggregator, create_span, StatusCode, SpanKind

# Create aggregator
aggregator = TracAggregator()

# Create spans from your microservices
span1 = create_span(
    trace_id="trace-123",
    span_id="span-1",
    service_name="api-gateway",
    operation_name="handle_request",
    start_time=1000.0,
    duration=0.5
)

span2 = create_span(
    trace_id="trace-123",
    span_id="span-2",
    parent_span_id="span-1",
    service_name="user-service",
    operation_name="get_user",
    start_time=1000.1,
    duration=0.2
)

# Ingest spans
aggregator.ingest_spans([span1, span2])

# Get trace
trace = aggregator.get_trace("trace-123")
print(f"Trace has {trace.span_count} spans across {trace.service_count} services")
```

### Analyzing Service Performance

```python
from TracAgg import TracAggregator, create_span, StatusCode

aggregator = TracAggregator()

# Simulate multiple requests
for i in range(100):
    span = create_span(
        trace_id=f"trace-{i}",
        span_id=f"span-{i}",
        service_name="auth-service",
        operation_name="authenticate",
        start_time=float(i * 100),
        duration=0.05 + (i % 10) * 0.01,
        status=StatusCode.ERROR if i % 20 == 0 else StatusCode.OK
    )
    aggregator.ingest_span(span)

# Get service metrics
metrics = aggregator.get_service_metrics("auth-service")
print(f"Auth Service:")
print(f"  Requests: {metrics.request_count}")
print(f"  Errors: {metrics.error_count}")
print(f"  Error Rate: {metrics.get_error_rate():.2%}")
print(f"  Avg Duration: {metrics.get_avg_duration():.4f}s")
print(f"  P95 Duration: {metrics.get_percentile(95):.4f}s")
print(f"  P99 Duration: {metrics.get_percentile(99):.4f}s")
```

### Critical Path Analysis

```python
from TracAgg import TracAggregator, create_span

aggregator = TracAggregator()

# Create a complex trace with multiple services
spans = [
    create_span("trace-1", "span-1", "api-gateway", "handle", 1000.0, 0.5),
    create_span("trace-1", "span-2", "user-service", "get_user", 1000.1, 0.2, parent_span_id="span-1"),
    create_span("trace-1", "span-3", "db-service", "query", 1000.15, 0.15, parent_span_id="span-2"),
    create_span("trace-1", "span-4", "cache-service", "get", 1000.12, 0.05, parent_span_id="span-2"),
]

aggregator.ingest_spans(spans)

# Analyze the trace
analysis = aggregator.analyze_trace("trace-1")
print(f"Total Duration: {analysis['total_duration']:.4f}s")
print(f"Critical Path:")
for step in analysis['critical_path']:
    print(f"  {step['service']}.{step['operation']}: {step['duration']:.4f}s")

print(f"\nService Breakdown:")
for service, breakdown in analysis['service_breakdown'].items():
    print(f"  {service}: {breakdown['duration']:.4f}s ({breakdown['percentage']:.1f}%)")
```

### Service Dependency Mapping

```python
from TracAgg import TracAggregator, create_span

aggregator = TracAggregator()

# Simulate service calls
spans = [
    create_span("trace-1", "span-1", "api-gateway", "handle", 1000.0, 0.5),
    create_span("trace-1", "span-2", "user-service", "get_user", 1000.1, 0.2, parent_span_id="span-1"),
    create_span("trace-1", "span-3", "order-service", "get_orders", 1000.15, 0.15, parent_span_id="span-1"),
    create_span("trace-1", "span-4", "inventory-service", "check", 1000.2, 0.1, parent_span_id="span-3"),
]

aggregator.ingest_spans(spans)

# Get dependency graph
dependencies = aggregator.get_service_dependencies()
print("Service Dependencies:")
for service, depends_on in dependencies.items():
    print(f"  {service} -> {', '.join(depends_on)}")
```

### Finding Slow Operations

```python
from TracAgg import TracAggregator, create_span
import random

aggregator = TracAggregator()

# Simulate various operations with different latencies
services = ["api", "user", "order", "payment"]
operations = ["create", "read", "update", "delete"]

for i in range(1000):
    service = random.choice(services)
    operation = random.choice(operations)
    duration = random.uniform(0.01, 0.5)
    
    span = create_span(
        trace_id=f"trace-{i}",
        span_id=f"span-{i}",
        service_name=service,
        operation_name=operation,
        start_time=float(i),
        duration=duration
    )
    aggregator.ingest_span(span)

# Find slowest operations
slow_ops = aggregator.get_slowest_operations(limit=5)
print("Slowest Operations:")
for service, operation, avg_duration in slow_ops:
    print(f"  {service}.{operation}: {avg_duration:.4f}s avg")
```

### Finding Error-Prone Operations

```python
from TracAgg import TracAggregator, create_span, StatusCode
import random

aggregator = TracAggregator()

# Simulate operations with varying error rates
for i in range(1000):
    # Some operations are more error-prone
    operation = "risky_operation" if i % 3 == 0 else "safe_operation"
    has_error = (operation == "risky_operation" and random.random() < 0.3)
    
    span = create_span(
        trace_id=f"trace-{i}",
        span_id=f"span-{i}",
        service_name="payment-service",
        operation_name=operation,
        start_time=float(i),
        duration=0.1,
        status=StatusCode.ERROR if has_error else StatusCode.OK,
        error_message="Payment failed" if has_error else None
    )
    aggregator.ingest_span(span)

# Find error-prone operations
error_ops = aggregator.get_error_prone_operations(limit=5)
print("Error-Prone Operations:")
for service, operation, error_rate, error_count in error_ops:
    print(f"  {service}.{operation}: {error_rate:.2%} ({error_count} errors)")
```

### Searching Traces

```python
from TracAgg import TracAggregator, create_span, StatusCode

aggregator = TracAggregator()

# Create various traces
for i in range(100):
    spans = [
        create_span(
            trace_id=f"trace-{i}",
            span_id=f"span-{i}-1",
            service_name="api-gateway",
            operation_name="handle_request",
            start_time=float(i * 100),
            duration=0.5 + (i % 10) * 0.1,
            status=StatusCode.ERROR if i % 20 == 0 else StatusCode.OK
        )
    ]
    aggregator.ingest_spans(spans)

# Search for slow traces
slow_traces = aggregator.search_traces(min_duration=1.0)
print(f"Found {len(slow_traces)} slow traces")

# Search for traces with errors
error_traces = aggregator.search_traces(has_errors=True)
print(f"Found {len(error_traces)} traces with errors")

# Search for traces involving specific service
api_traces = aggregator.search_traces(service_name="api-gateway")
print(f"Found {len(api_traces)} traces through api-gateway")
```

### Summary Statistics

```python
from TracAgg import TracAggregator, create_span
import random

aggregator = TracAggregator()

# Generate sample data
for i in range(1000):
    span = create_span(
        trace_id=f"trace-{i}",
        span_id=f"span-{i}",
        service_name=f"service-{i % 5}",
        operation_name="process",
        start_time=float(i),
        duration=random.uniform(0.01, 1.0)
    )
    aggregator.ingest_span(span)

# Get summary statistics
stats = aggregator.get_summary_statistics()
print(f"Total Traces: {stats['total_traces']}")
print(f"Total Spans: {stats['total_spans']}")
print(f"Services: {stats['service_count']}")
print(f"Avg Trace Duration: {stats['avg_trace_duration']:.4f}s")
print(f"P50 Trace Duration: {stats['p50_trace_duration']:.4f}s")
print(f"P95 Trace Duration: {stats['p95_trace_duration']:.4f}s")
print(f"P99 Trace Duration: {stats['p99_trace_duration']:.4f}s")
```

### Export and Import

```python
from TracAgg import TracAggregator, create_span

# Create and populate aggregator
aggregator = TracAggregator()
span = create_span(
    trace_id="trace-1",
    span_id="span-1",
    service_name="api",
    operation_name="handle",
    start_time=1000.0,
    duration=0.5
)
aggregator.ingest_span(span)

# Export to JSON
aggregator.export_to_json("traces.json")

# Import from JSON (in another session)
new_aggregator = TracAggregator()
new_aggregator.import_from_json("traces.json")
print(f"Loaded {len(new_aggregator.get_all_traces())} traces")
```

## Testing

Run the test suite:

```bash
python test_TracAgg.py
```

## Implementation Notes

- **Thread-safe**: All operations use locks for concurrent access
- **In-memory storage**: Traces stored locally for fast analysis
- **No external dependencies**: Uses only Python standard library
- **Flexible span model**: Compatible with various tracing formats
- **Efficient aggregation**: O(1) trace lookup, O(n) analysis operations

## API Reference

### TracAggregator

**Methods:**
- `ingest_span(span)` - Add a single span to the aggregator
- `ingest_spans(spans)` - Add multiple spans at once
- `get_trace(trace_id)` - Retrieve a specific trace
- `get_all_traces()` - Get all traces
- `search_traces(**criteria)` - Search traces with filters
- `get_service_metrics(service_name)` - Get metrics for a service
- `get_all_service_metrics()` - Get metrics for all services
- `get_service_dependencies()` - Get service dependency graph
- `get_slowest_operations(limit)` - Find slowest operations
- `get_error_prone_operations(limit)` - Find error-prone operations
- `analyze_trace(trace_id)` - Detailed trace analysis
- `get_summary_statistics()` - Overall system statistics
- `export_to_json(filename)` - Export traces to JSON
- `import_from_json(filename)` - Import traces from JSON
- `clear()` - Clear all data

### Span

**Attributes:**
- `trace_id` - Unique trace identifier
- `span_id` - Unique span identifier
- `parent_span_id` - Parent span ID (None for root)
- `service_name` - Name of the service
- `operation_name` - Name of the operation
- `start_time` - Start timestamp
- `duration` - Duration in seconds
- `status` - StatusCode (OK or ERROR)
- `kind` - SpanKind (SERVER, CLIENT, etc.)
- `attributes` - Additional metadata
- `error_message` - Error description if failed

### Trace

**Attributes:**
- `trace_id` - Unique trace identifier
- `spans` - List of spans in the trace
- `start_time` - Trace start time
- `duration` - Total trace duration
- `service_count` - Number of unique services
- `span_count` - Number of spans
- `error_count` - Number of failed spans
- `services` - Set of service names

**Methods:**
- `add_span(span)` - Add a span to the trace
- `get_root_span()` - Get the root span
- `get_critical_path()` - Calculate critical path

### ServiceMetrics

**Attributes:**
- `service_name` - Name of the service
- `request_count` - Total requests
- `error_count` - Total errors
- `total_duration` - Sum of all durations

**Methods:**
- `get_error_rate()` - Calculate error rate
- `get_avg_duration()` - Calculate average duration
- `get_percentile(percentile)` - Calculate duration percentile

## Use Cases

### Microservice Performance Monitoring

Use TracAgg to monitor the performance of your microservices architecture:

```python
# Continuously ingest spans from your services
# Periodically check for slow services
metrics = aggregator.get_all_service_metrics()
for service_name, metrics in metrics.items():
    if metrics.get_percentile(95) > 1.0:  # P95 > 1 second
        print(f"Warning: {service_name} is slow!")
```

### Debugging Distributed Transactions

Find and analyze problematic traces:

```python
# Find traces with errors
error_traces = aggregator.search_traces(has_errors=True)
for trace in error_traces:
    analysis = aggregator.analyze_trace(trace.trace_id)
    print(f"Trace {trace.trace_id} failed:")
    print(f"  Services involved: {', '.join(analysis['services'])}")
    print(f"  Duration: {analysis['total_duration']:.2f}s")
```

### Capacity Planning

Analyze service load and dependencies:

```python
# Understand which services handle the most load
all_metrics = aggregator.get_all_service_metrics()
sorted_services = sorted(
    all_metrics.items(),
    key=lambda x: x[1].request_count,
    reverse=True
)

print("Services by load:")
for service_name, metrics in sorted_services:
    print(f"  {service_name}: {metrics.request_count} requests")
```

### Service Dependency Visualization

Map your service architecture:

```python
dependencies = aggregator.get_service_dependencies()
print("digraph services {")
for service, deps in dependencies.items():
    for dep in deps:
        print(f'  "{service}" -> "{dep}";')
print("}")
```

## Differences from Production Tracing Systems

- **No real-time streaming**: Spans must be explicitly ingested
- **In-memory only**: No persistent storage (use export/import)
- **No distributed collection**: No agent/collector infrastructure
- **Manual instrumentation**: No automatic trace generation
- **Limited sampling**: No complex sampling strategies
- **No alerting**: Analysis only, no built-in alerts

## Example Integration

```python
# Example: Integrate with your application
from TracAgg import TracAggregator, create_span, StatusCode
import time

aggregator = TracAggregator()

def trace_request(service_name, operation_name, trace_id, parent_span_id=None):
    """Decorator to trace function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            span_id = f"{service_name}-{operation_name}-{time.time()}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                span = create_span(
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    service_name=service_name,
                    operation_name=operation_name,
                    start_time=start_time,
                    duration=duration,
                    status=StatusCode.OK
                )
                aggregator.ingest_span(span)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                span = create_span(
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    service_name=service_name,
                    operation_name=operation_name,
                    start_time=start_time,
                    duration=duration,
                    status=StatusCode.ERROR,
                    error_message=str(e)
                )
                aggregator.ingest_span(span)
                raise
        
        return wrapper
    return decorator

# Usage
@trace_request("user-service", "get_user", "trace-123")
def get_user(user_id):
    # Your business logic
    return {"id": user_id, "name": "Alice"}
```
