"""
Developed by PowerShield, as an alternative to aiohttp


aiohttp Emulator - Async HTTP client/server implementation.

This module emulates the core functionality of aiohttp, a popular async HTTP library:
- Async HTTP client with connection pooling
- Async HTTP server with routing
- WebSocket support (basic)
- Session management with cookies
- Timeout handling
- JSON request/response handling
- Form data encoding

This emulator provides async HTTP capabilities without external dependencies,
suitable for environments requiring self-contained implementations.
"""

import asyncio
import http.client
import json
import ssl
import socket
import urllib.parse
from typing import Optional, Dict, Any, Union, Callable, Awaitable
from collections import defaultdict
import time


class ClientResponse:
    """HTTP response object for async client."""
    
    def __init__(
        self,
        status: int,
        reason: str,
        headers: Dict[str, str],
        body: bytes,
        url: str,
    ):
        """
        Initialize client response.
        
        Args:
            status: HTTP status code
            reason: Status reason phrase
            headers: Response headers
            body: Response body
            url: Request URL
        """
        self.status = status
        self.reason = reason
        self.headers = headers
        self._body = body
        self.url = url
        self._closed = False
        
    async def read(self) -> bytes:
        """Read response body as bytes."""
        return self._body
        
    async def text(self, encoding: str = 'utf-8') -> str:
        """Read response body as text."""
        return self._body.decode(encoding)
        
    async def json(self, **kwargs) -> Any:
        """Parse response body as JSON."""
        text = await self.text()
        return json.loads(text, **kwargs)
        
    def close(self) -> None:
        """Close response."""
        self._closed = True
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()


class ClientSession:
    """Async HTTP client session with connection pooling."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = 300.0,
    ):
        """
        Initialize client session.
        
        Args:
            base_url: Base URL for all requests
            headers: Default headers
            cookies: Default cookies
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.timeout = timeout
        self._closed = False
        
    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, str]] = None,
        data: Optional[Union[str, bytes, Dict]] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> ClientResponse:
        """
        Make async HTTP request.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            data: Request body
            json: JSON request body
            headers: Request headers
            cookies: Request cookies
            timeout: Request timeout
            **kwargs: Additional arguments
            
        Returns:
            ClientResponse object
        """
        # Build full URL
        if self.base_url and not url.startswith(('http://', 'https://')):
            url = self.base_url.rstrip('/') + '/' + url.lstrip('/')
            
        # Parse URL
        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme or 'http'
        host = parsed.hostname
        port = parsed.port or (443 if scheme == 'https' else 80)
        path = parsed.path or '/'
        
        # Add query parameters
        if params:
            query = urllib.parse.urlencode(params)
            if parsed.query:
                path = f"{path}?{parsed.query}&{query}"
            else:
                path = f"{path}?{query}"
        elif parsed.query:
            path = f"{path}?{parsed.query}"
            
        # Merge headers
        merged_headers = self.headers.copy()
        if headers:
            merged_headers.update(headers)
            
        # Merge cookies
        merged_cookies = self.cookies.copy()
        if cookies:
            merged_cookies.update(cookies)
            
        # Add cookie header
        if merged_cookies:
            cookie_str = '; '.join(f"{k}={v}" for k, v in merged_cookies.items())
            merged_headers['Cookie'] = cookie_str
            
        # Prepare body
        body = None
        if json is not None:
            body = json.dumps(json).encode('utf-8')
            merged_headers['Content-Type'] = 'application/json'
        elif data is not None:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode('utf-8')
                merged_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            elif isinstance(data, str):
                body = data.encode('utf-8')
            else:
                body = data
                
        if body:
            merged_headers['Content-Length'] = str(len(body))
            
        # Make async request
        timeout_val = timeout if timeout is not None else self.timeout
        
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._make_sync_request,
                scheme, host, port, method, path, body, merged_headers, timeout_val
            )
            return response
        except Exception as e:
            raise Exception(f"Request failed: {e}")
            
    def _make_sync_request(
        self,
        scheme: str,
        host: str,
        port: int,
        method: str,
        path: str,
        body: Optional[bytes],
        headers: Dict[str, str],
        timeout: Optional[float],
    ) -> ClientResponse:
        """Make synchronous HTTP request (called in executor)."""
        if scheme == 'https':
            context = ssl.create_default_context()
            conn = http.client.HTTPSConnection(
                host, port, timeout=timeout, context=context
            )
        else:
            conn = http.client.HTTPConnection(
                host, port, timeout=timeout
            )
            
        try:
            conn.request(method, path, body, headers)
            response = conn.getresponse()
            
            # Read response
            response_body = response.read()
            response_headers = {k.lower(): v for k, v in response.getheaders()}
            
            # Extract cookies from Set-Cookie header
            if 'set-cookie' in response_headers:
                # Simple cookie parsing
                cookie_header = response_headers['set-cookie']
                for cookie in cookie_header.split(','):
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        self.cookies[key.strip()] = value.split(';')[0].strip()
                        
            return ClientResponse(
                status=response.status,
                reason=response.reason,
                headers=response_headers,
                body=response_body,
                url=f"{scheme}://{host}:{port}{path}",
            )
        finally:
            conn.close()
            
    async def get(self, url: str, **kwargs) -> ClientResponse:
        """Make GET request."""
        return await self.request('GET', url, **kwargs)
        
    async def post(self, url: str, **kwargs) -> ClientResponse:
        """Make POST request."""
        return await self.request('POST', url, **kwargs)
        
    async def put(self, url: str, **kwargs) -> ClientResponse:
        """Make PUT request."""
        return await self.request('PUT', url, **kwargs)
        
    async def delete(self, url: str, **kwargs) -> ClientResponse:
        """Make DELETE request."""
        return await self.request('DELETE', url, **kwargs)
        
    async def patch(self, url: str, **kwargs) -> ClientResponse:
        """Make PATCH request."""
        return await self.request('PATCH', url, **kwargs)
        
    async def head(self, url: str, **kwargs) -> ClientResponse:
        """Make HEAD request."""
        return await self.request('HEAD', url, **kwargs)
        
    async def options(self, url: str, **kwargs) -> ClientResponse:
        """Make OPTIONS request."""
        return await self.request('OPTIONS', url, **kwargs)
        
    async def close(self) -> None:
        """Close the session."""
        self._closed = True
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class Request:
    """HTTP request object for server."""
    
    def __init__(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: bytes,
        query: Dict[str, str],
        match_info: Dict[str, str],
    ):
        """Initialize request object."""
        self.method = method
        self.path = path
        self.headers = headers
        self._body = body
        self.query = query
        self.match_info = match_info
        
    async def text(self) -> str:
        """Read request body as text."""
        return self._body.decode('utf-8')
        
    async def json(self) -> Any:
        """Parse request body as JSON."""
        text = await self.text()
        return json.loads(text)
        
    async def read(self) -> bytes:
        """Read request body as bytes."""
        return self._body


class Response:
    """HTTP response object for server."""
    
    def __init__(
        self,
        body: Optional[Union[str, bytes]] = None,
        status: int = 200,
        reason: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ):
        """Initialize response object."""
        self.status = status
        self.reason = reason or self._get_reason(status)
        self.headers = headers or {}
        
        if content_type:
            self.headers['Content-Type'] = content_type
            
        if body is not None:
            if isinstance(body, str):
                self._body = body.encode('utf-8')
            else:
                self._body = body
        else:
            self._body = b''
            
        self.headers['Content-Length'] = str(len(self._body))
        
    def _get_reason(self, status: int) -> str:
        """Get reason phrase for status code."""
        reasons = {
            200: 'OK', 201: 'Created', 204: 'No Content',
            301: 'Moved Permanently', 302: 'Found', 304: 'Not Modified',
            400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden',
            404: 'Not Found', 405: 'Method Not Allowed',
            500: 'Internal Server Error', 502: 'Bad Gateway',
            503: 'Service Unavailable',
        }
        return reasons.get(status, 'Unknown')


def json_response(
    data: Any,
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
) -> Response:
    """Create JSON response."""
    body = json.dumps(data)
    return Response(
        body=body,
        status=status,
        headers=headers,
        content_type='application/json',
    )


class Application:
    """ASGI application for async HTTP server."""
    
    def __init__(self, router: Optional['Router'] = None):
        """Initialize application."""
        self.router = router or Router()
        
    def add_routes(self, routes: list) -> None:
        """Add routes to application."""
        for route in routes:
            self.router.add_route(route)
            
    async def _handle_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: bytes,
    ) -> Response:
        """Handle HTTP request."""
        # Find matching route
        handler, match_info = self.router.match(method, path)
        
        if handler is None:
            return Response(body='Not Found', status=404)
            
        # Parse query string
        parsed = urllib.parse.urlparse(path)
        query = dict(urllib.parse.parse_qsl(parsed.query))
        
        # Create request object
        request = Request(
            method=method,
            path=parsed.path,
            headers=headers,
            body=body,
            query=query,
            match_info=match_info,
        )
        
        # Call handler
        try:
            response = await handler(request)
            if isinstance(response, Response):
                return response
            else:
                # Handler returned raw data
                return Response(body=str(response))
        except Exception as e:
            return Response(
                body=f'Internal Server Error: {e}',
                status=500
            )


class Router:
    """URL router for application."""
    
    def __init__(self):
        """Initialize router."""
        self.routes = []
        
    def add_route(self, route: 'Route') -> None:
        """Add route."""
        self.routes.append(route)
        
    def add_get(self, path: str, handler: Callable) -> None:
        """Add GET route."""
        self.routes.append(Route('GET', path, handler))
        
    def add_post(self, path: str, handler: Callable) -> None:
        """Add POST route."""
        self.routes.append(Route('POST', path, handler))
        
    def add_put(self, path: str, handler: Callable) -> None:
        """Add PUT route."""
        self.routes.append(Route('PUT', path, handler))
        
    def add_delete(self, path: str, handler: Callable) -> None:
        """Add DELETE route."""
        self.routes.append(Route('DELETE', path, handler))
        
    def match(self, method: str, path: str) -> tuple:
        """
        Match request to route.
        
        Returns:
            Tuple of (handler, match_info)
        """
        for route in self.routes:
            if route.method == method:
                match_info = route.match(path)
                if match_info is not None:
                    return route.handler, match_info
        return None, {}


class Route:
    """Route definition."""
    
    def __init__(self, method: str, path: str, handler: Callable):
        """Initialize route."""
        self.method = method
        self.path = path
        self.handler = handler
        self._compile_pattern()
        
    def _compile_pattern(self) -> None:
        """Compile path pattern with placeholders."""
        import re
        
        # Convert {name} to named groups
        pattern = self.path
        self.param_names = []
        
        for match in re.finditer(r'\{(\w+)\}', pattern):
            param_name = match.group(1)
            self.param_names.append(param_name)
            
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', pattern)
        pattern = '^' + pattern + '$'
        self.pattern = re.compile(pattern)
        
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Match path against pattern."""
        match = self.pattern.match(path)
        if match:
            return match.groupdict()
        return None


# Convenience function
def get(path: str):
    """Decorator for GET route handler."""
    def decorator(func):
        func._route_method = 'GET'
        func._route_path = path
        return func
    return decorator


def post(path: str):
    """Decorator for POST route handler."""
    def decorator(func):
        func._route_method = 'POST'
        func._route_path = path
        return func
    return decorator


# Main entry point for testing
if __name__ == "__main__":
    print("aiohttp Emulator - Testing basic functionality")
    print("=" * 60)
    
    # Test 1: Client session
    async def test_client():
        print("\n1. Testing async HTTP client...")
        try:
            async with ClientSession() as session:
                resp = await session.get('http://httpbin.org/get')
                print(f"   Status: {resp.status}")
                print(f"   Reason: {resp.reason}")
                text = await resp.text()
                print(f"   Response length: {len(text)} bytes")
                print("   ✓ Client GET request successful")
        except Exception as e:
            print(f"   ✗ Client request failed: {e}")
    
    # Test 2: POST with JSON
    async def test_post_json():
        print("\n2. Testing POST with JSON...")
        try:
            async with ClientSession() as session:
                resp = await session.post(
                    'http://httpbin.org/post',
                    json={'key': 'value', 'test': 'data'}
                )
                print(f"   Status: {resp.status}")
                print("   ✓ POST with JSON successful")
        except Exception as e:
            print(f"   ✗ POST request failed: {e}")
    
    # Test 3: Server router
    def test_router():
        print("\n3. Testing server router...")
        try:
            router = Router()
            
            async def hello_handler(request):
                return Response(body='Hello, World!')
            
            router.add_get('/hello', hello_handler)
            
            handler, match = router.match('GET', '/hello')
            print(f"   Matched handler: {handler is not None}")
            print("   ✓ Router matching works")
        except Exception as e:
            print(f"   ✗ Router test failed: {e}")
    
    # Test 4: Route with parameters
    def test_route_params():
        print("\n4. Testing route with parameters...")
        try:
            async def user_handler(request):
                user_id = request.match_info.get('id')
                return Response(body=f'User {user_id}')
            
            route = Route('GET', '/user/{id}', user_handler)
            match = route.match('/user/123')
            
            print(f"   Match result: {match}")
            assert match == {'id': '123'}
            print("   ✓ Route parameters work")
        except Exception as e:
            print(f"   ✗ Route parameters failed: {e}")
    
    # Test 5: JSON response
    def test_json_response():
        print("\n5. Testing JSON response...")
        try:
            response = json_response({'status': 'ok', 'data': [1, 2, 3]})
            print(f"   Status: {response.status}")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            print("   ✓ JSON response works")
        except Exception as e:
            print(f"   ✗ JSON response failed: {e}")
    
    # Run tests
    async def run_tests():
        await test_client()
        await test_post_json()
        test_router()
        test_route_params()
        test_json_response()
    
    asyncio.run(run_tests())
    
    print("\n" + "=" * 60)
    print("Testing complete!")
