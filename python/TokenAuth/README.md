# PyJWT Emulator - JSON Web Token Implementation

A Python implementation that emulates the core functionality of PyJWT, the most popular JWT (JSON Web Token) library for Python.

## Overview

This emulator provides a complete JWT implementation for encoding, decoding, and validating JSON Web Tokens, following the JWT standard (RFC 7519) without external dependencies.

## Features

### Core Functionality
- **Token Encoding**: Create JWT tokens with any payload
- **Token Decoding**: Decode and verify JWT tokens
- **Signature Verification**: HMAC-based signature algorithms (HS256, HS384, HS512)
- **Claims Validation**: Automatic validation of standard JWT claims
- **Custom Headers**: Support for custom JWT headers
- **Flexible Options**: Configurable verification options

### Supported Algorithms
- HS256 (HMAC with SHA-256) - Default
- HS384 (HMAC with SHA-384)
- HS512 (HMAC with SHA-512)
- none (Unsigned tokens)

### Standard Claims Support
- **exp** (Expiration Time): Token expiration validation
- **nbf** (Not Before): Token validity start time
- **iat** (Issued At): Token issuance time
- **aud** (Audience): Intended token audience
- **iss** (Issuer): Token issuer
- **sub** (Subject): Token subject
- **jti** (JWT ID): Unique token identifier

### Exception Hierarchy
Complete exception hierarchy for error handling:
- `PyJWTError` - Base exception
- `InvalidTokenError` - Invalid token format or claims
- `DecodeError` - Token decoding errors
- `InvalidSignatureError` - Signature verification failure
- `ExpiredSignatureError` - Token has expired
- `InvalidAudienceError` - Audience mismatch
- `InvalidIssuerError` - Issuer mismatch
- `InvalidIssuedAtError` - Invalid issued at time
- `ImmatureSignatureError` - Token not yet valid (nbf)
- `MissingRequiredClaimError` - Required claim missing

## Usage

### Basic Token Creation

```python
from pyjwt_emulator import encode, decode

# Create a token
payload = {
    'user_id': 123,
    'username': 'john_doe',
    'role': 'admin'
}
secret = 'your-secret-key'

token = encode(payload, secret, algorithm='HS256')
print(token)
# eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxMjMsInVzZXJuYW1lIjoiam9obl9kb2UiLCJyb2xlIjoiYWRtaW4ifQ...
```

### Decoding and Verifying Tokens

```python
from pyjwt_emulator import decode

# Decode and verify a token
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
secret = 'your-secret-key'

try:
    payload = decode(token, secret, algorithms=['HS256'])
    print(f"User ID: {payload['user_id']}")
    print(f"Username: {payload['username']}")
except Exception as e:
    print(f"Token validation failed: {e}")
```

### Token with Expiration

```python
from datetime import datetime, timedelta
from pyjwt_emulator import encode, decode

# Create token that expires in 1 hour
payload = {
    'user_id': 123,
    'exp': datetime.utcnow() + timedelta(hours=1),
    'iat': datetime.utcnow()
}

token = encode(payload, 'secret', algorithm='HS256')

# Decode - will fail if expired
try:
    decoded = decode(token, 'secret', algorithms=['HS256'])
    print("Token is valid")
except ExpiredSignatureError:
    print("Token has expired")
```

### Helper Function for Expiration

```python
from pyjwt_emulator import create_token_with_expiration

# Create token with expiration (in seconds)
payload = {'user_id': 123, 'role': 'user'}
token = create_token_with_expiration(payload, 'secret', expires_in=3600)

# Or with timedelta
from datetime import timedelta
token = create_token_with_expiration(
    payload, 'secret', 
    expires_in=timedelta(hours=1)
)
```

### Audience and Issuer Claims

```python
from pyjwt_emulator import encode, decode

# Create token with audience and issuer
payload = {
    'user_id': 123,
    'aud': 'my-app',
    'iss': 'my-auth-service'
}

token = encode(payload, 'secret')

# Verify with expected audience and issuer
decoded = decode(
    token, 
    'secret',
    algorithms=['HS256'],
    audience='my-app',
    issuer='my-auth-service'
)
```

### Multiple Audiences

```python
# Token for multiple audiences
payload = {
    'user_id': 123,
    'aud': ['web-app', 'mobile-app', 'api']
}

token = encode(payload, 'secret')

# Verify for any of the audiences
decoded = decode(token, 'secret', algorithms=['HS256'], audience='web-app')
decoded = decode(token, 'secret', algorithms=['HS256'], audience='mobile-app')
```

### Time Leeway

```python
from pyjwt_emulator import decode, ExpiredSignatureError

# Token that expired 5 seconds ago
# ... (token creation)

# Decode with 10 second leeway
try:
    decoded = decode(token, 'secret', algorithms=['HS256'], leeway=10)
    print("Token accepted with leeway")
except ExpiredSignatureError:
    print("Token expired beyond leeway")
```

### Custom Headers

```python
from pyjwt_emulator import encode, get_unverified_header

# Create token with custom headers
payload = {'user_id': 123}
headers = {
    'kid': 'key-2024-01',  # Key ID
    'custom': 'value'
}

token = encode(payload, 'secret', headers=headers)

# Get header without verification
header = get_unverified_header(token)
print(header['kid'])  # 'key-2024-01'
print(header['alg'])  # 'HS256'
print(header['typ'])  # 'JWT'
```

### Decode Without Verification

```python
from pyjwt_emulator import decode

# Decode without verifying signature (useful for debugging)
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'

payload = decode(token, verify=False)
print(payload)
```

### Decode Complete Token

```python
from pyjwt_emulator import decode_complete

# Get all token components
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'

result = decode_complete(token, 'secret', algorithms=['HS256'])

print(result['header'])    # Token header
print(result['payload'])   # Token payload
print(result['signature']) # Token signature (base64url encoded)
```

### Different Algorithms

```python
from pyjwt_emulator import encode, decode

payload = {'user_id': 123}
secret = 'your-secret-key'

# HS256 (default)
token_256 = encode(payload, secret, algorithm='HS256')
decoded = decode(token_256, secret, algorithms=['HS256'])

# HS384
token_384 = encode(payload, secret, algorithm='HS384')
decoded = decode(token_384, secret, algorithms=['HS384'])

# HS512
token_512 = encode(payload, secret, algorithm='HS512')
decoded = decode(token_512, secret, algorithms=['HS512'])
```

### Custom Verification Options

```python
from pyjwt_emulator import decode

token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'

# Custom verification options
options = {
    'verify_signature': True,
    'verify_exp': True,
    'verify_nbf': True,
    'verify_iat': True,
    'verify_aud': False,  # Don't verify audience
    'verify_iss': False,  # Don't verify issuer
    'require_exp': True,  # Require exp claim
    'require_iat': False,
    'require_nbf': False,
}

decoded = decode(token, 'secret', algorithms=['HS256'], options=options)
```

### Error Handling

```python
from pyjwt_emulator import (
    decode, 
    InvalidSignatureError,
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    DecodeError
)

token = 'some-jwt-token'
secret = 'secret'

try:
    payload = decode(token, secret, algorithms=['HS256'])
    print(f"Valid token for user: {payload['user_id']}")
    
except InvalidSignatureError:
    print("Token signature is invalid")
    
except ExpiredSignatureError:
    print("Token has expired")
    
except InvalidAudienceError:
    print("Token audience doesn't match")
    
except InvalidIssuerError:
    print("Token issuer doesn't match")
    
except DecodeError as e:
    print(f"Token decoding failed: {e}")
```

## Token Structure

A JWT consists of three parts separated by dots (.):

```
header.payload.signature
```

### Header
Contains token metadata:
```json
{
  "typ": "JWT",
  "alg": "HS256"
}
```

### Payload
Contains the claims (data):
```json
{
  "user_id": 123,
  "username": "john_doe",
  "exp": 1672531200,
  "iat": 1672527600
}
```

### Signature
HMAC signature of `base64url(header).base64url(payload)` using the secret key.

## Standard Claims

### Registered Claims

- **iss** (Issuer): Identifies who issued the token
- **sub** (Subject): Identifies the subject of the token
- **aud** (Audience): Identifies the recipients of the token
- **exp** (Expiration Time): Time after which token is invalid (Unix timestamp)
- **nbf** (Not Before): Time before which token is invalid (Unix timestamp)
- **iat** (Issued At): Time at which token was issued (Unix timestamp)
- **jti** (JWT ID): Unique identifier for the token

### Custom Claims

You can add any custom claims to your payload:

```python
payload = {
    'user_id': 123,
    'username': 'john_doe',
    'role': 'admin',
    'permissions': ['read', 'write', 'delete'],
    'tenant_id': 'acme-corp'
}
```

## Security Considerations

### Secret Key
- Use a strong, random secret key
- Keep the secret key confidential
- Use different keys for different environments
- Rotate keys periodically

```python
import secrets

# Generate a secure random key
secret = secrets.token_urlsafe(32)
```

### Token Expiration
- Always set an expiration time (exp claim)
- Use short expiration times for sensitive operations
- Implement token refresh mechanisms for long sessions

### Algorithm Selection
- HS256 is suitable for most use cases
- HS384 and HS512 provide stronger security but larger tokens
- Never use 'none' algorithm in production

### Validation
- Always validate tokens on the server side
- Verify all relevant claims (exp, aud, iss)
- Use HTTPS to prevent token interception

## Implementation Notes

### Simulated vs. Real Implementation

This is an **emulator** designed for:
- Learning JWT concepts and implementation
- Testing JWT-based authentication without external dependencies
- Understanding token structure and validation
- Prototyping authentication systems

**Not suitable for:**
- Production authentication in security-critical applications (use the real PyJWT library)
- Applications requiring RSA or ECDSA algorithms
- Applications requiring advanced JWT features

### Key Differences from PyJWT

1. **Limited Algorithms**: Only HMAC algorithms (HS256, HS384, HS512)
   - Missing: RSA (RS256, RS384, RS512)
   - Missing: ECDSA (ES256, ES384, ES512)
   - Missing: PSS (PS256, PS384, PS512)

2. **No JWK Support**: JSON Web Key (JWK) handling not implemented

3. **No JWS/JWE**: Only basic JWT, no advanced JWS/JWE features

4. **Simplified API**: Some advanced PyJWT features not included

## Testing

Run the test suite:

```bash
cd pyjwt_emulator_tool
python -m pytest test_pyjwt_emulator.py -v
```

Or using unittest:

```bash
python test_pyjwt_emulator.py
```

Test coverage includes:
- Token encoding with various payloads
- Token decoding and verification
- Signature verification
- Claims validation (exp, nbf, iat, aud, iss)
- Time leeway handling
- Custom headers
- Error handling
- Different algorithms
- Edge cases

## Compatibility

- Python 3.6+
- No external dependencies (uses only standard library)
- Cross-platform (Windows, macOS, Linux)

## Use Cases

1. **Authentication**: User authentication tokens
2. **API Authorization**: API access tokens
3. **Single Sign-On**: SSO tokens
4. **Information Exchange**: Secure data exchange between parties
5. **Temporary Permissions**: Time-limited access tokens
6. **Microservices**: Service-to-service authentication

## Best Practices

1. **Always set expiration**: Include `exp` claim in all tokens
2. **Use strong secrets**: Generate cryptographically random secrets
3. **Validate thoroughly**: Verify all relevant claims
4. **Keep tokens short-lived**: Use refresh tokens for long sessions
5. **Store securely**: Never store tokens in localStorage without encryption
6. **Transmit securely**: Always use HTTPS
7. **Handle errors gracefully**: Implement proper error handling
8. **Rotate secrets**: Periodically rotate signing keys
9. **Monitor usage**: Log token creation and validation events
10. **Revocation strategy**: Implement token blacklisting if needed

## Common Patterns

### Access Token + Refresh Token

```python
from pyjwt_emulator import encode
from datetime import timedelta

# Short-lived access token (15 minutes)
access_token = create_token_with_expiration(
    {'user_id': 123, 'type': 'access'},
    'secret',
    expires_in=timedelta(minutes=15)
)

# Long-lived refresh token (7 days)
refresh_token = create_token_with_expiration(
    {'user_id': 123, 'type': 'refresh'},
    'secret',
    expires_in=timedelta(days=7)
)
```

### Role-Based Access

```python
payload = {
    'user_id': 123,
    'username': 'john_doe',
    'roles': ['user', 'admin'],
    'permissions': ['read', 'write', 'delete']
}

token = encode(payload, 'secret')
```

### Multi-Tenant Applications

```python
payload = {
    'user_id': 123,
    'tenant_id': 'acme-corp',
    'tenant_name': 'ACME Corporation'
}

token = encode(payload, 'secret')
```

## References

- [JWT Specification (RFC 7519)](https://tools.ietf.org/html/rfc7519)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [jwt.io](https://jwt.io/) - JWT debugger and resources

## License

This is an original implementation created for educational and development purposes. It emulates the API of PyJWT but contains no code from the original project.
