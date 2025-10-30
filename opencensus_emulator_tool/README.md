# OpenCensus Emulator

A pure Python implementation of OpenCensus distributed tracing without external dependencies.

## What This Emulates

**Emulates:** opencensus (Distributed tracing and monitoring framework)
**Original:** https://opencensus.io/

## Features

- **Trace and span creation** with hierarchical relationships
- **Span attributes** for metadata (tags/labels)
- **Span annotations** for timestamped events
- **Span status tracking** with standard status codes
- **Span kinds** (SERVER, CLIENT, PRODUCER, CONSUMER)
- **Parent-child span relationships** for distributed traces
- **Context propagation** using W3C Trace Context
- **Sampling strategies** (always, never, probability-based)
- **Exporters** (in-memory, console)
- **Thread-local context** management
- **Span links** for connecting related traces
- **Thread-safe** operations

## Core Components

- **opencensus_emulator.py**: Main implementation
  - `Span`: Represents a span in a trace
  - `Tracer`: Creates and manages spans
  - `SpanKind`: Enumeration of span types
  - `StatusCode`: Standard status codes
  - `Sampler`: Base class for sampling strategies
  - `Exporter`: Base class for exporting spans
  - `Propagator`: Context propagation utilities
  - `TraceContext`: W3C Trace Context implementation

## Usage

### Basic Tracing

```python
from opencensus_emulator import configure_tracer, span

# Configure tracer (optional)
configure_tracer()

# Create a span
with span("operation_name") as s:
    s.add_attribute("user_id", "12345")
    s.add_attribute("action", "purchase")
    
    # Your code here
    process_operation()
```

### Nested Spans

```python
from opencensus_emulator import span

with span("parent_operation") as parent:
    parent.add_attribute("level", "parent")
    
    # Child span
    with span("child_operation") as child:
        child.add_attribute("level", "child")
        
        # Grandchild span
        with span("grandchild_operation") as grandchild:
            grandchild.add_attribute("level", "grandchild")
```

### Span Attributes

```python
from opencensus_emulator import span

with span("database_query") as s:
    s.add_attribute("db.system", "postgresql")
    s.add_attribute("db.statement", "SELECT * FROM users")
    s.add_attributes({
        "db.name": "production",
        "db.user": "app_user"
    })
```

### Span Annotations (Events)

```python
from opencensus_emulator import span

with span("api_request") as s:
    s.add_annotation("request_started", method="GET", path="/api/users")
    
    # ... process request ...
    
    s.add_annotation("response_sent", status_code=200, size=1024)
```

### Span Status

```python
from opencensus_emulator import span, StatusCode

with span("operation") as s:
    try:
        # Your code
        result = risky_operation()
        s.set_status(StatusCode.OK)
    except ValueError as e:
        s.set_status(StatusCode.INVALID_ARGUMENT, str(e))
    except Exception as e:
        s.set_status(StatusCode.INTERNAL, str(e))
```

### Span Kinds

```python
from opencensus_emulator import span, SpanKind

# Server span (handling incoming request)
with span("handle_request", kind=SpanKind.SERVER) as s:
    s.add_attribute("http.method", "POST")
    s.add_attribute("http.target", "/api/users")

# Client span (making outgoing request)
with span("external_api_call", kind=SpanKind.CLIENT) as s:
    s.add_attribute("http.url", "https://api.example.com/data")
    s.add_attribute("http.method", "GET")

# Producer span (sending message)
with span("send_message", kind=SpanKind.PRODUCER) as s:
    s.add_attribute("messaging.system", "kafka")
    s.add_attribute("messaging.destination", "orders")

# Consumer span (receiving message)
with span("receive_message", kind=SpanKind.CONSUMER) as s:
    s.add_attribute("messaging.system", "kafka")
    s.add_attribute("messaging.source", "orders")
```

### Manual Span Management

```python
from opencensus_emulator import Tracer

tracer = Tracer()

# Start span
span = tracer.start_span("manual_span")
span.add_attribute("key", "value")

# Your code here

# End span
span.finish()
tracer.end_span(span)
```

### Context Propagation

```python
from opencensus_emulator import span, Propagator

# Service A
with span("service_a_operation") as span_a:
    # Inject trace context into headers
    headers = {}
    Propagator.inject(span_a, headers)
    
    # Send request to Service B with headers
    response = requests.get("http://service-b/api", headers=headers)

# Service B
def handle_request(headers):
    # Extract trace context from headers
    context = Propagator.extract(headers)
    
    # Create span with extracted context
    tracer = Tracer()
    if context:
        # Continue the trace
        with span("service_b_operation") as span_b:
            # This span will be part of the same trace
            process_request()
```

### Sampling

```python
from opencensus_emulator import (
    configure_tracer, AlwaysSampler, NeverSampler, ProbabilitySampler
)

# Always sample (default)
configure_tracer(sampler=AlwaysSampler())

# Never sample (useful for testing)
configure_tracer(sampler=NeverSampler())

# Sample 10% of traces
configure_tracer(sampler=ProbabilitySampler(0.1))
```

### Exporters

```python
from opencensus_emulator import (
    configure_tracer, InMemoryExporter, ConsoleExporter, span
)

# In-memory exporter (for testing)
exporter = InMemoryExporter()
configure_tracer(exporter=exporter)

with span("test_operation"):
    pass

# Get exported spans
spans = exporter.get_spans()
print(f"Captured {len(spans)} spans")

# Console exporter (for debugging)
configure_tracer(exporter=ConsoleExporter())

with span("debug_operation"):
    pass  # Will print span details to console
```

### Span Links

```python
from opencensus_emulator import Tracer

tracer = Tracer()

# Create two separate traces
span1 = tracer.start_span("trace1_span")
span1.finish()

span2 = tracer.start_span("trace2_span")

# Link span2 to span1
span2.add_link(
    span1.trace_id,
    span1.span_id,
    link_type="FOLLOWS_FROM",
    reason="related_operation"
)

span2.finish()
```

## Testing

Run the test suite:

```bash
python test_opencensus_emulator.py
```

## Implementation Notes

- **Thread-safe**: All operations use locks for thread safety
- **Thread-local context**: Current span stored in thread-local storage
- **W3C Trace Context**: Standard format for context propagation
- **In-memory storage**: Spans stored locally, not sent to tracing backend
- **No wire protocol**: No integration with actual OpenCensus agents/collectors

## API Compatibility

This emulator implements the core OpenCensus tracing API:

**Tracing:**
- `span()` - Context manager for creating spans
- `start_span()` - Start a new span
- `end_span()` - End a span
- `get_current_span()` - Get current span from context

**Span Operations:**
- `add_attribute()` - Add metadata to span
- `add_annotation()` - Add timestamped event
- `set_status()` - Set span status
- `add_link()` - Link to another span

**Configuration:**
- `configure_tracer()` - Configure global tracer
- `get_tracer()` - Get global tracer

**Context Propagation:**
- `Propagator.inject()` - Inject context into carrier
- `Propagator.extract()` - Extract context from carrier

## Differences from Official OpenCensus

- **No exporters to backends**: Only in-memory and console exporters
- **Simplified sampling**: Basic sampling strategies only
- **No stats/metrics**: Tracing only, no metrics collection
- **No tags propagation**: Only basic W3C Trace Context
- **No automatic instrumentation**: Manual instrumentation only
- **No integrations**: No framework-specific integrations (Flask, Django, etc.)

## Example Use Cases

### Web Service Tracing

```python
from opencensus_emulator import span, SpanKind, StatusCode

def handle_http_request(method, path):
    with span(f"{method} {path}", kind=SpanKind.SERVER) as s:
        s.add_attribute("http.method", method)
        s.add_attribute("http.target", path)
        s.add_attribute("http.host", "api.example.com")
        
        try:
            # Route to handler
            result = route_request(method, path)
            
            s.add_attribute("http.status_code", 200)
            s.set_status(StatusCode.OK)
            return result
            
        except ValueError as e:
            s.add_attribute("http.status_code", 400)
            s.set_status(StatusCode.INVALID_ARGUMENT, str(e))
            raise
```

### Database Query Tracing

```python
from opencensus_emulator import span

def execute_query(sql, params):
    with span("database.query") as s:
        s.add_attribute("db.system", "postgresql")
        s.add_attribute("db.statement", sql)
        s.add_attribute("db.name", "production")
        
        s.add_annotation("query_started")
        
        result = db.execute(sql, params)
        
        s.add_annotation("query_completed", rows=len(result))
        s.add_attribute("db.rows_affected", len(result))
        
        return result
```

### Microservices Tracing

```python
from opencensus_emulator import span, SpanKind, Propagator

# Service A
def call_service_b():
    with span("call_service_b", kind=SpanKind.CLIENT) as s:
        s.add_attribute("peer.service", "service-b")
        
        # Propagate context
        headers = {}
        Propagator.inject(s, headers)
        
        response = requests.post(
            "http://service-b/api/process",
            headers=headers,
            json={"data": "value"}
        )
        
        s.add_attribute("http.status_code", response.status_code)
        return response

# Service B
def handle_process_request(headers, data):
    # Extract context
    context = Propagator.extract(headers)
    
    with span("process_data", kind=SpanKind.SERVER) as s:
        if context:
            # This span is part of the distributed trace
            s.add_annotation("trace_continued", trace_id=context.trace_id)
        
        s.add_attribute("data.size", len(str(data)))
        result = process(data)
        return result
```

### Background Job Tracing

```python
from opencensus_emulator import span, configure_tracer, InMemoryExporter

# Configure for job monitoring
exporter = InMemoryExporter()
configure_tracer(exporter=exporter)

def process_job(job_id, job_type):
    with span(f"job.{job_type}") as s:
        s.add_attribute("job.id", job_id)
        s.add_attribute("job.type", job_type)
        
        with span("job.fetch_data") as fetch:
            data = fetch_data(job_id)
            fetch.add_attribute("data.size", len(data))
        
        with span("job.process") as process:
            result = process_data(data)
            process.add_attribute("result.size", len(result))
        
        with span("job.save_result") as save:
            save_result(result)
            save.add_annotation("result_saved")
        
        s.set_status(StatusCode.OK)
        return result
```

## Performance Considerations

- **Memory**: Spans stored in-memory; clear periodically in long-running apps
- **Context switching**: Thread-local storage has minimal overhead
- **Locking**: Operations are thread-safe but may contend under high load
- **Sampling**: Use probability sampling to reduce overhead
- **Attributes**: Keep attribute cardinality low to reduce memory

## Best Practices

1. **Use descriptive span names**: Clear, concise operation names
2. **Add relevant attributes**: Include key metadata for debugging
3. **Use appropriate span kinds**: SERVER, CLIENT, PRODUCER, CONSUMER
4. **Set status codes**: Always set status on span completion
5. **Add annotations for key events**: Mark important milestones
6. **Propagate context**: Use Propagator for distributed tracing
7. **Use sampling in production**: Reduce overhead with ProbabilitySampler
8. **Clean up spans**: Clear exporter periodically to prevent memory growth

## License

This emulator is part of the CIV-ARCOS project and is original code written from scratch. While it emulates OpenCensus functionality, it contains no code from the official OpenCensus project.
