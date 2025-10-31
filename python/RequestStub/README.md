# responses Emulator

A pure Python implementation that emulates responses functionality for mocking HTTP requests without external dependencies.

## What This Emulates

**Emulates:** responses (HTTP request mocking library)
**Original:** https://github.com/getsentry/responses

## Overview

This module provides a utility for mocking out the Python `requests` library, allowing you to write tests that don't make real HTTP requests. This is crucial for fast, reliable, and isolated unit tests.

## Features

- **Request Mocking**
  - Mock any HTTP method (GET, POST, PUT, PATCH, DELETE, etc.)
  - Return predefined responses
  - Support for JSON and text responses
  - Custom status codes and headers

- **URL Matching**
  - Exact URL matching
  - Regex pattern matching
  - Query string matching (optional)

- **Dynamic Responses**
  - Callback-based responses
  - Access request data in callbacks
  - Generate responses based on request

- **Call Recording**
  - Track all mocked requests
  - Inspect request details
  - Verify request parameters

- **Flexible Usage**
  - Context manager
  - Decorator
  - Manual start/stop

## Usage

### Basic Mocking with Context Manager

```python
from responses_emulator_tool.responses_emulator import RequestsMock
import requests

mock = RequestsMock()
mock.add(method='GET', url='https://api.example.com/users', json={'users': []}, status=200)

with mock:
    response = requests.get('https://api.example.com/users')
    print(response.json())  # {'users': []}
    print(response.status_code)  # 200
```

### Using Decorator

```python
from responses_emulator_tool import responses_emulator as responses
import requests

@responses.activate
def test_api():
    responses.add(
        method='GET',
        url='https://api.example.com/users',
        json={'users': ['Alice', 'Bob']},
        status=200
    )
    
    resp = requests.get('https://api.example.com/users')
    assert resp.status_code == 200
    assert len(resp.json()['users']) == 2

test_api()
```

### Multiple Responses

```python
mock = RequestsMock()

# Mock multiple endpoints
mock.add(method='GET', url='https://api.example.com/users', json={'users': []})
mock.add(method='POST', url='https://api.example.com/users', json={'id': 1, 'name': 'Alice'}, status=201)
mock.add(method='GET', url='https://api.example.com/users/1', json={'id': 1, 'name': 'Alice'})
mock.add(method='DELETE', url='https://api.example.com/users/1', status=204)

with mock:
    # Each request finds its matching response
    resp1 = requests.get('https://api.example.com/users')
    resp2 = requests.post('https://api.example.com/users', json={'name': 'Alice'})
    resp3 = requests.get('https://api.example.com/users/1')
    resp4 = requests.delete('https://api.example.com/users/1')
```

### Regex URL Matching

```python
import re

mock = RequestsMock()
pattern = re.compile(r'https://api\.example\.com/users/\d+')
mock.add(method='GET', url=pattern, json={'user': 'details'})

with mock:
    # Matches any URL like /users/123, /users/456, etc.
    resp1 = requests.get('https://api.example.com/users/123')
    resp2 = requests.get('https://api.example.com/users/456')
```

### Query String Matching

```python
mock = RequestsMock()

# Without match_querystring, ignores query parameters
mock.add(method='GET', url='https://api.example.com/users', json={'all': 'users'})

with mock:
    # Both work with the same mock
    resp1 = requests.get('https://api.example.com/users')
    resp2 = requests.get('https://api.example.com/users?page=1')

# With match_querystring, requires exact match
mock.reset()
mock.add(
    method='GET',
    url='https://api.example.com/users?page=1',
    json={'page': 1},
    match_querystring=True
)

with mock:
    resp = requests.get('https://api.example.com/users?page=1')  # Works
    # requests.get('https://api.example.com/users?page=2')  # Would fail
```

### Dynamic Responses with Callbacks

```python
import json

def request_callback(request):
    """Generate response based on request."""
    return json.dumps({
        'method': request.method,
        'url': request.url,
        'received': True
    })

mock = RequestsMock()
mock.add_callback(
    method='POST',
    url='https://api.example.com/echo',
    callback=request_callback
)

with mock:
    resp = requests.post('https://api.example.com/echo', json={'data': 'test'})
    data = resp.json()
    assert data['method'] == 'POST'
    assert data['received'] is True
```

### Custom Headers

```python
mock = RequestsMock()
mock.add(
    method='GET',
    url='https://api.example.com/secure',
    json={'data': 'secret'},
    headers={
        'X-API-Key': 'secret-key',
        'X-Rate-Limit': '100'
    }
)

with mock:
    resp = requests.get('https://api.example.com/secure')
    assert 'X-API-Key' in resp.headers
    assert resp.headers['X-API-Key'] == 'secret-key'
```

### Different Status Codes

```python
mock = RequestsMock()

# Success
mock.add(method='GET', url='https://api.example.com/ok', status=200)
mock.add(method='POST', url='https://api.example.com/created', status=201)

# Client errors
mock.add(method='GET', url='https://api.example.com/notfound', status=404)
mock.add(method='POST', url='https://api.example.com/badrequest', status=400)

# Server errors
mock.add(method='GET', url='https://api.example.com/error', status=500)
```

### Inspecting Calls

```python
mock = RequestsMock()
mock.add(method='POST', url='https://api.example.com/users', json={'id': 1}, status=201)

with mock:
    requests.post('https://api.example.com/users', json={'name': 'Alice'})
    requests.post('https://api.example.com/users', json={'name': 'Bob'})
    
    # Check how many times the endpoint was called
    assert len(mock.calls) == 2
    
    # Inspect individual calls
    first_call = mock.calls[0]
    assert first_call.request.method == 'POST'
    assert first_call.request.url == 'https://api.example.com/users'
```

### Resetting Mocks

```python
mock = RequestsMock()
mock.add(method='GET', url='https://api.example.com/users', json={'users': []})

with mock:
    requests.get('https://api.example.com/users')
    assert len(mock.calls) == 1
    
    # Reset removes all responses and call history
    mock.reset()
    assert len(mock.calls) == 0
    assert len(mock._responses) == 0
```

### Manual Start/Stop

```python
mock = RequestsMock()
mock.add(method='GET', url='https://api.example.com/users', json={'users': []})

# Manually control mocking
mock.start()
resp = requests.get('https://api.example.com/users')
mock.stop()

# After stop, real requests are made again
```

## HTTP Method Constants

```python
from responses_emulator_tool.responses_emulator import GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS

mock = RequestsMock()
mock.add(method=GET, url='https://api.example.com/users', json={'users': []})
mock.add(method=POST, url='https://api.example.com/users', json={'id': 1}, status=201)
```

## Implementation Details

### Pure Python Implementation

This emulator is implemented using only Python standard library:
- No external dependencies required
- Monkey-patches the `requests` library if available
- Falls back gracefully if `requests` is not installed

### Differences from responses

This is a simplified emulator. Some advanced features are not implemented:
- No passthrough to real requests
- No response streaming (partially supported)
- No file upload mocking
- No advanced matchers (only URL and method)
- Simplified callback interface
- No adapter-level mocking

For production use cases requiring these features, use the official responses library.

## Testing

Run the included tests:

```bash
python responses_emulator_tool/test_responses_emulator.py
```

Note: Some tests require the `requests` library to be installed. If not available, those tests will be skipped.

## Common Use Cases

### Testing API Clients

```python
@responses.activate
def test_user_api_client():
    responses.add(GET, 'https://api.example.com/users/1', json={'id': 1, 'name': 'Alice'})
    
    client = UserAPIClient()
    user = client.get_user(1)
    assert user['name'] == 'Alice'
```

### Testing Error Handling

```python
@responses.activate
def test_error_handling():
    responses.add(GET, 'https://api.example.com/users', status=500)
    
    client = UserAPIClient()
    with pytest.raises(APIError):
        client.get_users()
```

### Testing Retry Logic

```python
@responses.activate
def test_retry_logic():
    # First request fails
    responses.add(GET, 'https://api.example.com/users', status=503)
    # Second request succeeds
    responses.add(GET, 'https://api.example.com/users', json={'users': []}, status=200)
    
    client = UserAPIClient(max_retries=2)
    users = client.get_users()
    assert len(users) == 0
    assert len(responses.calls) == 2
```

## License

See LICENSE file in the repository root.
