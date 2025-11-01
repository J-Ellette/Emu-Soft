"""
Developed by PowerShield, as an alternative to Django
"""

"""HTTP Response handling module."""

from typing import Any, Dict, List, Optional, Tuple, Union
import json as json_module


class Response:
    """Represents an HTTP response.

    This class provides a simple interface for creating HTTP responses
    with various content types, status codes, and headers.
    """

    def __init__(
        self,
        content: Union[str, bytes, dict, list] = "",
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> None:
        """Initialize a Response object.

        Args:
            content: Response body content (str, bytes, or JSON-serializable)
            status_code: HTTP status code (default: 200)
            headers: Additional HTTP headers
            content_type: Content-Type header value
        """
        self.status_code = status_code
        self.headers = headers or {}

        # Handle different content types
        if isinstance(content, (dict, list)):
            self.body = json_module.dumps(content).encode("utf-8")
            if not content_type:
                content_type = "application/json"
        elif isinstance(content, str):
            self.body = content.encode("utf-8")
            if not content_type:
                content_type = "text/html; charset=utf-8"
        elif isinstance(content, bytes):
            self.body = content
            if not content_type:
                content_type = "application/octet-stream"
        else:
            self.body = str(content).encode("utf-8")
            if not content_type:
                content_type = "text/plain; charset=utf-8"

        if content_type:
            self.headers["content-type"] = content_type

    @property
    def status(self) -> int:
        """Get the status code (alias for status_code)."""
        return self.status_code

    def set_cookie(
        self,
        key: str,
        value: str,
        max_age: Optional[int] = None,
        httponly: bool = False,
        secure: bool = False,
        samesite: str = "Lax",
    ) -> None:
        """Set a cookie in the response.

        Args:
            key: Cookie name
            value: Cookie value
            max_age: Max age in seconds
            httponly: HttpOnly flag
            secure: Secure flag
            samesite: SameSite attribute
        """
        cookie = f"{key}={value}"

        if max_age is not None:
            cookie += f"; Max-Age={max_age}"

        if httponly:
            cookie += "; HttpOnly"

        if secure:
            cookie += "; Secure"

        if samesite:
            cookie += f"; SameSite={samesite}"

        self.headers["set-cookie"] = cookie

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        """ASGI callable interface.

        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Prepare headers for ASGI
        headers_list: List[Tuple[bytes, bytes]] = []
        for name, value in self.headers.items():
            name_bytes = name.encode("utf-8") if isinstance(name, str) else name
            value_bytes = value.encode("utf-8") if isinstance(value, str) else value
            headers_list.append((name_bytes, value_bytes))

        # Send response start
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": headers_list,
            }
        )

        # Send response body
        await send(
            {
                "type": "http.response.body",
                "body": self.body,
            }
        )

    def __repr__(self) -> str:
        """Return string representation of the response."""
        return f"<Response {self.status_code}>"


class JSONResponse(Response):
    """Convenience class for JSON responses."""

    def __init__(
        self,
        content: Union[dict, list],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize a JSON response.

        Args:
            content: JSON-serializable data
            status_code: HTTP status code (default: 200)
            headers: Additional HTTP headers
        """
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            content_type="application/json",
        )


class HTMLResponse(Response):
    """Convenience class for HTML responses."""

    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize an HTML response.

        Args:
            content: HTML string
            status_code: HTTP status code (default: 200)
            headers: Additional HTTP headers
        """
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            content_type="text/html; charset=utf-8",
        )


class PlainTextResponse(Response):
    """Convenience class for plain text responses."""

    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize a plain text response.

        Args:
            content: Plain text string
            status_code: HTTP status code (default: 200)
            headers: Additional HTTP headers
        """
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            content_type="text/plain; charset=utf-8",
        )
