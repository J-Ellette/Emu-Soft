"""
Developed by PowerShield, as an alternative to urllib3


urllib3 Emulator - A lightweight implementation of urllib3's core functionality.

This module emulates the essential features of urllib3, a powerful HTTP client library:
- Connection pooling and reuse
- Retry logic with backoff
- Request timeout handling
- HTTP/HTTPS support
- Response handling with proper status codes
- Header management
- URL encoding and query parameters

This emulator provides the core HTTP client functionality without external dependencies,
suitable for environments requiring self-contained implementations.
"""

import http.client
import urllib.parse
import ssl
import time
import socket
from typing import Optional, Dict, Any, Union, Tuple
from collections import defaultdict
import json


class Retry:
    """Retry configuration for failed requests."""
    
    def __init__(
        self,
        total: int = 10,
        connect: Optional[int] = None,
        read: Optional[int] = None,
        redirect: int = 5,
        status: Optional[int] = None,
        backoff_factor: float = 0,
        status_forcelist: Optional[set] = None,
    ):
        """
        Initialize retry configuration.
        
        Args:
            total: Total number of retries
            connect: Number of connection retries
            read: Number of read retries
            redirect: Maximum number of redirects
            status: Number of status retries
            backoff_factor: Backoff factor between retries
            status_forcelist: Set of status codes to force retry
        """
        self.total = total
        self.connect = connect if connect is not None else total
        self.read = read if read is not None else total
        self.redirect = redirect
        self.status = status if status is not None else total
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist or {500, 502, 503, 504}
        
    def sleep_for_retry(self, retry_count: int) -> None:
        """Sleep for calculated backoff time."""
        if self.backoff_factor > 0:
            sleep_time = self.backoff_factor * (2 ** retry_count)
            time.sleep(sleep_time)


class HTTPResponse:
    """HTTP response object mimicking urllib3.response.HTTPResponse."""
    
    def __init__(
        self,
        body: bytes = b"",
        headers: Optional[Dict[str, str]] = None,
        status: int = 200,
        version: int = 11,
        reason: str = "OK",
        preload_content: bool = True,
        original_response: Any = None,
    ):
        """
        Initialize HTTP response.
        
        Args:
            body: Response body as bytes
            headers: Response headers
            status: HTTP status code
            version: HTTP version
            reason: Status reason phrase
            preload_content: Whether to preload content
            original_response: Original response object
        """
        self.data = body
        self.headers = headers or {}
        self.status = status
        self.version = version
        self.reason = reason
        self._body = body
        self._original_response = original_response
        self._preload_content = preload_content
        
    def read(self, amt: Optional[int] = None) -> bytes:
        """
        Read response body.
        
        Args:
            amt: Number of bytes to read (None = all)
            
        Returns:
            Response body bytes
        """
        if amt is None:
            return self.data
        else:
            result = self.data[:amt]
            self.data = self.data[amt:]
            return result
            
    def json(self) -> Any:
        """Parse JSON response body."""
        return json.loads(self.data.decode('utf-8'))
        
    @property
    def text(self) -> str:
        """Get response body as text."""
        return self.data.decode('utf-8')
        
    def getheader(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get header value."""
        return self.headers.get(name.lower(), default)
        
    def getheaders(self) -> Dict[str, str]:
        """Get all headers."""
        return self.headers.copy()


class HTTPConnectionPool:
    """Connection pool for HTTP connections."""
    
    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        timeout: Union[float, Tuple[float, float]] = 5.0,
        maxsize: int = 1,
        block: bool = False,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[Union[Retry, bool, int]] = None,
        scheme: str = "http",
    ):
        """
        Initialize HTTP connection pool.
        
        Args:
            host: Host to connect to
            port: Port number
            timeout: Request timeout
            maxsize: Maximum pool size
            block: Whether to block when pool is full
            headers: Default headers
            retries: Retry configuration
            scheme: http or https
        """
        self.host = host
        self.port = port or (443 if scheme == "https" else 80)
        self.timeout = timeout
        self.maxsize = maxsize
        self.block = block
        self.headers = headers or {}
        self.scheme = scheme
        
        # Setup retries
        if retries is None:
            self.retries = Retry(0)
        elif isinstance(retries, bool):
            self.retries = Retry(3) if retries else Retry(0)
        elif isinstance(retries, int):
            self.retries = Retry(retries)
        else:
            self.retries = retries
            
        # Connection pool
        self._connections = []
        
    def _get_connection(self) -> http.client.HTTPConnection:
        """Get or create HTTP connection."""
        if self._connections:
            return self._connections.pop()
            
        if self.scheme == "https":
            context = ssl.create_default_context()
            return http.client.HTTPSConnection(
                self.host,
                self.port,
                timeout=self.timeout if isinstance(self.timeout, (int, float)) else self.timeout[0],
                context=context
            )
        else:
            return http.client.HTTPConnection(
                self.host,
                self.port,
                timeout=self.timeout if isinstance(self.timeout, (int, float)) else self.timeout[0]
            )
            
    def _return_connection(self, conn: http.client.HTTPConnection) -> None:
        """Return connection to pool."""
        if len(self._connections) < self.maxsize:
            self._connections.append(conn)
        else:
            conn.close()
            
    def urlopen(
        self,
        method: str,
        url: str,
        body: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[Union[Retry, bool, int]] = None,
        redirect: bool = True,
        timeout: Optional[Union[float, Tuple[float, float]]] = None,
        **kwargs
    ) -> HTTPResponse:
        """
        Make HTTP request.
        
        Args:
            method: HTTP method
            url: URL path
            body: Request body
            headers: Request headers
            retries: Retry configuration for this request
            redirect: Whether to follow redirects
            timeout: Request timeout
            **kwargs: Additional arguments
            
        Returns:
            HTTPResponse object
        """
        # Merge headers
        merged_headers = self.headers.copy()
        if headers:
            merged_headers.update(headers)
            
        # Get retry config for this request
        request_retries = retries if retries is not None else self.retries
        if isinstance(request_retries, bool):
            request_retries = Retry(3) if request_retries else Retry(0)
        elif isinstance(request_retries, int):
            request_retries = Retry(request_retries)
            
        retry_count = 0
        last_exception = None
        
        while retry_count <= request_retries.total:
            try:
                conn = self._get_connection()
                
                # Make request
                if body is not None:
                    if isinstance(body, str):
                        body = body.encode('utf-8')
                    merged_headers['Content-Length'] = str(len(body))
                    
                conn.request(method, url, body, merged_headers)
                response = conn.getresponse()
                
                # Read response
                response_body = response.read()
                response_headers = {k.lower(): v for k, v in response.getheaders()}
                
                # Return connection to pool
                self._return_connection(conn)
                
                # Check if we should retry based on status
                if response.status in request_retries.status_forcelist and retry_count < request_retries.total:
                    retry_count += 1
                    request_retries.sleep_for_retry(retry_count)
                    continue
                    
                # Handle redirects
                if redirect and response.status in (301, 302, 303, 307, 308):
                    if retry_count < request_retries.redirect:
                        location = response_headers.get('location')
                        if location:
                            # Parse new location
                            parsed = urllib.parse.urlparse(location)
                            if parsed.netloc:
                                # Absolute URL - would need new connection pool
                                # For simplicity, just return the redirect response
                                pass
                            else:
                                # Relative URL
                                retry_count += 1
                                return self.urlopen(method, location, body, headers, retries, redirect, timeout, **kwargs)
                
                return HTTPResponse(
                    body=response_body,
                    headers=response_headers,
                    status=response.status,
                    version=response.version,
                    reason=response.reason,
                    original_response=response,
                )
                
            except (socket.timeout, socket.error, http.client.HTTPException) as e:
                last_exception = e
                retry_count += 1
                if retry_count <= request_retries.total:
                    request_retries.sleep_for_retry(retry_count)
                else:
                    raise
                    
        if last_exception:
            raise last_exception
            
    def request(
        self,
        method: str,
        url: str,
        fields: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HTTPResponse:
        """
        Make HTTP request with optional form fields.
        
        Args:
            method: HTTP method
            url: URL path
            fields: Form fields
            headers: Request headers
            **kwargs: Additional arguments
            
        Returns:
            HTTPResponse object
        """
        body = None
        request_headers = headers.copy() if headers else {}
        
        if fields:
            body = urllib.parse.urlencode(fields)
            request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
        return self.urlopen(method, url, body, request_headers, **kwargs)
        
    def close(self) -> None:
        """Close all connections in pool."""
        for conn in self._connections:
            conn.close()
        self._connections.clear()


class PoolManager:
    """Manager for multiple connection pools."""
    
    def __init__(
        self,
        num_pools: int = 10,
        headers: Optional[Dict[str, str]] = None,
        timeout: Union[float, Tuple[float, float]] = 5.0,
        retries: Optional[Union[Retry, bool, int]] = None,
        **connection_pool_kw
    ):
        """
        Initialize pool manager.
        
        Args:
            num_pools: Maximum number of pools
            headers: Default headers
            timeout: Request timeout
            retries: Retry configuration
            **connection_pool_kw: Additional pool arguments
        """
        self.num_pools = num_pools
        self.headers = headers or {}
        self.timeout = timeout
        self.retries = retries
        self.connection_pool_kw = connection_pool_kw
        self._pools = {}
        
    def _get_pool_key(self, scheme: str, host: str, port: int) -> Tuple[str, str, int]:
        """Get pool key for connection pooling."""
        return (scheme, host, port)
        
    def connection_from_host(
        self,
        host: str,
        port: Optional[int] = None,
        scheme: str = "http",
        pool_kwargs: Optional[Dict] = None,
    ) -> HTTPConnectionPool:
        """
        Get or create connection pool for host.
        
        Args:
            host: Host to connect to
            port: Port number
            scheme: http or https
            pool_kwargs: Additional pool arguments
            
        Returns:
            HTTPConnectionPool instance
        """
        port = port or (443 if scheme == "https" else 80)
        pool_key = self._get_pool_key(scheme, host, port)
        
        if pool_key not in self._pools:
            # Create new pool
            kwargs = self.connection_pool_kw.copy()
            if pool_kwargs:
                kwargs.update(pool_kwargs)
                
            self._pools[pool_key] = HTTPConnectionPool(
                host=host,
                port=port,
                timeout=self.timeout,
                headers=self.headers,
                retries=self.retries,
                scheme=scheme,
                **kwargs
            )
            
        return self._pools[pool_key]
        
    def urlopen(
        self,
        method: str,
        url: str,
        redirect: bool = True,
        **kw
    ) -> HTTPResponse:
        """
        Make HTTP request using appropriate pool.
        
        Args:
            method: HTTP method
            url: Full URL
            redirect: Whether to follow redirects
            **kw: Additional arguments
            
        Returns:
            HTTPResponse object
        """
        # Parse URL
        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme or "http"
        host = parsed.hostname
        port = parsed.port
        path = parsed.path or "/"
        
        if parsed.query:
            path = f"{path}?{parsed.query}"
            
        # Get pool
        pool = self.connection_from_host(host, port, scheme)
        
        # Make request
        return pool.urlopen(method, path, redirect=redirect, **kw)
        
    def request(
        self,
        method: str,
        url: str,
        fields: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HTTPResponse:
        """
        Make HTTP request.
        
        Args:
            method: HTTP method
            url: Full URL
            fields: Form fields
            headers: Request headers
            **kwargs: Additional arguments
            
        Returns:
            HTTPResponse object
        """
        return self.urlopen(method, url, fields=fields, headers=headers, **kwargs)
        
    def clear(self) -> None:
        """Close all pools."""
        for pool in self._pools.values():
            pool.close()
        self._pools.clear()


# Convenience functions
def request(
    method: str,
    url: str,
    fields: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    **kwargs
) -> HTTPResponse:
    """
    Make a single HTTP request.
    
    Args:
        method: HTTP method
        url: Full URL
        fields: Form fields
        headers: Request headers
        **kwargs: Additional arguments
        
    Returns:
        HTTPResponse object
    """
    manager = PoolManager()
    return manager.request(method, url, fields, headers, **kwargs)


# Main entry point for testing
if __name__ == "__main__":
    print("urllib3 Emulator - Testing basic functionality")
    print("=" * 60)
    
    # Test 1: Simple GET request
    print("\n1. Testing simple GET request...")
    try:
        http = PoolManager()
        resp = http.request('GET', 'http://httpbin.org/get')
        print(f"   Status: {resp.status}")
        print(f"   Reason: {resp.reason}")
        print(f"   Content-Type: {resp.getheader('content-type')}")
        print("   ✓ GET request successful")
    except Exception as e:
        print(f"   ✗ GET request failed: {e}")
    
    # Test 2: POST request with data
    print("\n2. Testing POST request with data...")
    try:
        http = PoolManager()
        resp = http.request(
            'POST',
            'http://httpbin.org/post',
            fields={'key': 'value', 'test': 'data'}
        )
        print(f"   Status: {resp.status}")
        print("   ✓ POST request successful")
    except Exception as e:
        print(f"   ✗ POST request failed: {e}")
    
    # Test 3: Retry logic
    print("\n3. Testing retry configuration...")
    try:
        retry = Retry(total=3, backoff_factor=0.1)
        print(f"   Retry config: total={retry.total}, backoff={retry.backoff_factor}")
        print("   ✓ Retry configuration working")
    except Exception as e:
        print(f"   ✗ Retry configuration failed: {e}")
    
    # Test 4: Connection pooling
    print("\n4. Testing connection pooling...")
    try:
        pool = HTTPConnectionPool('httpbin.org', port=80)
        resp1 = pool.urlopen('GET', '/get')
        resp2 = pool.urlopen('GET', '/headers')
        print(f"   Request 1 status: {resp1.status}")
        print(f"   Request 2 status: {resp2.status}")
        pool.close()
        print("   ✓ Connection pooling working")
    except Exception as e:
        print(f"   ✗ Connection pooling failed: {e}")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
