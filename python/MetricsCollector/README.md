# Prometheus Emulator - Metrics Collection and Monitoring

This module emulates **Prometheus**, an open-source systems monitoring and alerting toolkit. Prometheus provides a powerful platform for collecting, storing, and querying time-series metrics data.

## What is Prometheus?

Prometheus is a monitoring system developed at SoundCloud that has become one of the most popular monitoring solutions. It provides:
- **Multi-dimensional data model** with time series identified by metric name and key/value pairs
- **Flexible query language (PromQL)** to leverage this dimensionality
- **Pull-based metrics collection** over HTTP
- **Time series storage** in memory and on local disk
- **Service discovery** or static configuration for target discovery
- **Alert manager** for handling alerts

Key features:
- Simple yet powerful data model
- Efficient time series database
- Integration with Grafana for visualization
- Wide ecosystem of exporters
- Native support for Kubernetes monitoring

## Features

This emulator implements core Prometheus functionality:

### Metric Types
- **Counter** - Monotonically increasing values (requests, errors)
- **Gauge** - Values that can go up and down (temperature, memory)
- **Histogram** - Bucketed observations (request durations, response sizes)
- **Summary** - Similar to histogram with quantile calculation

### Registry
- **Metric registration** - Register and manage metrics
- **Metric collection** - Export metrics in Prometheus format
- **Thread-safe operations** - Safe for concurrent use

### Utilities
- **HTTP server** - Serve metrics endpoint
- **Pushgateway support** - Push metrics for batch jobs
- **Timing utilities** - Context managers and decorators for timing
- **Info and Enum metrics** - Special metric types

## Usage Examples

### Counter Metrics

Counters are used for values that only increase (like request counts):

```python
from prometheus_emulator import Counter

# Create a counter
requests = Counter("http_requests_total", "Total HTTP requests")

# Increment the counter
requests.inc()      # Increment by 1
requests.inc(5)     # Increment by 5

# Get current value
count = requests.get()
print(f"Total requests: {count}")
```

#### Counter with Labels

Labels allow you to track dimensions of your metrics:

```python
from prometheus_emulator import Counter

# Create counter with labels
requests = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labels=["method", "status"]
)

# Increment with specific label values
requests.inc(method="GET", status="200")
requests.inc(method="GET", status="200")
requests.inc(method="POST", status="201")
requests.inc(method="GET", status="404")

# Get counts for specific labels
get_200 = requests.get(method="GET", status="200")
print(f"GET 200 requests: {get_200}")  # Output: 2

post_201 = requests.get(method="POST", status="201")
print(f"POST 201 requests: {post_201}")  # Output: 1
```

### Gauge Metrics

Gauges are used for values that can increase or decrease:

```python
from prometheus_emulator import Gauge

# Create a gauge
temperature = Gauge("room_temperature", "Room temperature in Celsius")

# Set absolute value
temperature.set(22.5)

# Increment/decrement
temperature.inc(0.5)    # Now 23.0
temperature.dec(1.0)    # Now 22.0

# Get current value
current = temperature.get()
print(f"Temperature: {current}°C")
```

#### Gauge with Labels

```python
from prometheus_emulator import Gauge

# Track temperature in multiple locations
temperature = Gauge(
    "temperature_celsius",
    "Temperature readings",
    labels=["location"]
)

temperature.set(22.5, location="office")
temperature.set(18.0, location="warehouse")
temperature.set(25.0, location="server_room")

# Query specific location
office_temp = temperature.get(location="office")
print(f"Office temperature: {office_temp}°C")
```

#### Set Gauge to Current Time

```python
from prometheus_emulator import Gauge

last_success = Gauge("job_last_success_timestamp", "Last successful job completion")

# Update when job completes
last_success.set_to_current_time()
```

### Histogram Metrics

Histograms sample observations and count them in configurable buckets:

```python
from prometheus_emulator import Histogram

# Create histogram with custom buckets
request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Record observations
request_duration.observe(0.025)  # 25ms request
request_duration.observe(0.150)  # 150ms request
request_duration.observe(0.500)  # 500ms request
request_duration.observe(2.000)  # 2s request

# Get statistics
total = request_duration.get_count()
sum_duration = request_duration.get_sum()
avg_duration = sum_duration / total

print(f"Total requests: {total}")
print(f"Average duration: {avg_duration:.3f}s")
```

#### Histogram with Labels

```python
from prometheus_emulator import Histogram

# Track request duration by endpoint
duration = Histogram(
    "api_request_duration_seconds",
    "API request duration",
    labels=["endpoint", "method"],
    buckets=[0.01, 0.1, 0.5, 1.0, 5.0]
)

# Record requests
duration.observe(0.025, endpoint="/api/users", method="GET")
duration.observe(0.150, endpoint="/api/users", method="GET")
duration.observe(0.800, endpoint="/api/posts", method="POST")

# Query specific endpoint
user_count = duration.get_count(endpoint="/api/users", method="GET")
user_sum = duration.get_sum(endpoint="/api/users", method="GET")
user_avg = user_sum / user_count

print(f"GET /api/users - Count: {user_count}, Avg: {user_avg:.3f}s")
```

### Summary Metrics

Summaries are similar to histograms but calculate quantiles:

```python
from prometheus_emulator import Summary

# Create summary
response_size = Summary(
    "http_response_size_bytes",
    "HTTP response size in bytes"
)

# Record observations
for size in [100, 150, 200, 180, 220, 190]:
    response_size.observe(size)

# Get statistics
count = response_size.get_count()
total = response_size.get_sum()
median = response_size.get_quantile(0.5)
p95 = response_size.get_quantile(0.95)

print(f"Requests: {count}")
print(f"Total size: {total} bytes")
print(f"Median: {median} bytes")
print(f"95th percentile: {p95} bytes")
```

### Registry

The registry manages all metrics:

```python
from prometheus_emulator import Registry, Counter, Gauge

# Create a custom registry
registry = Registry()

# Create and register metrics
requests = Counter("requests", "Request count")
memory = Gauge("memory_usage", "Memory usage in MB")

registry.register(requests)
registry.register(memory)

# Use the metrics
requests.inc()
memory.set(512)

# Collect all metrics
output = registry.collect()
print(output)
```

#### Global Registry

By default, a global registry is available:

```python
from prometheus_emulator import REGISTRY, Counter

# Metrics are automatically added to global registry
requests = Counter("requests", "Request count")
REGISTRY.register(requests)

# Later, collect all metrics
from prometheus_emulator import generate_latest

metrics_output = generate_latest()
print(metrics_output)
```

### Timing Operations

#### Using Timer Context Manager

```python
from prometheus_emulator import Histogram, Timer
import time

# Create histogram for timing
request_duration = Histogram(
    "request_processing_seconds",
    "Request processing time",
    labels=["handler"]
)

# Time a block of code
def process_request(handler_name):
    with Timer(request_duration, handler=handler_name):
        # Your code here
        time.sleep(0.1)  # Simulate work
        return "Success"

result = process_request("api_handler")
print(f"Duration recorded: {request_duration.get_sum():.3f}s")
```

#### Using Decorator

```python
from prometheus_emulator import Histogram, time_function

# Create histogram
function_duration = Histogram(
    "function_duration_seconds",
    "Function execution time",
    labels=["function"]
)

# Decorate function
@time_function(function_duration, function="data_processing")
def process_data(data):
    time.sleep(0.05)  # Simulate processing
    return len(data)

result = process_data([1, 2, 3, 4, 5])
print(f"Processed {result} items")
```

### HTTP Server

Start a metrics server to expose metrics:

```python
from prometheus_emulator import start_http_server, Counter, REGISTRY

# Create some metrics
requests = Counter("app_requests", "Application requests")
REGISTRY.register(requests)

# Start HTTP server on port 8000
start_http_server(8000)

# Metrics available at http://localhost:8000/metrics

# Application code
while True:
    requests.inc()
    time.sleep(1)
```

### Pushgateway Support

For batch jobs that don't run long enough to be scraped:

```python
from prometheus_emulator import push_to_gateway, Counter, REGISTRY

# Create metrics for batch job
job_duration = Counter("batch_job_duration_seconds", "Batch job duration")
REGISTRY.register(job_duration)

# Run your batch job
start = time.time()
# ... do work ...
duration = time.time() - start

job_duration.inc(duration)

# Push metrics to Pushgateway
push_to_gateway("localhost:9091", "batch_job", REGISTRY)
```

### Info Metrics

Info metrics expose text information as labels:

```python
from prometheus_emulator import info

# Create info metric
build_info = info(
    "app_build",
    "Application build information",
    version="1.2.3",
    commit="abc123",
    build_date="2024-01-15"
)

print(f"Version: {build_info['version']}")
```

### Enum Metrics

Enum metrics represent state as a gauge:

```python
from prometheus_emulator import enum

# Create enum metric
task_state = enum(
    "task_state",
    "Current task state",
    ["pending", "running", "completed", "failed"]
)

# Set state
task_state.set(1, state="running")
task_state.set(0, state="pending")
task_state.set(0, state="completed")
task_state.set(0, state="failed")
```

### Complete Application Example

```python
from prometheus_emulator import (
    Counter, Gauge, Histogram, Registry,
    start_http_server, Timer
)
import time
import random

# Create registry
registry = Registry()

# Define metrics
http_requests = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labels=["method", "endpoint", "status"]
)

active_connections = Gauge(
    "active_connections",
    "Number of active connections"
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    labels=["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Register metrics
registry.register(http_requests)
registry.register(active_connections)
registry.register(request_duration)

# Start metrics server
start_http_server(8000, registry)

# Application logic
def handle_request(method, endpoint):
    # Track active connections
    active_connections.inc()
    
    try:
        # Time the request
        with Timer(request_duration, endpoint=endpoint):
            # Simulate processing
            duration = random.uniform(0.01, 0.5)
            time.sleep(duration)
            
            # Simulate success/failure
            status = "200" if random.random() > 0.1 else "500"
            
        # Record request
        http_requests.inc(method=method, endpoint=endpoint, status=status)
        
        return status
        
    finally:
        # Decrease active connections
        active_connections.dec()

# Simulate traffic
endpoints = ["/api/users", "/api/posts", "/api/comments"]
methods = ["GET", "POST", "PUT", "DELETE"]

for _ in range(100):
    endpoint = random.choice(endpoints)
    method = random.choice(methods)
    status = handle_request(method, endpoint)
    print(f"{method} {endpoint} -> {status}")

# Print metrics
print("\n=== Metrics Summary ===")
print(f"Total requests: {http_requests.get(method='GET', endpoint='/api/users', status='200')}")
print(f"Active connections: {active_connections.get()}")
print(f"Request count: {request_duration.get_count(endpoint='/api/users')}")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python test_prometheus_emulator.py

# Run with verbose output
python test_prometheus_emulator.py -v

# Run specific test class
python -m unittest test_prometheus_emulator.TestCounter
```

The test suite covers:
- Counter operations (increment, labels, reset)
- Gauge operations (set, increment, decrement)
- Histogram bucketing and observations
- Summary quantile calculations
- Registry management
- Timer context manager
- Function decoration
- Integration scenarios

## Use Cases

Perfect for:
- **Application Monitoring** - Track application metrics and performance
- **Infrastructure Monitoring** - Monitor servers, containers, and services
- **Business Metrics** - Track business KPIs and SLAs
- **Development** - Test monitoring code without Prometheus server
- **CI/CD** - Monitor build and deployment metrics
- **Learning** - Learn Prometheus concepts and patterns

## Best Practices

### Metric Naming

Follow Prometheus naming conventions:

```python
# Good metric names
http_requests_total          # Counter
http_request_duration_seconds # Histogram
memory_usage_bytes           # Gauge
batch_job_last_success_time  # Gauge

# Include unit in name
# Use base units (seconds, bytes, not milliseconds, megabytes)
# Use descriptive names
```

### Label Usage

```python
# Good: Specific, bounded label values
requests = Counter("requests", "Requests", labels=["method", "status"])
requests.inc(method="GET", status="200")

# Bad: Unbounded label values (user IDs, timestamps, etc.)
# Don't do this - it creates too many time series
requests.inc(user_id="12345")  # BAD
```

### Metric Types

Choose the right metric type:

```python
# Counter: For values that only increase
error_count = Counter("errors_total", "Total errors")

# Gauge: For values that can increase or decrease
memory_usage = Gauge("memory_bytes", "Memory usage")

# Histogram: For observing distributions
request_size = Histogram("request_size_bytes", "Request sizes")

# Summary: For quantiles over sliding time window
response_time = Summary("response_time_seconds", "Response times")
```

## Limitations

This is an emulator for development and testing:
- In-memory storage only (no persistence)
- No PromQL query language
- No time series database
- No scraping or service discovery
- No alerting rules
- Simplified quantile calculation
- No remote write/read

## Supported Operations

### Metric Types
- ✅ Counter (inc, get, reset)
- ✅ Gauge (set, inc, dec, set_to_current_time)
- ✅ Histogram (observe, buckets, sum, count)
- ✅ Summary (observe, quantiles, sum, count)

### Registry
- ✅ Register/unregister metrics
- ✅ Collect metrics
- ✅ Thread-safe operations

### Utilities
- ✅ HTTP server simulation
- ✅ Pushgateway support
- ✅ Timer context manager
- ✅ Function decorator
- ✅ Info metrics
- ✅ Enum metrics

## Compatibility

Emulates core features of:
- Prometheus Python client library
- Prometheus data model
- Prometheus exposition format
- Common monitoring patterns

## Integration

Use as a drop-in replacement for Prometheus client:

```python
# Instead of:
# from prometheus_client import Counter, Gauge, Histogram

# Use:
from prometheus_emulator import Counter, Gauge, Histogram

# Your code works the same way
```

## License

Part of the Emu-Soft project. See main repository LICENSE.
