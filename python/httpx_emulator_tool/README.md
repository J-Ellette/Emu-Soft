# httpx Emulator

A lightweight implementation of httpx's core functionality - a modern HTTP client with unified sync/async API.

## Overview

This module emulates the essential features of httpx, a next-generation HTTP client for Python. It provides a clean, modern API that works seamlessly in both synchronous and asynchronous contexts.

## Features

### Unified API
- **Sync and Async**: Same API for both synchronous and asynchronous code
- **Context Managers**: Clean resource management with context managers
- **Convenience Functions**: Module-level functions for quick requests

### Rich Request/Response Interface
- **Request Object**: Full-featured request abstraction
- **Response Object**: Rich response interface with convenience methods
- **Headers**: Case-insensitive header handling
- **Status Helpers**: Built-in status code checking (is_success, is_error, is_redirect)

### HTTP Features
- **Multiple Methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **JSON Support**: Built-in JSON encoding/decoding
- **Form Data**: Automatic form encoding
- **Query Parameters**: Easy parameter handling
- **Custom Headers**: Full header customization
- **Cookies**: Cookie handling
- **Base URL**: Set base URL for all requests
- **Timeout**: Configurable request timeout
- **Redirects**: Optional redirect following

### HTTP/2 Concepts
- HTTP/2 flag available (conceptual in this emulator)
- Modern API design inspired by HTTP/2 patterns

## Usage

### Quick Start - Sync API

```python
import httpx_emulator as httpx

# Simple GET request
response = httpx.get('https://api.example.com/data')
print(response.status_code)
print(response.text)

# POST with JSON
response = httpx.post(
    'https://api.example.com/users',
    json={'name': 'John', 'age': 30}
)
print(response.json())
```

### Quick Start - Async API

```python
import asyncio
import httpx_emulator as httpx

async def main():
    # Async GET request
    response = await httpx.AsyncClient().get('https://api.example.com/data')
    print(response.status_code)
    print(await response.text)

asyncio.run(main())
```

### Using Client (Sync)

```python
import httpx_emulator as httpx

# Create a client
with httpx.Client() as client:
    # Make multiple requests
    resp1 = client.get('https://api.example.com/users')
    resp2 = client.get('https://api.example.com/posts')
    
print(resp1.status_code)
print(resp2.status_code)
```

### Using AsyncClient

```python
import asyncio
import httpx_emulator as httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Make multiple async requests
        resp1 = await client.get('https://api.example.com/users')
        resp2 = await client.get('https://api.example.com/posts')
        
    print(resp1.status_code)
    print(resp2.status_code)

asyncio.run(main())
```

### Client with Base URL

```python
import httpx_emulator as httpx

# Create client with base URL
with httpx.Client(base_url='https://api.example.com') as client:
    # All requests use the base URL
    users = client.get('/users')
    posts = client.get('/posts')
    
    # Create new user
    new_user = client.post('/users', json={'name': 'Jane'})
```

### Custom Headers and Cookies

```python
import httpx_emulator as httpx

# Set default headers
headers = {
    'User-Agent': 'MyApp/1.0',
    'Authorization': 'Bearer token123'
}

with httpx.Client(headers=headers) as client:
    response = client.get('https://api.example.com/protected')
    
# Per-request headers
response = httpx.get(
    'https://api.example.com/data',
    headers={'X-Custom-Header': 'value'}
)

# Cookies
cookies = {'session_id': 'abc123'}
response = httpx.get(
    'https://api.example.com/profile',
    cookies=cookies
)
```

### Query Parameters

```python
import httpx_emulator as httpx

# Query parameters as dict
response = httpx.get(
    'https://api.example.com/search',
    params={'q': 'python', 'page': '1', 'limit': '10'}
)

# URL will be: https://api.example.com/search?q=python&page=1&limit=10
```

### POST Requests

```python
import httpx_emulator as httpx

# POST with JSON
response = httpx.post(
    'https://api.example.com/users',
    json={'name': 'John', 'email': 'john@example.com'}
)

# POST with form data
response = httpx.post(
    'https://api.example.com/form',
    data={'username': 'john', 'password': 'secret'}
)

# POST with raw data
response = httpx.post(
    'https://api.example.com/raw',
    content=b'raw binary data',
    headers={'Content-Type': 'application/octet-stream'}
)
```

### Response Handling

```python
import httpx_emulator as httpx

response = httpx.get('https://api.example.com/data')

# Status code
print(f"Status: {response.status_code}")

# Status checks
if response.is_success:
    print("Success!")
elif response.is_error:
    print("Error!")
elif response.is_redirect:
    print("Redirect!")

# Raise exception for error status
response.raise_for_status()

# Body as text
text = response.text

# Body as JSON
data = response.json()

# Headers (case-insensitive)
content_type = response.headers['content-type']
content_type = response.headers.get('Content-Type')

# Original request
original_url = response.request.url
```

### Timeout Configuration

```python
import httpx_emulator as httpx

# Set timeout for client
with httpx.Client(timeout=30.0) as client:
    response = client.get('https://api.example.com/slow')

# Set timeout per request
response = httpx.get('https://api.example.com/data', timeout=10.0)
```

### Redirect Handling

```python
import httpx_emulator as httpx

# Follow redirects
with httpx.Client(follow_redirects=True, max_redirects=10) as client:
    response = client.get('https://example.com/redirect')
    # Will follow redirects automatically
```

## API Reference

### Client

Synchronous HTTP client.

**Constructor:**
```python
Client(
    base_url=None,          # Base URL for all requests
    headers=None,           # Default headers
    cookies=None,           # Default cookies
    timeout=5.0,            # Request timeout in seconds
    follow_redirects=False, # Follow redirects automatically
    max_redirects=20,       # Maximum redirects to follow
    http2=False             # Enable HTTP/2 (conceptual)
)
```

**Methods:**
- `request(method, url, **kwargs)` - Make HTTP request
- `get(url, **kwargs)` - Make GET request
- `post(url, **kwargs)` - Make POST request
- `put(url, **kwargs)` - Make PUT request
- `delete(url, **kwargs)` - Make DELETE request
- `patch(url, **kwargs)` - Make PATCH request
- `head(url, **kwargs)` - Make HEAD request
- `options(url, **kwargs)` - Make OPTIONS request
- `close()` - Close client

### AsyncClient

Asynchronous HTTP client with same API as Client.

All methods are async (use `await`):
```python
async with AsyncClient() as client:
    response = await client.get('https://api.example.com')
```

### Request

HTTP request object.

**Constructor:**
```python
Request(
    method,                 # HTTP method
    url,                    # Request URL
    params=None,            # Query parameters
    headers=None,           # Request headers
    cookies=None,           # Request cookies
    content=None,           # Raw bytes content
    data=None,              # Form data or string
    json=None               # JSON data
)
```

### Response

HTTP response object.

**Properties:**
- `status_code` - HTTP status code
- `reason_phrase` - Status reason
- `headers` - Response headers (case-insensitive)
- `content` - Response body as bytes
- `text` - Response body as string
- `request` - Original request object
- `url` - Request URL
- `is_success` - True if 2xx status
- `is_error` - True if 4xx or 5xx status
- `is_redirect` - True if 3xx status

**Methods:**
- `json(**kwargs)` - Parse response as JSON
- `raise_for_status()` - Raise exception if error status

### Headers

Case-insensitive headers dictionary.

```python
headers = Headers({'Content-Type': 'application/json'})
headers['content-type']  # Works
headers['Content-Type']  # Also works
headers['CONTENT-TYPE']  # Still works
```

### Convenience Functions

Module-level functions for quick requests:

```python
httpx.get(url, **kwargs)
httpx.post(url, **kwargs)
httpx.put(url, **kwargs)
httpx.delete(url, **kwargs)
httpx.patch(url, **kwargs)
httpx.head(url, **kwargs)
httpx.options(url, **kwargs)
httpx.request(method, url, **kwargs)
```

## Testing

Run the test suite:

```bash
python test_httpx_emulator.py
```

Run basic functionality demo:

```bash
python httpx_emulator.py
```

## Comparison with httpx

This emulator provides the core functionality of httpx:

### Implemented Features:
✓ Unified sync/async API  
✓ Rich Request/Response interface  
✓ Case-insensitive headers  
✓ Status code helpers  
✓ JSON encoding/decoding  
✓ Form data encoding  
✓ Query parameters  
✓ Custom headers and cookies  
✓ Base URL support  
✓ Timeout configuration  
✓ Redirect following  
✓ Context managers  

### Not Implemented (for simplicity):
✗ HTTP/2 protocol (flag exists but uses HTTP/1.1)  
✗ Connection pooling optimization  
✗ Streaming responses  
✗ Multipart file uploads  
✗ Authentication classes  
✗ Proxy support  
✗ Event hooks  
✗ Custom transports  

## Dependencies

- Python standard library only
- No external dependencies required
- Requires Python 3.7+ for async/await support

## Use Cases

- Modern HTTP client with clean API
- Projects requiring both sync and async HTTP
- Learning modern HTTP client patterns
- Testing code without external dependencies
- Systems with strict dependency requirements
- Educational purposes - understanding HTTP client design

## License

Part of the Emu-Soft project - emulating essential Python libraries.
