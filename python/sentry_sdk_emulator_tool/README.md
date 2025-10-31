# Sentry SDK Emulator

A pure Python implementation of Sentry SDK functionality without external dependencies.

## What This Emulates

**Emulates:** sentry-sdk (Error tracking and performance monitoring)
**Original:** https://docs.sentry.io/platforms/python/

## Features

- Exception capture with detailed stack traces
- Message logging with multiple severity levels (debug, info, warning, error, fatal)
- Breadcrumb tracking for context reconstruction
- User context binding (ID, email, username, IP)
- Tags for categorization and filtering
- Extra data for additional context
- Context data for structured information
- Event filtering and sampling
- Before-send hooks for event modification
- Scope management with push/pop operations
- Release and environment tracking
- Transaction tracking for performance monitoring
- Thread-safe operation

## Core Components

- **sentry_sdk_emulator.py**: Main implementation
  - `Level`: Enumeration for log levels
  - `Breadcrumb`: Breadcrumb data structure
  - `User`: User context data structure
  - `Event`: Event data structure
  - `Transaction`: Performance monitoring transaction
  - `Span`: Performance monitoring span
  - `Scope`: Scope for managing context data
  - `Hub`: Hub for managing scopes and clients
  - `Client`: Main client for capturing events

## Usage

### Basic Setup

```python
from sentry_sdk_emulator import init, capture_exception, capture_message

# Initialize the SDK
init(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
    release="my-app@1.0.0",
    environment="production",
    sample_rate=1.0
)

# Capture a message
capture_message("Application started", level="info")

# Capture an exception
try:
    result = 1 / 0
except Exception as e:
    capture_exception(e)
```

### User Context

```python
from sentry_sdk_emulator import set_user

set_user({
    "id": "12345",
    "email": "user@example.com",
    "username": "john_doe",
    "ip_address": "192.168.1.1"
})
```

### Tags and Extra Data

```python
from sentry_sdk_emulator import set_tag, set_tags, set_extra, set_extras

# Set individual tag
set_tag("server", "web-1")

# Set multiple tags
set_tags({
    "region": "us-west",
    "version": "1.0.0"
})

# Set extra data
set_extra("user_plan", "premium")
set_extras({
    "request_id": "abc-123",
    "session_duration": 3600
})
```

### Breadcrumbs

```python
from sentry_sdk_emulator import add_breadcrumb

# Add breadcrumbs to track user actions
add_breadcrumb(
    message="User logged in",
    category="auth",
    level="info"
)

add_breadcrumb(
    message="API request",
    category="http",
    level="info",
    data={"url": "/api/users", "method": "GET"}
)
```

### Scope Management

```python
from sentry_sdk_emulator import push_scope, configure_scope

# Push a new scope for temporary context
with push_scope() as scope:
    scope.set_tag("request_id", "abc-123")
    scope.set_extra("user_data", {"premium": True})
    capture_message("Processing request")
# Scope is automatically popped after the context

# Configure the current scope
with configure_scope() as scope:
    scope.set_user({"id": "123"})
    scope.set_tag("endpoint", "/api/users")
```

### Event Filtering

```python
from sentry_sdk_emulator import init

def before_send(event, hint):
    # Modify events before sending
    event.tags['modified'] = 'yes'
    
    # Filter out certain events
    if event.get('transaction') == '/health':
        return None  # Don't send this event
    
    return event

init(
    dsn="...",
    before_send=before_send
)
```

### Performance Monitoring

```python
from sentry_sdk_emulator import start_transaction

# Start a transaction
transaction = start_transaction(
    name="process_order",
    op="task"
)

# Your code here
process_order()

# Transaction data is captured
```

### Sampling

```python
from sentry_sdk_emulator import init

# Only send 25% of events
init(
    dsn="...",
    sample_rate=0.25
)
```

## Testing

Run the test suite:

```bash
python test_sentry_sdk_emulator.py
```

## Implementation Notes

- Events are stored in-memory (not sent to actual Sentry servers)
- Thread-safe scope management using thread-local storage
- Automatic exception context capture from `sys.exc_info()`
- Stack trace formatting with file, function, and line information
- Breadcrumb limiting to prevent memory issues (default: 100)
- Probabilistic sampling based on sample_rate
- Before-send hooks for event modification and filtering
- No external dependencies required

## API Compatibility

This emulator implements the core Sentry SDK API:

- `init()` - Initialize the SDK
- `capture_exception()` - Capture exceptions
- `capture_message()` - Capture messages
- `add_breadcrumb()` - Add breadcrumbs
- `set_user()` - Set user context
- `set_tag()` / `set_tags()` - Set tags
- `set_extra()` / `set_extras()` - Set extra data
- `set_context()` - Set context data
- `set_level()` - Set log level
- `set_transaction()` - Set transaction name
- `push_scope()` - Push a new scope
- `configure_scope()` - Configure current scope
- `start_transaction()` - Start a transaction
- `flush()` - Flush pending events
- `close()` - Close the SDK

## Differences from Official SDK

- **No network communication**: Events are stored locally instead of being sent to Sentry servers
- **Simplified transaction/span tracking**: Basic structure without full distributed tracing
- **In-memory storage**: Events are kept in memory for inspection
- **No async support**: Synchronous operation only
- **Limited integrations**: No automatic framework integrations (Django, Flask, etc.)

## Testing Utilities

For testing purposes, the emulator provides additional functions:

```python
from sentry_sdk_emulator import get_events, clear_events

# Get all captured events
events = get_events()
for event in events:
    print(f"Event: {event.message or event.exception}")

# Clear captured events
clear_events()
```

## Why This Was Created

This emulator was created as part of the CIV-ARCOS project to provide error tracking and monitoring capabilities without external dependencies or network communication, ensuring a self-contained civilian version of military-grade software assurance tools.

## Example Use Cases

### Web Application Error Tracking

```python
from sentry_sdk_emulator import init, capture_exception, set_user, add_breadcrumb

init(dsn="...", environment="production")

def handle_request(user_id, action):
    set_user({"id": user_id})
    add_breadcrumb(message=f"User action: {action}", category="user")
    
    try:
        # Process request
        pass
    except Exception as e:
        capture_exception(e)
```

### Background Job Monitoring

```python
from sentry_sdk_emulator import init, capture_message, set_tags, push_scope

init(dsn="...", environment="production")

def process_job(job_id):
    with push_scope() as scope:
        scope.set_tags({
            "job_id": job_id,
            "job_type": "data_processing"
        })
        
        capture_message("Job started", level="info")
        
        try:
            # Process job
            pass
        except Exception as e:
            capture_exception(e)
            raise
        finally:
            capture_message("Job completed", level="info")
```

## Performance Considerations

- **Memory**: Events are stored in-memory; use `clear_events()` periodically in long-running applications
- **Thread-safety**: Scope data is thread-local; each thread has its own context
- **Sampling**: Use sample_rate < 1.0 to reduce event volume in high-traffic scenarios
- **Breadcrumbs**: Limited to 100 per scope to prevent memory growth
- **Stack traces**: Full stack trace capture may have performance impact in tight loops

## License

This emulator is part of the CIV-ARCOS project and is original code written from scratch. While it emulates Sentry SDK functionality, it contains no code from the official Sentry SDK.
