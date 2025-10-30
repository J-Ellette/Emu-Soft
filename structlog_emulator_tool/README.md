# structlog Emulator

A pure Python implementation that emulates the core functionality of structlog for structured logging without external dependencies.

## Overview

This module provides structured logging capabilities that go beyond traditional text-based logging. It allows you to add context to your logs, process them through pipelines, and output in multiple formats (JSON, key-value, console).

## Features

- **Context Binding**
  - Bind key-value pairs to loggers for automatic inclusion
  - Create new loggers with additional context
  - Unbind context when no longer needed

- **BoundLogger**
  - Immutable context binding (creates new logger instances)
  - Thread-safe logging
  - Fluent API for chaining

- **Processor Pipeline**
  - Chain multiple processors for log transformation
  - Filter logs based on level or custom criteria
  - Add timestamps, log levels, and other metadata

- **Multiple Output Formats**
  - JSON output for machine parsing
  - Key-value pairs for grep-friendly logs
  - Console output with colors for human readability

- **Log Levels**
  - debug, info, warning, error, critical
  - Level filtering in processor pipeline

- **Thread-Local Context**
  - Request-scoped context management
  - Automatic context cleanup with context managers

- **Standard Library Integration**
  - Uses only Python standard library
  - Can wrap standard logging loggers

## Usage

### Basic Logging

```python
from structlog_emulator import get_logger

log = get_logger()
log.info("application started", version="1.0.0")
log.warning("low disk space", available_mb=100)
log.error("connection failed", host="example.com", port=80)
```

### Console Logger (Human-Readable)

```python
from structlog_emulator import create_console_logger

log = create_console_logger(level='info', colors=True)
log.info("user logged in", user_id=123, username="john")
# Output: 2024-01-01 12:00:00 INFO     user logged in           user_id=123 username=john
```

### JSON Logger (Machine-Readable)

```python
from structlog_emulator import create_json_logger

log = create_json_logger(level='info')
log.info("order placed", order_id=456, amount=99.99, currency="USD")
# Output: {"event": "order placed", "level": "info", "timestamp": "2024-01-01T12:00:00", ...}
```

### Context Binding

```python
from structlog_emulator import get_logger

log = get_logger()

# Bind context that will be included in all subsequent logs
request_log = log.bind(request_id="abc-123", user_id=789)

request_log.info("processing request")
# Includes request_id and user_id automatically

request_log.info("request completed", duration_ms=150)
# Also includes request_id and user_id
```

### Chaining Context

```python
log = get_logger()
request_log = log.bind(request_id="abc-123")
user_log = request_log.bind(user_id=456)

user_log.info("user action", action="purchase")
# Includes both request_id and user_id
```

### Unbinding Context

```python
log = get_logger().bind(temp="data", keep="this")
new_log = log.unbind("temp")  # Remove "temp" key

new_log.info("event")  # Only includes "keep" key
```

### Creating Fresh Logger

```python
log = get_logger().bind(old="value")
new_log = log.new(new="value")  # Start fresh with only new context

new_log.info("event")  # Only includes "new" key
```

### Custom Processors

```python
from structlog_emulator import configure, get_logger, add_timestamp, JSONRenderer

def add_app_info(event_dict):
    """Add application information to all logs"""
    event_dict['app'] = 'myapp'
    event_dict['version'] = '1.0.0'
    return event_dict

# Configure global processors
configure(processors=[
    add_timestamp,
    add_app_info,
    JSONRenderer(),
])

log = get_logger()
log.info("test")  # Includes app and version fields
```

### Log Level Filtering

```python
from structlog_emulator import (
    configure, get_logger, add_timestamp,
    filter_by_level, ConsoleRenderer, PrintLogger
)

# Only log warning and above
processors = [
    add_timestamp,
    filter_by_level('warning'),
    ConsoleRenderer(),
    PrintLogger(),
]

configure(processors=processors)

log = get_logger()
log.debug("debug message")    # Filtered out
log.info("info message")      # Filtered out
log.warning("warning message") # Logged
log.error("error message")     # Logged
```

### Thread-Local Context

Useful for web applications to track request context:

```python
from structlog_emulator import (
    get_logger, threadlocal_context,
    merge_threadlocal_context
)

log = get_logger()

# In a request handler
with threadlocal_context(request_id="req-123", user_id=456):
    log.info("request started")
    # Do work...
    log.info("request completed")
    # All logs within this context include request_id and user_id

# Or manually merge/unbind
merge_threadlocal_context(session_id="sess-789")
log.info("action")  # Includes session_id

from structlog_emulator import unbind_threadlocal_context
unbind_threadlocal_context("session_id")
```

### Different Renderers

#### JSON Renderer

```python
from structlog_emulator import JSONRenderer

renderer = JSONRenderer(sort_keys=True)
result = renderer({
    "event": "test",
    "level": "info",
    "data": 123
})
# Output: {"data": 123, "event": "test", "level": "info"}
```

#### Key-Value Renderer

```python
from structlog_emulator import KeyValueRenderer

# Simple key=value output
renderer = KeyValueRenderer()
result = renderer({"event": "test", "level": "info"})
# Output: event=test level=info

# With custom key order
renderer = KeyValueRenderer(key_order=["timestamp", "level", "event"])
# Output puts timestamp, level, event first, then remaining keys
```

#### Console Renderer

```python
from structlog_emulator import ConsoleRenderer

# Colored output for terminal
renderer = ConsoleRenderer(colors=True, pad_event=30)
result = renderer({
    "event": "user action",
    "level": "info",
    "user_id": 123
})
# Output: 2024-01-01 12:00:00 INFO     user action                user_id=123
```

## Advanced Usage

### Custom Processor That Modifies Events

```python
def add_hostname(event_dict):
    """Add hostname to all events"""
    import socket
    event_dict['hostname'] = socket.gethostname()
    return event_dict

def uppercase_event(event_dict):
    """Make event message uppercase"""
    event_dict['event'] = event_dict['event'].upper()
    return event_dict

configure(processors=[
    add_timestamp,
    add_hostname,
    uppercase_event,
    JSONRenderer(),
])
```

### Custom Processor That Filters

```python
def filter_sensitive(event_dict):
    """Filter out logs containing sensitive data"""
    if 'password' in event_dict or 'secret' in event_dict:
        return None  # Returning None filters the event
    return event_dict

configure(processors=[
    filter_sensitive,
    JSONRenderer(),
])
```

### Wrapping Standard Logging

```python
import logging
from structlog_emulator import wrap_logger

stdlib_logger = logging.getLogger('myapp')
log = wrap_logger(stdlib_logger)

log.info("structured log", key="value")
```

## Processor Order Matters

Processors are executed in order, and each processor receives the output of the previous one:

```python
# Good: Add timestamp before filtering
processors = [
    add_timestamp,        # Adds timestamp
    filter_by_level('warning'),  # Filters based on level
    JSONRenderer(),       # Renders to JSON
]

# Bad: Filter before adding required fields
processors = [
    filter_by_level('warning'),  # Might filter before timestamp added
    add_timestamp,
    JSONRenderer(),
]
```

## Log Levels

Available log levels in order of severity:
- `debug` - Detailed information for diagnosing problems
- `info` - General informational messages
- `warning` - Warning messages for potentially problematic situations
- `error` - Error messages for serious problems
- `critical` - Critical messages for very serious problems

There's also:
- `msg()` - Generic message (defaults to info level)
- `warn()` - Alias for warning()
- `exception()` - Logs error with exception traceback

## Testing

Run the test suite:

```bash
python test_structlog_emulator.py
```

The test suite includes:
- Context binding and unbinding (9 tests)
- Processor functionality (5 tests)
- Renderer output formats (8 tests)
- Configuration and setup (3 tests)
- Convenience functions (3 tests)
- Thread-local context (5 tests)
- Processor pipeline (2 tests)

## Use Cases

This emulator is ideal for:
- **Web Applications**: Track requests with request IDs and user context
- **Microservices**: Structured logs for easy parsing and aggregation
- **Development**: Human-readable console logs during development
- **Production**: Machine-readable JSON logs for log aggregation services
- **Debugging**: Rich context in logs without manual string formatting
- **Testing**: Structured logging in test environments
- **Analytics**: Easy extraction of metrics from logs

## Benefits of Structured Logging

1. **Machine Readable**: Easy to parse and analyze programmatically
2. **Rich Context**: Include any data as fields, not just in message strings
3. **Searchable**: Query logs by specific field values
4. **Aggregatable**: Combine logs from multiple sources efficiently
5. **Consistent Format**: Same structure across all logs
6. **Type Safety**: Fields maintain their types (numbers, booleans, etc.)

## Comparison with String Formatting

Traditional logging:
```python
log.info(f"User {user_id} purchased item {item_id} for ${amount}")
# Hard to extract user_id, item_id, amount programmatically
```

Structured logging:
```python
log.info("purchase completed", 
    user_id=user_id, 
    item_id=item_id, 
    amount=amount
)
# Easy to query: "show all purchases where amount > 100"
```

## Implementation Details

### Thread Safety

- Each `bind()`, `unbind()`, `new()` creates a new logger instance
- Context is immutable and not shared between logger instances
- Thread-local storage is used for request-scoped context
- Safe to use in multi-threaded applications

### Performance

- Minimal overhead for context binding (creates new dict)
- Processors run only when log is actually emitted
- Level filtering can short-circuit processor pipeline
- No expensive string formatting until final renderer

### Compatibility

- Pure Python implementation
- Uses only standard library modules
- Compatible with Python 3.6+
- Can integrate with standard logging module

## Limitations

Compared to the full structlog library:
- Simplified processor API (doesn't pass logger_name, method_name to all processors)
- No built-in integrations with popular logging frameworks
- No advanced serialization for complex types
- Simplified exception logging
- Basic thread-local context (no contextvars support)

These limitations keep the implementation simple while covering the most common use cases.

## Contributing

This is part of the Emu-Soft repository's collection of emulated tools. Improvements and bug fixes are welcome!

## License

This implementation is part of the Emu-Soft project and follows the same license terms.
