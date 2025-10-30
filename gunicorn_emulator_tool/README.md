# Gunicorn Emulator

A lightweight emulation of Gunicorn's WSGI server functionality for serving Python web applications with worker process management.

## Features

- **WSGI 1.0 Support**: Full WSGI protocol implementation
- **Multi-Process Workers**: Pre-fork worker model with configurable worker count
- **Process Management**: Automatic worker monitoring and restart
- **HTTP Server**: Built-in HTTP/1.1 server
- **Production-Ready Architecture**: Master-worker process pattern
- **Simple Interface**: Easy-to-use API matching Gunicorn
- **Request/Response Handling**: Complete HTTP message parsing and generation

## What It Emulates

This tool emulates core functionality of [Gunicorn](https://github.com/benoitc/gunicorn), the Python WSGI HTTP Server for UNIX.

### Core Components Implemented

1. **WSGI Server**
   - HTTP/1.1 protocol support
   - Request parsing and routing
   - Response building
   - WSGI environ construction

2. **Arbiter (Master Process)**
   - Worker process management
   - Process monitoring and restart
   - Graceful shutdown
   - Signal handling

3. **Worker Processes**
   - Pre-fork worker model
   - Independent request handling
   - Application loading per worker
   - Request statistics

4. **Multi-Processing**
   - Multiple worker processes
   - CPU-based worker count defaults
   - Process isolation
   - Load distribution

## Usage

### As a Module

```python
from gunicorn_emulator import GunicornEmulator

# Run WSGI application with 4 workers
GunicornEmulator.run(
    app="myapp:application",
    bind="0.0.0.0:8000",
    workers=4,
    worker_connections=1000
)
```

### Command Line

```bash
# Basic usage
python gunicorn_emulator.py myapp:application

# Custom host and port
python gunicorn_emulator.py myapp:application -b 0.0.0.0:5000

# Multiple workers (default: CPU count)
python gunicorn_emulator.py myapp:application -w 4

# Worker connections
python gunicorn_emulator.py myapp:application --worker-connections 2000

# Set timeout
python gunicorn_emulator.py myapp:application -t 60
```

## Examples

### Simple WSGI Application

```python
# app.py

def application(environ, start_response):
    """Simple WSGI application"""
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    
    return [b'Hello, World!']
```

Run it:
```bash
python gunicorn_emulator.py app:application -w 2
# Visit http://127.0.0.1:8000
```

### JSON API

```python
# api.py
import json

def application(environ, start_response):
    """JSON API example"""
    path = environ.get('PATH_INFO', '/')
    
    if path == '/':
        response_data = {
            'message': 'Welcome to the API',
            'endpoints': ['/users', '/posts']
        }
    elif path == '/users':
        response_data = {
            'users': [
                {'id': 1, 'name': 'Alice'},
                {'id': 2, 'name': 'Bob'}
            ]
        }
    else:
        response_data = {'error': 'Not found'}
    
    body = json.dumps(response_data).encode('utf-8')
    
    status = '200 OK'
    headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(body)))
    ]
    start_response(status, headers)
    
    return [body]
```

Run it:
```bash
python gunicorn_emulator.py api:application -w 4
```

### Query Parameters

```python
# query_app.py
from urllib.parse import parse_qs

def application(environ, start_response):
    """Handle query parameters"""
    query_string = environ.get('QUERY_STRING', '')
    params = parse_qs(query_string)
    
    name = params.get('name', ['World'])[0]
    message = f'Hello, {name}!'
    
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    
    return [message.encode('utf-8')]
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

def application(environ, start_response):
    """Handle POST requests"""
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if method == 'POST':
        # Read request body
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            content_length = 0
        
        body = environ['wsgi.input'].read(content_length)
        
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
    
    status = '200 OK'
    headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(body)))
    ]
    start_response(status, headers)
    
    return [body]
```

Test it:
```bash
curl -X POST http://127.0.0.1:8000 \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

### Flask Integration

```python
# flask_app.py
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Flask!'

@app.route('/api/data')
def data():
    return {'message': 'API response'}

# WSGI application
application = app
```

Run it:
```bash
python gunicorn_emulator.py flask_app:application -w 4 -b 0.0.0.0:8000
```

## API Reference

### GunicornEmulator

Main interface for running WSGI applications.

**Static Methods:**
- `run(app, bind='127.0.0.1:8000', workers=None, worker_connections=1000, daemon=False, timeout=30, log_level='info')`
  - `app` (str): Application import string (e.g., "main:app")
  - `bind` (str): The socket to bind (HOST:PORT)
  - `workers` (int): Number of worker processes (default: CPU count)
  - `worker_connections` (int): Max simultaneous clients per worker
  - `daemon` (bool): Daemonize the process
  - `timeout` (int): Worker timeout in seconds
  - `log_level` (str): Logging level

### Arbiter

Master process that manages workers.

**Methods:**
- `__init__(app_path, workers, host, port, worker_connections, daemon, timeout)`
- `start_workers()`: Start all worker processes
- `monitor_workers()`: Monitor and restart failed workers
- `shutdown()`: Graceful shutdown of all workers
- `run()`: Main arbiter loop

### Worker

Worker process for handling requests.

**Methods:**
- `__init__(worker_id, app_path, host, port, worker_connections)`
- `load_application()`: Load WSGI application
- `handle_request(conn, addr, server_addr)`: Handle single request
- `run()`: Main worker loop

### WSGIRequest

Represents an HTTP request.

**Attributes:**
- `method` (str): HTTP method
- `path` (str): Request path
- `query_string` (str): Query string
- `headers` (dict): Request headers
- `body` (bytes): Request body

**Methods:**
- `to_wsgi_environ()`: Convert to WSGI environ dict

### WSGIResponse

Builds HTTP responses.

**Methods:**
- `start_response(status, headers, exc_info=None)`: WSGI start_response
- `write(data)`: Write response body
- `to_http_response()`: Convert to HTTP bytes

## WSGI Protocol

The emulator implements WSGI 1.0 protocol (PEP 3333):

### Environ Dictionary
```python
{
    'REQUEST_METHOD': 'GET',
    'SCRIPT_NAME': '',
    'PATH_INFO': '/hello',
    'QUERY_STRING': 'name=Alice',
    'CONTENT_TYPE': 'text/plain',
    'CONTENT_LENGTH': '123',
    'SERVER_NAME': '127.0.0.1',
    'SERVER_PORT': '8000',
    'SERVER_PROTOCOL': 'HTTP/1.1',
    'wsgi.version': (1, 0),
    'wsgi.url_scheme': 'http',
    'wsgi.input': <file-like object>,
    'wsgi.errors': <stderr>,
    'wsgi.multithread': False,
    'wsgi.multiprocess': True,
    'wsgi.run_once': False,
    'REMOTE_ADDR': '127.0.0.1',
    'REMOTE_PORT': '54321',
    'HTTP_HOST': 'localhost',
    # ... other HTTP headers as HTTP_*
}
```

### Application Interface
```python
def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b'Response body']
```

## Worker Management

The emulator uses a pre-fork worker model:

1. **Master Process (Arbiter)**
   - Manages worker processes
   - Monitors worker health
   - Restarts failed workers
   - Handles shutdown signals

2. **Worker Processes**
   - Independent request handlers
   - Load application on startup
   - Handle multiple requests
   - Report statistics

**Benefits:**
- Process isolation
- Fault tolerance
- Load distribution
- Scalability

## Command-Line Options

```
usage: gunicorn_emulator.py [-h] [-b BIND] [-w WORKERS]
                           [--worker-connections WORKER_CONNECTIONS]
                           [-D] [-t TIMEOUT]
                           [--log-level {debug,info,warning,error,critical}]
                           app

Gunicorn WSGI Server Emulator

positional arguments:
  app                   Application import string (module:app)

optional arguments:
  -h, --help            Show help message
  -b BIND, --bind BIND  Socket to bind (default: 127.0.0.1:8000)
  -w WORKERS, --workers WORKERS
                        Number of worker processes (default: CPU count)
  --worker-connections WORKER_CONNECTIONS
                        Max simultaneous clients (default: 1000)
  -D, --daemon          Daemonize the process
  -t TIMEOUT, --timeout TIMEOUT
                        Worker timeout in seconds (default: 30)
  --log-level {debug,info,warning,error,critical}
                        Logging level (default: info)
```

## Limitations

This is an educational emulation with some limitations:

1. **HTTP/1.1 Only**: No HTTP/2 support
2. **No SSL/TLS**: HTTPS not supported
3. **Basic Parsing**: May not handle all HTTP edge cases
4. **No Async Workers**: Only sync workers (no gevent, eventlet)
5. **Limited Configuration**: Subset of Gunicorn options
6. **No Worker Classes**: Single worker type only
7. **No Hooks**: Pre/post fork hooks not implemented

## Testing

Run the test suite:

```bash
python test_gunicorn_emulator.py
```

Tests cover:
- Request parsing
- WSGI environ conversion
- Response building
- WSGI application integration
- Query parameters
- POST body handling
- Multiple headers
- URL decoding

## Complexity

**Implementation Complexity**: High

This emulator involves:
- Socket programming
- HTTP protocol implementation
- WSGI protocol specification
- Multi-processing
- Process management
- Signal handling
- IPC (inter-process communication)

The server implementation requires understanding of networking, HTTP, WSGI, and Unix process management.

## Integration

Works with WSGI frameworks and applications:
- Flask
- Django
- Bottle
- Pyramid
- Raw WSGI applications

Can be used for:
- Development servers
- Testing WSGI applications
- Learning WSGI protocol
- Production-like testing
- Multi-process testing

## Performance

Not intended for high-performance production use. For production, use:
- Real Gunicorn
- uWSGI
- mod_wsgi
- Other production WSGI servers

## Dependencies

- Python 3.6+ (requires multiprocessing)
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
