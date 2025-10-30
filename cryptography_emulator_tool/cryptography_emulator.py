"""
Cryptography Emulator - Modern Cryptographic Recipes
Emulates the popular cryptography library for secure cryptographic operations
"""

import hashlib
import hmac
import os
import base64
import struct
import time
from typing import Union, Optional, Tuple


# ============================================================================
# Exceptions
# ============================================================================

class CryptographyError(Exception):
    """Base exception for cryptography errors"""
    pass


class InvalidSignature(CryptographyError):
    """Exception for invalid signatures"""
    pass


class InvalidKey(CryptographyError):
    """Exception for invalid keys"""
    pass


class InvalidToken(CryptographyError):
    """Exception for invalid tokens"""
    pass


class AlreadyFinalized(CryptographyError):
    """Exception when an operation is already finalized"""
    pass


# ============================================================================
# Utilities
# ============================================================================

def constant_time_bytes_eq(a: bytes, b: bytes) -> bool:
    """Compare two byte strings in constant time
    
    Args:
        a: First byte string
        b: Second byte string
        
    Returns:
        True if equal, False otherwise
    """
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    
    return result == 0


# ============================================================================
# Fernet - Symmetric Encryption
# ============================================================================

class Fernet:
    """Fernet provides authenticated symmetric encryption
    
    Fernet guarantees that a message encrypted using it cannot be
    manipulated or read without the key. It is an implementation of
    symmetric authenticated cryptography.
    """
    
    def __init__(self, key: bytes):
        """Initialize Fernet with a key
        
        Args:
            key: 32 bytes URL-safe base64-encoded key
            
        Raises:
            InvalidKey: If key is invalid
        """
        if not isinstance(key, bytes):
            raise TypeError("key must be bytes")
        
        try:
            key_bytes = base64.urlsafe_b64decode(key)
        except Exception:
            raise InvalidKey("Fernet key must be 32 url-safe base64-encoded bytes")
        
        if len(key_bytes) != 32:
            raise InvalidKey("Fernet key must be 32 url-safe base64-encoded bytes")
        
        self._signing_key = key_bytes[:16]
        self._encryption_key = key_bytes[16:]
    
    @classmethod
    def generate_key(cls) -> bytes:
        """Generate a new Fernet key
        
        Returns:
            32 bytes URL-safe base64-encoded key
        """
        key = os.urandom(32)
        return base64.urlsafe_b64encode(key)
    
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted token
        """
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        
        current_time = int(time.time())
        iv = os.urandom(16)
        
        # Simple XOR-based encryption (in real cryptography, use AES)
        # This is a simplified implementation for educational purposes
        ciphertext = self._xor_encrypt(data, self._encryption_key, iv)
        
        # Build the token
        version = b'\x80'
        timestamp = struct.pack('>Q', current_time)
        
        basic_parts = version + timestamp + iv + ciphertext
        
        # Generate HMAC
        h = hmac.new(self._signing_key, basic_parts, hashlib.sha256)
        hmac_sig = h.digest()
        
        token = basic_parts + hmac_sig
        return base64.urlsafe_b64encode(token)
    
    def decrypt(self, token: bytes, ttl: Optional[int] = None) -> bytes:
        """Decrypt a token
        
        Args:
            token: Encrypted token
            ttl: Time-to-live in seconds (if specified, checks age)
            
        Returns:
            Decrypted data
            
        Raises:
            InvalidToken: If token is invalid or expired
        """
        if not isinstance(token, bytes):
            raise TypeError("token must be bytes")
        
        try:
            data = base64.urlsafe_b64decode(token)
        except Exception:
            raise InvalidToken("Token is not valid base64")
        
        if len(data) < 57:  # Minimum token size
            raise InvalidToken("Token is too short")
        
        # Extract parts
        version = data[0:1]
        timestamp_bytes = data[1:9]
        iv = data[9:25]
        ciphertext = data[25:-32]
        hmac_sig = data[-32:]
        
        if version != b'\x80':
            raise InvalidToken("Invalid token version")
        
        # Verify HMAC
        basic_parts = data[:-32]
        h = hmac.new(self._signing_key, basic_parts, hashlib.sha256)
        expected_hmac = h.digest()
        
        if not constant_time_bytes_eq(hmac_sig, expected_hmac):
            raise InvalidToken("Token signature is invalid")
        
        # Check TTL
        timestamp = struct.unpack('>Q', timestamp_bytes)[0]
        if ttl is not None:
            current_time = int(time.time())
            age = current_time - timestamp
            if age > ttl:
                raise InvalidToken(f"Token is expired (age: {age}s, ttl: {ttl}s)")
            if age < 0:
                raise InvalidToken("Token timestamp is in the future")
        
        # Decrypt
        plaintext = self._xor_encrypt(ciphertext, self._encryption_key, iv)
        return plaintext
    
    def _xor_encrypt(self, data: bytes, key: bytes, iv: bytes) -> bytes:
        """Simple XOR-based encryption (educational purposes)
        
        In production, use proper AES encryption from a real crypto library.
        This is a simplified implementation to demonstrate the concept.
        
        Args:
            data: Data to encrypt/decrypt
            key: Encryption key
            iv: Initialization vector
            
        Returns:
            Encrypted/decrypted data
        """
        # Generate keystream from key and IV
        keystream = bytearray()
        counter = 0
        
        while len(keystream) < len(data):
            # Mix key, IV, and counter
            block = hashlib.sha256(key + iv + struct.pack('>Q', counter)).digest()
            keystream.extend(block)
            counter += 1
        
        # XOR data with keystream
        result = bytearray()
        for i, byte in enumerate(data):
            result.append(byte ^ keystream[i])
        
        return bytes(result)
    
    def encrypt_at_time(self, data: bytes, current_time: int) -> bytes:
        """Encrypt data with a specific timestamp (for testing)
        
        Args:
            data: Data to encrypt
            current_time: Unix timestamp to use
            
        Returns:
            Encrypted token
        """
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        
        iv = os.urandom(16)
        ciphertext = self._xor_encrypt(data, self._encryption_key, iv)
        
        version = b'\x80'
        timestamp = struct.pack('>Q', current_time)
        
        basic_parts = version + timestamp + iv + ciphertext
        
        h = hmac.new(self._signing_key, basic_parts, hashlib.sha256)
        hmac_sig = h.digest()
        
        token = basic_parts + hmac_sig
        return base64.urlsafe_b64encode(token)


class MultiFernet:
    """Encrypt and decrypt with multiple Fernet keys (for key rotation)"""
    
    def __init__(self, fernets: list):
        """Initialize with list of Fernet instances
        
        Args:
            fernets: List of Fernet instances
        """
        if not fernets:
            raise ValueError("MultiFernet requires at least one Fernet instance")
        
        self._fernets = fernets
    
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt with the first Fernet key
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted token
        """
        return self._fernets[0].encrypt(data)
    
    def decrypt(self, token: bytes, ttl: Optional[int] = None) -> bytes:
        """Decrypt with any of the Fernet keys
        
        Tries each key in order until one succeeds.
        
        Args:
            token: Encrypted token
            ttl: Time-to-live in seconds
            
        Returns:
            Decrypted data
            
        Raises:
            InvalidToken: If none of the keys can decrypt
        """
        for fernet in self._fernets:
            try:
                return fernet.decrypt(token, ttl=ttl)
            except InvalidToken:
                pass
        
        raise InvalidToken("Could not decrypt token with any key")
    
    def rotate(self, msg: bytes) -> bytes:
        """Rotate a token to use the primary key
        
        Args:
            msg: Token encrypted with any key
            
        Returns:
            Token encrypted with primary key
        """
        return self.encrypt(self.decrypt(msg))


# ============================================================================
# Hashing
# ============================================================================

class Hash:
    """Hash context for computing message digests"""
    
    def __init__(self, algorithm: str):
        """Initialize hash context
        
        Args:
            algorithm: Hash algorithm name (e.g., 'sha256', 'sha512', 'md5')
        """
        self.algorithm = algorithm
        self._ctx = hashlib.new(algorithm)
        self._finalized = False
    
    def update(self, data: bytes) -> None:
        """Update the hash with new data
        
        Args:
            data: Data to hash
            
        Raises:
            AlreadyFinalized: If hash is already finalized
        """
        if self._finalized:
            raise AlreadyFinalized("Hash context has already been finalized")
        
        self._ctx.update(data)
    
    def finalize(self) -> bytes:
        """Finalize and return the hash digest
        
        Returns:
            Hash digest bytes
            
        Raises:
            AlreadyFinalized: If already finalized
        """
        if self._finalized:
            raise AlreadyFinalized("Hash context has already been finalized")
        
        self._finalized = True
        return self._ctx.digest()
    
    def copy(self) -> 'Hash':
        """Create a copy of the hash context
        
        Returns:
            New Hash instance with same state
        """
        new_hash = Hash(self.algorithm)
        new_hash._ctx = self._ctx.copy()
        new_hash._finalized = self._finalized
        return new_hash


# Hash algorithm convenience classes
class SHA1:
    """SHA1 hash algorithm"""
    name = 'sha1'
    digest_size = 20


class SHA224:
    """SHA224 hash algorithm"""
    name = 'sha224'
    digest_size = 28


class SHA256:
    """SHA256 hash algorithm"""
    name = 'sha256'
    digest_size = 32


class SHA384:
    """SHA384 hash algorithm"""
    name = 'sha384'
    digest_size = 48


class SHA512:
    """SHA512 hash algorithm"""
    name = 'sha512'
    digest_size = 64


class SHA512_224:
    """SHA512/224 hash algorithm"""
    name = 'sha512_224'
    digest_size = 28


class SHA512_256:
    """SHA512/256 hash algorithm"""
    name = 'sha512_256'
    digest_size = 32


class MD5:
    """MD5 hash algorithm (not recommended for security)"""
    name = 'md5'
    digest_size = 16


class BLAKE2b:
    """BLAKE2b hash algorithm"""
    name = 'blake2b'
    digest_size = 64


class BLAKE2s:
    """BLAKE2s hash algorithm"""
    name = 'blake2s'
    digest_size = 32


def hashes_Hash(algorithm) -> Hash:
    """Create a hash context
    
    Args:
        algorithm: Hash algorithm (e.g., SHA256())
        
    Returns:
        Hash context
    """
    return Hash(algorithm.name)


# ============================================================================
# HMAC
# ============================================================================

class HMAC:
    """HMAC (Hash-based Message Authentication Code)"""
    
    def __init__(self, key: bytes, algorithm):
        """Initialize HMAC
        
        Args:
            key: Secret key
            algorithm: Hash algorithm (e.g., SHA256())
        """
        self.algorithm = algorithm
        self._ctx = hmac.new(key, digestmod=algorithm.name)
        self._finalized = False
    
    def update(self, data: bytes) -> None:
        """Update HMAC with new data
        
        Args:
            data: Data to authenticate
            
        Raises:
            AlreadyFinalized: If already finalized
        """
        if self._finalized:
            raise AlreadyFinalized("HMAC context has already been finalized")
        
        self._ctx.update(data)
    
    def finalize(self) -> bytes:
        """Finalize and return the HMAC
        
        Returns:
            HMAC bytes
            
        Raises:
            AlreadyFinalized: If already finalized
        """
        if self._finalized:
            raise AlreadyFinalized("HMAC context has already been finalized")
        
        self._finalized = True
        return self._ctx.digest()
    
    def verify(self, signature: bytes) -> None:
        """Verify an HMAC signature
        
        Args:
            signature: Expected signature
            
        Raises:
            InvalidSignature: If signature doesn't match
            AlreadyFinalized: If already finalized
        """
        digest = self.finalize()
        if not constant_time_bytes_eq(digest, signature):
            raise InvalidSignature("HMAC signature verification failed")
    
    def copy(self) -> 'HMAC':
        """Create a copy of the HMAC context
        
        Returns:
            New HMAC instance with same state
        """
        new_hmac = object.__new__(HMAC)
        new_hmac.algorithm = self.algorithm
        new_hmac._ctx = self._ctx.copy()
        new_hmac._finalized = self._finalized
        return new_hmac


# ============================================================================
# Key Derivation Functions (KDF)
# ============================================================================

class PBKDF2HMAC:
    """PBKDF2 (Password-Based Key Derivation Function 2) using HMAC"""
    
    def __init__(self, algorithm, length: int, salt: bytes, 
                 iterations: int):
        """Initialize PBKDF2HMAC
        
        Args:
            algorithm: Hash algorithm (e.g., SHA256())
            length: Desired length of derived key
            salt: Salt value
            iterations: Number of iterations
        """
        self.algorithm = algorithm
        self.length = length
        self.salt = salt
        self.iterations = iterations
        self._used = False
    
    def derive(self, key_material: bytes) -> bytes:
        """Derive a key from key material
        
        Args:
            key_material: Input key material (e.g., password)
            
        Returns:
            Derived key
            
        Raises:
            AlreadyFinalized: If already used
        """
        if self._used:
            raise AlreadyFinalized("PBKDF2HMAC has already been used")
        
        self._used = True
        
        return hashlib.pbkdf2_hmac(
            self.algorithm.name,
            key_material,
            self.salt,
            self.iterations,
            dklen=self.length
        )
    
    def verify(self, key_material: bytes, expected_key: bytes) -> None:
        """Verify that key material derives to expected key
        
        Args:
            key_material: Input key material
            expected_key: Expected derived key
            
        Raises:
            InvalidKey: If derived key doesn't match
        """
        derived = hashlib.pbkdf2_hmac(
            self.algorithm.name,
            key_material,
            self.salt,
            self.iterations,
            dklen=self.length
        )
        
        if not constant_time_bytes_eq(derived, expected_key):
            raise InvalidKey("Key verification failed")


class Scrypt:
    """Scrypt key derivation function"""
    
    def __init__(self, salt: bytes, length: int, n: int, r: int, p: int):
        """Initialize Scrypt
        
        Args:
            salt: Salt value
            length: Desired length of derived key
            n: CPU/memory cost parameter (must be power of 2)
            r: Block size parameter
            p: Parallelization parameter
        """
        self.salt = salt
        self.length = length
        self.n = n
        self.r = r
        self.p = p
        self._used = False
    
    def derive(self, key_material: bytes) -> bytes:
        """Derive a key using Scrypt
        
        Args:
            key_material: Input key material
            
        Returns:
            Derived key
            
        Raises:
            AlreadyFinalized: If already used
        """
        if self._used:
            raise AlreadyFinalized("Scrypt has already been used")
        
        self._used = True
        
        try:
            return hashlib.scrypt(
                key_material,
                salt=self.salt,
                n=self.n,
                r=self.r,
                p=self.p,
                dklen=self.length
            )
        except AttributeError:
            # Fallback if scrypt not available (Python < 3.6)
            # Use PBKDF2 as a substitute with adjusted iterations
            iterations = self.n * self.r * self.p
            return hashlib.pbkdf2_hmac(
                'sha256',
                key_material,
                self.salt,
                iterations,
                dklen=self.length
            )
    
    def verify(self, key_material: bytes, expected_key: bytes) -> None:
        """Verify that key material derives to expected key
        
        Args:
            key_material: Input key material
            expected_key: Expected derived key
            
        Raises:
            InvalidKey: If derived key doesn't match
        """
        # Create new instance for verification
        kdf = Scrypt(self.salt, self.length, self.n, self.r, self.p)
        derived = kdf.derive(key_material)
        
        if not constant_time_bytes_eq(derived, expected_key):
            raise InvalidKey("Key verification failed")


class HKDF:
    """HKDF (HMAC-based Extract-and-Expand Key Derivation Function)"""
    
    def __init__(self, algorithm, length: int, salt: Optional[bytes], 
                 info: Optional[bytes]):
        """Initialize HKDF
        
        Args:
            algorithm: Hash algorithm
            length: Desired length of output key material
            salt: Optional salt value
            info: Optional context and application specific information
        """
        self.algorithm = algorithm
        self.length = length
        self.salt = salt if salt else b'\x00' * algorithm.digest_size
        self.info = info if info else b''
        self._used = False
    
    def derive(self, key_material: bytes) -> bytes:
        """Derive key material using HKDF
        
        Args:
            key_material: Input key material
            
        Returns:
            Derived key material
            
        Raises:
            AlreadyFinalized: If already used
        """
        if self._used:
            raise AlreadyFinalized("HKDF has already been used")
        
        self._used = True
        
        # Extract
        prk = hmac.new(self.salt, key_material, self.algorithm.name).digest()
        
        # Expand
        okm = b''
        previous = b''
        
        for i in range(1, (self.length // self.algorithm.digest_size) + 2):
            previous = hmac.new(
                prk,
                previous + self.info + bytes([i]),
                self.algorithm.name
            ).digest()
            okm += previous
        
        return okm[:self.length]
    
    def verify(self, key_material: bytes, expected_key: bytes) -> None:
        """Verify key derivation
        
        Args:
            key_material: Input key material
            expected_key: Expected derived key
            
        Raises:
            InvalidKey: If derived key doesn't match
        """
        kdf = HKDF(self.algorithm, self.length, self.salt, self.info)
        derived = kdf.derive(key_material)
        
        if not constant_time_bytes_eq(derived, expected_key):
            raise InvalidKey("Key verification failed")


# ============================================================================
# Padding
# ============================================================================

class PKCS7:
    """PKCS7 padding scheme"""
    
    def __init__(self, block_size: int):
        """Initialize PKCS7 padding
        
        Args:
            block_size: Block size in bits (must be multiple of 8)
        """
        if block_size % 8 != 0:
            raise ValueError("block_size must be a multiple of 8")
        
        self.block_size = block_size // 8
    
    def pad(self, data: bytes) -> bytes:
        """Add PKCS7 padding to data
        
        Args:
            data: Data to pad
            
        Returns:
            Padded data
        """
        padding_length = self.block_size - (len(data) % self.block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def unpad(self, data: bytes) -> bytes:
        """Remove PKCS7 padding from data
        
        Args:
            data: Padded data
            
        Returns:
            Unpadded data
            
        Raises:
            ValueError: If padding is invalid
        """
        if not data:
            raise ValueError("Data is empty")
        
        padding_length = data[-1]
        
        if padding_length > self.block_size or padding_length == 0:
            raise ValueError("Invalid padding")
        
        # Verify all padding bytes are correct
        for i in range(1, padding_length + 1):
            if data[-i] != padding_length:
                raise ValueError("Invalid padding")
        
        return data[:-padding_length]


# ============================================================================
# Two-Factor Authentication (TOTP/HOTP)
# ============================================================================

class TOTP:
    """Time-based One-Time Password"""
    
    def __init__(self, key: bytes, length: int = 6, algorithm=None, 
                 time_step: int = 30):
        """Initialize TOTP
        
        Args:
            key: Shared secret key
            length: Number of digits in OTP
            algorithm: Hash algorithm (default: SHA1)
            time_step: Time step in seconds (default: 30)
        """
        self.key = key
        self.length = length
        self.algorithm = algorithm if algorithm else SHA1()
        self.time_step = time_step
    
    def generate(self, time_value: Optional[int] = None) -> str:
        """Generate TOTP code
        
        Args:
            time_value: Unix timestamp (default: current time)
            
        Returns:
            TOTP code as string
        """
        if time_value is None:
            time_value = int(time.time())
        
        counter = time_value // self.time_step
        return self._hotp(counter)
    
    def verify(self, totp: str, time_value: Optional[int] = None) -> bool:
        """Verify a TOTP code
        
        Args:
            totp: TOTP code to verify
            time_value: Unix timestamp (default: current time)
            
        Returns:
            True if valid, False otherwise
        """
        if time_value is None:
            time_value = int(time.time())
        
        # Check current window and one window before/after
        for offset in [0, -1, 1]:
            expected = self.generate(time_value + (offset * self.time_step))
            if constant_time_bytes_eq(totp.encode(), expected.encode()):
                return True
        
        return False
    
    def _hotp(self, counter: int) -> str:
        """Generate HOTP code
        
        Args:
            counter: Counter value
            
        Returns:
            HOTP code as string
        """
        # Convert counter to bytes
        counter_bytes = struct.pack('>Q', counter)
        
        # Generate HMAC
        h = hmac.new(self.key, counter_bytes, self.algorithm.name)
        hmac_result = h.digest()
        
        # Dynamic truncation
        offset = hmac_result[-1] & 0x0f
        truncated = struct.unpack('>I', hmac_result[offset:offset+4])[0]
        truncated &= 0x7fffffff
        
        # Generate OTP
        otp = truncated % (10 ** self.length)
        return str(otp).zfill(self.length)


class HOTP:
    """HMAC-based One-Time Password"""
    
    def __init__(self, key: bytes, length: int = 6, algorithm=None):
        """Initialize HOTP
        
        Args:
            key: Shared secret key
            length: Number of digits in OTP
            algorithm: Hash algorithm (default: SHA1)
        """
        self.key = key
        self.length = length
        self.algorithm = algorithm if algorithm else SHA1()
    
    def generate(self, counter: int) -> str:
        """Generate HOTP code
        
        Args:
            counter: Counter value
            
        Returns:
            HOTP code as string
        """
        counter_bytes = struct.pack('>Q', counter)
        
        h = hmac.new(self.key, counter_bytes, self.algorithm.name)
        hmac_result = h.digest()
        
        offset = hmac_result[-1] & 0x0f
        truncated = struct.unpack('>I', hmac_result[offset:offset+4])[0]
        truncated &= 0x7fffffff
        
        otp = truncated % (10 ** self.length)
        return str(otp).zfill(self.length)
    
    def verify(self, hotp: str, counter: int) -> bool:
        """Verify an HOTP code
        
        Args:
            hotp: HOTP code to verify
            counter: Counter value
            
        Returns:
            True if valid, False otherwise
        """
        expected = self.generate(counter)
        return constant_time_bytes_eq(hotp.encode(), expected.encode())
