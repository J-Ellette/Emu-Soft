"""
Developed by PowerShield, as an alternative to bcrypt


bcrypt Emulator - Password Hashing Library
Emulates the popular bcrypt library for secure password hashing
"""

import hashlib
import hmac
import base64
import os
from typing import Union


# bcrypt prefix for versioning
BCRYPT_PREFIX = b'$2b$'  # bcrypt version 2b
DEFAULT_ROUNDS = 12  # Default cost factor


class BcryptError(Exception):
    """Base exception for bcrypt errors"""
    pass


class InvalidSaltError(BcryptError):
    """Exception for invalid salt"""
    pass


# Custom base64 alphabet for bcrypt (different from standard base64)
BCRYPT_ALPHABET = b'./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'


def _bcrypt_encode(data: bytes) -> bytes:
    """Encode data using bcrypt's custom base64
    
    Args:
        data: Bytes to encode
        
    Returns:
        Encoded bytes
    """
    result = bytearray()
    
    # Process 3 bytes at a time
    for i in range(0, len(data), 3):
        chunk = data[i:i+3]
        
        # Pad if needed
        while len(chunk) < 3:
            chunk += b'\x00'
        
        # Convert to 4 base64 characters
        val = (chunk[0] << 16) | (chunk[1] << 8) | chunk[2]
        
        result.append(BCRYPT_ALPHABET[(val >> 18) & 0x3F])
        result.append(BCRYPT_ALPHABET[(val >> 12) & 0x3F])
        result.append(BCRYPT_ALPHABET[(val >> 6) & 0x3F])
        result.append(BCRYPT_ALPHABET[val & 0x3F])
    
    return bytes(result)


def _bcrypt_decode(data: bytes) -> bytes:
    """Decode bcrypt's custom base64
    
    Args:
        data: Encoded bytes
        
    Returns:
        Decoded bytes
    """
    result = bytearray()
    
    # Create reverse lookup
    lookup = {c: i for i, c in enumerate(BCRYPT_ALPHABET)}
    
    # Process 4 characters at a time
    for i in range(0, len(data), 4):
        chunk = data[i:i+4]
        
        if len(chunk) < 4:
            break
        
        # Convert from base64
        val = 0
        for c in chunk:
            if c not in lookup:
                raise ValueError(f"Invalid character in bcrypt hash: {chr(c)}")
            val = (val << 6) | lookup[c]
        
        # Extract 3 bytes
        result.append((val >> 16) & 0xFF)
        result.append((val >> 8) & 0xFF)
        result.append(val & 0xFF)
    
    return bytes(result)


def _pbkdf2_hmac_sha256(password: bytes, salt: bytes, rounds: int) -> bytes:
    """Simple PBKDF2-HMAC-SHA256 implementation
    
    Args:
        password: Password bytes
        salt: Salt bytes
        rounds: Number of iterations
        
    Returns:
        Derived key bytes
    """
    # This is a simplified version - real bcrypt uses Blowfish
    # We use PBKDF2 as a secure alternative
    key_length = 24  # bcrypt produces 24 bytes
    
    derived_key = hashlib.pbkdf2_hmac('sha256', password, salt, rounds, dklen=key_length)
    return derived_key


def gensalt(rounds: int = DEFAULT_ROUNDS, prefix: bytes = BCRYPT_PREFIX) -> bytes:
    """Generate a random salt for bcrypt hashing
    
    Args:
        rounds: Cost factor (4-31), higher = more secure but slower
        prefix: Bcrypt version prefix (default: $2b$)
        
    Returns:
        Salt bytes in bcrypt format
        
    Raises:
        ValueError: If rounds is out of valid range
    """
    if rounds < 4 or rounds > 31:
        raise ValueError(f"Invalid rounds: {rounds}. Must be between 4 and 31")
    
    # Generate 16 random bytes
    random_bytes = os.urandom(16)
    
    # Encode using bcrypt's base64
    encoded_salt = _bcrypt_encode(random_bytes)[:22]  # bcrypt uses 22 chars
    
    # Format: $2b$12$salt...
    rounds_str = f"{rounds:02d}".encode('ascii')
    return prefix + rounds_str + b'$' + encoded_salt


def hashpw(password: Union[str, bytes], salt: bytes) -> bytes:
    """Hash a password using bcrypt
    
    Args:
        password: Password to hash (str or bytes)
        salt: Salt from gensalt()
        
    Returns:
        Hashed password in bcrypt format
        
    Raises:
        InvalidSaltError: If salt format is invalid
    """
    # Convert password to bytes if needed
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Parse salt
    if not salt.startswith(BCRYPT_PREFIX):
        raise InvalidSaltError(f"Invalid salt prefix. Expected {BCRYPT_PREFIX!r}")
    
    # Extract components from salt: $2b$12$salt...
    parts = salt.split(b'$')
    if len(parts) < 4:
        raise InvalidSaltError("Invalid salt format")
    
    version = b'$' + parts[1] + b'$'
    rounds_str = parts[2]
    salt_encoded = parts[3]
    
    # Parse rounds
    try:
        rounds = int(rounds_str.decode('ascii'))
    except (ValueError, UnicodeDecodeError):
        raise InvalidSaltError("Invalid rounds in salt")
    
    # Decode salt
    try:
        # Pad to 24 chars if needed for decoding
        padded_salt = salt_encoded + b'AA'
        salt_bytes = _bcrypt_decode(padded_salt)[:16]
    except Exception as e:
        raise InvalidSaltError(f"Invalid salt encoding: {e}")
    
    # Hash the password
    # Real bcrypt uses Blowfish cipher in EKSBlowfish mode
    # We simulate with PBKDF2-HMAC-SHA256
    iterations = 2 ** rounds  # Exponential work factor
    derived = _pbkdf2_hmac_sha256(password, salt_bytes, iterations)
    
    # Encode the hash
    hash_encoded = _bcrypt_encode(derived)[:31]  # bcrypt uses 31 chars for hash
    
    # Build final hash: $2b$12$salt..hash..
    result = version + rounds_str + b'$' + salt_encoded + hash_encoded
    
    return result


def checkpw(password: Union[str, bytes], hashed_password: bytes) -> bool:
    """Check if a password matches its hash
    
    Args:
        password: Plain text password to check
        hashed_password: Hashed password from hashpw()
        
    Returns:
        True if password matches, False otherwise
    """
    # Convert password to bytes if needed
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    try:
        # Extract the salt from the hashed password
        # Format: $2b$12$saltxxxxxxxxxxxxxx (22 chars) + hashxxxxxxxxxx (31 chars)
        parts = hashed_password.split(b'$')
        if len(parts) < 4:
            return False
        
        # Extract salt part (22 characters of base64)
        salt_and_hash = parts[3]
        if len(salt_and_hash) < 22:
            return False
        
        salt_encoded = salt_and_hash[:22]
        
        # Reconstruct the full salt format: $2b$12$salt...
        salt = b'$'.join(parts[:3]) + b'$' + salt_encoded
        
        # Hash the password with the extracted salt
        new_hash = hashpw(password, salt)
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(new_hash, hashed_password)
        
    except Exception:
        # Any error in processing means invalid hash or password
        return False


def kdf(password: Union[str, bytes], salt: bytes, desired_key_bytes: int,
        rounds: int = DEFAULT_ROUNDS) -> bytes:
    """Key derivation function using bcrypt
    
    Args:
        password: Password to derive key from
        salt: Salt bytes (raw, not bcrypt-formatted)
        desired_key_bytes: Number of bytes to derive
        rounds: Cost factor
        
    Returns:
        Derived key bytes
    """
    # Convert password to bytes if needed
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Use PBKDF2 for key derivation
    iterations = 2 ** rounds
    return hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen=desired_key_bytes)


# Module-level constants
__version__ = '4.0.1'  # Match common bcrypt version


# Helper functions for common use cases
def hash_password(password: str, rounds: int = DEFAULT_ROUNDS) -> str:
    """Hash a password (convenience function)
    
    Args:
        password: Plain text password
        rounds: Cost factor (default: 12)
        
    Returns:
        Hashed password as string
    """
    salt = gensalt(rounds)
    hashed = hashpw(password, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (convenience function)
    
    Args:
        password: Plain text password
        hashed_password: Hashed password string
        
    Returns:
        True if password matches, False otherwise
    """
    return checkpw(password, hashed_password.encode('utf-8'))


# Module-level exports
__all__ = [
    'gensalt',
    'hashpw',
    'checkpw',
    'kdf',
    'hash_password',
    'verify_password',
    'BcryptError',
    'InvalidSaltError',
    '__version__',
]
