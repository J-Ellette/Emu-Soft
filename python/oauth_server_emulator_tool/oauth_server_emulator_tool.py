#!/usr/bin/env python3
"""
OAuth 2.0/OIDC Server Emulator - Authentication and Authorization

This module emulates core OAuth 2.0 and OpenID Connect (OIDC) functionality including:
- Authorization code flow
- Client credentials flow
- Implicit flow
- Resource owner password credentials flow
- Token generation and validation
- OpenID Connect ID tokens
- Token introspection and revocation
- Client registration and management
"""

import json
import time
import hashlib
import hmac
import secrets
import base64
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import urllib.parse


class GrantType(Enum):
    """OAuth 2.0 grant types"""
    AUTHORIZATION_CODE = "authorization_code"
    IMPLICIT = "implicit"
    PASSWORD = "password"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"


class TokenType(Enum):
    """Token types"""
    BEARER = "Bearer"
    MAC = "MAC"


class ResponseType(Enum):
    """OAuth 2.0 response types"""
    CODE = "code"
    TOKEN = "token"
    ID_TOKEN = "id_token"


@dataclass
class Client:
    """OAuth 2.0 client application"""
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    scopes: List[str]
    client_name: Optional[str] = None
    token_endpoint_auth_method: str = "client_secret_basic"
    
    def validate_redirect_uri(self, uri: str) -> bool:
        """Validate if redirect URI is registered"""
        return uri in self.redirect_uris
    
    def supports_grant_type(self, grant_type: str) -> bool:
        """Check if client supports grant type"""
        return grant_type in self.grant_types
    
    def has_scope(self, scope: str) -> bool:
        """Check if client has access to scope"""
        return scope in self.scopes


@dataclass
class User:
    """Resource owner (user)"""
    user_id: str
    username: str
    password_hash: str
    email: Optional[str] = None
    email_verified: bool = False
    phone_number: Optional[str] = None
    phone_number_verified: bool = False
    profile: Dict[str, Any] = field(default_factory=dict)
    
    def verify_password(self, password: str) -> bool:
        """Verify user password"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return hmac.compare_digest(password_hash, self.password_hash)


@dataclass
class AuthorizationCode:
    """Authorization code for code flow"""
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scopes: Set[str]
    expires_at: float
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if authorization code is expired"""
        return time.time() > self.expires_at


@dataclass
class AccessToken:
    """OAuth 2.0 access token"""
    token: str
    token_type: str
    client_id: str
    user_id: Optional[str]
    scopes: Set[str]
    expires_at: float
    issued_at: float
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return time.time() > self.expires_at
    
    def has_scope(self, scope: str) -> bool:
        """Check if token has specific scope"""
        return scope in self.scopes


@dataclass
class RefreshToken:
    """OAuth 2.0 refresh token"""
    token: str
    client_id: str
    user_id: Optional[str]
    scopes: Set[str]
    expires_at: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if refresh token is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@dataclass
class IDToken:
    """OpenID Connect ID token"""
    iss: str  # Issuer
    sub: str  # Subject (user_id)
    aud: str  # Audience (client_id)
    exp: int  # Expiration time
    iat: int  # Issued at time
    auth_time: Optional[int] = None
    nonce: Optional[str] = None
    acr: Optional[str] = None
    amr: Optional[List[str]] = None
    azp: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    phone_number: Optional[str] = None
    phone_number_verified: Optional[bool] = None
    name: Optional[str] = None
    
    def to_jwt(self, secret: str) -> str:
        """Convert ID token to JWT format"""
        header = {"alg": "HS256", "typ": "JWT"}
        
        payload = {
            "iss": self.iss,
            "sub": self.sub,
            "aud": self.aud,
            "exp": self.exp,
            "iat": self.iat
        }
        
        # Add optional claims
        if self.auth_time is not None:
            payload["auth_time"] = self.auth_time
        if self.nonce:
            payload["nonce"] = self.nonce
        if self.email:
            payload["email"] = self.email
        if self.email_verified is not None:
            payload["email_verified"] = self.email_verified
        if self.name:
            payload["name"] = self.name
        
        # Encode header and payload
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).rstrip(b'=').decode()
        
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).rstrip(b'=').decode()
        
        # Create signature
        message = f"{header_b64}.{payload_b64}".encode()
        signature = hmac.new(
            secret.encode(),
            message,
            hashlib.sha256
        ).digest()
        
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"


class OAuthServer:
    """OAuth 2.0 and OpenID Connect server emulator"""
    
    def __init__(self, issuer: str = "https://auth.example.com"):
        self.issuer = issuer
        self.clients: Dict[str, Client] = {}
        self.users: Dict[str, User] = {}
        self.authorization_codes: Dict[str, AuthorizationCode] = {}
        self.access_tokens: Dict[str, AccessToken] = {}
        self.refresh_tokens: Dict[str, RefreshToken] = {}
        self.jwt_secret = secrets.token_urlsafe(32)
        
        # Default scopes
        self.supported_scopes = {
            "openid", "profile", "email", "phone", "address",
            "read", "write", "admin"
        }
    
    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: List[str],
        grant_types: List[str],
        response_types: List[str],
        scopes: List[str],
        client_name: Optional[str] = None
    ) -> Client:
        """Register a new OAuth 2.0 client"""
        client = Client(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uris=redirect_uris,
            grant_types=grant_types,
            response_types=response_types,
            scopes=scopes,
            client_name=client_name
        )
        self.clients[client_id] = client
        return client
    
    def register_user(
        self,
        user_id: str,
        username: str,
        password: str,
        email: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None
    ) -> User:
        """Register a new user"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            email=email,
            profile=profile or {}
        )
        self.users[user_id] = user
        return user
    
    def authorize(
        self,
        client_id: str,
        response_type: str,
        redirect_uri: str,
        scope: str,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authorization endpoint - initiate authorization flow"""
        # Validate client
        if client_id not in self.clients:
            return {"error": "invalid_client"}
        
        client = self.clients[client_id]
        
        # Validate redirect URI
        if not client.validate_redirect_uri(redirect_uri):
            return {"error": "invalid_redirect_uri"}
        
        # Validate response type
        if response_type not in client.response_types:
            return {"error": "unsupported_response_type"}
        
        # Parse scopes
        requested_scopes = set(scope.split())
        
        # Validate scopes
        for s in requested_scopes:
            if not client.has_scope(s):
                return {"error": "invalid_scope", "scope": s}
        
        # Return authorization request (would normally show consent screen)
        return {
            "status": "authorization_required",
            "client_id": client_id,
            "client_name": client.client_name,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "nonce": nonce
        }
    
    def grant_authorization(
        self,
        user_id: str,
        client_id: str,
        redirect_uri: str,
        scopes: Set[str],
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ) -> str:
        """Grant authorization and generate authorization code"""
        # Generate authorization code
        code = secrets.token_urlsafe(32)
        
        auth_code = AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            expires_at=time.time() + 600,  # 10 minutes
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        self.authorization_codes[code] = auth_code
        
        # Build redirect URL
        params = {"code": code}
        if state:
            params["state"] = state
        
        redirect_url = f"{redirect_uri}?{urllib.parse.urlencode(params)}"
        return redirect_url
    
    def token(
        self,
        grant_type: str,
        client_id: str,
        client_secret: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Token endpoint - exchange credentials for tokens"""
        # Validate client
        if client_id not in self.clients:
            return {"error": "invalid_client"}
        
        client = self.clients[client_id]
        
        # Verify client secret
        if client.client_secret != client_secret:
            return {"error": "invalid_client"}
        
        # Validate grant type
        if not client.supports_grant_type(grant_type):
            return {"error": "unsupported_grant_type"}
        
        # Handle different grant types
        if grant_type == GrantType.AUTHORIZATION_CODE.value:
            return self._handle_authorization_code_grant(client, **kwargs)
        elif grant_type == GrantType.PASSWORD.value:
            return self._handle_password_grant(client, **kwargs)
        elif grant_type == GrantType.CLIENT_CREDENTIALS.value:
            return self._handle_client_credentials_grant(client, **kwargs)
        elif grant_type == GrantType.REFRESH_TOKEN.value:
            return self._handle_refresh_token_grant(client, **kwargs)
        else:
            return {"error": "unsupported_grant_type"}
    
    def _handle_authorization_code_grant(
        self,
        client: Client,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle authorization code grant"""
        # Validate authorization code
        if code not in self.authorization_codes:
            return {"error": "invalid_grant"}
        
        auth_code = self.authorization_codes[code]
        
        # Validate code is not expired
        if auth_code.is_expired():
            del self.authorization_codes[code]
            return {"error": "invalid_grant", "error_description": "Code expired"}
        
        # Validate client_id matches
        if auth_code.client_id != client.client_id:
            return {"error": "invalid_grant"}
        
        # Validate redirect_uri matches
        if auth_code.redirect_uri != redirect_uri:
            return {"error": "invalid_grant"}
        
        # PKCE validation
        if auth_code.code_challenge:
            if not code_verifier:
                return {"error": "invalid_request", "error_description": "code_verifier required"}
            
            # Verify code challenge
            if auth_code.code_challenge_method == "S256":
                computed_challenge = base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode()).digest()
                ).rstrip(b'=').decode()
            else:
                computed_challenge = code_verifier
            
            if not hmac.compare_digest(computed_challenge, auth_code.code_challenge):
                return {"error": "invalid_grant", "error_description": "Invalid code_verifier"}
        
        # Generate tokens
        user_id = auth_code.user_id
        scopes = auth_code.scopes
        
        # Remove used authorization code
        del self.authorization_codes[code]
        
        return self._generate_tokens(client, user_id, scopes)
    
    def _handle_password_grant(
        self,
        client: Client,
        username: str,
        password: str,
        scope: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle resource owner password credentials grant"""
        # Find user by username
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            return {"error": "invalid_grant"}
        
        # Verify password
        if not user.verify_password(password):
            return {"error": "invalid_grant"}
        
        # Parse scopes
        scopes = set(scope.split()) if scope else set()
        
        return self._generate_tokens(client, user.user_id, scopes)
    
    def _handle_client_credentials_grant(
        self,
        client: Client,
        scope: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle client credentials grant"""
        # Parse scopes
        scopes = set(scope.split()) if scope else set()
        
        return self._generate_tokens(client, None, scopes)
    
    def _handle_refresh_token_grant(
        self,
        client: Client,
        refresh_token: str,
        scope: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle refresh token grant"""
        # Validate refresh token
        if refresh_token not in self.refresh_tokens:
            return {"error": "invalid_grant"}
        
        rt = self.refresh_tokens[refresh_token]
        
        # Validate token is not expired
        if rt.is_expired():
            del self.refresh_tokens[refresh_token]
            return {"error": "invalid_grant"}
        
        # Validate client_id matches
        if rt.client_id != client.client_id:
            return {"error": "invalid_grant"}
        
        # Parse new scopes (cannot exceed original scopes)
        if scope:
            new_scopes = set(scope.split())
            if not new_scopes.issubset(rt.scopes):
                return {"error": "invalid_scope"}
        else:
            new_scopes = rt.scopes
        
        return self._generate_tokens(client, rt.user_id, new_scopes)
    
    def _generate_tokens(
        self,
        client: Client,
        user_id: Optional[str],
        scopes: Set[str]
    ) -> Dict[str, Any]:
        """Generate access token, refresh token, and optionally ID token"""
        now = time.time()
        
        # Generate access token
        access_token_str = secrets.token_urlsafe(32)
        access_token = AccessToken(
            token=access_token_str,
            token_type=TokenType.BEARER.value,
            client_id=client.client_id,
            user_id=user_id,
            scopes=scopes,
            expires_at=now + 3600,  # 1 hour
            issued_at=now
        )
        self.access_tokens[access_token_str] = access_token
        
        # Generate refresh token
        refresh_token_str = secrets.token_urlsafe(32)
        refresh_token = RefreshToken(
            token=refresh_token_str,
            client_id=client.client_id,
            user_id=user_id,
            scopes=scopes,
            expires_at=now + 2592000  # 30 days
        )
        self.refresh_tokens[refresh_token_str] = refresh_token
        
        response = {
            "access_token": access_token_str,
            "token_type": TokenType.BEARER.value,
            "expires_in": 3600,
            "refresh_token": refresh_token_str,
            "scope": " ".join(scopes)
        }
        
        # Generate ID token if OpenID Connect scope is present
        if "openid" in scopes and user_id:
            user = self.users.get(user_id)
            if user:
                id_token = IDToken(
                    iss=self.issuer,
                    sub=user_id,
                    aud=client.client_id,
                    exp=int(now + 3600),
                    iat=int(now),
                    email=user.email if "email" in scopes else None,
                    email_verified=user.email_verified if "email" in scopes else None,
                    name=user.profile.get("name") if "profile" in scopes else None
                )
                response["id_token"] = id_token.to_jwt(self.jwt_secret)
        
        return response
    
    def introspect(
        self,
        token: str,
        token_type_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Introspect token to get metadata"""
        # Check if it's an access token
        if token in self.access_tokens:
            access_token = self.access_tokens[token]
            
            if access_token.is_expired():
                return {"active": False}
            
            return {
                "active": True,
                "client_id": access_token.client_id,
                "username": access_token.user_id,
                "scope": " ".join(access_token.scopes),
                "exp": int(access_token.expires_at),
                "iat": int(access_token.issued_at),
                "token_type": access_token.token_type
            }
        
        # Check if it's a refresh token
        if token in self.refresh_tokens:
            refresh_token = self.refresh_tokens[token]
            
            if refresh_token.is_expired():
                return {"active": False}
            
            return {
                "active": True,
                "client_id": refresh_token.client_id,
                "username": refresh_token.user_id,
                "scope": " ".join(refresh_token.scopes),
                "token_type": "refresh_token"
            }
        
        return {"active": False}
    
    def revoke(self, token: str, token_type_hint: Optional[str] = None) -> bool:
        """Revoke a token"""
        # Try to revoke access token
        if token in self.access_tokens:
            del self.access_tokens[token]
            return True
        
        # Try to revoke refresh token
        if token in self.refresh_tokens:
            del self.refresh_tokens[token]
            return True
        
        return False
    
    def userinfo(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token"""
        # Validate access token
        if access_token not in self.access_tokens:
            return {"error": "invalid_token"}
        
        token = self.access_tokens[access_token]
        
        # Check if token is expired
        if token.is_expired():
            return {"error": "invalid_token"}
        
        # Check if openid scope is present
        if "openid" not in token.scopes:
            return {"error": "insufficient_scope"}
        
        # Get user
        if not token.user_id:
            return {"error": "invalid_token"}
        
        user = self.users.get(token.user_id)
        if not user:
            return {"error": "invalid_token"}
        
        # Build userinfo response
        userinfo = {"sub": user.user_id}
        
        if "profile" in token.scopes:
            userinfo.update(user.profile)
        
        if "email" in token.scopes:
            userinfo["email"] = user.email
            userinfo["email_verified"] = user.email_verified
        
        if "phone" in token.scopes:
            userinfo["phone_number"] = user.phone_number
            userinfo["phone_number_verified"] = user.phone_number_verified
        
        return userinfo
    
    def get_discovery_document(self) -> Dict[str, Any]:
        """Get OpenID Connect discovery document"""
        return {
            "issuer": self.issuer,
            "authorization_endpoint": f"{self.issuer}/authorize",
            "token_endpoint": f"{self.issuer}/token",
            "userinfo_endpoint": f"{self.issuer}/userinfo",
            "introspection_endpoint": f"{self.issuer}/introspect",
            "revocation_endpoint": f"{self.issuer}/revoke",
            "jwks_uri": f"{self.issuer}/.well-known/jwks.json",
            "response_types_supported": ["code", "token", "id_token", "code token", "code id_token", "token id_token"],
            "grant_types_supported": ["authorization_code", "implicit", "password", "client_credentials", "refresh_token"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["HS256"],
            "scopes_supported": list(self.supported_scopes),
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
            "claims_supported": ["sub", "iss", "aud", "exp", "iat", "auth_time", "nonce", "email", "email_verified", "name"]
        }


if __name__ == "__main__":
    # Example usage
    server = OAuthServer(issuer="https://auth.example.com")
    
    # Register a client
    client = server.register_client(
        client_id="webapp123",
        client_secret="secret456",
        redirect_uris=["https://webapp.example.com/callback"],
        grant_types=["authorization_code", "refresh_token", "password"],
        response_types=["code"],
        scopes=["openid", "profile", "email", "read", "write"],
        client_name="Example Web App"
    )
    
    # Register a user
    user = server.register_user(
        user_id="user123",
        username="john.doe",
        password="password123",
        email="john.doe@example.com",
        profile={"name": "John Doe", "given_name": "John", "family_name": "Doe"}
    )
    
    print("=== OAuth 2.0/OIDC Server Emulator Demo ===\n")
    
    # 1. Authorization Code Flow
    print("1. Authorization Code Flow")
    print("-" * 50)
    
    # Initiate authorization
    auth_request = server.authorize(
        client_id="webapp123",
        response_type="code",
        redirect_uri="https://webapp.example.com/callback",
        scope="openid profile email",
        state="xyz123"
    )
    print(f"Authorization Request: {json.dumps(auth_request, indent=2)}")
    
    # User grants authorization
    redirect_url = server.grant_authorization(
        user_id="user123",
        client_id="webapp123",
        redirect_uri="https://webapp.example.com/callback",
        scopes={"openid", "profile", "email"},
        state="xyz123"
    )
    print(f"\nRedirect URL: {redirect_url}")
    
    # Extract code from redirect URL
    code = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_url).query)["code"][0]
    
    # Exchange code for tokens
    token_response = server.token(
        grant_type="authorization_code",
        client_id="webapp123",
        client_secret="secret456",
        code=code,
        redirect_uri="https://webapp.example.com/callback"
    )
    print(f"\nToken Response: {json.dumps({k: v[:20] + '...' if isinstance(v, str) and len(v) > 20 else v for k, v in token_response.items()}, indent=2)}")
    
    access_token = token_response["access_token"]
    
    # 2. Get user info
    print("\n2. UserInfo Endpoint")
    print("-" * 50)
    userinfo = server.userinfo(access_token)
    print(f"UserInfo: {json.dumps(userinfo, indent=2)}")
    
    # 3. Token introspection
    print("\n3. Token Introspection")
    print("-" * 50)
    introspection = server.introspect(access_token)
    print(f"Token Introspection: {json.dumps(introspection, indent=2)}")
    
    # 4. Password Grant
    print("\n4. Resource Owner Password Credentials Flow")
    print("-" * 50)
    password_token = server.token(
        grant_type="password",
        client_id="webapp123",
        client_secret="secret456",
        username="john.doe",
        password="password123",
        scope="openid email"
    )
    print(f"Password Grant Token: {json.dumps({k: v[:20] + '...' if isinstance(v, str) and len(v) > 20 else v for k, v in password_token.items()}, indent=2)}")
    
    # 5. Refresh token
    print("\n5. Refresh Token Flow")
    print("-" * 50)
    refresh_token = token_response["refresh_token"]
    refreshed_token = server.token(
        grant_type="refresh_token",
        client_id="webapp123",
        client_secret="secret456",
        refresh_token=refresh_token
    )
    print(f"Refreshed Token: {json.dumps({k: v[:20] + '...' if isinstance(v, str) and len(v) > 20 else v for k, v in refreshed_token.items()}, indent=2)}")
    
    # 6. Token revocation
    print("\n6. Token Revocation")
    print("-" * 50)
    revoked = server.revoke(access_token)
    print(f"Token Revoked: {revoked}")
    
    # Try to use revoked token
    introspection_after_revoke = server.introspect(access_token)
    print(f"Introspection After Revocation: {json.dumps(introspection_after_revoke, indent=2)}")
    
    # 7. Discovery document
    print("\n7. OpenID Connect Discovery Document")
    print("-" * 50)
    discovery = server.get_discovery_document()
    print(f"Discovery Document: {json.dumps(discovery, indent=2)}")
