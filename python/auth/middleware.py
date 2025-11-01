"""
Developed by PowerShield, as an alternative to Django Auth
"""

"""Authentication middleware for request processing."""

from typing import Any
from framework.middleware import Middleware
from framework.request import Request
from framework.response import Response
from auth.session import SessionManager
from auth.authentication import get_current_user


class AuthMiddleware(Middleware):
    """Middleware to attach user and session to requests."""

    def __init__(self, session_manager: SessionManager) -> None:
        """Initialize auth middleware.

        Args:
            session_manager: SessionManager instance
        """
        self.session_manager = session_manager

    async def process_request(self, request: Request) -> Any:
        """Process the request to add user and session.

        Args:
            request: Request object

        Returns:
            None to continue processing
        """
        # Get session ID from cookie
        session_id = request.cookies.get("session_id")

        if session_id:
            # Get session from manager
            session = await self.session_manager.get_session(session_id)
            if session:
                # Attach session to request
                request.session = session

                # Get and attach user
                user = await get_current_user(session)
                request.user = user
            else:
                # Session not found or expired
                request.session = None
                request.user = None
        else:
            # No session cookie
            request.session = None
            request.user = None

        return None

    async def process_response(self, request: Request, response: Response) -> Response:
        """Process the response to set session cookie if needed.

        Args:
            request: Request object
            response: Response object

        Returns:
            Modified Response object
        """
        # If session exists on request, set cookie
        if hasattr(request, "session") and request.session:
            response.set_cookie(
                "session_id",
                request.session.session_id,
                max_age=self.session_manager.session_timeout,
                httponly=True,
                secure=True,  # Should be True in production (HTTPS)
                samesite="Lax",
            )

        return response


class RequireAuthMiddleware(Middleware):
    """Middleware to require authentication for all requests."""

    def __init__(self, exempt_paths: list = None) -> None:
        """Initialize require auth middleware.

        Args:
            exempt_paths: List of paths that don't require authentication
        """
        self.exempt_paths = exempt_paths or ["/login", "/logout", "/public"]

    async def process_request(self, request: Request) -> Any:
        """Process the request to check authentication.

        Args:
            request: Request object

        Returns:
            None to continue, or Response to short-circuit
        """
        # Check if path is exempt
        for exempt_path in self.exempt_paths:
            if request.path.startswith(exempt_path):
                return None

        # Check if user is authenticated
        if not hasattr(request, "user") or not request.user:
            return Response({"error": "Authentication required"}, status_code=401)

        return None


class RateLimitMiddleware(Middleware):
    """Middleware to limit request rate per user/IP."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        """Initialize rate limit middleware.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict = {}

    async def process_request(self, request: Request) -> Any:
        """Process the request to check rate limits.

        Args:
            request: Request object

        Returns:
            None to continue, or Response to short-circuit
        """
        from datetime import datetime, timedelta

        # Get identifier (user ID or IP)
        identifier = None
        if hasattr(request, "user") and request.user:
            identifier = f"user_{request.user.id}"
        else:
            # Use IP address from headers or client
            identifier = request.headers.get("X-Forwarded-For", "unknown")

        # Get current time
        now = datetime.utcnow()

        # Initialize or get request list for this identifier
        if identifier not in self._requests:
            self._requests[identifier] = []

        # Clean up old requests
        cutoff = now - timedelta(seconds=self.window_seconds)
        self._requests[identifier] = [
            req_time for req_time in self._requests[identifier] if req_time > cutoff
        ]

        # Check if limit exceeded
        if len(self._requests[identifier]) >= self.max_requests:
            return Response({"error": "Rate limit exceeded"}, status_code=429)

        # Add current request
        self._requests[identifier].append(now)

        return None
