"""
Developed by PowerShield, as an alternative to Requests


Requests Emulator - HTTP Library
Emulates the popular requests library for making HTTP requests
"""

import socket
import json
import urllib.parse
from typing import Dict, Optional, Any, Union, Tuple
from http.client import HTTPConnection, HTTPSConnection, HTTPResponse as StdHTTPResponse
import io


class Response:
    """HTTP Response object"""
    
    def __init__(self):
        self.status_code: int = 0
        self.reason: str = ""
        self.headers: Dict[str, str] = {}
        self._content: bytes = b""
        self._encoding: Optional[str] = None
        self.url: str = ""
        self.request = None
        self.history: list = []
    
    @property
    def content(self) -> bytes:
        """Response content in bytes"""
        return self._content
    
    @property
    def text(self) -> str:
        """Response content as string"""
        encoding = self.encoding or 'utf-8'
        return self._content.decode(encoding, errors='replace')
    
    @property
    def encoding(self) -> Optional[str]:
        """Get or detect encoding"""
        if self._encoding:
            return self._encoding
        
        # Try to get from Content-Type header
        content_type = self.headers.get('content-type', '').lower()
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[1].split(';')[0].strip()
            return charset
        
        return 'utf-8'
    
    @encoding.setter
    def encoding(self, value: str):
        """Set encoding"""
        self._encoding = value
    
    def json(self, **kwargs) -> Any:
        """Parse JSON response"""
        return json.loads(self.text, **kwargs)
    
    @property
    def ok(self) -> bool:
        """True if status code is less than 400"""
        return 200 <= self.status_code < 400
    
    def raise_for_status(self):
        """Raise HTTPError for bad status codes"""
        if not self.ok:
            raise HTTPError(f"{self.status_code} Error: {self.reason}", response=self)


class Request:
    """HTTP Request object"""
    
    def __init__(self, method: str, url: str, headers: Optional[Dict] = None,
                 data: Optional[Union[str, bytes, Dict]] = None,
                 json_data: Optional[Any] = None,
                 params: Optional[Dict] = None):
        self.method = method.upper()
        self.url = url
        self.headers = headers or {}
        self.data = data
        self.json_data = json_data
        self.params = params


class HTTPError(Exception):
    """HTTP error exception"""
    
    def __init__(self, message: str, response: Optional[Response] = None):
        super().__init__(message)
        self.response = response


class Session:
    """HTTP Session for persistent connections"""
    
    def __init__(self):
        self.headers: Dict[str, str] = {}
        self.cookies: Dict[str, str] = {}
        self.auth: Optional[Tuple[str, str]] = None
        self.verify: bool = True
        self.proxies: Dict[str, str] = {}
        self.timeout: Optional[float] = None
    
    def request(self, method: str, url: str, **kwargs) -> Response:
        """Make HTTP request with session settings"""
        # Merge session headers with request headers
        headers = self.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        # Add session cookies
        if self.cookies:
            cookie_header = '; '.join([f"{k}={v}" for k, v in self.cookies.items()])
            if 'Cookie' in headers:
                headers['Cookie'] += '; ' + cookie_header
            else:
                headers['Cookie'] = cookie_header
        
        # Add session auth
        if self.auth and 'auth' not in kwargs:
            kwargs['auth'] = self.auth
        
        # Add session timeout
        if self.timeout and 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        # Make request
        response = request(method, url, **kwargs)
        
        # Update session cookies from response
        if 'set-cookie' in response.headers:
            cookie_str = response.headers['set-cookie']
            # Simple cookie parsing
            for part in cookie_str.split(';'):
                if '=' in part:
                    key, value = part.split('=', 1)
                    self.cookies[key.strip()] = value.strip()
        
        return response
    
    def get(self, url: str, **kwargs) -> Response:
        """GET request"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Response:
        """POST request"""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> Response:
        """PUT request"""
        return self.request('PUT', url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> Response:
        """PATCH request"""
        return self.request('PATCH', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Response:
        """DELETE request"""
        return self.request('DELETE', url, **kwargs)
    
    def head(self, url: str, **kwargs) -> Response:
        """HEAD request"""
        return self.request('HEAD', url, **kwargs)
    
    def options(self, url: str, **kwargs) -> Response:
        """OPTIONS request"""
        return self.request('OPTIONS', url, **kwargs)
    
    def close(self):
        """Close session (no-op for simplicity)"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


def request(method: str, url: str, 
           params: Optional[Dict] = None,
           data: Optional[Union[str, bytes, Dict]] = None,
           json: Optional[Any] = None,
           headers: Optional[Dict] = None,
           cookies: Optional[Dict] = None,
           auth: Optional[Tuple[str, str]] = None,
           timeout: Optional[float] = None,
           allow_redirects: bool = True,
           verify: bool = True,
           **kwargs) -> Response:
    """
    Make an HTTP request
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        params: URL parameters
        data: Request body (form data or raw)
        json: JSON data to send
        headers: HTTP headers
        cookies: Cookies to send
        auth: (username, password) tuple for basic auth
        timeout: Request timeout in seconds
        allow_redirects: Follow redirects
        verify: Verify SSL certificates (not implemented)
        
    Returns:
        Response object
    """
    # Parse URL
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme or 'http'
    host = parsed.hostname
    port = parsed.port or (443 if scheme == 'https' else 80)
    path = parsed.path or '/'
    
    # Add query parameters
    if params:
        query_string = urllib.parse.urlencode(params)
        if parsed.query:
            path += f"?{parsed.query}&{query_string}"
        else:
            path += f"?{query_string}"
    elif parsed.query:
        path += f"?{parsed.query}"
    
    # Prepare headers
    request_headers = {
        'Host': host,
        'User-Agent': 'Python-Requests-Emulator/1.0',
        'Accept': '*/*',
        'Connection': 'close'
    }
    
    if headers:
        request_headers.update(headers)
    
    # Add cookies
    if cookies:
        cookie_header = '; '.join([f"{k}={v}" for k, v in cookies.items()])
        request_headers['Cookie'] = cookie_header
    
    # Prepare body
    body = None
    if json is not None:
        body = json.dumps(json).encode('utf-8')
        request_headers['Content-Type'] = 'application/json'
        request_headers['Content-Length'] = str(len(body))
    elif data is not None:
        if isinstance(data, dict):
            # Form data
            body = urllib.parse.urlencode(data).encode('utf-8')
            request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        elif isinstance(data, str):
            body = data.encode('utf-8')
        else:
            body = data
        
        if body:
            request_headers['Content-Length'] = str(len(body))
    
    # Add basic auth
    if auth:
        import base64
        username, password = auth
        credentials = f"{username}:{password}".encode('utf-8')
        b64_credentials = base64.b64encode(credentials).decode('ascii')
        request_headers['Authorization'] = f"Basic {b64_credentials}"
    
    # Make connection
    if scheme == 'https':
        # Note: SSL verification not fully implemented
        try:
            import ssl
            context = ssl.create_default_context()
            if not verify:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            conn = HTTPSConnection(host, port, timeout=timeout, context=context)
        except:
            conn = HTTPSConnection(host, port, timeout=timeout)
    else:
        conn = HTTPConnection(host, port, timeout=timeout)
    
    try:
        # Send request
        conn.request(method, path, body=body, headers=request_headers)
        
        # Get response
        http_response = conn.getresponse()
        
        # Create Response object
        response = Response()
        response.status_code = http_response.status
        response.reason = http_response.reason
        response.url = url
        
        # Get headers
        for key, value in http_response.getheaders():
            response.headers[key.lower()] = value
        
        # Read content
        response._content = http_response.read()
        
        # Handle redirects
        if allow_redirects and 300 <= response.status_code < 400:
            location = response.headers.get('location')
            if location:
                # Add to history
                response.history.append(response)
                
                # Make new request
                if not location.startswith('http'):
                    # Relative URL
                    location = urllib.parse.urljoin(url, location)
                
                return request(method, location, params=params, data=data,
                             json=json, headers=headers, cookies=cookies,
                             auth=auth, timeout=timeout, allow_redirects=allow_redirects,
                             verify=verify, **kwargs)
        
        return response
    
    finally:
        conn.close()


def get(url: str, **kwargs) -> Response:
    """GET request"""
    return request('GET', url, **kwargs)


def post(url: str, **kwargs) -> Response:
    """POST request"""
    return request('POST', url, **kwargs)


def put(url: str, **kwargs) -> Response:
    """PUT request"""
    return request('PUT', url, **kwargs)


def patch(url: str, **kwargs) -> Response:
    """PATCH request"""
    return request('PATCH', url, **kwargs)


def delete(url: str, **kwargs) -> Response:
    """DELETE request"""
    return request('DELETE', url, **kwargs)


def head(url: str, **kwargs) -> Response:
    """HEAD request"""
    return request('HEAD', url, **kwargs)


def options(url: str, **kwargs) -> Response:
    """OPTIONS request"""
    return request('OPTIONS', url, **kwargs)


# Convenience alias for requests.Session
session = Session
