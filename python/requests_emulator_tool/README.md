# Requests Emulator

A lightweight emulation of the popular Python Requests library for making HTTP requests.

## Features

- **Simple API**: Easy-to-use interface matching the requests library
- **HTTP Methods**: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
- **Session Support**: Persistent sessions with cookies and headers
- **Authentication**: Basic authentication support
- **JSON Handling**: Automatic JSON encoding/decoding
- **Parameters**: URL parameter handling
- **Headers**: Custom header support
- **Cookies**: Cookie management
- **Response Objects**: Rich response interface with content, text, and JSON properties
- **Error Handling**: HTTP error exceptions

## What It Emulates

This tool emulates core functionality of the [Requests](https://requests.readthedocs.io/) library by Kenneth Reitz, the most popular HTTP library for Python.

### Core Components Implemented

1. **HTTP Client**
   - All major HTTP methods
   - Request/response handling
   - Header management
   - URL parameter encoding

2. **Session Management**
   - Persistent sessions
   - Cookie persistence
   - Header persistence
   - Authentication persistence

3. **Response Object**
   - Content access (bytes/text)
   - JSON parsing
   - Status checking
   - Header access
   - Encoding detection

4. **Authentication**
   - Basic authentication
   - Session-based auth

## Usage

### Simple Requests

```python
import requests_emulator as requests

# GET request
response = requests.get('http://httpbin.org/get')
print(response.status_code)  # 200
print(response.text)

# POST with JSON
response = requests.post('http://httpbin.org/post', json={'key': 'value'})
data = response.json()

# POST with form data
response = requests.post('http://httpbin.org/post', data={'key': 'value'})

# PUT request
response = requests.put('http://httpbin.org/put', json={'updated': True})

# DELETE request
response = requests.delete('http://httpbin.org/delete')
```

### URL Parameters

```python
import requests_emulator as requests

# Add parameters to URL
params = {'q': 'python', 'page': 1}
response = requests.get('http://api.example.com/search', params=params)
# Requests: http://api.example.com/search?q=python&page=1
```

### Custom Headers

```python
import requests_emulator as requests

headers = {
    'User-Agent': 'My App/1.0',
    'Accept': 'application/json',
    'X-API-Key': 'secret-key'
}

response = requests.get('http://api.example.com', headers=headers)
```

### Authentication

```python
import requests_emulator as requests

# Basic authentication
response = requests.get(
    'http://api.example.com/protected',
    auth=('username', 'password')
)
```

### Cookies

```python
import requests_emulator as requests

# Send cookies
cookies = {'session_id': '123456'}
response = requests.get('http://example.com', cookies=cookies)

# Access response cookies
print(response.headers.get('set-cookie'))
```

### Sessions

```python
import requests_emulator as requests

# Create a session
session = requests.Session()

# Session persists cookies
session.get('http://example.com/login')
session.post('http://example.com/login', data={'user': 'me', 'pass': 'secret'})

# Subsequent requests use the same cookies
response = session.get('http://example.com/profile')

# Session persists headers
session.headers['X-API-Key'] = 'my-key'
session.get('http://api.example.com/data')  # Includes X-API-Key

# Context manager
with requests.Session() as session:
    session.get('http://example.com')
```

### Response Object

```python
import requests_emulator as requests

response = requests.get('http://httpbin.org/get')

# Status code
print(response.status_code)  # 200
print(response.reason)  # OK

# Content
print(response.content)  # bytes
print(response.text)  # str

# JSON
data = response.json()  # Parse JSON response

# Headers
print(response.headers['content-type'])

# Check status
if response.ok:
    print("Success!")

# Raise exception for errors
response.raise_for_status()
```

## Examples

### API Client

```python
import requests_emulator as requests

class APIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers['X-API-Key'] = api_key
    
    def get_user(self, user_id):
        url = f"{self.base_url}/users/{user_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def create_user(self, user_data):
        url = f"{self.base_url}/users"
        response = self.session.post(url, json=user_data)
        response.raise_for_status()
        return response.json()

# Usage
client = APIClient('https://api.example.com', 'my-api-key')
user = client.get_user(123)
```

### Download File

```python
import requests_emulator as requests

def download_file(url, filename):
    response = requests.get(url)
    
    if response.ok:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    return False

# Usage
download_file('http://example.com/file.pdf', 'local_file.pdf')
```

### Error Handling

```python
import requests_emulator as requests
from requests_emulator import HTTPError

try:
    response = requests.get('http://api.example.com/data')
    response.raise_for_status()
    data = response.json()
except HTTPError as e:
    print(f"HTTP error: {e}")
    print(f"Status code: {e.response.status_code}")
except Exception as e:
    print(f"Error: {e}")
```

### RESTful API Operations

```python
import requests_emulator as requests

base_url = 'http://api.example.com'

# CREATE
response = requests.post(f'{base_url}/posts', json={
    'title': 'Hello',
    'body': 'World'
})
post = response.json()

# READ
response = requests.get(f'{base_url}/posts/{post["id"]}')
post = response.json()

# UPDATE
response = requests.put(f'{base_url}/posts/{post["id"]}', json={
    'title': 'Updated',
    'body': 'Content'
})

# PARTIAL UPDATE
response = requests.patch(f'{base_url}/posts/{post["id"]}', json={
    'title': 'New Title'
})

# DELETE
response = requests.delete(f'{base_url}/posts/{post["id"]}')
```

### Web Scraping

```python
import requests_emulator as requests

def scrape_page(url):
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0'
    })
    
    if response.ok:
        return response.text
    return None

html = scrape_page('http://example.com')
```

## API Reference

### Module Functions

**HTTP Methods:**
- `get(url, **kwargs)` - GET request
- `post(url, **kwargs)` - POST request
- `put(url, **kwargs)` - PUT request
- `patch(url, **kwargs)` - PATCH request
- `delete(url, **kwargs)` - DELETE request
- `head(url, **kwargs)` - HEAD request
- `options(url, **kwargs)` - OPTIONS request

**Generic:**
- `request(method, url, **kwargs)` - Generic HTTP request

**Session:**
- `Session()` - Create a session object

### Request Parameters

All HTTP method functions accept these parameters:

- `url` (str): URL to request
- `params` (dict): URL parameters
- `data` (dict/str/bytes): Request body data
- `json` (any): JSON data to send
- `headers` (dict): HTTP headers
- `cookies` (dict): Cookies to send
- `auth` (tuple): (username, password) for basic auth
- `timeout` (float): Request timeout in seconds
- `allow_redirects` (bool): Follow redirects (default: True)
- `verify` (bool): Verify SSL certificates (default: True)

### Response Object

**Properties:**
- `status_code` (int): HTTP status code
- `reason` (str): Status reason phrase
- `headers` (dict): Response headers
- `content` (bytes): Response body as bytes
- `text` (str): Response body as string
- `encoding` (str): Response encoding
- `url` (str): Final URL
- `ok` (bool): True if status < 400

**Methods:**
- `json(**kwargs)`: Parse JSON response
- `raise_for_status()`: Raise HTTPError for bad status

### Session Object

**Properties:**
- `headers` (dict): Persistent headers
- `cookies` (dict): Persistent cookies
- `auth` (tuple): Persistent authentication
- `timeout` (float): Default timeout
- `verify` (bool): SSL verification

**Methods:**
- `request(method, url, **kwargs)`: Make request
- `get(url, **kwargs)`: GET request
- `post(url, **kwargs)`: POST request
- `put(url, **kwargs)`: PUT request
- `patch(url, **kwargs)`: PATCH request
- `delete(url, **kwargs)`: DELETE request
- `head(url, **kwargs)`: HEAD request
- `options(url, **kwargs)`: OPTIONS request
- `close()`: Close session

### HTTPError Exception

Raised when `response.raise_for_status()` is called on a response with status >= 400.

**Attributes:**
- `response` (Response): The response object

## HTTP Methods

### GET
Retrieve data from a server.
```python
response = requests.get('http://api.example.com/users')
```

### POST
Submit data to create a new resource.
```python
response = requests.post('http://api.example.com/users', json={'name': 'John'})
```

### PUT
Update an entire resource.
```python
response = requests.put('http://api.example.com/users/1', json={'name': 'Jane'})
```

### PATCH
Partially update a resource.
```python
response = requests.patch('http://api.example.com/users/1', json={'email': 'new@example.com'})
```

### DELETE
Remove a resource.
```python
response = requests.delete('http://api.example.com/users/1')
```

### HEAD
Get headers only (no body).
```python
response = requests.head('http://example.com')
```

### OPTIONS
Get allowed HTTP methods.
```python
response = requests.options('http://api.example.com/users')
```

## Status Codes

Common HTTP status codes:

- **2xx Success**
  - 200 OK
  - 201 Created
  - 204 No Content

- **3xx Redirection**
  - 301 Moved Permanently
  - 302 Found
  - 304 Not Modified

- **4xx Client Error**
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found

- **5xx Server Error**
  - 500 Internal Server Error
  - 502 Bad Gateway
  - 503 Service Unavailable

## Limitations

This is an educational emulation with some limitations:

1. **Basic Implementation**: Uses Python's http.client internally
2. **Limited SSL Verification**: SSL certificate verification is simplified
3. **No Streaming**: No support for streaming uploads/downloads
4. **No Proxies**: Proxy support not fully implemented
5. **No Connection Pooling**: No advanced connection management
6. **Simplified Cookies**: Basic cookie handling
7. **No Multipart**: File uploads not fully implemented
8. **No Hooks**: Request/response hooks not implemented

## Testing

Run the test suite:

```bash
python test_requests_emulator.py
```

Tests cover:
- Response object functionality
- Request object creation
- Session management
- HTTP methods
- Error handling
- Parameter handling
- Authentication

## Complexity

**Implementation Complexity**: Medium

This emulator involves:
- HTTP protocol handling
- URL parsing and encoding
- JSON serialization/deserialization
- Cookie management
- Authentication schemes
- Response parsing

The implementation builds on Python's standard library http.client.

## Comparison with Real Requests

### Similarities
- Same API interface
- Same method signatures
- Response object structure
- Session management
- Authentication support

### Differences
- Real requests has more features
- Real requests has better performance
- Real requests has connection pooling
- Real requests has streaming support
- Real requests has comprehensive SSL handling

## Use Cases

- Learning HTTP concepts
- Testing HTTP clients
- Simple API interactions
- Prototyping applications
- Educational purposes
- Minimal-dependency projects

## Dependencies

- Python 3.6+
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
