# OAuth 2.0/OIDC Server Emulator - Authentication and Authorization

A lightweight emulation of **OAuth 2.0** and **OpenID Connect (OIDC)** server functionality for authentication and authorization.

## Features

This emulator implements core OAuth 2.0 and OIDC functionality:

### OAuth 2.0 Grant Types
- **Authorization Code Flow**: Most secure flow for web applications
- **Implicit Flow**: For browser-based applications (legacy)
- **Resource Owner Password Credentials**: Direct username/password exchange
- **Client Credentials**: For service-to-service authentication
- **Refresh Token**: Token renewal mechanism

### OpenID Connect
- **ID Token Generation**: JWT-based identity tokens
- **UserInfo Endpoint**: Get user profile information
- **Discovery Document**: Well-known OIDC configuration

### Token Management
- **Access Tokens**: Bearer tokens for API access
- **Refresh Tokens**: Long-lived tokens for token renewal
- **Token Introspection**: Query token metadata and validity
- **Token Revocation**: Invalidate tokens

### Client Management
- **Client Registration**: Register OAuth 2.0 clients
- **Redirect URI Validation**: Secure redirect handling
- **Scope Management**: Fine-grained permission control
- **Multiple Grant Type Support**: Per-client grant type configuration

### Security Features
- **PKCE Support**: Proof Key for Code Exchange
- **Scope Validation**: Enforce client scope permissions
- **Token Expiration**: Automatic token lifecycle management
- **Secure Token Generation**: Cryptographically secure tokens

## What It Emulates

This tool emulates core functionality of OAuth 2.0 and OpenID Connect (OIDC) authorization servers like:
- [Keycloak](https://www.keycloak.org/)
- [Auth0](https://auth0.com/)
- [Okta](https://www.okta.com/)
- [ORY Hydra](https://www.ory.sh/hydra/)

### Core Components Implemented

1. **OAuth 2.0 Core**
   - Authorization endpoint
   - Token endpoint
   - All standard grant types
   - Token introspection
   - Token revocation

2. **OpenID Connect**
   - ID token generation (JWT)
   - UserInfo endpoint
   - Discovery document
   - Standard OIDC scopes

3. **Client Management**
   - Client registration
   - Credential validation
   - Scope enforcement
   - Redirect URI validation

## Usage

### Basic Setup

```python
from oauth_server_emulator_tool import OAuthServer

# Create OAuth server
server = OAuthServer(issuer="https://auth.example.com")

# Register a client application
client = server.register_client(
    client_id="webapp123",
    client_secret="secret456",
    redirect_uris=["https://webapp.example.com/callback"],
    grant_types=["authorization_code", "refresh_token"],
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
    profile={"name": "John Doe"}
)
```

### Authorization Code Flow

```python
import urllib.parse

# Step 1: Initiate authorization
auth_request = server.authorize(
    client_id="webapp123",
    response_type="code",
    redirect_uri="https://webapp.example.com/callback",
    scope="openid profile email",
    state="xyz123"
)

# Step 2: User grants authorization
redirect_url = server.grant_authorization(
    user_id="user123",
    client_id="webapp123",
    redirect_uri="https://webapp.example.com/callback",
    scopes={"openid", "profile", "email"},
    state="xyz123"
)

# Step 3: Extract authorization code
code = urllib.parse.parse_qs(
    urllib.parse.urlparse(redirect_url).query
)["code"][0]

# Step 4: Exchange code for tokens
token_response = server.token(
    grant_type="authorization_code",
    client_id="webapp123",
    client_secret="secret456",
    code=code,
    redirect_uri="https://webapp.example.com/callback"
)

print(f"Access Token: {token_response['access_token']}")
print(f"ID Token: {token_response['id_token']}")
print(f"Refresh Token: {token_response['refresh_token']}")
```

### Password Grant Flow

```python
# Exchange username/password for tokens
token_response = server.token(
    grant_type="password",
    client_id="webapp123",
    client_secret="secret456",
    username="john.doe",
    password="password123",
    scope="openid email"
)

access_token = token_response["access_token"]
```

### Client Credentials Flow

```python
# Service-to-service authentication
token_response = server.token(
    grant_type="client_credentials",
    client_id="service123",
    client_secret="service_secret",
    scope="read write"
)
```

### Token Refresh

```python
# Refresh an expired access token
refresh_token = token_response["refresh_token"]

refreshed = server.token(
    grant_type="refresh_token",
    client_id="webapp123",
    client_secret="secret456",
    refresh_token=refresh_token
)

new_access_token = refreshed["access_token"]
```

### UserInfo Endpoint

```python
# Get user information using access token
userinfo = server.userinfo(access_token)

print(f"User ID: {userinfo['sub']}")
print(f"Email: {userinfo['email']}")
print(f"Name: {userinfo['name']}")
```

### Token Introspection

```python
# Check token validity and metadata
introspection = server.introspect(access_token)

if introspection["active"]:
    print(f"Token is active")
    print(f"Client ID: {introspection['client_id']}")
    print(f"Scopes: {introspection['scope']}")
    print(f"Expires: {introspection['exp']}")
else:
    print("Token is not active")
```

### Token Revocation

```python
# Revoke a token
revoked = server.revoke(access_token)

if revoked:
    print("Token revoked successfully")
```

### PKCE (Proof Key for Code Exchange)

```python
import hashlib
import base64
import secrets

# Generate code verifier and challenge
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()

# Initiate authorization with PKCE
auth_request = server.authorize(
    client_id="mobile_app",
    response_type="code",
    redirect_uri="myapp://callback",
    scope="openid profile",
    code_challenge=code_challenge,
    code_challenge_method="S256"
)

# Grant authorization
redirect_url = server.grant_authorization(
    user_id="user123",
    client_id="mobile_app",
    redirect_uri="myapp://callback",
    scopes={"openid", "profile"},
    code_challenge=code_challenge,
    code_challenge_method="S256"
)

# Extract code and exchange with verifier
code = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_url).query)["code"][0]

token_response = server.token(
    grant_type="authorization_code",
    client_id="mobile_app",
    client_secret="",
    code=code,
    redirect_uri="myapp://callback",
    code_verifier=code_verifier
)
```

### Discovery Document

```python
# Get OpenID Connect discovery document
discovery = server.get_discovery_document()

print(f"Issuer: {discovery['issuer']}")
print(f"Authorization Endpoint: {discovery['authorization_endpoint']}")
print(f"Token Endpoint: {discovery['token_endpoint']}")
print(f"Supported Scopes: {discovery['scopes_supported']}")
```

## Testing

```bash
python oauth_server_emulator_tool.py
```

The demo script will demonstrate:
1. Authorization code flow
2. UserInfo endpoint
3. Token introspection
4. Password grant flow
5. Refresh token flow
6. Token revocation
7. Discovery document

## Use Cases

1. **Development**: Test OAuth 2.0 integrations without external dependencies
2. **Learning**: Understand OAuth 2.0 and OIDC flows
3. **Testing**: Mock authentication for automated tests
4. **Prototyping**: Quick authentication setup for prototypes
5. **Education**: Teaching OAuth 2.0 concepts

## Supported Scopes

- `openid`: OpenID Connect authentication
- `profile`: User profile information
- `email`: Email address and verification status
- `phone`: Phone number and verification status
- `address`: Physical address
- `read`: Read access to resources
- `write`: Write access to resources
- `admin`: Administrative access

## Key Differences from Production OAuth Servers

1. **No Persistent Storage**: All data is in-memory
2. **Simple JWT**: Uses HMAC-SHA256, not RSA/ECDSA
3. **No Consent UI**: Authorization is granted programmatically
4. **Simplified Validation**: Basic validation only
5. **No Rate Limiting**: No throttling or abuse prevention
6. **No Multi-tenancy**: Single issuer only

## Security Considerations

This is an emulator for development and testing purposes. For production:
- Use established OAuth 2.0 servers (Keycloak, Auth0, etc.)
- Implement proper password hashing (bcrypt, Argon2)
- Use asymmetric JWT signing (RSA/ECDSA)
- Implement rate limiting and abuse detection
- Use HTTPS for all endpoints
- Store secrets securely (HSM, vault)
- Implement comprehensive audit logging

## License

Educational emulator for learning purposes.

## References

- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [OAuth 2.0 Token Introspection](https://tools.ietf.org/html/rfc7662)
- [OAuth 2.0 Token Revocation](https://tools.ietf.org/html/rfc7009)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
