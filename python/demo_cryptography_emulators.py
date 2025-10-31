"""
Demo script for SecureSign (itsdangerous) and CryptoLib (cryptography) emulators

This script demonstrates the key features of both emulators:
- SecureSign: Cryptographic signing and serialization
- CryptoLib: Modern cryptographic operations
"""

import sys
import time
import os
import json
import traceback

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SecureSign'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CryptoLib'))

from SecureSign import (
    Signer, TimestampSigner, Serializer, TimedSerializer,
    URLSafeSerializer, URLSafeTimedSerializer,
    BadSignature, SignatureExpired
)

from CryptoLib import (
    Fernet, MultiFernet,
    Hash, HMAC, SHA256, SHA512,
    PBKDF2HMAC, Scrypt, HKDF,
    PKCS7, TOTP, HOTP,
    InvalidToken, InvalidSignature
)


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_itsdangerous():
    """Demonstrate itsdangerous emulator features"""
    print_section("itsdangerous Emulator Demo")
    
    # 1. Basic Signer
    print("1. Basic Signer - Sign and verify data")
    print("-" * 40)
    signer = Signer('my-secret-key')
    data = 'hello world'
    signed = signer.sign(data)
    print(f"Original data: {data}")
    print(f"Signed data:   {signed.decode()}")
    unsigned = signer.unsign(signed)
    print(f"Unsigned data: {unsigned.decode()}")
    
    # Try tampering
    try:
        tampered = signed[:-5] + b'xxxxx'
        signer.unsign(tampered)
    except BadSignature as e:
        print(f"✓ Tampering detected: {e}")
    
    # 2. TimestampSigner
    print("\n2. TimestampSigner - Time-limited signatures")
    print("-" * 40)
    ts_signer = TimestampSigner('my-secret-key')
    signed_with_time = ts_signer.sign('temporary data')
    print(f"Signed with timestamp: {signed_with_time.decode()}")
    
    # Verify fresh signature
    unsigned = ts_signer.unsign(signed_with_time, max_age=60)
    print(f"Unsigned (max_age=60s): {unsigned.decode()}")
    
    # 3. Serializer
    print("\n3. Serializer - Sign complex data structures")
    print("-" * 40)
    serializer = Serializer('my-secret-key')
    session_data = {
        'user_id': 123,
        'username': 'john_doe',
        'role': 'admin',
        'permissions': ['read', 'write', 'delete']
    }
    print(f"Original data: {session_data}")
    
    token = serializer.dumps(session_data)
    print(f"Signed token: {token[:50]}...")
    
    loaded = serializer.loads(token)
    print(f"Loaded data: {loaded}")
    
    # 4. TimedSerializer
    print("\n4. TimedSerializer - Expiring tokens")
    print("-" * 40)
    timed_serializer = TimedSerializer('my-secret-key')
    
    reset_token_data = {
        'user_id': 123,
        'email': 'user@example.com',
        'action': 'password_reset'
    }
    
    token = timed_serializer.dumps(reset_token_data)
    print(f"Password reset token: {token[:50]}...")
    
    # Load with max_age
    try:
        loaded = timed_serializer.loads(token, max_age=3600)
        print(f"Token valid (max_age=1 hour): {loaded}")
    except SignatureExpired:
        print("Token expired!")


def demo_cryptography():
    """Demonstrate cryptography emulator features"""
    print_section("Cryptography Emulator Demo")
    
    # 1. Fernet Encryption
    print("1. Fernet - Symmetric authenticated encryption")
    print("-" * 40)
    key = Fernet.generate_key()
    print(f"Generated key: {key.decode()[:40]}...")
    
    f = Fernet(key)
    plaintext = b'This is a secret message!'
    
    token = f.encrypt(plaintext)
    print(f"Plaintext:  {plaintext.decode()}")
    print(f"Encrypted:  {token.decode()[:50]}...")
    
    decrypted = f.decrypt(token)
    print(f"Decrypted:  {decrypted.decode()}")
    
    # Decrypt with TTL
    decrypted = f.decrypt(token, ttl=60)
    print(f"✓ Token valid within TTL (60 seconds)")
    
    # 2. MultiFernet - Key Rotation
    print("\n2. MultiFernet - Key rotation support")
    print("-" * 40)
    old_key = Fernet.generate_key()
    new_key = Fernet.generate_key()
    
    # Encrypt with old key
    old_fernet = Fernet(old_key)
    old_token = old_fernet.encrypt(b'data encrypted with old key')
    print(f"Old token: {old_token.decode()[:40]}...")
    
    # Create MultiFernet with both keys
    mf = MultiFernet([Fernet(new_key), Fernet(old_key)])
    
    # Can decrypt old token
    decrypted = mf.decrypt(old_token)
    print(f"✓ Old token decrypted: {decrypted.decode()}")
    
    # Rotate to new key
    new_token = mf.rotate(old_token)
    print(f"Rotated token: {new_token.decode()[:40]}...")
    
    # 3. Hashing
    print("\n3. Hash - Cryptographic hash functions")
    print("-" * 40)
    h = Hash('sha256')
    h.update(b'Hello ')
    h.update(b'World')
    digest = h.finalize()
    print(f"SHA256('Hello World'): {digest.hex()}")
    
    # 4. HMAC
    print("\n4. HMAC - Message authentication")
    print("-" * 40)
    api_key = b'shared-secret-key'
    message = b'{"user": "john", "action": "read"}'
    
    h = HMAC(api_key, SHA256())
    h.update(message)
    signature = h.finalize()
    print(f"Message:   {message.decode()}")
    print(f"Signature: {signature.hex()[:40]}...")
    
    # Verify
    h2 = HMAC(api_key, SHA256())
    h2.update(message)
    try:
        h2.verify(signature)
        print("✓ Signature verified!")
    except InvalidSignature:
        print("✗ Signature invalid!")
    
    # 5. PBKDF2 - Password hashing
    print("\n5. PBKDF2HMAC - Password-based key derivation")
    print("-" * 40)
    password = b'my-secure-password'
    salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    
    key = kdf.derive(password)
    # NOTE: Logging password in clear text is acceptable in this demo script
    # for educational purposes only. Never log passwords in production code!
    print(f"Password: {password.decode()}")
    print(f"Salt:     {salt.hex()}")
    print(f"Derived key: {key.hex()}")
    
    # Verify password
    kdf2 = PBKDF2HMAC(SHA256(), 32, salt, 100000)
    try:
        kdf2.verify(password, key)
        print("✓ Password verified!")
    except:
        print("✗ Password incorrect!")
    
    # 6. TOTP - Two-Factor Authentication
    print("\n6. TOTP - Time-based One-Time Password (2FA)")
    print("-" * 40)
    secret = os.urandom(20)
    totp = TOTP(secret, length=6)
    
    code = totp.generate()
    print(f"Current TOTP code: {code}")
    
    # Verify code
    if totp.verify(code):
        print("✓ TOTP code verified!")
    else:
        print("✗ TOTP code invalid!")
    
    # 7. PKCS7 Padding
    print("\n7. PKCS7 - Padding for block ciphers")
    print("-" * 40)
    padder = PKCS7(128)  # 128-bit blocks (16 bytes)
    
    data = b'hello world'
    padded = padder.pad(data)
    print(f"Original ({len(data)} bytes): {data}")
    print(f"Padded ({len(padded)} bytes):   {padded.hex()}")
    
    unpadded = padder.unpad(padded)
    print(f"Unpadded: {unpadded}")
    print(f"✓ Padding/unpadding successful")


def demo_use_cases():
    """Demonstrate real-world use cases"""
    print_section("Real-World Use Cases")
    
    # 1. Session Management
    print("1. Session Management with Fernet")
    print("-" * 40)
    session_key = Fernet.generate_key()
    f = Fernet(session_key)
    
    session_data = json.dumps({
        'user_id': 123,
        'username': 'john',
        'role': 'admin',
        'login_time': int(time.time())
    })
    
    session_token = f.encrypt(session_data.encode())
    print(f"Session token created: {session_token.decode()[:40]}...")
    
    # Later, verify and load session
    try:
        data = json.loads(f.decrypt(session_token, ttl=3600))
        print(f"Session loaded: User {data['username']} (ID: {data['user_id']})")
    except InvalidToken:
        print("Session expired or invalid")
    
    # 2. Password Storage
    print("\n2. Secure Password Storage with PBKDF2")
    print("-" * 40)
    
    def hash_password(password):
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        key = kdf.derive(password.encode())
        # Store salt + key together
        return salt.hex() + ':' + key.hex()
    
    def verify_password(password, stored_hash):
        salt_hex, key_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        
        kdf = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        try:
            kdf.verify(password.encode(), stored_key)
            return True
        except:
            return False
    
    password = 'my-secure-password-123'
    stored = hash_password(password)
    print(f"Stored hash: {stored[:60]}...")
    
    # NOTE: Displaying passwords in demo for educational purposes only.
    # Never display passwords in production code!
    print(f"Verify correct password: {verify_password(password, stored)}")
    print(f"Verify wrong password:   {verify_password('wrong', stored)}")
    
    # 3. API Request Signing
    print("\n3. API Request Signing with HMAC")
    print("-" * 40)
    api_secret = b'shared-api-secret-key'
    
    def sign_request(method, path, body):
        data = f"{method}:{path}:{body}".encode()
        h = HMAC(api_secret, SHA256())
        h.update(data)
        return h.finalize().hex()
    
    def verify_request(method, path, body, signature):
        expected = sign_request(method, path, body)
        return expected == signature
    
    request = ('GET', '/api/users', '{}')
    signature = sign_request(*request)
    
    print(f"Request: {request[0]} {request[1]}")
    print(f"Signature: {signature[:40]}...")
    print(f"Verify: {verify_request(*request, signature)}")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("  Emu-Soft Cryptography Emulators Demo")
    print("  Demonstrating itsdangerous and cryptography")
    print("="*60)
    
    try:
        demo_itsdangerous()
        demo_cryptography()
        demo_use_cases()
        
        print("\n" + "="*60)
        print("  Demo completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
