"""URL routing system with pattern matching and decorators."""

from typing import Callable, Dict, List, Optional, Pattern, Tuple
import re
from framework.request import Request
from framework.response import Response


class Route:
    """Represents a single route with pattern matching."""

    def __init__(self, path: str, handler: Callable, methods: List[str]) -> None:
        """Initialize a route.

        Args:
            path: URL path pattern (e.g., '/users/{id}')
            handler: Callable that handles requests for this route
            methods: List of allowed HTTP methods
        """
        self.path = path
        self.handler = handler
        self.methods = [m.upper() for m in methods]
        self.pattern, self.param_names = self._compile_pattern(path)

    def _compile_pattern(self, path: str) -> Tuple[Pattern[str], List[str]]:
        """Compile a path pattern into a regex.

        Converts patterns like '/users/{id}' into regex patterns
        and extracts parameter names.

        Args:
            path: Path pattern string

        Returns:
            Tuple of (compiled regex pattern, list of parameter names)
        """
        param_names = []
        pattern = path

        # Find all {param} patterns
        for match in re.finditer(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", path):
            param_name = match.group(1)
            param_names.append(param_name)
            # Replace {param} with a regex group
            pattern = pattern.replace(match.group(0), r"(?P<" + param_name + r">[^/]+)")

        # Anchor the pattern
        pattern = f"^{pattern}$"
        return re.compile(pattern), param_names

    def match(self, path: str, method: str) -> Optional[Dict[str, str]]:
        """Check if a path and method match this route.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Dictionary of path parameters if matched, None otherwise
        """
        if method.upper() not in self.methods:
            return None

        match = self.pattern.match(path)
        if match:
            return match.groupdict()
        return None

    def __repr__(self) -> str:
        """Return string representation of the route."""
        return f"<Route {self.path} {self.methods}>"


class Router:
    """URL router for managing routes and dispatching requests."""

    def __init__(self) -> None:
        """Initialize the router."""
        self.routes: List[Route] = []

    def add_route(self, path: str, handler: Callable, methods: Optional[List[str]] = None) -> None:
        """Add a route to the router.

        Args:
            path: URL path pattern
            handler: Request handler function
            methods: List of allowed HTTP methods (default: ['GET'])
        """
        if methods is None:
            methods = ["GET"]
        route = Route(path, handler, methods)
        self.routes.append(route)

    def route(self, path: str, methods: Optional[List[str]] = None) -> Callable:
        """Decorator for adding routes.

        Usage:
            @router.route('/users/{id}', methods=['GET', 'POST'])
            async def user_handler(request, id):
                return Response(f"User {id}")

        Args:
            path: URL path pattern
            methods: List of allowed HTTP methods

        Returns:
            Decorator function
        """

        def decorator(handler: Callable) -> Callable:
            self.add_route(path, handler, methods)
            return handler

        return decorator

    def get(self, path: str) -> Callable:
        """Decorator for GET routes.

        Args:
            path: URL path pattern

        Returns:
            Decorator function
        """
        return self.route(path, methods=["GET"])

    def post(self, path: str) -> Callable:
        """Decorator for POST routes.

        Args:
            path: URL path pattern

        Returns:
            Decorator function
        """
        return self.route(path, methods=["POST"])

    def put(self, path: str) -> Callable:
        """Decorator for PUT routes.

        Args:
            path: URL path pattern

        Returns:
            Decorator function
        """
        return self.route(path, methods=["PUT"])

    def delete(self, path: str) -> Callable:
        """Decorator for DELETE routes.

        Args:
            path: URL path pattern

        Returns:
            Decorator function
        """
        return self.route(path, methods=["DELETE"])

    def patch(self, path: str) -> Callable:
        """Decorator for PATCH routes.

        Args:
            path: URL path pattern

        Returns:
            Decorator function
        """
        return self.route(path, methods=["PATCH"])

    async def dispatch(self, request: Request) -> Response:
        """Dispatch a request to the appropriate handler.

        Args:
            request: Request object

        Returns:
            Response object
        """
        # Try to match each route
        for route in self.routes:
            params = route.match(request.path, request.method)
            if params is not None:
                # Call the handler with request and path parameters
                response = await route.handler(request, **params)
                # Ensure we return a Response object
                if not isinstance(response, Response):
                    response = Response(str(response))
                return response

        # No route matched
        return Response(
            content=f"Not Found: {request.path}", status_code=404, content_type="text/plain"
        )

    def __repr__(self) -> str:
        """Return string representation of the router."""
        return f"<Router {len(self.routes)} routes>"
