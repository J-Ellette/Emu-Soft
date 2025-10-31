# itsdangerous Emulator

A Python implementation that emulates the popular `itsdangerous` library for safely signing and verifying data.

## Overview

This module provides cryptographic signing utilities to securely sign data and verify signatures. It's commonly used for:
- Session management
- Token generation (e.g., password reset tokens)
- Cookie signing
- API signatures
- Any scenario where you need to verify data hasn't been tampered with

## Features

- **Basic Signing**: Sign and verify data with HMAC-based signatures
- **Timestamp Signing**: Add timestamps to signatures for expiration support
- **Serialization**: Sign complex data structures (dicts, lists, etc.)
- **Timed Serialization**: Serialize with expiration support
- **URL-Safe Encoding**: All signatures are URL-safe by default
- **Constant-Time Comparison**: Protection against timing attacks
- **Key Derivation**: Multiple key derivation methods (django-concat, hmac, concat)
- **Compression**: Automatic compression for large payloads

## Components

### Signer
Basic signer for signing and verifying simple data.

```python
from itsdangerous_emulator import Signer

# Create a signer
signer = Signer('my-secret-key')

# Sign data
signed = signer.sign('my-data')
# Returns: b'my-data.signature'

# Verify and unsign
original = signer.unsign(signed)
# Returns: b'my-data'
```

### TimestampSigner
Signer that adds timestamps for expiration support.

```python
from itsdangerous_emulator import TimestampSigner, SignatureExpired

# Create a timestamp signer
signer = TimestampSigner('my-secret-key')

# Sign with timestamp
signed = signer.sign('my-data')

# Unsign with max age check (in seconds)
try:
    original = signer.unsign(signed, max_age=3600)  # Valid for 1 hour
except SignatureExpired:
    print("Signature expired!")

# Get timestamp along with data
data, timestamp = signer.unsign(signed, return_timestamp=True)
```

### Serializer
Sign complex data structures (dicts, lists, etc.).

```python
from itsdangerous_emulator import Serializer

# Create a serializer
serializer = Serializer('my-secret-key')

# Serialize and sign
data = {'user_id': 123, 'username': 'john'}
signed = serializer.dumps(data)
# Returns: URL-safe signed string

# Deserialize and verify
original = serializer.loads(signed)
# Returns: {'user_id': 123, 'username': 'john'}
```

### TimedSerializer
Serialize with expiration support.

```python
from itsdangerous_emulator import TimedSerializer, SignatureExpired

# Create a timed serializer
serializer = TimedSerializer('my-secret-key')

# Serialize with timestamp
data = {'user_id': 123, 'action': 'reset_password'}
token = serializer.dumps(data)

# Deserialize with expiration check
try:
    original = serializer.loads(token, max_age=3600)  # Valid for 1 hour
except SignatureExpired:
    print("Token expired!")
```

## Common Use Cases

### 1. Session Management
```python
from itsdangerous_emulator import URLSafeSerializer

serializer = URLSafeSerializer('session-secret-key')

# Create session token
session_data = {'user_id': 123, 'role': 'admin'}
session_token = serializer.dumps(session_data)

# Store in cookie or send to client
# ...

# Later, verify and load session
try:
    session = serializer.loads(session_token)
    print(f"User {session['user_id']} is logged in")
except BadSignature:
    print("Invalid session!")
```

### 2. Password Reset Tokens
```python
from itsdangerous_emulator import URLSafeTimedSerializer, SignatureExpired

serializer = URLSafeTimedSerializer('password-reset-secret')

# Generate reset token
token = serializer.dumps({'user_id': 123, 'email': 'user@example.com'})

# Send token via email
# ...

# Later, verify token (valid for 1 hour)
try:
    data = serializer.loads(token, max_age=3600)
    user_id = data['user_id']
    # Allow password reset for user_id
except SignatureExpired:
    print("Reset link expired")
except BadSignature:
    print("Invalid reset link")
```

### 3. API Token Generation
```python
from itsdangerous_emulator import TimestampSigner

signer = TimestampSigner('api-secret-key')

# Generate API token
api_key = f"user_123_{int(time.time())}"
token = signer.sign(api_key)

# Verify API token (valid for 24 hours)
try:
    verified_key = signer.unsign(token, max_age=86400)
    print(f"Valid API key: {verified_key}")
except SignatureExpired:
    print("API token expired")
```

### 4. Cookie Signing
```python
from itsdangerous_emulator import Signer

signer = Signer('cookie-secret')

# Sign cookie value
cookie_value = 'user_preferences_data'
signed_cookie = signer.sign(cookie_value)

# Store in browser cookie
# ...

# Later, verify cookie
try:
    original_value = signer.unsign(signed_cookie)
    # Use original_value
except BadSignature:
    print("Cookie has been tampered with!")
```

## Security Features

### Constant-Time Comparison
All signature verification uses constant-time comparison to prevent timing attacks:

```python
from itsdangerous_emulator import _constant_time_compare

# Safe comparison
is_equal = _constant_time_compare(b'signature1', b'signature2')
```

### Key Derivation
Multiple key derivation methods are supported:

```python
from itsdangerous_emulator import Signer

# Django-style key derivation (default)
signer1 = Signer('secret', key_derivation='django-concat')

# HMAC-based key derivation
signer2 = Signer('secret', key_derivation='hmac')

# Simple concatenation
signer3 = Signer('secret', key_derivation='concat')
```

### Salt
Salt values ensure different signatures for different purposes:

```python
from itsdangerous_emulator import Signer

# Different salts produce different signatures
session_signer = Signer('secret', salt=b'session')
api_signer = Signer('secret', salt=b'api-token')

# Same data, different signatures
session_token = session_signer.sign('user-123')
api_token = api_signer.sign('user-123')
# session_token != api_token
```

## Exceptions

- **BadSignature**: Base exception for signature errors
- **BadTimeSignature**: Timestamp-related signature errors
- **SignatureExpired**: Signature has exceeded max_age
- **BadPayload**: Payload cannot be decoded/deserialized

## Convenience Functions

```python
from itsdangerous_emulator import sign, unsign

# Quick signing
signed = sign('my-data', 'secret-key')

# Quick unsigning
original = unsign(signed, 'secret-key')
```

## Implementation Details

- Uses HMAC-SHA1 by default (configurable)
- URL-safe Base64 encoding without padding
- Automatic compression for large payloads (using zlib)
- JSON serialization for complex data structures
- Protection against timing attacks
- Compatible with the original itsdangerous API

## Dependencies

Uses only Python standard library:
- `hmac` - HMAC message authentication
- `hashlib` - Hash functions
- `json` - JSON serialization
- `base64` - Base64 encoding
- `time` - Timestamp handling
- `zlib` - Data compression

## Testing

Run the test suite:

```bash
python test_itsdangerous_emulator.py
```

Tests cover:
- Basic signing and verification
- Timestamp signing with expiration
- Serialization of complex data structures
- Error handling and edge cases
- Security features (timing attacks, tampering)
- Unicode and binary data
- Compression

## Use Cases in Web Applications

1. **Session Management**: Securely store session data in cookies
2. **CSRF Protection**: Generate and verify CSRF tokens
3. **Password Reset**: Create time-limited password reset links
4. **Email Verification**: Generate email confirmation tokens
5. **API Authentication**: Create signed API tokens
6. **Remember Me**: Implement secure "remember me" functionality
7. **Single Sign-On**: Generate and verify SSO tokens
8. **Rate Limiting**: Create signed tokens for rate limit tracking

## Best Practices

1. **Use Strong Secret Keys**: Generate cryptographically secure random keys
2. **Rotate Keys Periodically**: Change secret keys on a regular schedule
3. **Use Appropriate max_age**: Set reasonable expiration times for tokens
4. **Use Different Salts**: Use different salts for different purposes
5. **Store Secrets Securely**: Never commit secrets to version control
6. **Validate All Input**: Always validate data after unsigning
7. **Use HTTPS**: Only transmit tokens over secure connections

## Example: Complete Session System

```python
from itsdangerous_emulator import URLSafeTimedSerializer, SignatureExpired, BadSignature

class SessionManager:
    def __init__(self, secret_key):
        self.serializer = URLSafeTimedSerializer(secret_key)
        self.max_age = 3600 * 24  # 24 hours
    
    def create_session(self, user_id, user_data):
        """Create a new session token"""
        session_data = {
            'user_id': user_id,
            'data': user_data,
        }
        return self.serializer.dumps(session_data)
    
    def load_session(self, token):
        """Load and verify a session token"""
        try:
            session_data = self.serializer.loads(token, max_age=self.max_age)
            return session_data
        except SignatureExpired:
            raise Exception("Session expired - please log in again")
        except BadSignature:
            raise Exception("Invalid session token")

# Usage
session_mgr = SessionManager('my-secret-key')

# Create session
token = session_mgr.create_session(123, {'username': 'john', 'role': 'admin'})

# Later, load session
try:
    session = session_mgr.load_session(token)
    print(f"User {session['user_id']} loaded")
except Exception as e:
    print(f"Session error: {e}")
```

## License

This is an emulation/recreation of the itsdangerous library for educational purposes. The original itsdangerous library is created by Armin Ronacher and the Pallets team.
