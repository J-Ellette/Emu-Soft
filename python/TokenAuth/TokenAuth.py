"""
Developed by PowerShield, as an alternative to PyJWT


PyJWT Emulator - JSON Web Token implementation
Emulates the popular PyJWT library for encoding and decoding JWT tokens
"""

import hmac
import hashlib
import json
import base64
import time
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta


class PyJWTError(Exception):
    """Base exception for PyJWT errors"""
    pass


class InvalidTokenError(PyJWTError):
    """Exception for invalid tokens"""
    pass


class DecodeError(InvalidTokenError):
    """Exception for decoding errors"""
    pass


class InvalidSignatureError(DecodeError):
    """Exception for invalid signatures"""
    pass


class ExpiredSignatureError(InvalidTokenError):
    """Exception for expired tokens"""
    pass


class InvalidAudienceError(InvalidTokenError):
    """Exception for invalid audience"""
    pass


class InvalidIssuerError(InvalidTokenError):
    """Exception for invalid issuer"""
    pass


class InvalidIssuedAtError(InvalidTokenError):
    """Exception for invalid issued at time"""
    pass


class ImmatureSignatureError(InvalidTokenError):
    """Exception for tokens used before nbf (not before) time"""
    pass


class MissingRequiredClaimError(InvalidTokenError):
    """Exception for missing required claims"""
    pass


def _base64url_encode(data: bytes) -> str:
    """Encode data using base64url encoding
    
    Args:
        data: Bytes to encode
        
    Returns:
        Base64url encoded string
    """
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _base64url_decode(data: str) -> bytes:
    """Decode base64url encoded data
    
    Args:
        data: Base64url encoded string
        
    Returns:
        Decoded bytes
    """
    # Add padding if needed
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += '=' * padding
    
    return base64.urlsafe_b64decode(data)


def _sign_hmac_sha256(message: bytes, key: Union[str, bytes]) -> bytes:
    """Sign message using HMAC-SHA256
    
    Args:
        message: Message to sign
        key: Secret key
        
    Returns:
        Signature bytes
    """
    if isinstance(key, str):
        key = key.encode('utf-8')
    
    return hmac.new(key, message, hashlib.sha256).digest()


def _sign_hmac_sha384(message: bytes, key: Union[str, bytes]) -> bytes:
    """Sign message using HMAC-SHA384
    
    Args:
        message: Message to sign
        key: Secret key
        
    Returns:
        Signature bytes
    """
    if isinstance(key, str):
        key = key.encode('utf-8')
    
    return hmac.new(key, message, hashlib.sha384).digest()


def _sign_hmac_sha512(message: bytes, key: Union[str, bytes]) -> bytes:
    """Sign message using HMAC-SHA512
    
    Args:
        message: Message to sign
        key: Secret key
        
    Returns:
        Signature bytes
    """
    if isinstance(key, str):
        key = key.encode('utf-8')
    
    return hmac.new(key, message, hashlib.sha512).digest()


def _verify_signature(message: bytes, signature: bytes, key: Union[str, bytes], algorithm: str) -> bool:
    """Verify signature
    
    Args:
        message: Original message
        signature: Signature to verify
        key: Secret key
        algorithm: Algorithm used
        
    Returns:
        True if signature is valid, False otherwise
    """
    if algorithm == 'HS256':
        expected = _sign_hmac_sha256(message, key)
    elif algorithm == 'HS384':
        expected = _sign_hmac_sha384(message, key)
    elif algorithm == 'HS512':
        expected = _sign_hmac_sha512(message, key)
    else:
        raise DecodeError(f"Unsupported algorithm: {algorithm}")
    
    return hmac.compare_digest(signature, expected)


def encode(payload: Dict[str, Any], key: Union[str, bytes], algorithm: str = 'HS256',
           headers: Optional[Dict[str, Any]] = None) -> str:
    """Encode a JWT token
    
    Args:
        payload: JWT claims dictionary
        key: Secret key for signing
        algorithm: Algorithm to use (default: HS256)
        headers: Optional additional headers
        
    Returns:
        Encoded JWT token string
        
    Raises:
        PyJWTError: If encoding fails
    """
    # Validate algorithm
    if algorithm not in ['HS256', 'HS384', 'HS512', 'none']:
        raise PyJWTError(f"Unsupported algorithm: {algorithm}")
    
    # Build header
    header = {
        'typ': 'JWT',
        'alg': algorithm
    }
    if headers:
        header.update(headers)
    
    # Convert datetime objects to timestamps
    processed_payload = _process_payload(payload)
    
    # Encode header and payload
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(processed_payload, separators=(',', ':')).encode('utf-8')
    
    header_b64 = _base64url_encode(header_json)
    payload_b64 = _base64url_encode(payload_json)
    
    # Create signing input
    signing_input = f"{header_b64}.{payload_b64}"
    
    # Sign the token
    if algorithm == 'none':
        # Unsigned token
        signature_b64 = ''
    elif algorithm == 'HS256':
        signature = _sign_hmac_sha256(signing_input.encode('utf-8'), key)
        signature_b64 = _base64url_encode(signature)
    elif algorithm == 'HS384':
        signature = _sign_hmac_sha384(signing_input.encode('utf-8'), key)
        signature_b64 = _base64url_encode(signature)
    elif algorithm == 'HS512':
        signature = _sign_hmac_sha512(signing_input.encode('utf-8'), key)
        signature_b64 = _base64url_encode(signature)
    
    # Build final token
    if signature_b64:
        return f"{signing_input}.{signature_b64}"
    else:
        return f"{signing_input}."


def decode(jwt_token: str, key: Union[str, bytes] = None, algorithms: Optional[list] = None,
           options: Optional[Dict[str, Any]] = None, audience: Optional[Union[str, list]] = None,
           issuer: Optional[str] = None, leeway: Union[int, float, timedelta] = 0,
           verify: bool = True) -> Dict[str, Any]:
    """Decode and verify a JWT token
    
    Args:
        jwt_token: JWT token string
        key: Secret key for verification (required if verify=True)
        algorithms: List of allowed algorithms (default: ['HS256'])
        options: Options for verification
        audience: Expected audience claim(s)
        issuer: Expected issuer claim
        leeway: Time leeway in seconds for exp, nbf, iat validation
        verify: Whether to verify signature and claims (default: True)
        
    Returns:
        Decoded payload dictionary
        
    Raises:
        DecodeError: If token format is invalid
        InvalidSignatureError: If signature verification fails
        ExpiredSignatureError: If token has expired
        InvalidAudienceError: If audience claim doesn't match
        InvalidIssuerError: If issuer claim doesn't match
    """
    if algorithms is None:
        algorithms = ['HS256']
    
    if options is None:
        options = {
            'verify_signature': True,
            'verify_exp': True,
            'verify_nbf': True,
            'verify_iat': True,
            'verify_aud': True,
            'verify_iss': True,
            'require_exp': False,
            'require_iat': False,
            'require_nbf': False,
        }
    
    # Parse token
    try:
        parts = jwt_token.split('.')
        if len(parts) != 3:
            raise DecodeError(f"Invalid token format: expected 3 parts, got {len(parts)}")
        
        header_b64, payload_b64, signature_b64 = parts
        
        # Decode header
        header_json = _base64url_decode(header_b64)
        header = json.loads(header_json)
        
        # Decode payload
        payload_json = _base64url_decode(payload_b64)
        payload = json.loads(payload_json)
        
    except (ValueError, json.JSONDecodeError) as e:
        raise DecodeError(f"Invalid token: {str(e)}")
    
    # Verify algorithm
    algorithm = header.get('alg', 'none')
    if algorithm not in algorithms:
        raise InvalidTokenError(f"Algorithm {algorithm} not in allowed algorithms: {algorithms}")
    
    # Verify signature
    if verify and options.get('verify_signature', True) and algorithm != 'none':
        if key is None:
            raise DecodeError("Key is required for signature verification")
        
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = _base64url_decode(signature_b64)
        
        if not _verify_signature(signing_input, signature, key, algorithm):
            raise InvalidSignatureError("Signature verification failed")
    
    # Verify claims
    if verify:
        _verify_claims(payload, options, audience, issuer, leeway)
    
    return payload


def decode_complete(jwt_token: str, key: Union[str, bytes] = None, algorithms: Optional[list] = None,
                    options: Optional[Dict[str, Any]] = None, audience: Optional[Union[str, list]] = None,
                    issuer: Optional[str] = None, leeway: Union[int, float, timedelta] = 0,
                    verify: bool = True) -> Dict[str, Any]:
    """Decode JWT token and return all components
    
    Args:
        Same as decode()
        
    Returns:
        Dictionary with 'header', 'payload', and 'signature' keys
    """
    # Parse token
    parts = jwt_token.split('.')
    if len(parts) != 3:
        raise DecodeError(f"Invalid token format: expected 3 parts, got {len(parts)}")
    
    header_b64, payload_b64, signature_b64 = parts
    
    # Decode components
    header_json = _base64url_decode(header_b64)
    header = json.loads(header_json)
    
    # Decode and verify payload
    payload = decode(jwt_token, key, algorithms, options, audience, issuer, leeway, verify)
    
    return {
        'header': header,
        'payload': payload,
        'signature': signature_b64
    }


def get_unverified_header(jwt_token: str) -> Dict[str, Any]:
    """Get JWT header without verification
    
    Args:
        jwt_token: JWT token string
        
    Returns:
        Header dictionary
        
    Raises:
        DecodeError: If token format is invalid
    """
    parts = jwt_token.split('.')
    if len(parts) != 3:
        raise DecodeError(f"Invalid token format: expected 3 parts, got {len(parts)}")
    
    header_b64 = parts[0]
    header_json = _base64url_decode(header_b64)
    return json.loads(header_json)


def _process_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process payload to convert datetime objects to timestamps
    
    Args:
        payload: Payload dictionary
        
    Returns:
        Processed payload dictionary
    """
    processed = {}
    for key, value in payload.items():
        if isinstance(value, datetime):
            # Convert to Unix timestamp
            processed[key] = int(value.timestamp())
        elif isinstance(value, timedelta):
            # Convert timedelta to seconds
            processed[key] = int(value.total_seconds())
        else:
            processed[key] = value
    
    return processed


def _verify_claims(payload: Dict[str, Any], options: Dict[str, Any],
                   audience: Optional[Union[str, list]], issuer: Optional[str],
                   leeway: Union[int, float, timedelta]) -> None:
    """Verify JWT claims
    
    Args:
        payload: Decoded payload
        options: Verification options
        audience: Expected audience
        issuer: Expected issuer
        leeway: Time leeway in seconds
        
    Raises:
        ExpiredSignatureError: If token has expired
        ImmatureSignatureError: If token is not yet valid
        InvalidAudienceError: If audience doesn't match
        InvalidIssuerError: If issuer doesn't match
        MissingRequiredClaimError: If required claim is missing
    """
    # Convert leeway to seconds
    if isinstance(leeway, timedelta):
        leeway = leeway.total_seconds()
    
    now = time.time()
    
    # Verify expiration (exp)
    if options.get('verify_exp', True):
        if options.get('require_exp', False) and 'exp' not in payload:
            raise MissingRequiredClaimError("Token is missing the 'exp' claim")
        
        if 'exp' in payload:
            exp = payload['exp']
            if not isinstance(exp, (int, float)):
                raise DecodeError("Expiration time must be a number")
            
            if exp < (now - leeway):
                raise ExpiredSignatureError("Token has expired")
    
    # Verify not before (nbf)
    if options.get('verify_nbf', True):
        if options.get('require_nbf', False) and 'nbf' not in payload:
            raise MissingRequiredClaimError("Token is missing the 'nbf' claim")
        
        if 'nbf' in payload:
            nbf = payload['nbf']
            if not isinstance(nbf, (int, float)):
                raise DecodeError("Not before time must be a number")
            
            if nbf > (now + leeway):
                raise ImmatureSignatureError("Token is not yet valid")
    
    # Verify issued at (iat)
    if options.get('verify_iat', True):
        if options.get('require_iat', False) and 'iat' not in payload:
            raise MissingRequiredClaimError("Token is missing the 'iat' claim")
        
        if 'iat' in payload:
            iat = payload['iat']
            if not isinstance(iat, (int, float)):
                raise DecodeError("Issued at time must be a number")
            
            # Check if iat is in the future (with leeway)
            if iat > (now + leeway):
                raise InvalidIssuedAtError("Token issued at time is in the future")
    
    # Verify audience (aud)
    if options.get('verify_aud', True) and audience is not None:
        if 'aud' not in payload:
            raise MissingRequiredClaimError("Token is missing the 'aud' claim")
        
        token_aud = payload['aud']
        
        # Normalize audience to list
        if isinstance(audience, str):
            audience = [audience]
        
        # Normalize token audience to list
        if isinstance(token_aud, str):
            token_aud = [token_aud]
        
        # Check if any expected audience matches
        if not any(aud in token_aud for aud in audience):
            raise InvalidAudienceError(f"Token audience {token_aud} doesn't match expected {audience}")
    
    # Verify issuer (iss)
    if options.get('verify_iss', True) and issuer is not None:
        if 'iss' not in payload:
            raise MissingRequiredClaimError("Token is missing the 'iss' claim")
        
        if payload['iss'] != issuer:
            raise InvalidIssuerError(f"Token issuer {payload['iss']} doesn't match expected {issuer}")


# Helper function for creating tokens with expiration
def create_token_with_expiration(payload: Dict[str, Any], key: Union[str, bytes],
                                 expires_in: Union[int, timedelta],
                                 algorithm: str = 'HS256') -> str:
    """Create JWT token with expiration time
    
    Args:
        payload: JWT claims
        key: Secret key
        expires_in: Expiration time (seconds or timedelta)
        algorithm: Algorithm to use
        
    Returns:
        Encoded JWT token
    """
    if isinstance(expires_in, int):
        expires_in = timedelta(seconds=expires_in)
    
    exp = datetime.utcnow() + expires_in
    payload = payload.copy()
    payload['exp'] = exp
    payload['iat'] = datetime.utcnow()
    
    return encode(payload, key, algorithm)


# Module-level exports
__all__ = [
    'encode',
    'decode',
    'decode_complete',
    'get_unverified_header',
    'create_token_with_expiration',
    'PyJWTError',
    'InvalidTokenError',
    'DecodeError',
    'InvalidSignatureError',
    'ExpiredSignatureError',
    'InvalidAudienceError',
    'InvalidIssuerError',
    'InvalidIssuedAtError',
    'ImmatureSignatureError',
    'MissingRequiredClaimError',
]
