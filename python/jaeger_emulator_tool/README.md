# Jaeger Emulator - Distributed Tracing

A lightweight emulation of **Jaeger**, the open-source distributed tracing system used for monitoring and troubleshooting microservices-based distributed systems.

## Features

This emulator implements core Jaeger functionality:

### Span Management
- **Span Creation**: Create spans for tracking operations
- **Parent-Child Relationships**: Build span hierarchies
- **Span Lifecycle**: Start and finish spans with timing
- **Span Kind**: Support for client, server, producer, consumer, and internal spans
- **Tags**: Add metadata to spans
- **Logs**: Add timestamped log entries within spans

### Trace Management
- **Trace Collection**: Aggregate spans into complete traces
- **Trace Storage**: Store and retrieve traces
- **Trace Querying**: Find traces by service, operation, tags, and duration
- **Trace Metadata**: Track services, timing, and span counts

### Context Propagation
- **Context Injection**: Inject trace context into HTTP headers
- **Context Extraction**: Extract trace context from HTTP headers
- **Baggage**: Propagate key-value pairs across service boundaries
- **Uber Trace ID Format**: Standard Jaeger header format

### Service Tracking
- **Service Registry**: Track all services reporting traces
- **Operation Registry**: Track operations per service
- **Span Counting**: Count spans per service
- **Service Dependencies**: Build service dependency graphs

### Analysis
- **Trace Statistics**: Calculate trace counts, durations, and averages
- **Dependency Graph**: Visualize service-to-service dependencies
- **Duration Filtering**: Find slow or fast traces
- **Tag-based Search**: Query traces by tags

## What It Emulates

This tool emulates core functionality of [Jaeger](https://www.jaegertracing.io/), the CNCF distributed tracing platform inspired by Dapper and OpenZipkin.

### Core Components Implemented

1. **Tracer API**
   - Span creation and lifecycle
   - Context propagation
   - Tag and log management

2. **Trace Collection**
   - Span reporting
   - Trace aggregation
   - Service tracking

3. **Query Service**
   - Trace retrieval by ID
   - Trace search by criteria
   - Service and operation listing
   - Dependency graph generation

4. **Context Propagation**
   - Uber trace ID format
   - Header injection/extraction
   - Baggage propagation

## Usage

### Basic Span Creation

```python
from jaeger_emulator import JaegerEmulator, SpanKind

# Create emulator
jaeger = JaegerEmulator()

# Get tracer for service
tracer = jaeger.get_tracer("my-service")

# Create and finish a span
span = tracer.start_span(
    "process-request",
    tags={"user.id": "123", "request.type": "api"}
)

# Do work...
import time
time.sleep(0.01)

# Finish span
tracer.finish_span(span)

# Retrieve trace
trace = jaeger.get_trace(span.trace_id)
print(f"Trace duration: {trace.duration * 1000:.2f}ms")
```

### Parent-Child Spans

```python
# Create parent span
parent_span = tracer.start_span("parent-operation", kind=SpanKind.SERVER)

# Create child span
from jaeger_emulator import SpanContext

child_context = SpanContext(parent_span.trace_id, parent_span.span_id)
child_span = tracer.start_span(
    "child-operation",
    parent=child_context,
    kind=SpanKind.INTERNAL
)

# Finish in reverse order
tracer.finish_span(child_span)
tracer.finish_span(parent_span)
```

### Cross-Service Tracing

```python
# Frontend service
frontend_tracer = jaeger.get_tracer("frontend")
frontend_span = frontend_tracer.start_span(
    "HTTP GET /users",
    kind=SpanKind.SERVER,
    tags={"http.method": "GET", "http.url": "/users"}
)

# Inject context into headers
headers = {}
frontend_tracer.inject(frontend_span, headers)

# Send headers to backend service...

# Backend service
backend_tracer = jaeger.get_tracer("backend-api")
parent_context = backend_tracer.extract(headers)

backend_span = backend_tracer.start_span(
    "GET /api/users",
    parent=parent_context,
    kind=SpanKind.SERVER
)

# Database call
db_tracer = jaeger.get_tracer("database")
db_headers = {}
backend_tracer.inject(backend_span, db_headers)
db_context = db_tracer.extract(db_headers)

db_span = db_tracer.start_span(
    "SELECT users",
    parent=db_context,
    kind=SpanKind.CLIENT,
    tags={"db.type": "postgresql", "db.statement": "SELECT * FROM users"}
)

# Finish all spans
db_tracer.finish_span(db_span)
backend_tracer.finish_span(backend_span)
frontend_tracer.finish_span(frontend_span)
```

### Querying Traces

```python
# Find all traces for a service
traces = jaeger.find_traces(service="backend-api", limit=10)

# Find slow traces
slow_traces = jaeger.find_traces(
    service="backend-api",
    min_duration=0.1,  # 100ms+
    limit=20
)

# Find traces by operation
api_traces = jaeger.find_traces(
    operation="GET /api/users",
    limit=10
)

# Find traces by tags
error_traces = jaeger.find_traces(
    tags={"http.status": 500},
    limit=10
)

for trace in traces:
    print(f"Trace {trace.trace_id}: {len(trace.spans)} spans, {trace.duration * 1000:.2f}ms")
```

### Service Dependencies

```python
# Get all services
services = jaeger.get_services()
print(f"Services: {services}")

# Get operations for a service
operations = jaeger.get_operations("backend-api")
print(f"Operations: {operations}")

# Get service dependency graph
dependencies = jaeger.get_dependencies()
for parent, children in dependencies.items():
    print(f"{parent} -> {', '.join(children)}")
```

### Statistics

```python
# Get overall statistics
stats = jaeger.get_trace_statistics()
print(f"Total traces: {stats['trace_count']}")
print(f"Total spans: {stats['span_count']}")
print(f"Avg duration: {stats['avg_duration'] * 1000:.2f}ms")
print(f"Max duration: {stats['max_duration'] * 1000:.2f}ms")

# Get statistics for specific service
service_stats = jaeger.get_trace_statistics(service="backend-api")
```

### Complete Example

```python
import time
from jaeger_emulator import JaegerEmulator, SpanKind

# Setup
jaeger = JaegerEmulator()

# Simulate e-commerce transaction
frontend = jaeger.get_tracer("web-frontend")
cart_service = jaeger.get_tracer("cart-service")
payment_service = jaeger.get_tracer("payment-service")
db = jaeger.get_tracer("postgres")

# User clicks checkout
root = frontend.start_span("POST /checkout", kind=SpanKind.SERVER,
                          tags={"user.id": "user123", "cart.items": 3})

# Call cart service
headers = {}
frontend.inject(root, headers)
cart_ctx = cart_service.extract(headers)

cart_span = cart_service.start_span("get-cart", parent=cart_ctx, kind=SpanKind.SERVER)
time.sleep(0.01)
cart_service.finish_span(cart_span)

# Call payment service
payment_headers = {}
frontend.inject(root, payment_headers)
payment_ctx = payment_service.extract(payment_headers)

payment_span = payment_service.start_span("process-payment", parent=payment_ctx,
                                         kind=SpanKind.SERVER,
                                         tags={"amount": 99.99, "currency": "USD"})

# Database call from payment service
db_headers = {}
payment_service.inject(payment_span, db_headers)
db_ctx = db.extract(db_headers)

db_span = db.start_span("INSERT payment", parent=db_ctx, kind=SpanKind.CLIENT,
                       tags={"db.type": "postgresql"})
time.sleep(0.005)
db.finish_span(db_span)

time.sleep(0.02)
payment_service.finish_span(payment_span)
frontend.finish_span(root)

# Analyze
trace = list(jaeger.traces.values())[0]
print(f"Checkout transaction: {trace.duration * 1000:.2f}ms")
print(f"Services involved: {', '.join(trace.services)}")
print(f"Total spans: {len(trace.spans)}")

deps = jaeger.get_dependencies()
print("\nService dependencies:")
for svc, deps_list in deps.items():
    print(f"  {svc} -> {', '.join(deps_list)}")
```

## Testing

```bash
python test_jaeger_emulator.py
```

## Use Cases

1. **Microservices Development**: Test tracing integration without Jaeger
2. **Learning Distributed Tracing**: Understand tracing concepts
3. **Testing**: Validate trace generation in tests
4. **Performance Analysis**: Identify bottlenecks in service calls
5. **Dependency Mapping**: Understand service relationships

## Key Differences from Real Jaeger

1. **No Network Protocol**: Doesn't implement Thrift or gRPC protocols
2. **In-Memory Storage**: No persistent storage backend
3. **No UI**: No web interface for visualization
4. **Simplified Sampling**: No sampling strategies
5. **No Agents/Collectors**: Direct span reporting
6. **Limited Query API**: Simplified querying

## License

Educational emulator for learning purposes.

## References

- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTracing Specification](https://opentracing.io/specification/)
- [Distributed Tracing Concepts](https://www.jaegertracing.io/docs/1.21/architecture/)
