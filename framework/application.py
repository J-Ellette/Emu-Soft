"""Main ASGI application class."""

from typing import Any, Dict
from framework.request import Request
from framework.response import Response
from framework.routing import Router
from framework.middleware import MiddlewarePipeline


class Application:
    """Main ASGI application class.

    This is the core of the web framework, handling ASGI protocol
    and routing requests through middleware to handlers.
    """

    def __init__(self) -> None:
        """Initialize the application."""
        self.router = Router()
        self.middleware = MiddlewarePipeline()

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        """ASGI callable interface.

        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Only handle HTTP requests
        if scope["type"] != "http":
            return

        # Create request object
        request = Request(scope, receive)

        try:
            # Process request through middleware
            early_response = await self.middleware.process_request(request)

            if isinstance(early_response, Response):
                # Middleware returned a response, use it
                response = early_response
            else:
                # Dispatch to router
                response = await self.router.dispatch(request)

            # Process response through middleware
            response = await self.middleware.process_response(request, response)

        except Exception as e:
            # Handle errors with a 500 response
            response = Response(
                content=f"Internal Server Error: {str(e)}",
                status_code=500,
                content_type="text/plain",
            )

        # Send the response
        await response(scope, receive, send)

    def route(self, *args: Any, **kwargs: Any) -> Any:
        """Delegate route decorator to router.

        Returns:
            Router's route decorator
        """
        return self.router.route(*args, **kwargs)

    def get(self, *args: Any, **kwargs: Any) -> Any:
        """Delegate GET route decorator to router.

        Returns:
            Router's get decorator
        """
        return self.router.get(*args, **kwargs)

    def post(self, *args: Any, **kwargs: Any) -> Any:
        """Delegate POST route decorator to router.

        Returns:
            Router's post decorator
        """
        return self.router.post(*args, **kwargs)

    def put(self, *args: Any, **kwargs: Any) -> Any:
        """Delegate PUT route decorator to router.

        Returns:
            Router's put decorator
        """
        return self.router.put(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> Any:
        """Delegate DELETE route decorator to router.

        Returns:
            Router's delete decorator
        """
        return self.router.delete(*args, **kwargs)

    def patch(self, *args: Any, **kwargs: Any) -> Any:
        """Delegate PATCH route decorator to router.

        Returns:
            Router's patch decorator
        """
        return self.router.patch(*args, **kwargs)

    def add_middleware(self, *args: Any, **kwargs: Any) -> None:
        """Delegate add_middleware to middleware pipeline.

        Args:
            *args: Arguments to pass to middleware pipeline
            **kwargs: Keyword arguments to pass to middleware pipeline
        """
        self.middleware.add_middleware(*args, **kwargs)
