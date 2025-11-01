"""
Developed by PowerShield, as an alternative to Django Auth
"""

"""JWT token generation and validation."""

import jwt
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class JWTTokenManager:
    """Manages JWT token creation and validation."""

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        """Initialize JWT token manager.

        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(
        self,
        user_id: int,
        username: str,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a JWT access token.

        Args:
            user_id: User ID
            username: Username
            expires_delta: Token expiration time (default: 15 minutes)
            additional_claims: Additional claims to include

        Returns:
            JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=15)

        expire = datetime.utcnow() + expires_delta
        claims = {
            "sub": str(user_id),
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }

        if additional_claims:
            claims.update(additional_claims)

        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(
        self,
        user_id: int,
        username: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT refresh token.

        Args:
            user_id: User ID
            username: Username
            expires_delta: Token expiration time (default: 7 days)

        Returns:
            JWT refresh token string
        """
        if expires_delta is None:
            expires_delta = timedelta(days=7)

        expire = datetime.utcnow() + expires_delta
        claims = {
            "sub": str(user_id),
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }

        token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token claims or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Token is invalid
            return None

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode a JWT token without verification (for inspection).

        Args:
            token: JWT token string

        Returns:
            Decoded token claims or None if invalid
        """
        try:
            payload = jwt.decode(
                token, options={"verify_signature": False}, algorithms=[self.algorithm]
            )
            return payload
        except jwt.InvalidTokenError:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create a new access token from a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token or None if refresh token is invalid
        """
        payload = self.verify_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            return None

        user_id = int(payload["sub"])
        username = payload["username"]

        return self.create_access_token(user_id, username)


async def create_token_pair(
    user_id: int, username: str, token_manager: JWTTokenManager
) -> Dict[str, str]:
    """Create access and refresh token pair.

    Args:
        user_id: User ID
        username: Username
        token_manager: JWTTokenManager instance

    Returns:
        Dictionary with access_token and refresh_token
    """
    access_token = token_manager.create_access_token(user_id, username)
    refresh_token = token_manager.create_refresh_token(user_id, username)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
