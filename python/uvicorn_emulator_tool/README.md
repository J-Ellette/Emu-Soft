# Uvicorn Emulator

A lightweight emulation of Uvicorn's ASGI server functionality for serving Python web applications.

## Features

- **ASGI 3.0 Support**: Full ASGI protocol implementation
- **HTTP Server**: Built-in HTTP/1.1 server
- **Auto-Reload**: File watching with automatic server restart
- **Async Support**: Full asyncio integration
- **Simple Interface**: Easy-to-use API matching Uvicorn
- **Request/Response Handling**: Complete HTTP message parsing and generation
- **Production-Ready**: Suitable for development and testing

## What It Emulates

This tool emulates core functionality of [Uvicorn](https://github.com/encode/uvicorn), the lightning-fast ASGI server implementation.

### Core Components Implemented

1. **ASGI Server**
   - HTTP/1.1 protocol support
   - Request parsing and routing
   - Response building
   - Async request handling

2. **Auto-Reload System**
   - File system watching
   - Automatic server restart on code changes
   - Configurable watch directories
   - Efficient change detection

3. **Application Loading**
   - Dynamic module importing
   - Hot reloading of application code
   - Support for import strings (e.g., "main:app")

## Usage

### As a Module

```python
from uvicorn_emulator import UvicornEmulator

# Run ASGI application
UvicornEmulator.run(
    app="main:app",
    host="127.0.0.1",
    port=8000,
    reload=True,
    reload_dirs=["."]
)
```

### Command Line

```bash
# Basic usage
python uvicorn_emulator.py main:app

# Custom host and port
python uvicorn_emulator.py main:app --host 0.0.0.0 --port 5000

# Enable auto-reload
python uvicorn_emulator.py main:app --reload

# Watch specific directories
python uvicorn_emulator.py main:app --reload --reload-dir ./src --reload-dir ./lib

# Set log level
python uvicorn_emulator.py main:app --log-level debug
```

## Examples

### Simple ASGI Application

```python
# main.py

async def app(scope, receive, send):
    """Simple ASGI application"""
    assert scope['type'] == 'http'
    
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            [b'content-type', b'text/plain'],
        ],
    })
    await send({
        'type': 'http.response.body',
        'body': b'Hello, World!',
    })
```

Run it:
```bash
python uvicorn_emulator.py main:app
# Visit http://127.0.0.1:8000
```

### JSON API

```python
# api.py
import json

async def app(scope, receive, send):
    """JSON API example"""
    if scope['path'] == '/':
        response_data = {
            'message': 'Welcome to the API',
            'endpoints': ['/users', '/posts']
        }
    elif scope['path'] == '/users':
        response_data = {
            'users': [
                {'id': 1, 'name': 'Alice'},
                {'id': 2, 'name': 'Bob'}
            ]
        }
    else:
        response_data = {'error': 'Not found'}
    
    body = json.dumps(response_data).encode('utf-8')
    
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            [b'content-type', b'application/json'],
        ],
    })
    await send({
        'type': 'http.response.body',
        'body': body,
    })
```

Run it:
```bash
python uvicorn_emulator.py api:app --reload
```

### With Query Parameters

```python
# query_app.py
from urllib.parse import parse_qs

async def app(scope, receive, send):
    """Handle query parameters"""
    query_string = scope['query_string'].decode('utf-8')
    params = parse_qs(query_string)
    
    name = params.get('name', ['World'])[0]
    message = f'Hello, {name}!'
    
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/plain']],
    })
    await send({
        'type': 'http.response.body',
        'body': message.encode('utf-8'),
    })
```

Test it:
```bash
curl "http://127.0.0.1:8000?name=Alice"
# Output: Hello, Alice!
```

### POST Request Handling

```python
# post_app.py
import json

async def app(scope, receive, send):
    """Handle POST requests"""
    if scope['method'] == 'POST':
        # Read request body
        body = b''
        while True:
            message = await receive()
            if message['type'] == 'http.request':
                body += message.get('body', b'')
                if not message.get('more_body'):
                    break
        
        # Parse JSON
        try:
            data = json.loads(body)
            response = {
                'received': data,
                'status': 'success'
            }
        except:
            response = {'error': 'Invalid JSON'}
    else:
        response = {'error': 'Method not allowed'}
    
    body = json.dumps(response).encode('utf-8')
    
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'application/json']],
    })
    await send({
        'type': 'http.response.body',
        'body': body,
    })
```

Test it:
```bash
curl -X POST http://127.0.0.1:8000 \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

## API Reference

### UvicornEmulator

Main interface for running ASGI applications.

**Static Methods:**
- `run(app, host='127.0.0.1', port=8000, reload=False, reload_dirs=None, log_level='info')`
  - `app` (str): Application import string (e.g., "main:app")
  - `host` (str): Bind host
  - `port` (int): Bind port
  - `reload` (bool): Enable auto-reload
  - `reload_dirs` (List[str]): Directories to watch
  - `log_level` (str): Logging level

### ASGIServer

Low-level ASGI server.

**Methods:**
- `__init__(app, host, port, reload, reload_dirs)`
- `start()`: Start the server
- `stop()`: Stop the server

### ASGIRequest

Represents an HTTP request.

**Attributes:**
- `method` (str): HTTP method
- `path` (str): Request path
- `query_string` (bytes): Query string
- `headers` (dict): Request headers
- `body` (bytes): Request body

**Methods:**
- `to_asgi_scope()`: Convert to ASGI scope dict

### ASGIResponse

Builds HTTP responses.

**Methods:**
- `add_start_event(event)`: Handle response start
- `add_body_event(event)`: Handle response body
- `to_http_response()`: Convert to HTTP bytes

### FileWatcher

Watches files for changes.

**Methods:**
- `__init__(paths)`: Initialize with paths to watch
- `check_changes()`: Check if any files changed

## ASGI Protocol

The emulator implements ASGI 3.0 protocol:

### Scope Dictionary
```python
{
    'type': 'http',
    'method': 'GET',
    'path': '/hello',
    'query_string': b'',
    'headers': [(b'host', b'localhost')],
    'server': ('127.0.0.1', 8000),
    'client': ('127.0.0.1', 54321),
}
```

### Messages

**Receive (from server to app):**
```python
{'type': 'http.request', 'body': b'...', 'more_body': False}
{'type': 'http.disconnect'}
```

**Send (from app to server):**
```python
{'type': 'http.response.start', 'status': 200, 'headers': [...]}
{'type': 'http.response.body', 'body': b'...', 'more_body': False}
```

## Auto-Reload

The auto-reload feature watches Python files for changes:

1. Scans specified directories for `.py` files
2. Records modification times
3. Checks periodically (every second)
4. Restarts server when changes detected
5. Reloads application module

**Benefits:**
- Faster development workflow
- No manual server restarts
- Catches file additions/deletions
- Efficient polling mechanism

## Limitations

This is an educational emulation with some limitations:

1. **HTTP/1.1 Only**: No HTTP/2 or HTTP/3 support
2. **No WebSockets**: ASGI WebSocket protocol not implemented
3. **No SSL/TLS**: HTTPS not supported
4. **Single-threaded**: One request at a time (but async)
5. **Basic Parsing**: May not handle all HTTP edge cases
6. **No Worker Processes**: Single process only

## Testing

Run the test suite:

```bash
python test_uvicorn_emulator.py
```

Tests cover:
- Request parsing
- ASGI scope conversion
- Response building
- File watching
- ASGI app integration
- Query string handling
- POST body handling

## Complexity

**Implementation Complexity**: Medium-High

This emulator involves:
- Socket programming
- HTTP protocol implementation
- ASGI protocol specification
- Async/await patterns
- File system monitoring
- Module hot reloading

The server implementation requires understanding of networking, HTTP, and async Python programming.

## Integration

Works with ASGI frameworks:
- FastAPI (with some limitations)
- Starlette
- Quart
- Raw ASGI applications

Can be used for:
- Development servers
- Testing ASGI applications
- Learning ASGI protocol
- Prototyping web services

## Dependencies

- Python 3.7+ (requires asyncio)
- No external dependencies required

## Performance

Not intended for production use. For production, use:
- Real Uvicorn
- Hypercorn
- Daphne
- Other production ASGI servers

## License

Part of the Emu-Soft project - see main repository LICENSE.
