"""Middleware pipeline for request/response processing."""

from typing import Any, List
from mycms.core.framework.request import Request
from mycms.core.framework.response import Response


class Middleware:
    """Base middleware class.

    All middleware should inherit from this class and implement
    the process_request and/or process_response methods.
    """

    async def process_request(self, request: Request) -> Any:
        """Process the request before it reaches the handler.

        Args:
            request: Request object

        Returns:
            None to continue processing, or a Response to short-circuit
        """
        pass

    async def process_response(self, request: Request, response: Response) -> Response:
        """Process the response before it's sent to the client.

        Args:
            request: Request object
            response: Response object

        Returns:
            Modified or new Response object
        """
        return response


class MiddlewarePipeline:
    """Manages the middleware execution pipeline."""

    def __init__(self) -> None:
        """Initialize the middleware pipeline."""
        self.middleware_stack: List[Middleware] = []

    def add_middleware(self, middleware: Middleware) -> None:
        """Add middleware to the pipeline.

        Args:
            middleware: Middleware instance to add
        """
        self.middleware_stack.append(middleware)

    async def process_request(self, request: Request) -> Any:
        """Process request through all middleware.

        Args:
            request: Request object

        Returns:
            None to continue, or Response to short-circuit
        """
        for middleware in self.middleware_stack:
            result = await middleware.process_request(request)
            if isinstance(result, Response):
                # Middleware returned a response, short-circuit
                return result
        return None

    async def process_response(self, request: Request, response: Response) -> Response:
        """Process response through all middleware in reverse order.

        Args:
            request: Request object
            response: Response object

        Returns:
            Processed Response object
        """
        # Process middleware in reverse order for response
        for middleware in reversed(self.middleware_stack):
            response = await middleware.process_response(request, response)
        return response


class CORSMiddleware(Middleware):
    """Middleware for handling Cross-Origin Resource Sharing (CORS)."""

    def __init__(
        self,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
    ) -> None:
        """Initialize CORS middleware.

        Args:
            allow_origins: List of allowed origins (default: ['*'])
            allow_methods: List of allowed HTTP methods
            allow_headers: List of allowed headers
        """
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "PATCH"]
        self.allow_headers = allow_headers or ["*"]

    async def process_response(self, request: Request, response: Response) -> Response:
        """Add CORS headers to the response.

        Args:
            request: Request object
            response: Response object

        Returns:
            Response with CORS headers
        """
        response.headers["Access-Control-Allow-Origin"] = ", ".join(self.allow_origins)
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        return response


class SecurityHeadersMiddleware(Middleware):
    """Middleware for adding security headers to responses."""

    async def process_response(self, request: Request, response: Response) -> Response:
        """Add security headers to the response.

        Args:
            request: Request object
            response: Response object

        Returns:
            Response with security headers
        """
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
