"""
itsdangerous Emulator - Cryptographic Signing Library
Emulates the popular itsdangerous library for safely signing and verifying data
"""

import hmac
import hashlib
import json
import base64
import time
import zlib
from typing import Any, Dict, Optional, Union, Tuple


class BadSignature(Exception):
    """Exception raised when a signature is invalid"""
    pass


class BadTimeSignature(BadSignature):
    """Exception raised when a time-based signature is invalid"""
    pass


class SignatureExpired(BadTimeSignature):
    """Exception raised when a signature has expired"""
    
    def __init__(self, message: str, payload=None, date_signed=None):
        """Initialize expired signature exception
        
        Args:
            message: Error message
            payload: The payload that was being verified
            date_signed: The timestamp when signature was created
        """
        super().__init__(message)
        self.payload = payload
        self.date_signed = date_signed


class BadPayload(BadSignature):
    """Exception raised when the payload cannot be decoded"""
    pass


def _constant_time_compare(val1: bytes, val2: bytes) -> bool:
    """Compare two byte strings in constant time to prevent timing attacks
    
    Args:
        val1: First byte string
        val2: Second byte string
        
    Returns:
        True if equal, False otherwise
    """
    if len(val1) != len(val2):
        return False
    
    result = 0
    for x, y in zip(val1, val2):
        result |= x ^ y
    
    return result == 0


def _base64_encode(data: bytes) -> bytes:
    """Encode data using URL-safe base64 without padding
    
    Args:
        data: Bytes to encode
        
    Returns:
        Base64 encoded bytes
    """
    return base64.urlsafe_b64encode(data).rstrip(b'=')


def _base64_decode(data: Union[str, bytes]) -> bytes:
    """Decode URL-safe base64 data, handling missing padding
    
    Args:
        data: Base64 encoded data
        
    Returns:
        Decoded bytes
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # Add padding if needed
    padding = b'=' * (4 - (len(data) % 4))
    if padding != b'====':
        data += padding
    
    try:
        return base64.urlsafe_b64decode(data)
    except Exception as e:
        raise BadPayload(f"Could not decode base64 data: {e}")


class SigningAlgorithm:
    """Base class for signing algorithms"""
    
    def get_signature(self, key: bytes, value: bytes) -> bytes:
        """Generate signature for value using key
        
        Args:
            key: Secret key
            value: Value to sign
            
        Returns:
            Signature bytes
        """
        raise NotImplementedError
    
    def verify_signature(self, key: bytes, value: bytes, sig: bytes) -> bool:
        """Verify signature for value using key
        
        Args:
            key: Secret key
            value: Value to verify
            sig: Signature to check
            
        Returns:
            True if valid, False otherwise
        """
        try:
            expected_sig = self.get_signature(key, value)
            return _constant_time_compare(sig, expected_sig)
        except Exception:
            return False


class HMACAlgorithm(SigningAlgorithm):
    """HMAC-based signing algorithm"""
    
    def __init__(self, digest_method=hashlib.sha1):
        """Initialize HMAC algorithm
        
        Args:
            digest_method: Hash function to use (default: SHA1)
        """
        self.digest_method = digest_method
    
    def get_signature(self, key: bytes, value: bytes) -> bytes:
        """Generate HMAC signature
        
        Args:
            key: Secret key
            value: Value to sign
            
        Returns:
            HMAC signature
        """
        mac = hmac.new(key, msg=value, digestmod=self.digest_method)
        return mac.digest()


class Signer:
    """Basic signer for signing and verifying data
    
    Note: Uses SHA1 by default to maintain compatibility with the original
    itsdangerous library. For new applications requiring higher security,
    consider passing digest_method=hashlib.sha256 or use the cryptography
    library instead.
    """
    
    def __init__(self, secret_key: Union[str, bytes], 
                 salt: Union[str, bytes] = b'itsdangerous.Signer',
                 sep: bytes = b'.',
                 key_derivation: str = 'django-concat',
                 digest_method=hashlib.sha1,
                 algorithm: Optional[SigningAlgorithm] = None):
        """Initialize signer
        
        Args:
            secret_key: Secret key for signing
            salt: Salt for key derivation
            sep: Separator between value and signature
            key_derivation: Key derivation method ('django-concat' or 'hmac')
            digest_method: Hash function to use (default: SHA1 for compatibility)
            algorithm: Signing algorithm (if None, uses HMACAlgorithm)
        """
        if isinstance(secret_key, str):
            secret_key = secret_key.encode('utf-8')
        
        if isinstance(salt, str):
            salt = salt.encode('utf-8')
        
        self.secret_key = secret_key
        self.salt = salt
        self.sep = sep
        self.key_derivation = key_derivation
        self.digest_method = digest_method
        
        if algorithm is None:
            algorithm = HMACAlgorithm(digest_method)
        self.algorithm = algorithm
    
    def derive_key(self) -> bytes:
        """Derive signing key from secret key and salt
        
        Returns:
            Derived key
        """
        if self.key_derivation == 'concat':
            return self.secret_key + self.salt
        elif self.key_derivation == 'django-concat':
            return hashlib.sha1(self.salt + b'signer' + self.secret_key).digest()
        elif self.key_derivation == 'hmac':
            mac = hmac.new(self.secret_key, self.salt, digestmod=self.digest_method)
            return mac.digest()
        elif self.key_derivation == 'none':
            return self.secret_key
        else:
            raise ValueError(f"Unknown key derivation method: {self.key_derivation}")
    
    def get_signature(self, value: Union[str, bytes]) -> bytes:
        """Get signature for a value
        
        Args:
            value: Value to sign
            
        Returns:
            Signature bytes
        """
        if isinstance(value, str):
            value = value.encode('utf-8')
        
        key = self.derive_key()
        sig = self.algorithm.get_signature(key, value)
        return _base64_encode(sig)
    
    def sign(self, value: Union[str, bytes]) -> bytes:
        """Sign a value
        
        Args:
            value: Value to sign
            
        Returns:
            Signed value (value + separator + signature)
        """
        if isinstance(value, str):
            value = value.encode('utf-8')
        
        return value + self.sep + self.get_signature(value)
    
    def verify_signature(self, value: Union[str, bytes], sig: Union[str, bytes]) -> bool:
        """Verify a signature for a value
        
        Args:
            value: Value to verify
            sig: Signature to check
            
        Returns:
            True if valid, False otherwise
        """
        if isinstance(value, str):
            value = value.encode('utf-8')
        if isinstance(sig, str):
            sig = sig.encode('utf-8')
        
        key = self.derive_key()
        try:
            decoded_sig = _base64_decode(sig)
            return self.algorithm.verify_signature(key, value, decoded_sig)
        except Exception:
            return False
    
    def unsign(self, signed_value: Union[str, bytes]) -> bytes:
        """Unsign a signed value
        
        Args:
            signed_value: Signed value to verify and extract
            
        Returns:
            Original unsigned value
            
        Raises:
            BadSignature: If signature is invalid
        """
        if isinstance(signed_value, str):
            signed_value = signed_value.encode('utf-8')
        
        if self.sep not in signed_value:
            raise BadSignature(f"No {self.sep!r} found in value")
        
        value, sig = signed_value.rsplit(self.sep, 1)
        
        if self.verify_signature(value, sig):
            return value
        
        raise BadSignature(f"Signature {sig!r} does not match")


class TimestampSigner(Signer):
    """Signer that adds a timestamp to the signature"""
    
    def get_timestamp(self) -> int:
        """Get current timestamp
        
        Returns:
            Current Unix timestamp
        """
        return int(time.time())
    
    def timestamp_to_datetime(self, ts: int):
        """Convert timestamp to datetime (returns None in this implementation)
        
        Args:
            ts: Unix timestamp
            
        Returns:
            None (datetime not available in minimal implementation)
        """
        return None
    
    def sign(self, value: Union[str, bytes]) -> bytes:
        """Sign a value with timestamp
        
        Args:
            value: Value to sign
            
        Returns:
            Signed value with timestamp
        """
        if isinstance(value, str):
            value = value.encode('utf-8')
        
        timestamp = str(self.get_timestamp()).encode('utf-8')
        value_with_ts = value + self.sep + _base64_encode(timestamp)
        return value_with_ts + self.sep + self.get_signature(value_with_ts)
    
    def unsign(self, signed_value: Union[str, bytes], 
               max_age: Optional[int] = None,
               return_timestamp: bool = False) -> Union[bytes, Tuple[bytes, int]]:
        """Unsign a timestamped value
        
        Args:
            signed_value: Signed value to verify
            max_age: Maximum age in seconds (if None, age is not checked)
            return_timestamp: If True, return tuple of (value, timestamp)
            
        Returns:
            Original value or tuple of (value, timestamp)
            
        Raises:
            SignatureExpired: If signature has expired
            BadTimeSignature: If timestamp is invalid
        """
        if isinstance(signed_value, str):
            signed_value = signed_value.encode('utf-8')
        
        # First unsign normally
        result = Signer.unsign(self, signed_value)
        
        # Split value and timestamp
        if self.sep not in result:
            raise BadTimeSignature("Timestamp missing")
        
        value, ts_bytes = result.rsplit(self.sep, 1)
        
        try:
            ts_decoded = _base64_decode(ts_bytes)
            timestamp = int(ts_decoded.decode('utf-8'))
        except Exception as e:
            raise BadTimeSignature(f"Malformed timestamp: {e}")
        
        # Check age if specified
        if max_age is not None:
            age = self.get_timestamp() - timestamp
            if age > max_age:
                raise SignatureExpired(
                    f"Signature age {age} > {max_age} seconds",
                    payload=value,
                    date_signed=timestamp
                )
            if age < 0:
                raise SignatureExpired(
                    "Signature timestamp is in the future",
                    payload=value,
                    date_signed=timestamp
                )
        
        if return_timestamp:
            return value, timestamp
        return value


class Serializer:
    """Serializer for signing and verifying complex data structures"""
    
    def __init__(self, secret_key: Union[str, bytes],
                 salt: Union[str, bytes] = b'itsdangerous',
                 serializer=None,
                 signer: Optional[Signer] = None,
                 signer_kwargs: Optional[Dict] = None):
        """Initialize serializer
        
        Args:
            secret_key: Secret key for signing
            salt: Salt for key derivation
            serializer: Serialization module (default: json)
            signer: Signer class to use
            signer_kwargs: Additional kwargs for signer
        """
        self.secret_key = secret_key
        self.salt = salt
        
        if serializer is None:
            self.serializer = json
            self.is_text_serializer = True
        else:
            self.serializer = serializer
            self.is_text_serializer = False
        
        if signer is None:
            self.signer = Signer
        else:
            self.signer = signer
        
        self.signer_kwargs = signer_kwargs or {}
    
    def make_signer(self, salt: Optional[Union[str, bytes]] = None) -> Signer:
        """Create a signer instance
        
        Args:
            salt: Optional salt override
            
        Returns:
            Signer instance
        """
        if salt is None:
            salt = self.salt
        
        return self.signer(self.secret_key, salt=salt, **self.signer_kwargs)
    
    def dumps(self, obj: Any, salt: Optional[Union[str, bytes]] = None) -> str:
        """Serialize and sign an object
        
        Args:
            obj: Object to serialize
            salt: Optional salt override
            
        Returns:
            Signed serialized string
        """
        # Serialize
        payload = self.dump_payload(obj)
        
        # Sign
        signer = self.make_signer(salt)
        signed = signer.sign(payload)
        
        return signed.decode('utf-8') if isinstance(signed, bytes) else signed
    
    def dump_payload(self, obj: Any) -> bytes:
        """Serialize object to bytes
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serialized bytes
        """
        json_str = self.serializer.dumps(obj, separators=(',', ':'))
        if isinstance(json_str, str):
            json_str = json_str.encode('utf-8')
        
        is_compressed = False
        compressed = zlib.compress(json_str)
        
        # Only use compression if it's actually smaller
        if len(compressed) < len(json_str) - 1:
            json_str = compressed
            is_compressed = True
        
        payload = _base64_encode(json_str)
        
        if is_compressed:
            payload = b'.' + payload
        
        return payload
    
    def loads(self, signed_payload: Union[str, bytes],
              salt: Optional[Union[str, bytes]] = None) -> Any:
        """Unsign and deserialize an object
        
        Args:
            signed_payload: Signed payload to deserialize
            salt: Optional salt override
            
        Returns:
            Deserialized object
            
        Raises:
            BadSignature: If signature is invalid
        """
        signer = self.make_signer(salt)
        payload = signer.unsign(signed_payload)
        return self.load_payload(payload)
    
    def load_payload(self, payload: bytes) -> Any:
        """Deserialize a payload
        
        Args:
            payload: Serialized payload
            
        Returns:
            Deserialized object
            
        Raises:
            BadPayload: If payload cannot be deserialized
        """
        is_compressed = False
        if payload.startswith(b'.'):
            payload = payload[1:]
            is_compressed = True
        
        try:
            json_bytes = _base64_decode(payload)
        except Exception as e:
            raise BadPayload(f"Could not decode payload: {e}")
        
        if is_compressed:
            try:
                json_bytes = zlib.decompress(json_bytes)
            except Exception as e:
                raise BadPayload(f"Could not decompress payload: {e}")
        
        try:
            return self.serializer.loads(json_bytes.decode('utf-8'))
        except Exception as e:
            raise BadPayload(f"Could not deserialize payload: {e}")


class TimedSerializer(Serializer):
    """Serializer that adds timestamp to signatures"""
    
    def __init__(self, secret_key: Union[str, bytes],
                 salt: Union[str, bytes] = b'itsdangerous',
                 serializer=None,
                 signer_kwargs: Optional[Dict] = None):
        """Initialize timed serializer
        
        Args:
            secret_key: Secret key for signing
            salt: Salt for key derivation
            serializer: Serialization module
            signer_kwargs: Additional kwargs for signer
        """
        super().__init__(
            secret_key=secret_key,
            salt=salt,
            serializer=serializer,
            signer=TimestampSigner,
            signer_kwargs=signer_kwargs
        )
    
    def loads(self, signed_payload: Union[str, bytes],
              max_age: Optional[int] = None,
              salt: Optional[Union[str, bytes]] = None,
              return_timestamp: bool = False) -> Any:
        """Unsign and deserialize with timestamp validation
        
        Args:
            signed_payload: Signed payload
            max_age: Maximum age in seconds
            salt: Optional salt override
            return_timestamp: If True, return tuple of (obj, timestamp)
            
        Returns:
            Deserialized object or tuple of (object, timestamp)
            
        Raises:
            SignatureExpired: If signature has expired
        """
        signer = self.make_signer(salt)
        
        if return_timestamp:
            payload, timestamp = signer.unsign(signed_payload, max_age=max_age, 
                                              return_timestamp=True)
            obj = self.load_payload(payload)
            return obj, timestamp
        else:
            payload = signer.unsign(signed_payload, max_age=max_age)
            return self.load_payload(payload)


# Convenience classes with URL-safe names
class URLSafeSerializer(Serializer):
    """URL-safe serializer (alias for Serializer with URL-safe encoding)"""
    pass


class URLSafeTimedSerializer(TimedSerializer):
    """URL-safe timed serializer (alias for TimedSerializer)"""
    pass


# Convenience functions
def sign(value: Union[str, bytes], secret_key: Union[str, bytes],
         salt: Union[str, bytes] = b'itsdangerous') -> str:
    """Convenience function to sign a value
    
    Args:
        value: Value to sign
        secret_key: Secret key
        salt: Salt for key derivation
        
    Returns:
        Signed value as string
    """
    s = Signer(secret_key, salt=salt)
    return s.sign(value).decode('utf-8')


def unsign(signed_value: Union[str, bytes], secret_key: Union[str, bytes],
           salt: Union[str, bytes] = b'itsdangerous') -> str:
    """Convenience function to unsign a value
    
    Args:
        signed_value: Signed value
        secret_key: Secret key
        salt: Salt for key derivation
        
    Returns:
        Original value as string
        
    Raises:
        BadSignature: If signature is invalid
    """
    s = Signer(secret_key, salt=salt)
    return s.unsign(signed_value).decode('utf-8')
