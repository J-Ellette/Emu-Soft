# urllib3 Emulator

A lightweight implementation of urllib3's core functionality without external dependencies.

## Overview

This module emulates the essential features of urllib3, a powerful, user-friendly HTTP client library for Python. It provides production-grade HTTP client capabilities with connection pooling, retry logic, and robust error handling.

## Features

### Core Functionality
- **Connection Pooling**: Reuse HTTP connections for improved performance
- **Retry Logic**: Configurable retry mechanism with exponential backoff
- **HTTP/HTTPS Support**: Full support for both HTTP and HTTPS protocols
- **Request Timeout**: Configurable timeout for requests
- **Header Management**: Custom header support for requests
- **Response Handling**: Comprehensive response object with multiple access methods

### Advanced Features
- **Redirect Following**: Automatic handling of HTTP redirects
- **Status Code Retry**: Retry on specific HTTP status codes (e.g., 500, 502, 503, 504)
- **Form Encoding**: Automatic URL encoding of form fields
- **Connection Reuse**: Efficient connection pooling to minimize overhead
- **Multiple Pool Management**: PoolManager for handling multiple hosts

## Usage

### Basic Usage

```python
from urllib3_emulator import PoolManager

# Create a pool manager
http = PoolManager()

# Make a GET request
response = http.request('GET', 'http://httpbin.org/get')
print(f"Status: {response.status}")
print(f"Body: {response.text}")

# Make a POST request with form data
response = http.request(
    'POST',
    'http://httpbin.org/post',
    fields={'key': 'value', 'name': 'test'}
)
```

### Connection Pooling

```python
from urllib3_emulator import HTTPConnectionPool

# Create a connection pool for a specific host
pool = HTTPConnectionPool('example.com', port=80, maxsize=10)

# Make multiple requests using the same pool
resp1 = pool.urlopen('GET', '/page1')
resp2 = pool.urlopen('GET', '/page2')

# Close the pool when done
pool.close()
```

### Retry Configuration

```python
from urllib3_emulator import PoolManager, Retry

# Configure retry behavior
retry = Retry(
    total=5,                    # Total number of retries
    backoff_factor=0.5,         # Backoff between retries
    status_forcelist={500, 502, 503}  # Status codes to retry
)

# Create pool manager with retry configuration
http = PoolManager(retries=retry)

# Make request with automatic retry
response = http.request('GET', 'http://example.com/api')
```

### Custom Headers

```python
from urllib3_emulator import PoolManager

# Set default headers for all requests
http = PoolManager(headers={
    'User-Agent': 'My-Application/1.0',
    'Accept': 'application/json'
})

# Make request with additional headers
response = http.request(
    'GET',
    'http://api.example.com/data',
    headers={'Authorization': 'Bearer token123'}
)
```

### Response Handling

```python
# Read response as bytes
data = response.read()

# Read response as text
text = response.text

# Parse JSON response
json_data = response.json()

# Access specific headers
content_type = response.getheader('content-type')

# Get all headers
all_headers = response.getheaders()

# Check status
if response.status == 200:
    print("Success!")
```

## API Reference

### PoolManager

Main class for managing multiple connection pools.

**Constructor:**
```python
PoolManager(
    num_pools=10,           # Maximum number of pools
    headers=None,           # Default headers
    timeout=5.0,            # Request timeout
    retries=None            # Retry configuration
)
```

**Methods:**
- `request(method, url, fields=None, headers=None, **kwargs)` - Make HTTP request
- `urlopen(method, url, redirect=True, **kw)` - Make HTTP request with redirect
- `connection_from_host(host, port=None, scheme='http')` - Get pool for specific host
- `clear()` - Close all connection pools

### HTTPConnectionPool

Connection pool for a single host.

**Constructor:**
```python
HTTPConnectionPool(
    host,                   # Host to connect to
    port=None,              # Port number
    timeout=5.0,            # Request timeout
    maxsize=1,              # Maximum pool size
    retries=None,           # Retry configuration
    scheme='http'           # http or https
)
```

**Methods:**
- `urlopen(method, url, body=None, headers=None, retries=None, redirect=True, timeout=None)` - Make request
- `request(method, url, fields=None, headers=None, **kwargs)` - Make request with form fields
- `close()` - Close all connections in pool

### Retry

Retry configuration for failed requests.

**Constructor:**
```python
Retry(
    total=10,               # Total number of retries
    connect=None,           # Connection retries
    read=None,              # Read retries
    redirect=5,             # Maximum redirects
    status=None,            # Status retries
    backoff_factor=0,       # Backoff factor
    status_forcelist=None   # Status codes to retry
)
```

**Methods:**
- `sleep_for_retry(retry_count)` - Sleep for calculated backoff time

### HTTPResponse

HTTP response object.

**Properties:**
- `data` - Response body as bytes
- `text` - Response body as string
- `status` - HTTP status code
- `reason` - Status reason phrase
- `headers` - Response headers dict
- `version` - HTTP version

**Methods:**
- `read(amt=None)` - Read response body
- `json()` - Parse JSON response
- `getheader(name, default=None)` - Get specific header
- `getheaders()` - Get all headers

## Testing

Run the test suite:

```bash
python test_urllib3_emulator.py
```

Run basic functionality demo:

```bash
python urllib3_emulator.py
```

## Comparison with urllib3

This emulator provides the core functionality of urllib3:

### Implemented Features:
✓ Connection pooling and reuse  
✓ Retry logic with backoff  
✓ HTTP/HTTPS support  
✓ Request timeout handling  
✓ Custom headers  
✓ Form field encoding  
✓ Redirect following  
✓ Response object with multiple access methods  

### Not Implemented (for simplicity):
✗ Multipart file uploads  
✗ Proxy support  
✗ Advanced SSL/TLS configuration  
✗ gzip/deflate encoding  
✗ Chunked transfer encoding  
✗ HTTP/2 support  

## Dependencies

- Python standard library only
- No external dependencies required

## Use Cases

- Environments requiring self-contained HTTP client
- Educational purposes - understanding HTTP client internals
- Lightweight applications where full urllib3 is not needed
- Systems with strict dependency requirements
- Military-grade software requiring auditable code

## License

Part of the Emu-Soft project - emulating essential Python libraries.
