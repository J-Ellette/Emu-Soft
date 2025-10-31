# aiohttp Emulator

A lightweight implementation of aiohttp's core async HTTP client/server functionality without external dependencies.

## Overview

This module emulates the essential features of aiohttp, a popular asynchronous HTTP client/server framework for Python. It provides async HTTP capabilities suitable for building modern async web applications and services.

## Features

### Async HTTP Client
- **ClientSession**: Session management with connection pooling
- **Cookie Support**: Automatic cookie handling across requests
- **Timeout Handling**: Configurable request timeouts
- **Multiple HTTP Methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **JSON Support**: Built-in JSON encoding/decoding
- **Form Data**: Automatic form encoding
- **Context Managers**: Clean async resource management

### Async HTTP Server
- **Application**: ASGI-style application framework
- **Router**: Flexible URL routing with path parameters
- **Request/Response**: Clean HTTP abstractions
- **JSON Responses**: Helper for JSON API responses
- **Route Decorators**: Clean decorator-based routing
- **Path Parameters**: Extract parameters from URLs

## Usage

### Async HTTP Client

#### Basic GET Request

```python
import asyncio
from aiohttp_emulator import ClientSession

async def main():
    async with ClientSession() as session:
        async with await session.get('http://api.example.com/data') as resp:
            print(f"Status: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}")

asyncio.run(main())
```

#### POST Request with JSON

```python
import asyncio
from aiohttp_emulator import ClientSession

async def main():
    async with ClientSession() as session:
        data = {'name': 'John', 'age': 30}
        resp = await session.post('http://api.example.com/users', json=data)
        print(f"Status: {resp.status}")
        result = await resp.json()
        print(f"Result: {result}")

asyncio.run(main())
```

#### Session with Base URL and Headers

```python
from aiohttp_emulator import ClientSession

async def main():
    headers = {
        'User-Agent': 'MyApp/1.0',
        'Authorization': 'Bearer token123'
    }
    
    async with ClientSession(
        base_url='http://api.example.com',
        headers=headers,
        timeout=30.0
    ) as session:
        # All requests will use base_url and headers
        resp = await session.get('/users')
        users = await resp.json()
        
        resp = await session.get('/posts')
        posts = await resp.json()

asyncio.run(main())
```

### Async HTTP Server

#### Basic Server Application

```python
from aiohttp_emulator import Application, Router, Response, json_response

# Create router
router = Router()

async def hello(request):
    return Response(body='Hello, World!', status=200)

async def get_user(request):
    user_id = request.match_info['id']
    return json_response({'id': user_id, 'name': 'John Doe'})

# Add routes
router.add_get('/hello', hello)
router.add_get('/user/{id}', get_user)

# Create application
app = Application(router=router)
```

#### Using Route Decorators

```python
from aiohttp_emulator import get, post, json_response

@get('/api/status')
async def status_handler(request):
    return json_response({'status': 'ok'})

@post('/api/data')
async def create_data(request):
    data = await request.json()
    # Process data
    return json_response({'result': 'created'}, status=201)
```

#### Route with Path Parameters

```python
from aiohttp_emulator import Router, json_response

router = Router()

async def get_post(request):
    user_id = request.match_info['user_id']
    post_id = request.match_info['post_id']
    
    return json_response({
        'user_id': user_id,
        'post_id': post_id,
        'title': 'Sample Post'
    })

router.add_get('/user/{user_id}/post/{post_id}', get_post)
```

#### Handling Query Parameters

```python
async def search_handler(request):
    query = request.query.get('q', '')
    page = request.query.get('page', '1')
    
    return json_response({
        'query': query,
        'page': page,
        'results': []
    })

router.add_get('/search', search_handler)
```

#### Request Body Parsing

```python
async def create_user(request):
    # Parse JSON body
    data = await request.json()
    
    # Or read as text
    # text = await request.text()
    
    # Or read raw bytes
    # body = await request.read()
    
    return json_response({
        'created': True,
        'user': data
    }, status=201)

router.add_post('/users', create_user)
```

## API Reference

### ClientSession

Async HTTP client session with connection pooling.

**Constructor:**
```python
ClientSession(
    base_url=None,          # Base URL for all requests
    headers=None,           # Default headers
    cookies=None,           # Default cookies
    timeout=300.0           # Request timeout in seconds
)
```

**Methods:**
- `async request(method, url, *, params=None, data=None, json=None, headers=None, cookies=None, timeout=None)` - Make HTTP request
- `async get(url, **kwargs)` - Make GET request
- `async post(url, **kwargs)` - Make POST request
- `async put(url, **kwargs)` - Make PUT request
- `async delete(url, **kwargs)` - Make DELETE request
- `async patch(url, **kwargs)` - Make PATCH request
- `async head(url, **kwargs)` - Make HEAD request
- `async options(url, **kwargs)` - Make OPTIONS request
- `async close()` - Close session

### ClientResponse

HTTP response object from async client.

**Properties:**
- `status` - HTTP status code
- `reason` - Status reason phrase
- `headers` - Response headers dict
- `url` - Request URL

**Methods:**
- `async read()` - Read response body as bytes
- `async text(encoding='utf-8')` - Read response body as text
- `async json(**kwargs)` - Parse response body as JSON
- `close()` - Close response

### Application

ASGI application for async HTTP server.

**Constructor:**
```python
Application(router=None)  # Optional router instance
```

**Methods:**
- `add_routes(routes)` - Add list of routes

### Router

URL router for handling requests.

**Methods:**
- `add_route(route)` - Add route instance
- `add_get(path, handler)` - Add GET route
- `add_post(path, handler)` - Add POST route
- `add_put(path, handler)` - Add PUT route
- `add_delete(path, handler)` - Add DELETE route
- `match(method, path)` - Match request to handler

### Route

Route definition with path parameters.

**Constructor:**
```python
Route(method, path, handler)
```

Path parameters are specified with `{param_name}` syntax.

### Request

HTTP request object passed to handlers.

**Properties:**
- `method` - HTTP method
- `path` - Request path
- `headers` - Request headers
- `query` - Query parameters dict
- `match_info` - Path parameters dict

**Methods:**
- `async text()` - Read body as text
- `async json()` - Parse body as JSON
- `async read()` - Read body as bytes

### Response

HTTP response object returned from handlers.

**Constructor:**
```python
Response(
    body=None,              # Response body (str or bytes)
    status=200,             # HTTP status code
    reason=None,            # Status reason phrase
    headers=None,           # Response headers
    content_type=None       # Content-Type header
)
```

### json_response()

Helper function for JSON responses.

```python
json_response(
    data,                   # Data to serialize as JSON
    status=200,             # HTTP status code
    headers=None            # Additional headers
)
```

## Testing

Run the test suite:

```bash
python test_aiohttp_emulator.py
```

Run basic functionality demo:

```bash
python aiohttp_emulator.py
```

## Comparison with aiohttp

This emulator provides the core functionality of aiohttp:

### Implemented Features:
✓ Async HTTP client with sessions  
✓ Cookie handling  
✓ Timeout support  
✓ Multiple HTTP methods  
✓ JSON encoding/decoding  
✓ Form data encoding  
✓ Async HTTP server application  
✓ URL routing with path parameters  
✓ Request/Response abstractions  
✓ Route decorators  

### Not Implemented (for simplicity):
✗ WebSocket full implementation  
✗ Multipart file uploads  
✗ Streaming responses  
✗ Middleware system  
✗ Static file serving  
✗ CORS handling  
✗ SSL/TLS advanced configuration  
✗ Connection pooling optimization  
✗ HTTP/2 support  

## Dependencies

- Python standard library only
- No external dependencies required
- Requires Python 3.7+ for async/await support

## Use Cases

- Async web applications requiring HTTP client
- API clients with async operations
- Microservices with async HTTP
- Learning async programming patterns
- Testing async code without external dependencies
- Systems with strict dependency requirements

## License

Part of the Emu-Soft project - emulating essential Python libraries.
