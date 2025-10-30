# Prometheus Client Emulator

A pure Python implementation of Prometheus client functionality without external dependencies.

## What This Emulates

**Emulates:** prometheus_client (Python client for Prometheus monitoring)
**Original:** https://github.com/prometheus/client_python

## Features

- **Counter** metrics (monotonically increasing values)
- **Gauge** metrics (arbitrary up/down values)
- **Histogram** metrics (observations with configurable buckets)
- **Summary** metrics (observations with quantiles)
- Multi-dimensional metrics with labels
- Collector registry for metric management
- Prometheus text format exposition
- Context manager support for timing
- Process and platform metrics collectors
- Thread-safe operations
- No external dependencies

## Core Components

- **prometheus_client_emulator.py**: Main implementation
  - `Counter`: Monotonically increasing counter
  - `Gauge`: Value that can go up and down
  - `Histogram`: Observations bucketed into configurable ranges
  - `Summary`: Observations with sum and count
  - `CollectorRegistry`: Registry for managing metrics
  - `ProcessCollector`: System process metrics
  - `PlatformCollector`: Python platform information

## Usage

### Counter

```python
from prometheus_client_emulator import Counter, REGISTRY

# Create a counter
requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ('method', 'endpoint')
)
REGISTRY.register(requests_total)

# Increment counter
requests_total.inc(labels={'method': 'GET', 'endpoint': '/api/users'})
requests_total.inc(5, labels={'method': 'POST', 'endpoint': '/api/users'})

# Using labels() for convenience
http_requests = Counter('requests', 'HTTP requests', ('method',))
REGISTRY.register(http_requests)

get_counter = http_requests.labels(method='GET')
get_counter.inc()
get_counter.inc()
```

### Gauge

```python
from prometheus_client_emulator import Gauge, REGISTRY

# Create a gauge
temperature = Gauge('temperature_celsius', 'Current temperature')
REGISTRY.register(temperature)

# Set value
temperature.set(23.5)

# Increment/decrement
temperature.inc(1.5)
temperature.dec(0.5)

# Set to current time
temperature.set_to_current_time()

# With labels
memory_usage = Gauge('memory_usage_bytes', 'Memory usage', ('server',))
REGISTRY.register(memory_usage)

web1_memory = memory_usage.labels(server='web-1')
web1_memory.set(1024 * 1024 * 512)  # 512 MB
```

### Histogram

```python
from prometheus_client_emulator import Histogram, REGISTRY

# Create a histogram
request_duration = Histogram(
    'request_duration_seconds',
    'Request duration',
    buckets=(.01, .05, .1, .5, 1.0, 5.0, float('inf'))
)
REGISTRY.register(request_duration)

# Observe values
request_duration.observe(0.05)
request_duration.observe(0.15)
request_duration.observe(0.75)

# Time a block of code
with request_duration.time():
    # Your code here
    process_request()

# With labels
api_latency = Histogram(
    'api_latency_seconds',
    'API latency',
    ('endpoint',)
)
REGISTRY.register(api_latency)

with api_latency.labels(endpoint='/api/users').time():
    fetch_users()
```

### Summary

```python
from prometheus_client_emulator import Summary, REGISTRY

# Create a summary
response_size = Summary('response_size_bytes', 'Response size')
REGISTRY.register(response_size)

# Observe values
response_size.observe(1024)
response_size.observe(2048)
response_size.observe(512)

# Time a block of code
with response_size.time():
    # Your code here
    generate_response()
```

### Registry

```python
from prometheus_client_emulator import CollectorRegistry, Counter

# Create custom registry
my_registry = CollectorRegistry()

# Register metrics
counter = Counter('my_counter', 'My counter')
my_registry.register(counter)

# Unregister
my_registry.unregister(counter)

# Get all collectors
collectors = my_registry.collect()

# Get specific metric value
value = my_registry.get_sample_value('my_counter', {'label': 'value'})
```

### Metrics Exposition

```python
from prometheus_client_emulator import generate_latest, REGISTRY

# Generate Prometheus text format
metrics_text = generate_latest(REGISTRY)
print(metrics_text)

# Output:
# # HELP http_requests_total Total HTTP requests
# # TYPE http_requests_total counter
# http_requests_total{method="GET",endpoint="/api/users"} 1.0
# http_requests_total{method="POST",endpoint="/api/users"} 5.0
```

### Process Metrics

```python
from prometheus_client_emulator import ProcessCollector, REGISTRY

# Add process metrics
process_collector = ProcessCollector(REGISTRY)

# Metrics added:
# - process_cpu_seconds_total
# - process_open_fds
# - process_max_fds
# - process_virtual_memory_bytes
# - process_resident_memory_bytes
# - process_start_time_seconds
```

### Platform Metrics

```python
from prometheus_client_emulator import PlatformCollector, REGISTRY

# Add platform metrics
platform_collector = PlatformCollector(REGISTRY)

# Metrics added:
# - python_info (with version, implementation, etc.)
```

## Testing

Run the test suite:

```bash
python test_prometheus_client_emulator.py
```

## Implementation Notes

- **Thread-safe**: All metric operations use locks for thread safety
- **No network**: Metrics are stored in-memory, not sent to Prometheus
- **Text format only**: Only Prometheus text format is supported
- **Simplified quantiles**: Summary metrics track observations but don't calculate quantiles
- **Basic process metrics**: Process collector provides structure but may not populate all values on all platforms

## API Compatibility

This emulator implements the core Prometheus client API:

**Metrics:**
- `Counter` - Monotonically increasing counter
- `Gauge` - Value that can go up or down
- `Histogram` - Observations with buckets
- `Summary` - Observations with sum and count

**Methods:**
- `inc()` - Increment counter/gauge
- `dec()` - Decrement gauge
- `set()` - Set gauge value
- `observe()` - Add observation to histogram/summary
- `time()` - Context manager for timing
- `labels()` - Get child metric with labels

**Registry:**
- `register()` - Register a collector
- `unregister()` - Unregister a collector
- `collect()` - Get all collectors
- `get_sample_value()` - Get metric value

**Exposition:**
- `generate_latest()` - Generate Prometheus text format

## Differences from Official Client

- **No HTTP server**: Use `generate_latest()` manually
- **No push gateway support**: Metrics stay in-memory
- **Simplified summaries**: No quantile calculation
- **No custom collectors**: Only built-in metric types
- **Basic process metrics**: Limited platform support
- **No multiprocess support**: Single process only

## Example Use Cases

### Web Application Monitoring

```python
from prometheus_client_emulator import Counter, Histogram, REGISTRY, generate_latest

# Request counter
http_requests = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ('method', 'endpoint', 'status')
)
REGISTRY.register(http_requests)

# Request duration
http_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ('method', 'endpoint')
)
REGISTRY.register(http_duration)

def handle_request(method, endpoint):
    with http_duration.labels(method=method, endpoint=endpoint).time():
        # Process request
        status = process()
        http_requests.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        return status

# Expose metrics
def metrics_endpoint():
    return generate_latest(REGISTRY)
```

### Background Job Monitoring

```python
from prometheus_client_emulator import Counter, Gauge, Summary, REGISTRY

# Job counters
jobs_started = Counter('jobs_started_total', 'Jobs started', ('job_type',))
jobs_completed = Counter('jobs_completed_total', 'Jobs completed', ('job_type', 'status'))
REGISTRY.register(jobs_started)
REGISTRY.register(jobs_completed)

# Active jobs gauge
jobs_active = Gauge('jobs_active', 'Currently active jobs', ('job_type',))
REGISTRY.register(jobs_active)

# Job duration
job_duration = Summary('job_duration_seconds', 'Job duration', ('job_type',))
REGISTRY.register(job_duration)

def run_job(job_type):
    jobs_started.labels(job_type=job_type).inc()
    jobs_active.labels(job_type=job_type).inc()
    
    try:
        with job_duration.labels(job_type=job_type).time():
            # Process job
            result = process_job()
        
        jobs_completed.labels(job_type=job_type, status='success').inc()
        return result
    except Exception as e:
        jobs_completed.labels(job_type=job_type, status='failure').inc()
        raise
    finally:
        jobs_active.labels(job_type=job_type).dec()
```

### Database Connection Pool Monitoring

```python
from prometheus_client_emulator import Gauge, Counter, Histogram, REGISTRY

# Pool metrics
db_connections_active = Gauge('db_connections_active', 'Active database connections')
db_connections_idle = Gauge('db_connections_idle', 'Idle database connections')
db_queries_total = Counter('db_queries_total', 'Total database queries', ('operation',))
db_query_duration = Histogram('db_query_duration_seconds', 'Query duration', ('operation',))

REGISTRY.register(db_connections_active)
REGISTRY.register(db_connections_idle)
REGISTRY.register(db_queries_total)
REGISTRY.register(db_query_duration)

class DatabasePool:
    def query(self, operation, sql):
        db_connections_idle.dec()
        db_connections_active.inc()
        db_queries_total.labels(operation=operation).inc()
        
        try:
            with db_query_duration.labels(operation=operation).time():
                return execute_query(sql)
        finally:
            db_connections_active.dec()
            db_connections_idle.inc()
```

## Performance Considerations

- **Memory**: Metrics are stored in-memory; label cardinality affects memory usage
- **Locking**: All operations use locks; high contention may impact performance
- **Label cardinality**: Keep label values bounded to prevent memory growth
- **Histogram buckets**: More buckets = more memory per observation
- **Summary observations**: Stored in memory; may grow unbounded

## Best Practices

1. **Keep label cardinality low**: Don't use unbounded values (user IDs, timestamps) as labels
2. **Use appropriate metric types**: Counter for things that increase, Gauge for current state
3. **Choose histogram buckets carefully**: Based on expected value distribution
4. **Name metrics clearly**: Use `_total` suffix for counters, `_seconds` for durations
5. **Document metrics**: Provide clear documentation strings
6. **Use base units**: Seconds (not milliseconds), bytes (not kilobytes)

## License

This emulator is part of the CIV-ARCOS project and is original code written from scratch. While it emulates Prometheus client functionality, it contains no code from the official Prometheus client library.
