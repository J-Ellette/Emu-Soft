"""API Framework for building RESTful endpoints."""

from typing import Any, Callable, Dict, List, Optional
from mycms.core.framework.request import Request
from mycms.core.framework.response import Response, JSONResponse


class APIEndpoint:
    """Represents a single API endpoint with method handlers."""

    def __init__(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize an API endpoint.

        Args:
            path: URL path for the endpoint
            methods: Allowed HTTP methods (default: ["GET"])
            name: Optional endpoint name
        """
        self.path = path
        self.methods = methods or ["GET"]
        self.name = name or path
        self.handlers: Dict[str, Callable] = {}

    def add_handler(self, method: str, handler: Callable) -> None:
        """Add a method handler to the endpoint.

        Args:
            method: HTTP method (GET, POST, etc.)
            handler: Handler function
        """
        self.handlers[method.upper()] = handler

    async def handle(self, request: Request) -> Response:
        """Handle an incoming request.

        Args:
            request: Request object

        Returns:
            Response object
        """
        method = request.method.upper()

        if method not in self.methods:
            return JSONResponse(
                {"error": f"Method {method} not allowed"},
                status_code=405,
            )

        handler = self.handlers.get(method)
        if not handler:
            return JSONResponse(
                {"error": f"No handler for method {method}"},
                status_code=501,
            )

        try:
            return await handler(request)
        except Exception as e:
            return JSONResponse(
                {"error": "Internal server error", "detail": str(e)},
                status_code=500,
            )


class APIView:
    """Base class for API views with RESTful method handlers."""

    allowed_methods: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE"]

    async def dispatch(self, request: Request, **kwargs: Any) -> Response:
        """Dispatch request to appropriate method handler.

        Args:
            request: Request object
            **kwargs: Additional keyword arguments

        Returns:
            Response object
        """
        method = request.method.upper()

        if method not in self.allowed_methods:
            return JSONResponse(
                {"error": f"Method {method} not allowed"},
                status_code=405,
            )

        handler = getattr(self, method.lower(), None)
        if not handler:
            return JSONResponse(
                {"error": f"Method {method} not implemented"},
                status_code=501,
            )

        try:
            return await handler(request, **kwargs)
        except Exception as e:
            return JSONResponse(
                {"error": "Internal server error", "detail": str(e)},
                status_code=500,
            )

    async def get(self, request: Request, **kwargs: Any) -> Response:
        """Handle GET requests."""
        return JSONResponse(
            {"error": "GET method not implemented"},
            status_code=501,
        )

    async def post(self, request: Request, **kwargs: Any) -> Response:
        """Handle POST requests."""
        return JSONResponse(
            {"error": "POST method not implemented"},
            status_code=501,
        )

    async def put(self, request: Request, **kwargs: Any) -> Response:
        """Handle PUT requests."""
        return JSONResponse(
            {"error": "PUT method not implemented"},
            status_code=501,
        )

    async def patch(self, request: Request, **kwargs: Any) -> Response:
        """Handle PATCH requests."""
        return JSONResponse(
            {"error": "PATCH method not implemented"},
            status_code=501,
        )

    async def delete(self, request: Request, **kwargs: Any) -> Response:
        """Handle DELETE requests."""
        return JSONResponse(
            {"error": "DELETE method not implemented"},
            status_code=501,
        )


class APIRouter:
    """Router for managing API endpoints."""

    def __init__(self, prefix: str = "") -> None:
        """Initialize the API router.

        Args:
            prefix: URL prefix for all routes (e.g., "/api/v1")
        """
        self.prefix = prefix.rstrip("/")
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.views: Dict[str, APIView] = {}

    def add_endpoint(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        handler: Optional[Callable] = None,
        name: Optional[str] = None,
    ) -> APIEndpoint:
        """Add an API endpoint.

        Args:
            path: URL path
            methods: Allowed HTTP methods
            handler: Optional handler function
            name: Optional endpoint name

        Returns:
            Created APIEndpoint
        """
        full_path = f"{self.prefix}{path}"
        endpoint = APIEndpoint(full_path, methods, name)

        if handler:
            for method in endpoint.methods:
                endpoint.add_handler(method, handler)

        self.endpoints[full_path] = endpoint
        return endpoint

    def add_view(self, path: str, view: APIView, name: Optional[str] = None) -> None:
        """Add an API view.

        Args:
            path: URL path
            view: APIView instance
            name: Optional view name
        """
        full_path = f"{self.prefix}{path}"
        self.views[full_path] = view

    def route(
        self, path: str, methods: Optional[List[str]] = None, name: Optional[str] = None
    ) -> Callable:
        """Decorator for adding route handlers.

        Args:
            path: URL path
            methods: Allowed HTTP methods
            name: Optional route name

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            self.add_endpoint(path, methods, handler, name)
            return handler

        return decorator

    async def handle(self, request: Request) -> Optional[Response]:
        """Handle an incoming request by routing to appropriate endpoint.

        Args:
            request: Request object

        Returns:
            Response object or None if no matching route
        """
        path = request.path

        # Check endpoints
        if path in self.endpoints:
            return await self.endpoints[path].handle(request)

        # Check views
        if path in self.views:
            return await self.views[path].dispatch(request)

        # Try pattern matching for dynamic routes
        for route_path, endpoint in self.endpoints.items():
            if self._match_route(route_path, path):
                return await endpoint.handle(request)

        for route_path, view in self.views.items():
            if self._match_route(route_path, path):
                return await view.dispatch(request)

        return None

    def _match_route(self, route_pattern: str, request_path: str) -> bool:
        """Simple route pattern matching.

        Args:
            route_pattern: Route pattern (e.g., "/api/users/{id}")
            request_path: Actual request path

        Returns:
            True if pattern matches
        """
        route_parts = route_pattern.split("/")
        path_parts = request_path.split("/")

        if len(route_parts) != len(path_parts):
            return False

        for route_part, path_part in zip(route_parts, path_parts):
            if route_part.startswith("{") and route_part.endswith("}"):
                # Dynamic segment
                continue
            elif route_part != path_part:
                return False

        return True

    def get_routes(self) -> List[Dict[str, Any]]:
        """Get list of all registered routes.

        Returns:
            List of route information dictionaries
        """
        routes = []

        for path, endpoint in self.endpoints.items():
            routes.append(
                {
                    "path": path,
                    "methods": endpoint.methods,
                    "name": endpoint.name,
                    "type": "endpoint",
                }
            )

        for path, view in self.views.items():
            routes.append(
                {
                    "path": path,
                    "methods": view.allowed_methods,
                    "name": view.__class__.__name__,
                    "type": "view",
                }
            )

        return routes
