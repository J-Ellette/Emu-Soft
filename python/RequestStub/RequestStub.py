#!/usr/bin/env python3
"""
Developed by PowerShield, as an alternative to responses

responses Emulator - HTTP Request Mocking

Emulates responses library functionality for mocking HTTP requests without external dependencies.
responses is a utility library for mocking out the requests library.

Reference: https://github.com/getsentry/responses
"""

import json
import re
from typing import Any, Dict, List, Optional, Union, Callable
from urllib.parse import urlparse, parse_qs, urlencode
import functools


class CallList(list):
    """A list of calls with additional query methods."""
    
    def __init__(self):
        super().__init__()
    
    def add(self, request):
        """Add a request to the call list."""
        self.append(request)
    
    def reset(self):
        """Clear all recorded calls."""
        self.clear()


class Call:
    """Represents a recorded request call."""
    
    def __init__(self, method, url, body=None, headers=None):
        self.request = type('Request', (), {
            'method': method,
            'url': url,
            'body': body,
            'headers': headers or {}
        })()


class Response:
    """Represents a mocked HTTP response."""
    
    def __init__(
        self,
        method: str,
        url: Union[str, re.Pattern],
        body: Union[str, bytes, dict, Callable] = '',
        json: Optional[dict] = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: str = 'text/plain',
        stream: bool = False,
        match_querystring: bool = False,
    ):
        self.method = method.upper()
        self.url = url
        self._body = body
        self._json = json
        self.status = status
        self.headers = headers or {}
        self.content_type = content_type
        self.stream = stream
        self.match_querystring = match_querystring
        self.call_count = 0
        
        # Set default content type
        if json is not None and 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'
        elif 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = content_type
    
    def matches(self, method: str, url: str) -> bool:
        """Check if this response matches the given request."""
        # Check method
        if self.method != 'ANY' and self.method != method.upper():
            return False
        
        # Check URL
        if isinstance(self.url, re.Pattern):
            if not self.url.match(url):
                return False
        else:
            if self.match_querystring:
                # Exact match including query string
                if self.url != url:
                    return False
            else:
                # Match without query string
                request_base = url.split('?')[0]
                response_base = self.url.split('?')[0] if isinstance(self.url, str) else self.url
                if request_base != response_base:
                    return False
        
        return True
    
    def get_response(self, request=None):
        """Get the response body."""
        self.call_count += 1
        
        if callable(self._body):
            # Dynamic response
            body = self._body(request)
        elif self._json is not None:
            # JSON response
            body = json.dumps(self._json)
        else:
            body = self._body
        
        # Convert to bytes if needed
        if isinstance(body, str):
            body = body.encode('utf-8')
        elif not isinstance(body, bytes):
            body = str(body).encode('utf-8')
        
        return body


class RequestsMock:
    """Mock for requests library."""
    
    def __init__(self):
        self._responses = []
        self.calls = CallList()
        self._real_request = None
        self._is_started = False
    
    def add(
        self,
        method: str = 'GET',
        url: Union[str, re.Pattern] = '',
        body: Union[str, bytes, dict, Callable] = '',
        json: Optional[dict] = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: str = 'text/plain',
        stream: bool = False,
        match_querystring: bool = False,
    ):
        """Add a mocked response."""
        response = Response(
            method=method,
            url=url,
            body=body,
            json=json,
            status=status,
            headers=headers,
            content_type=content_type,
            stream=stream,
            match_querystring=match_querystring,
        )
        self._responses.append(response)
        return response
    
    def add_callback(
        self,
        method: str,
        url: Union[str, re.Pattern],
        callback: Callable,
        content_type: str = 'text/plain',
        match_querystring: bool = False,
    ):
        """Add a callback-based response."""
        return self.add(
            method=method,
            url=url,
            body=callback,
            content_type=content_type,
            match_querystring=match_querystring,
        )
    
    def reset(self):
        """Reset all mocked responses and recorded calls."""
        self._responses.clear()
        self.calls.reset()
    
    def start(self):
        """Start intercepting requests."""
        if self._is_started:
            return
        
        self._is_started = True
        
        # Patch the requests module if available
        try:
            import requests
            self._real_request = requests.request
            requests.request = self._mock_request
            requests.get = lambda url, **kwargs: self._mock_request('GET', url, **kwargs)
            requests.post = lambda url, **kwargs: self._mock_request('POST', url, **kwargs)
            requests.put = lambda url, **kwargs: self._mock_request('PUT', url, **kwargs)
            requests.patch = lambda url, **kwargs: self._mock_request('PATCH', url, **kwargs)
            requests.delete = lambda url, **kwargs: self._mock_request('DELETE', url, **kwargs)
            requests.head = lambda url, **kwargs: self._mock_request('HEAD', url, **kwargs)
            requests.options = lambda url, **kwargs: self._mock_request('OPTIONS', url, **kwargs)
        except ImportError:
            pass
    
    def stop(self):
        """Stop intercepting requests."""
        if not self._is_started:
            return
        
        self._is_started = False
        
        # Restore original requests functions
        if self._real_request:
            try:
                import requests
                requests.request = self._real_request
                # Restore other methods
                requests.get = lambda url, **kwargs: self._real_request('GET', url, **kwargs)
                requests.post = lambda url, **kwargs: self._real_request('POST', url, **kwargs)
                requests.put = lambda url, **kwargs: self._real_request('PUT', url, **kwargs)
                requests.patch = lambda url, **kwargs: self._real_request('PATCH', url, **kwargs)
                requests.delete = lambda url, **kwargs: self._real_request('DELETE', url, **kwargs)
                requests.head = lambda url, **kwargs: self._real_request('HEAD', url, **kwargs)
                requests.options = lambda url, **kwargs: self._real_request('OPTIONS', url, **kwargs)
            except ImportError:
                pass
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
    
    def _mock_request(self, method, url, **kwargs):
        """Mock a request."""
        # Record the call
        call = Call(
            method=method.upper(),
            url=url,
            body=kwargs.get('data') or kwargs.get('json'),
            headers=kwargs.get('headers')
        )
        self.calls.add(call)
        
        # Find matching response
        for response in self._responses:
            if response.matches(method, url):
                body = response.get_response(call.request)
                
                # Create mock response object with proper methods
                class MockResponse:
                    def __init__(self, status, headers, content, url, request_obj):
                        self.status_code = status
                        self.headers = headers
                        self.content = content
                        self.text = content.decode('utf-8') if isinstance(content, bytes) else content
                        self.ok = 200 <= status < 300
                        self.url = url
                        self.request = request_obj
                    
                    def json(self):
                        if isinstance(self.content, bytes):
                            return json.loads(self.content)
                        return json.loads(self.content)
                    
                    def raise_for_status(self):
                        if not self.ok:
                            raise Exception(f"HTTP {self.status_code}")
                
                mock_response = MockResponse(
                    status=response.status,
                    headers=response.headers,
                    content=body,
                    url=url,
                    request_obj=call.request
                )
                
                return mock_response
        
        # No matching response found
        raise ConnectionError(f"Connection refused: No mock registered for {method} {url}")


# Global instance for decorator usage
_default_mock = RequestsMock()


def activate(func=None):
    """
    Decorator to activate response mocking for a test function.
    
    Usage:
        @responses.activate
        def test_something():
            responses.add(...)
    """
    if func is None:
        # Used as context manager
        return _default_mock
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with _default_mock:
            return func(*args, **kwargs)
    
    return wrapper


# Convenience methods for the global instance
def add(*args, **kwargs):
    """Add a response to the global mock."""
    return _default_mock.add(*args, **kwargs)


def add_callback(*args, **kwargs):
    """Add a callback to the global mock."""
    return _default_mock.add_callback(*args, **kwargs)


def reset():
    """Reset the global mock."""
    _default_mock.reset()


def start():
    """Start the global mock."""
    _default_mock.start()


def stop():
    """Stop the global mock."""
    _default_mock.stop()


# Request method constants
GET = 'GET'
POST = 'POST'
PUT = 'PUT'
PATCH = 'PATCH'
DELETE = 'DELETE'
HEAD = 'HEAD'
OPTIONS = 'OPTIONS'


# Example usage
if __name__ == "__main__":
    print("Testing responses emulator...")
    
    # Test without requests library (basic functionality)
    mock = RequestsMock()
    mock.add(method='GET', url='https://api.example.com/users', json={'users': []}, status=200)
    mock.add(method='POST', url='https://api.example.com/users', json={'id': 1, 'name': 'John'}, status=201)
    
    print("Added mock responses:")
    print(f"  - GET https://api.example.com/users")
    print(f"  - POST https://api.example.com/users")
    
    # Test matching
    for response in mock._responses:
        print(f"\nTesting {response.method} {response.url}")
        matches = response.matches('GET', 'https://api.example.com/users')
        print(f"  Matches GET request: {matches}")
    
    print("\n✓ responses emulator basic functionality working!")
    
    # Test with requests if available
    try:
        import requests
        
        print("\nTesting with requests library...")
        with mock:
            resp = requests.get('https://api.example.com/users')
            print(f"  GET status: {resp.status_code}")
            print(f"  GET response: {resp.json()}")
            
            resp = requests.post('https://api.example.com/users', json={'name': 'Jane'})
            print(f"  POST status: {resp.status_code}")
            print(f"  POST response: {resp.json()}")
        
        print("\n✓ responses emulator working with requests library!")
    except ImportError:
        print("\nrequests library not available, skipping integration test")
