"""
Developed by PowerShield, as an alternative to Django Security
"""

"""Security middleware for protecting the application."""

from typing import Any, Optional, Dict, Set
from datetime import datetime, timezone, timedelta
import secrets
from framework.middleware import Middleware
from framework.request import Request
from framework.response import Response


class SecurityHeadersMiddleware(Middleware):
    """Middleware to add security headers to responses."""

    def __init__(
        self,
        csp_policy: Optional[str] = None,
        hsts_max_age: int = 31536000,
        frame_options: str = "DENY",
    ) -> None:
        """Initialize security headers middleware.

        Args:
            csp_policy: Content Security Policy header value
            hsts_max_age: HSTS max-age in seconds (default: 1 year)
            frame_options: X-Frame-Options header value
        """
        self.csp_policy = csp_policy or "default-src 'self'"
        self.hsts_max_age = hsts_max_age
        self.frame_options = frame_options

    async def process_response(self, request: Request, response: Response) -> Response:
        """Add security headers to response.

        Args:
            request: Request object
            response: Response object

        Returns:
            Response with security headers added
        """
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Clickjacking protection
        response.headers["X-Frame-Options"] = self.frame_options

        # HSTS (only for HTTPS)
        if request.scope.get("scheme") == "https":
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains"
            )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class CSRFMiddleware(Middleware):
    """Middleware to protect against Cross-Site Request Forgery attacks."""

    def __init__(
        self,
        exempt_paths: Optional[Set[str]] = None,
        token_name: str = "csrf_token",
        cookie_name: str = "csrf_token",
    ) -> None:
        """Initialize CSRF middleware.

        Args:
            exempt_paths: Set of paths to exempt from CSRF protection
            token_name: Name of the CSRF token in forms/headers
            cookie_name: Name of the CSRF cookie
        """
        self.exempt_paths = exempt_paths or set()
        self.token_name = token_name
        self.cookie_name = cookie_name
        self._tokens: Dict[str, datetime] = {}

    def _generate_token(self) -> str:
        """Generate a new CSRF token.

        Returns:
            Random CSRF token
        """
        return secrets.token_urlsafe(32)

    def _get_token_from_request(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request.

        Args:
            request: Request object

        Returns:
            CSRF token or None
        """
        # Try header first
        token = request.headers.get(f"X-{self.token_name.upper()}")
        if token:
            return token

        # Try form data
        if hasattr(request, "form"):
            token = request.form.get(self.token_name)
            if token:
                return token

        return None

    async def process_request(self, request: Request) -> Any:
        """Validate CSRF token for state-changing requests.

        Args:
            request: Request object

        Returns:
            None to continue, Response to short-circuit
        """
        # Skip safe methods
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return None

        # Skip exempt paths
        if request.path in self.exempt_paths:
            return None

        # Get cookie token
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            return Response(
                content={"error": "CSRF token missing"},
                status_code=403,
            )

        # Get request token
        request_token = self._get_token_from_request(request)
        if not request_token:
            return Response(
                content={"error": "CSRF token missing from request"},
                status_code=403,
            )

        # Compare tokens
        if not secrets.compare_digest(cookie_token, request_token):
            return Response(
                content={"error": "CSRF token mismatch"},
                status_code=403,
            )

        return None

    async def process_response(self, request: Request, response: Response) -> Response:
        """Add CSRF token to response.

        Args:
            request: Request object
            response: Response object

        Returns:
            Response with CSRF token
        """
        # Generate or retrieve token
        token = request.cookies.get(self.cookie_name)
        if not token:
            token = self._generate_token()
            response.set_cookie(
                self.cookie_name,
                token,
                httponly=True,
                secure=request.scope.get("scheme") == "https",
                samesite="Strict",
            )

        return response


class RateLimitMiddleware(Middleware):
    """Middleware to limit request rates per IP address."""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        exempt_paths: Optional[Set[str]] = None,
    ) -> None:
        """Initialize rate limit middleware.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
            exempt_paths: Set of paths to exempt from rate limiting
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exempt_paths = exempt_paths or set()
        self._requests: Dict[str, list] = {}

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.

        Args:
            request: Request object

        Returns:
            Client IP address
        """
        # Check for X-Forwarded-For header (proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to remote address
        return getattr(request, "client_ip", "unknown")

    def _clean_old_requests(self, ip: str) -> None:
        """Remove old requests outside the time window.

        Args:
            ip: Client IP address
        """
        if ip not in self._requests:
            return

        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.window_seconds)
        self._requests[ip] = [timestamp for timestamp in self._requests[ip] if timestamp > cutoff]

    async def process_request(self, request: Request) -> Any:
        """Check rate limit for request.

        Args:
            request: Request object

        Returns:
            None to continue, Response to short-circuit
        """
        # Skip exempt paths
        if request.path in self.exempt_paths:
            return None

        ip = self._get_client_ip(request)

        # Clean old requests
        self._clean_old_requests(ip)

        # Check limit
        if ip not in self._requests:
            self._requests[ip] = []

        if len(self._requests[ip]) >= self.max_requests:
            return Response(
                content={"error": "Rate limit exceeded"},
                status_code=429,
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(
                        int(
                            (
                                datetime.now(timezone.utc) + timedelta(seconds=self.window_seconds)
                            ).timestamp()
                        )
                    ),
                },
            )

        # Record request
        self._requests[ip].append(datetime.now(timezone.utc))

        return None
