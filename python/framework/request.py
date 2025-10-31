"""HTTP Request handling module."""

from typing import Any, Dict, Optional
from urllib.parse import parse_qs


class Request:
    """Represents an HTTP request.

    This class wraps the ASGI scope and provides convenient access to
    request data such as method, path, headers, query parameters, and body.
    """

    def __init__(self, scope: Dict[str, Any], receive: Any) -> None:
        """Initialize a Request object.

        Args:
            scope: ASGI scope dictionary containing request metadata
            receive: ASGI receive callable for reading request body
        """
        self.scope = scope
        self.receive = receive
        self._body: Optional[bytes] = None

    @property
    def method(self) -> str:
        """Get the HTTP method (GET, POST, etc.)."""
        return self.scope.get("method", "GET")

    @property
    def path(self) -> str:
        """Get the request path."""
        return self.scope.get("path", "/")

    @property
    def query_string(self) -> str:
        """Get the raw query string."""
        qs = self.scope.get("query_string", b"")
        return qs.decode("utf-8") if isinstance(qs, bytes) else qs

    @property
    def query_params(self) -> Dict[str, Any]:
        """Parse and return query parameters as a dictionary."""
        qs = self.query_string
        if not qs:
            return {}
        parsed = parse_qs(qs)
        # Return single values for single-item lists
        return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}

    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers as a dictionary."""
        headers = {}
        for name, value in self.scope.get("headers", []):
            name_str = name.decode("utf-8") if isinstance(name, bytes) else name
            value_str = value.decode("utf-8") if isinstance(value, bytes) else value
            headers[name_str.lower()] = value_str
        return headers

    @property
    def cookies(self) -> Dict[str, str]:
        """Get cookies from the request.

        Returns:
            Dictionary of cookie name-value pairs
        """
        cookies = {}
        cookie_header = self.headers.get("cookie", "")
        if cookie_header:
            for cookie in cookie_header.split(";"):
                cookie = cookie.strip()
                if "=" in cookie:
                    key, value = cookie.split("=", 1)
                    cookies[key.strip()] = value.strip()
        return cookies

    async def body(self) -> bytes:
        """Read and return the request body.

        The body is cached after the first read to avoid consuming
        the stream multiple times.
        """
        if self._body is None:
            body_parts = []
            while True:
                message = await self.receive()
                if message["type"] == "http.request":
                    body = message.get("body", b"")
                    if body:
                        body_parts.append(body)
                    if not message.get("more_body", False):
                        break
            self._body = b"".join(body_parts)
        return self._body

    async def json(self) -> Any:
        """Parse request body as JSON.

        Returns:
            Parsed JSON data

        Raises:
            json.JSONDecodeError: If body is not valid JSON
        """
        import json

        body = await self.body()
        return json.loads(body.decode("utf-8"))

    def __repr__(self) -> str:
        """Return string representation of the request."""
        return f"<Request {self.method} {self.path}>"
