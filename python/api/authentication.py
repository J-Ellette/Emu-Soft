"""
Developed by PowerShield, as an alternative to Django REST Framework
"""

"""API authentication mechanisms."""

import secrets
import hashlib
from typing import Any, Callable, Dict, Optional, Tuple
from functools import wraps
from datetime import datetime, timedelta
from framework.request import Request
from framework.response import Response, JSONResponse
from auth.tokens import JWTTokenManager
from auth.models import User


def create_token(
    payload: Dict[str, Any], secret_key: str, expires_in_seconds: int, algorithm: str
) -> str:
    """Create a JWT token.

    Args:
        payload: Token payload
        secret_key: Secret key for signing
        expires_in_seconds: Token expiration time
        algorithm: JWT algorithm

    Returns:
        JWT token string
    """
    manager = JWTTokenManager(secret_key, algorithm)
    # Use the user_id from payload
    user_id = payload.get("user_id", "")
    token_type = payload.get("type", "access")

    if token_type == "refresh":
        return manager.create_refresh_token(
            user_id=user_id,  # type: ignore[arg-type]
            username=user_id,
            expires_delta=timedelta(seconds=expires_in_seconds),
        )
    else:
        return manager.create_access_token(
            user_id=user_id,  # type: ignore[arg-type]
            username=user_id,
            expires_delta=timedelta(seconds=expires_in_seconds),
        )


def verify_token(token: str, secret_key: str, algorithm: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token.

    Args:
        token: JWT token string
        secret_key: Secret key
        algorithm: JWT algorithm

    Returns:
        Token payload if valid, None otherwise
    """
    manager = JWTTokenManager(secret_key, algorithm)
    payload = manager.verify_token(token)
    if payload:
        # Map 'sub' to 'user_id' for compatibility
        payload["user_id"] = payload.get("sub")
    return payload


class APIKey:
    """Represents an API key for authentication."""

    def __init__(
        self,
        key: str,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        """Initialize an API key.

        Args:
            key: The API key string
            user_id: Associated user ID
            name: Optional key name/description
            expires_at: Expiration datetime
            created_at: Creation datetime
        """
        self.key = key
        self.user_id = user_id
        self.name = name
        self.expires_at = expires_at
        self.created_at = created_at or datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if the API key is expired.

        Returns:
            True if expired, False otherwise
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @staticmethod
    def generate_key(length: int = 32) -> str:
        """Generate a random API key.

        Args:
            length: Length of the key in bytes

        Returns:
            Generated API key as hex string
        """
        return secrets.token_hex(length)

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for secure storage.

        Args:
            key: API key to hash

        Returns:
            Hashed key
        """
        return hashlib.sha256(key.encode()).hexdigest()


class APIKeyAuth:
    """API key authentication handler."""

    def __init__(self, header_name: str = "X-API-Key") -> None:
        """Initialize API key authentication.

        Args:
            header_name: HTTP header name for API key
        """
        self.header_name = header_name
        # In-memory storage for demo purposes
        # In production, this should be stored in database
        self._api_keys: dict[str, APIKey] = {}

    def create_api_key(
        self,
        user_id: str,
        name: Optional[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> Tuple[str, APIKey]:
        """Create a new API key.

        Args:
            user_id: User ID to associate with key
            name: Optional key name
            expires_in_days: Optional expiration in days

        Returns:
            Tuple of (raw_key, APIKey object)
        """
        raw_key = APIKey.generate_key()
        hashed_key = APIKey.hash_key(raw_key)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        api_key = APIKey(
            key=hashed_key,
            user_id=user_id,
            name=name,
            expires_at=expires_at,
        )

        self._api_keys[hashed_key] = api_key
        return raw_key, api_key

    def verify_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Verify an API key.

        Args:
            raw_key: Raw API key from request

        Returns:
            APIKey object if valid, None otherwise
        """
        hashed_key = APIKey.hash_key(raw_key)
        api_key = self._api_keys.get(hashed_key)

        if not api_key:
            return None

        if api_key.is_expired():
            return None

        return api_key

    async def authenticate(self, request: Request) -> Optional[str]:
        """Authenticate a request using API key.

        Args:
            request: Request object

        Returns:
            User ID if authenticated, None otherwise
        """
        api_key = request.headers.get(self.header_name.lower())
        if not api_key:
            return None

        key_obj = self.verify_api_key(api_key)
        if not key_obj:
            return None

        return key_obj.user_id

    def revoke_api_key(self, raw_key: str) -> bool:
        """Revoke an API key.

        Args:
            raw_key: Raw API key to revoke

        Returns:
            True if revoked, False if not found
        """
        hashed_key = APIKey.hash_key(raw_key)
        if hashed_key in self._api_keys:
            del self._api_keys[hashed_key]
            return True
        return False


class TokenAuth:
    """JWT token-based authentication handler."""

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        """Initialize token authentication.

        Args:
            secret_key: Secret key for token signing
            algorithm: JWT algorithm to use
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, user_id: str, expires_in_seconds: int = 3600) -> str:
        """Create an access token for a user.

        Args:
            user_id: User ID
            expires_in_seconds: Token expiration time

        Returns:
            JWT token string
        """
        payload = {"user_id": user_id, "type": "access"}
        return create_token(
            payload,
            secret_key=self.secret_key,
            expires_in_seconds=expires_in_seconds,
            algorithm=self.algorithm,
        )

    def create_refresh_token(self, user_id: str, expires_in_seconds: int = 86400 * 30) -> str:
        """Create a refresh token for a user.

        Args:
            user_id: User ID
            expires_in_seconds: Token expiration time (default: 30 days)

        Returns:
            JWT token string
        """
        payload = {"user_id": user_id, "type": "refresh"}
        return create_token(
            payload,
            secret_key=self.secret_key,
            expires_in_seconds=expires_in_seconds,
            algorithm=self.algorithm,
        )

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify a JWT token.

        Args:
            token: JWT token string

        Returns:
            Token payload if valid, None otherwise
        """
        return verify_token(token, secret_key=self.secret_key, algorithm=self.algorithm)

    async def authenticate(self, request: Request) -> Optional[str]:
        """Authenticate a request using JWT token.

        Args:
            request: Request object

        Returns:
            User ID if authenticated, None otherwise
        """
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        payload = self.verify_token(token)
        if not payload:
            return None

        return payload.get("user_id")


def require_api_auth(
    auth_handler: Optional[APIKeyAuth | TokenAuth] = None,
) -> Callable:
    """Decorator to require API authentication for an endpoint.

    Args:
        auth_handler: Authentication handler (APIKeyAuth or TokenAuth)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
            if not auth_handler:
                return JSONResponse(
                    {"error": "Authentication handler not configured"},
                    status_code=500,
                )

            user_id = await auth_handler.authenticate(request)
            if not user_id:
                return JSONResponse(
                    {"error": "Authentication required"},
                    status_code=401,
                )

            # Attach user_id to request
            request.user_id = user_id  # type: ignore[attr-defined]

            # Try to load user
            try:
                user = await User.get(id=user_id)
                request.user = user  # type: ignore[attr-defined]
            except Exception:
                pass

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_bearer_token(secret_key: str, algorithm: str = "HS256") -> Callable:
    """Decorator to require Bearer token authentication.

    Args:
        secret_key: Secret key for token verification
        algorithm: JWT algorithm

    Returns:
        Decorator function
    """
    token_auth = TokenAuth(secret_key, algorithm)
    return require_api_auth(token_auth)
