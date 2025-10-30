# Cryptography Emulator

A Python implementation that emulates the popular `cryptography` library for modern cryptographic operations.

## Overview

This module provides comprehensive cryptographic primitives including:
- **Fernet**: Symmetric authenticated encryption
- **Hashing**: SHA1, SHA256, SHA512, MD5, BLAKE2, etc.
- **HMAC**: Hash-based Message Authentication Code
- **KDF**: Key Derivation Functions (PBKDF2, Scrypt, HKDF)
- **Padding**: PKCS7 padding for block ciphers
- **OTP**: Time-based (TOTP) and HMAC-based (HOTP) One-Time Passwords

## Features

- **Symmetric Encryption**: Fernet for secure authenticated encryption
- **Multiple Hash Algorithms**: SHA family, MD5, BLAKE2
- **Key Derivation**: Industry-standard KDFs for password hashing
- **Message Authentication**: HMAC for data integrity
- **Constant-Time Operations**: Protection against timing attacks
- **Two-Factor Authentication**: TOTP/HOTP implementations
- **Standard Compliance**: Follows cryptographic best practices

## Components

### Fernet - Symmetric Encryption

Fernet provides authenticated symmetric encryption with automatic key rotation support.

```python
from cryptography_emulator import Fernet

# Generate a key
key = Fernet.generate_key()
f = Fernet(key)

# Encrypt data
token = f.encrypt(b'secret message')

# Decrypt data
plaintext = f.decrypt(token)
print(plaintext)  # b'secret message'

# Decrypt with TTL (time-to-live)
try:
    plaintext = f.decrypt(token, ttl=3600)  # Valid for 1 hour
except InvalidToken:
    print("Token expired or invalid")
```

### MultiFernet - Key Rotation

Handle multiple keys for seamless key rotation:

```python
from cryptography_emulator import Fernet, MultiFernet

# Old and new keys
key1 = Fernet.generate_key()
key2 = Fernet.generate_key()

# Create MultiFernet with both keys
mf = MultiFernet([
    Fernet(key1),  # Current key (used for encryption)
    Fernet(key2),  # Old key (for decryption only)
])

# Encrypts with key1
token = mf.encrypt(b'data')

# Can decrypt with either key
plaintext = mf.decrypt(token)

# Rotate old tokens to new key
token_new = mf.rotate(token)
```

### Hashing

Compute cryptographic hashes of data:

```python
from cryptography_emulator import Hash, SHA256, hashes_Hash

# Method 1: Using Hash class
h = Hash('sha256')
h.update(b'hello ')
h.update(b'world')
digest = h.finalize()

# Method 2: Using hash algorithm objects
h = hashes_Hash(SHA256())
h.update(b'hello world')
digest = h.finalize()

# Available algorithms
from cryptography_emulator import (
    SHA1, SHA224, SHA256, SHA384, SHA512,
    SHA512_224, SHA512_256,
    MD5, BLAKE2b, BLAKE2s
)
```

### HMAC - Message Authentication

Generate and verify HMACs for data integrity:

```python
from cryptography_emulator import HMAC, SHA256

key = b'secret-key'

# Generate HMAC
h = HMAC(key, SHA256())
h.update(b'message to authenticate')
signature = h.finalize()

# Verify HMAC
h2 = HMAC(key, SHA256())
h2.update(b'message to authenticate')
try:
    h2.verify(signature)
    print("Signature valid!")
except InvalidSignature:
    print("Signature invalid!")
```

### PBKDF2HMAC - Password-Based Key Derivation

Derive keys from passwords using PBKDF2:

```python
from cryptography_emulator import PBKDF2HMAC, SHA256
import os

# Generate salt
salt = os.urandom(16)

# Create KDF
kdf = PBKDF2HMAC(
    algorithm=SHA256(),
    length=32,
    salt=salt,
    iterations=100000
)

# Derive key from password
key = kdf.derive(b'my-password')

# Verify password
kdf2 = PBKDF2HMAC(SHA256(), 32, salt, 100000)
try:
    kdf2.verify(b'my-password', key)
    print("Password correct!")
except InvalidKey:
    print("Password incorrect!")
```

### Scrypt - Memory-Hard Key Derivation

Use Scrypt for more secure password hashing:

```python
from cryptography_emulator import Scrypt
import os

salt = os.urandom(16)

# Create Scrypt KDF
kdf = Scrypt(
    salt=salt,
    length=32,
    n=2**14,  # CPU/memory cost
    r=8,      # Block size
    p=1       # Parallelization
)

# Derive key
key = kdf.derive(b'my-password')

# Verify password
kdf2 = Scrypt(salt, 32, n=2**14, r=8, p=1)
try:
    kdf2.verify(b'my-password', key)
    print("Password correct!")
except InvalidKey:
    print("Password incorrect!")
```

### HKDF - HMAC-Based Key Derivation

Derive multiple keys from a single secret:

```python
from cryptography_emulator import HKDF, SHA256
import os

# Input key material
ikm = b'shared-secret'
salt = os.urandom(16)
info = b'application-specific-context'

# Create HKDF
kdf = HKDF(
    algorithm=SHA256(),
    length=32,
    salt=salt,
    info=info
)

# Derive key
key = kdf.derive(ikm)

# Derive different keys with different info
kdf_enc = HKDF(SHA256(), 32, salt, b'encryption')
kdf_auth = HKDF(SHA256(), 32, salt, b'authentication')

encryption_key = kdf_enc.derive(ikm)
auth_key = kdf_auth.derive(ikm)
```

### PKCS7 Padding

Pad data for block ciphers:

```python
from cryptography_emulator import PKCS7

# Create padder for 128-bit blocks (16 bytes)
padder = PKCS7(128)

# Pad data
data = b'hello world'
padded = padder.pad(data)

# Unpad data
unpadded = padder.unpad(padded)
assert unpadded == data
```

### TOTP - Time-Based One-Time Password

Implement two-factor authentication:

```python
from cryptography_emulator import TOTP
import os

# Generate secret key (share with user)
key = os.urandom(20)

# Create TOTP generator
totp = TOTP(key, length=6, time_step=30)

# Generate current code
code = totp.generate()
print(f"Current code: {code}")

# Verify code
if totp.verify(code):
    print("Code is valid!")
else:
    print("Code is invalid!")

# Codes change every 30 seconds
import time
time.sleep(30)
new_code = totp.generate()
print(f"New code: {new_code}")
```

### HOTP - HMAC-Based One-Time Password

Counter-based one-time passwords:

```python
from cryptography_emulator import HOTP
import os

# Generate secret key
key = os.urandom(20)

# Create HOTP generator
hotp = HOTP(key, length=6)

# Generate codes with counter
code_0 = hotp.generate(0)
code_1 = hotp.generate(1)
code_2 = hotp.generate(2)

# Verify code
if hotp.verify(code_1, 1):
    print("Code is valid!")
```

## Common Use Cases

### 1. Secure Session Tokens

```python
from cryptography_emulator import Fernet
import json

key = Fernet.generate_key()
f = Fernet(key)

# Create session token
session_data = {'user_id': 123, 'role': 'admin'}
token = f.encrypt(json.dumps(session_data).encode())

# Later, verify and load session
try:
    data = json.loads(f.decrypt(token, ttl=3600))
    print(f"User {data['user_id']} logged in")
except InvalidToken:
    print("Session expired or invalid")
```

### 2. Password Storage

```python
from cryptography_emulator import PBKDF2HMAC, SHA256
import os
import base64

def hash_password(password: str) -> str:
    """Hash a password for storage"""
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(SHA256(), 32, salt, 100000)
    key = kdf.derive(password.encode())
    
    # Store salt and key together
    return base64.b64encode(salt + key).decode()

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash"""
    data = base64.b64decode(stored_hash)
    salt = data[:16]
    stored_key = data[16:]
    
    kdf = PBKDF2HMAC(SHA256(), 32, salt, 100000)
    try:
        kdf.verify(password.encode(), stored_key)
        return True
    except InvalidKey:
        return False

# Usage
hashed = hash_password('my-secure-password')
print(verify_password('my-secure-password', hashed))  # True
print(verify_password('wrong-password', hashed))      # False
```

### 3. API Signature Verification

```python
from cryptography_emulator import HMAC, SHA256

def sign_request(secret_key: bytes, data: bytes) -> bytes:
    """Sign API request"""
    h = HMAC(secret_key, SHA256())
    h.update(data)
    return h.finalize()

def verify_request(secret_key: bytes, data: bytes, signature: bytes) -> bool:
    """Verify API request signature"""
    h = HMAC(secret_key, SHA256())
    h.update(data)
    try:
        h.verify(signature)
        return True
    except InvalidSignature:
        return False

# Usage
secret = b'shared-api-secret'
request_data = b'{"user": "john", "action": "read"}'

# Client signs request
signature = sign_request(secret, request_data)

# Server verifies request
if verify_request(secret, request_data, signature):
    print("Request authenticated!")
```

### 4. Two-Factor Authentication

```python
from cryptography_emulator import TOTP
import os
import qrcode  # External package for QR generation

def setup_2fa(username: str):
    """Setup 2FA for user"""
    # Generate secret
    secret = os.urandom(20)
    
    # Create TOTP generator
    totp = TOTP(secret)
    
    # Generate QR code for user
    # (In real app, encode secret as base32 for compatibility)
    uri = f"otpauth://totp/{username}?secret={secret.hex()}"
    
    return secret, uri

def verify_2fa_code(secret: bytes, code: str) -> bool:
    """Verify 2FA code"""
    totp = TOTP(secret)
    return totp.verify(code)

# Setup for user
secret, qr_uri = setup_2fa('john@example.com')
print(f"Scan QR code: {qr_uri}")

# User enters code from authenticator app
user_code = "123456"  # From authenticator app
if verify_2fa_code(secret, user_code):
    print("2FA code verified!")
```

### 5. File Encryption

```python
from cryptography_emulator import Fernet

def encrypt_file(filename: str, key: bytes):
    """Encrypt a file"""
    f = Fernet(key)
    
    with open(filename, 'rb') as file:
        data = file.read()
    
    encrypted = f.encrypt(data)
    
    with open(filename + '.enc', 'wb') as file:
        file.write(encrypted)

def decrypt_file(filename: str, key: bytes):
    """Decrypt a file"""
    f = Fernet(key)
    
    with open(filename, 'rb') as file:
        encrypted = file.read()
    
    try:
        decrypted = f.decrypt(encrypted)
        
        output_name = filename.replace('.enc', '')
        with open(output_name, 'wb') as file:
            file.write(decrypted)
        
        return True
    except InvalidToken:
        return False

# Usage
key = Fernet.generate_key()
encrypt_file('secret.txt', key)
decrypt_file('secret.txt.enc', key)
```

## Security Considerations

1. **Use Strong Keys**: Always generate keys with cryptographically secure random number generators
2. **Key Storage**: Never store keys in code or version control
3. **Key Derivation**: Use appropriate iteration counts (100,000+ for PBKDF2)
4. **Time Synchronization**: TOTP requires accurate system time
5. **Constant-Time Operations**: All comparison operations use constant-time functions to prevent timing attacks
6. **TTL for Tokens**: Always use TTL when decrypting Fernet tokens to limit token lifetime
7. **Salt Uniqueness**: Use unique salts for each password hash
8. **Algorithm Selection**: Prefer SHA256 or SHA512 over SHA1 or MD5

## Algorithm Information

### Hash Algorithms

| Algorithm | Digest Size | Security | Notes |
|-----------|-------------|----------|-------|
| SHA256    | 32 bytes    | High     | Recommended for general use |
| SHA512    | 64 bytes    | High     | Recommended for high security |
| SHA1      | 20 bytes    | Low      | Deprecated, not recommended |
| MD5       | 16 bytes    | Broken   | Not secure, legacy only |
| BLAKE2b   | 64 bytes    | High     | Modern, fast alternative |
| BLAKE2s   | 32 bytes    | High     | Faster on 32-bit platforms |

### Key Derivation Functions

| KDF        | Speed    | Memory Hard | Best For |
|------------|----------|-------------|----------|
| PBKDF2HMAC | Fast     | No          | General password hashing |
| Scrypt     | Slow     | Yes         | High-security password hashing |
| HKDF       | Very Fast| No          | Key expansion from secrets |

### Recommended Parameters

**PBKDF2HMAC:**
- Iterations: 100,000+ (increase over time)
- Algorithm: SHA256
- Key length: 32 bytes

**Scrypt:**
- n: 2^14 or higher (CPU/memory cost)
- r: 8 (block size)
- p: 1 (parallelization)
- Key length: 32 bytes

**Fernet:**
- Automatically uses 32-byte keys
- Built-in timestamp for expiration
- AES-128 in CBC mode (simplified in this implementation)

## Implementation Notes

This is an educational implementation that demonstrates cryptographic concepts. Some differences from the production `cryptography` library:

1. **Fernet Encryption**: Uses simplified XOR-based encryption instead of AES-128-CBC for educational purposes. In production, use proper AES encryption.
2. **Scrypt Fallback**: Falls back to PBKDF2 if `hashlib.scrypt` is not available (Python < 3.6)
3. **No Asymmetric Crypto**: This implementation focuses on symmetric cryptography
4. **Simplified OTP**: TOTP/HOTP use basic implementations suitable for educational purposes

For production use, please use the official `cryptography` library which has:
- Proper AES encryption
- Full asymmetric cryptography support
- Hardware acceleration
- Extensive security audits
- Professional maintenance

## Dependencies

Uses only Python standard library:
- `hashlib` - Hash functions and KDFs
- `hmac` - HMAC operations
- `os` - Secure random number generation
- `base64` - Base64 encoding
- `struct` - Binary data packing
- `time` - Timestamp handling

## Testing

Run the test suite:

```bash
python test_cryptography_emulator.py
```

Tests cover:
- Fernet encryption/decryption (12 tests)
- MultiFernet key rotation (4 tests)
- Hash algorithms (4 tests)
- HMAC operations (4 tests)
- PBKDF2HMAC (6 tests)
- Scrypt (3 tests)
- HKDF (4 tests)
- PKCS7 padding (5 tests)
- TOTP (5 tests)
- HOTP (4 tests)
- Edge cases and security features

Total: 52 tests

## Best Practices

1. **Key Generation**: Always use `os.urandom()` or `Fernet.generate_key()`
2. **Key Storage**: Use environment variables or secure key management systems
3. **Password Hashing**: Use PBKDF2 or Scrypt with high iteration counts
4. **Token Expiration**: Always set TTL when decrypting Fernet tokens
5. **Secure Transmission**: Only transmit tokens over HTTPS
6. **Error Handling**: Catch and handle cryptographic exceptions appropriately
7. **Key Rotation**: Use MultiFernet to support seamless key rotation
8. **Audit Logging**: Log all authentication and cryptographic operations

## License

This is an emulation/recreation of the cryptography library for educational purposes. The original cryptography library is created by the Python Cryptographic Authority.
