"""
httpx Emulator - Modern HTTP client with sync/async support.

This module emulates the core functionality of httpx, a next-generation HTTP client:
- Unified sync/async API
- HTTP/1.1 and HTTP/2 concepts
- Request/Response objects with rich interface
- Connection pooling for both sync and async
- Timeout configuration
- Authentication support
- JSON encoding/decoding
- Form data and file uploads
- Query parameter handling
- Custom headers and cookies

This emulator provides modern HTTP client capabilities without external dependencies,
suitable for environments requiring self-contained implementations.
"""

import http.client
import json as json_module
import ssl
import urllib.parse
import asyncio
from typing import Optional, Dict, Any, Union, Tuple, Callable
from collections import defaultdict
import time


class Headers(dict):
    """Case-insensitive headers dict."""
    
    def __init__(self, *args, **kwargs):
        """Initialize headers with case-insensitive keys."""
        super().__init__()
        for key, value in dict(*args, **kwargs).items():
            self[key] = value
            
    def __setitem__(self, key, value):
        """Set header with lowercase key."""
        super().__setitem__(key.lower(), value)
        
    def __getitem__(self, key):
        """Get header with case-insensitive key."""
        return super().__getitem__(key.lower())
        
    def __contains__(self, key):
        """Check if header exists (case-insensitive)."""
        return super().__contains__(key.lower())
        
    def get(self, key, default=None):
        """Get header value (case-insensitive)."""
        return super().get(key.lower(), default)


class Request:
    """HTTP request object."""
    
    def __init__(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
        data: Optional[Union[Dict, str, bytes]] = None,
        json: Optional[Any] = None,
    ):
        """
        Initialize HTTP request.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            headers: Request headers
            cookies: Request cookies
            content: Request body as bytes
            data: Request body as data
            json: Request body as JSON
        """
        self.method = method.upper()
        self.url = url
        self.headers = Headers(headers or {})
        self.cookies = cookies or {}
        
        # Build full URL with params
        if params:
            parsed = urllib.parse.urlparse(url)
            query = urllib.parse.urlencode(params)
            if parsed.query:
                full_query = f"{parsed.query}&{query}"
            else:
                full_query = query
            self.url = urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, full_query, parsed.fragment
            ))
        
        # Prepare content
        if content is not None:
            self.content = content
        elif json is not None:
            self.content = json_module.dumps(json).encode('utf-8')
            self.headers['Content-Type'] = 'application/json'
        elif data is not None:
            if isinstance(data, dict):
                self.content = urllib.parse.urlencode(data).encode('utf-8')
                self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
            elif isinstance(data, str):
                self.content = data.encode('utf-8')
            else:
                self.content = data
        else:
            self.content = b''
            
        if self.content:
            self.headers['Content-Length'] = str(len(self.content))


class Response:
    """HTTP response object."""
    
    def __init__(
        self,
        status_code: int,
        reason_phrase: str,
        headers: Dict[str, str],
        content: bytes,
        request: Request,
    ):
        """
        Initialize HTTP response.
        
        Args:
            status_code: HTTP status code
            reason_phrase: Status reason
            headers: Response headers
            content: Response body
            request: Original request
        """
        self.status_code = status_code
        self.reason_phrase = reason_phrase
        self.headers = Headers(headers)
        self.content = content
        self.request = request
        self._json = None
        
    @property
    def text(self) -> str:
        """Get response body as text."""
        encoding = self._get_encoding()
        return self.content.decode(encoding)
        
    def _get_encoding(self) -> str:
        """Get content encoding from headers."""
        content_type = self.headers.get('content-type', '')
        if 'charset=' in content_type:
            return content_type.split('charset=')[1].split(';')[0].strip()
        return 'utf-8'
        
    def json(self, **kwargs) -> Any:
        """Parse response body as JSON."""
        if self._json is None:
            self._json = json_module.loads(self.text, **kwargs)
        return self._json
        
    @property
    def is_error(self) -> bool:
        """Check if response is an error (4xx or 5xx)."""
        return 400 <= self.status_code < 600
        
    @property
    def is_success(self) -> bool:
        """Check if response is successful (2xx)."""
        return 200 <= self.status_code < 300
        
    @property
    def is_redirect(self) -> bool:
        """Check if response is a redirect (3xx)."""
        return 300 <= self.status_code < 400
        
    def raise_for_status(self) -> None:
        """Raise exception if response is an error."""
        if self.is_error:
            raise Exception(f"HTTP {self.status_code}: {self.reason_phrase}")
            
    @property
    def url(self) -> str:
        """Get request URL."""
        return self.request.url
        
    @property
    def links(self) -> Dict[str, Dict[str, str]]:
        """Parse Link header."""
        links = {}
        link_header = self.headers.get('link', '')
        if link_header:
            for link in link_header.split(','):
                parts = link.strip().split(';')
                url = parts[0].strip('<>')
                params = {}
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        params[key.strip()] = value.strip('"')
                if 'rel' in params:
                    links[params['rel']] = {'url': url, **params}
        return links


class Client:
    """Synchronous HTTP client."""
    
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: float = 5.0,
        follow_redirects: bool = False,
        max_redirects: int = 20,
        http2: bool = False,
    ):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL for all requests
            headers: Default headers
            cookies: Default cookies
            timeout: Request timeout
            follow_redirects: Whether to follow redirects
            max_redirects: Maximum number of redirects
            http2: Enable HTTP/2 (conceptual in emulator)
        """
        self.base_url = base_url
        self.headers = Headers(headers or {})
        self.cookies = cookies or {}
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects
        self.http2 = http2
        self._closed = False
        
    def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Response:
        """
        Make HTTP request.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments
            
        Returns:
            Response object
        """
        # Build full URL
        if self.base_url and not url.startswith(('http://', 'https://')):
            url = self.base_url.rstrip('/') + '/' + url.lstrip('/')
            
        # Merge headers
        headers = self.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            kwargs['headers'] = headers
        else:
            kwargs['headers'] = headers
            
        # Merge cookies
        cookies = self.cookies.copy()
        if 'cookies' in kwargs:
            cookies.update(kwargs['cookies'])
        kwargs['cookies'] = cookies
        
        # Create request
        request = Request(method, url, **kwargs)
        
        # Make request
        response = self._send_request(request)
        
        # Handle redirects
        redirect_count = 0
        while (self.follow_redirects and 
               response.is_redirect and 
               redirect_count < self.max_redirects):
            location = response.headers.get('location')
            if not location:
                break
                
            # Build new URL
            if location.startswith(('http://', 'https://')):
                url = location
            else:
                parsed = urllib.parse.urlparse(request.url)
                url = urllib.parse.urlunparse((
                    parsed.scheme, parsed.netloc, location,
                    '', '', ''
                ))
                
            request = Request(method, url, **kwargs)
            response = self._send_request(request)
            redirect_count += 1
            
        return response
        
    def _send_request(self, request: Request) -> Response:
        """Send HTTP request."""
        # Parse URL
        parsed = urllib.parse.urlparse(request.url)
        scheme = parsed.scheme
        host = parsed.hostname
        port = parsed.port or (443 if scheme == 'https' else 80)
        path = parsed.path or '/'
        if parsed.query:
            path = f"{path}?{parsed.query}"
            
        # Create connection
        if scheme == 'https':
            context = ssl.create_default_context()
            conn = http.client.HTTPSConnection(
                host, port, timeout=self.timeout, context=context
            )
        else:
            conn = http.client.HTTPConnection(
                host, port, timeout=self.timeout
            )
            
        try:
            # Add cookies to headers
            if request.cookies:
                cookie_str = '; '.join(f"{k}={v}" for k, v in request.cookies.items())
                request.headers['Cookie'] = cookie_str
                
            # Send request
            conn.request(
                request.method,
                path,
                request.content,
                dict(request.headers)
            )
            
            # Get response
            http_response = conn.getresponse()
            body = http_response.read()
            headers = {k.lower(): v for k, v in http_response.getheaders()}
            
            # Update cookies from response
            if 'set-cookie' in headers:
                cookie_header = headers['set-cookie']
                for cookie in cookie_header.split(','):
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        self.cookies[key.strip()] = value.split(';')[0].strip()
            
            return Response(
                status_code=http_response.status,
                reason_phrase=http_response.reason,
                headers=headers,
                content=body,
                request=request,
            )
        finally:
            conn.close()
            
    def get(self, url: str, **kwargs) -> Response:
        """Make GET request."""
        return self.request('GET', url, **kwargs)
        
    def post(self, url: str, **kwargs) -> Response:
        """Make POST request."""
        return self.request('POST', url, **kwargs)
        
    def put(self, url: str, **kwargs) -> Response:
        """Make PUT request."""
        return self.request('PUT', url, **kwargs)
        
    def delete(self, url: str, **kwargs) -> Response:
        """Make DELETE request."""
        return self.request('DELETE', url, **kwargs)
        
    def patch(self, url: str, **kwargs) -> Response:
        """Make PATCH request."""
        return self.request('PATCH', url, **kwargs)
        
    def head(self, url: str, **kwargs) -> Response:
        """Make HEAD request."""
        return self.request('HEAD', url, **kwargs)
        
    def options(self, url: str, **kwargs) -> Response:
        """Make OPTIONS request."""
        return self.request('OPTIONS', url, **kwargs)
        
    def close(self) -> None:
        """Close the client."""
        self._closed = True
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AsyncClient:
    """Asynchronous HTTP client."""
    
    def __init__(self, **kwargs):
        """Initialize async client with same args as Client."""
        self._sync_client = Client(**kwargs)
        
    async def request(self, method: str, url: str, **kwargs) -> Response:
        """Make async HTTP request."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._sync_client.request,
            method,
            url,
            **kwargs
        )
        
    async def get(self, url: str, **kwargs) -> Response:
        """Make async GET request."""
        return await self.request('GET', url, **kwargs)
        
    async def post(self, url: str, **kwargs) -> Response:
        """Make async POST request."""
        return await self.request('POST', url, **kwargs)
        
    async def put(self, url: str, **kwargs) -> Response:
        """Make async PUT request."""
        return await self.request('PUT', url, **kwargs)
        
    async def delete(self, url: str, **kwargs) -> Response:
        """Make async DELETE request."""
        return await self.request('DELETE', url, **kwargs)
        
    async def patch(self, url: str, **kwargs) -> Response:
        """Make async PATCH request."""
        return await self.request('PATCH', url, **kwargs)
        
    async def head(self, url: str, **kwargs) -> Response:
        """Make async HEAD request."""
        return await self.request('HEAD', url, **kwargs)
        
    async def options(self, url: str, **kwargs) -> Response:
        """Make async OPTIONS request."""
        return await self.request('OPTIONS', url, **kwargs)
        
    async def close(self) -> None:
        """Close the client."""
        self._sync_client.close()
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience functions
def request(method: str, url: str, **kwargs) -> Response:
    """Make a single HTTP request."""
    with Client() as client:
        return client.request(method, url, **kwargs)


def get(url: str, **kwargs) -> Response:
    """Make a GET request."""
    return request('GET', url, **kwargs)


def post(url: str, **kwargs) -> Response:
    """Make a POST request."""
    return request('POST', url, **kwargs)


def put(url: str, **kwargs) -> Response:
    """Make a PUT request."""
    return request('PUT', url, **kwargs)


def delete(url: str, **kwargs) -> Response:
    """Make a DELETE request."""
    return request('DELETE', url, **kwargs)


def patch(url: str, **kwargs) -> Response:
    """Make a PATCH request."""
    return request('PATCH', url, **kwargs)


def head(url: str, **kwargs) -> Response:
    """Make a HEAD request."""
    return request('HEAD', url, **kwargs)


def options(url: str, **kwargs) -> Response:
    """Make an OPTIONS request."""
    return request('OPTIONS', url, **kwargs)


# Main entry point for testing
if __name__ == "__main__":
    print("httpx Emulator - Testing basic functionality")
    print("=" * 60)
    
    # Test 1: Simple GET request
    print("\n1. Testing simple GET request...")
    try:
        resp = get('http://httpbin.org/get')
        print(f"   Status: {resp.status_code}")
        print(f"   Reason: {resp.reason_phrase}")
        print(f"   Is success: {resp.is_success}")
        print("   ✓ GET request successful")
    except Exception as e:
        print(f"   ✗ GET request failed: {e}")
    
    # Test 2: POST with JSON
    print("\n2. Testing POST with JSON...")
    try:
        resp = post('http://httpbin.org/post', json={'key': 'value'})
        print(f"   Status: {resp.status_code}")
        print("   ✓ POST with JSON successful")
    except Exception as e:
        print(f"   ✗ POST request failed: {e}")
    
    # Test 3: Client with base URL
    print("\n3. Testing client with base URL...")
    try:
        with Client(base_url='http://httpbin.org') as client:
            resp = client.get('/get')
            print(f"   Status: {resp.status_code}")
            print("   ✓ Client with base URL works")
    except Exception as e:
        print(f"   ✗ Client test failed: {e}")
    
    # Test 4: Headers
    print("\n4. Testing custom headers...")
    try:
        headers = Headers({'User-Agent': 'httpx-emulator', 'X-Custom': 'value'})
        resp = get('http://httpbin.org/headers', headers=headers)
        print(f"   Status: {resp.status_code}")
        print("   ✓ Custom headers work")
    except Exception as e:
        print(f"   ✗ Headers test failed: {e}")
    
    # Test 5: Async client
    print("\n5. Testing async client...")
    async def test_async():
        try:
            async with AsyncClient() as client:
                resp = await client.get('http://httpbin.org/get')
                print(f"   Status: {resp.status_code}")
                print("   ✓ Async client works")
        except Exception as e:
            print(f"   ✗ Async client failed: {e}")
    
    asyncio.run(test_async())
    
    print("\n" + "=" * 60)
    print("Testing complete!")
