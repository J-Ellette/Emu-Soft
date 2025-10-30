"""
Tests for PyJWT emulator
"""

import unittest
import time
from datetime import datetime, timedelta
from pyjwt_emulator import (
    encode, decode, decode_complete, get_unverified_header,
    create_token_with_expiration,
    PyJWTError, InvalidTokenError, DecodeError, InvalidSignatureError,
    ExpiredSignatureError, InvalidAudienceError, InvalidIssuerError,
    ImmatureSignatureError, MissingRequiredClaimError
)


class TestEncoding(unittest.TestCase):
    """Test JWT encoding"""
    
    def test_encode_basic(self):
        """Test basic token encoding"""
        payload = {'user_id': 123, 'username': 'testuser'}
        secret = 'secret-key'
        
        token = encode(payload, secret)
        
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split('.')), 3)
    
    def test_encode_with_algorithm(self):
        """Test encoding with different algorithms"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        
        # HS256
        token_256 = encode(payload, secret, algorithm='HS256')
        self.assertIsInstance(token_256, str)
        
        # HS384
        token_384 = encode(payload, secret, algorithm='HS384')
        self.assertIsInstance(token_384, str)
        
        # HS512
        token_512 = encode(payload, secret, algorithm='HS512')
        self.assertIsInstance(token_512, str)
    
    def test_encode_with_headers(self):
        """Test encoding with custom headers"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        headers = {'kid': 'key-123'}
        
        token = encode(payload, secret, headers=headers)
        header = get_unverified_header(token)
        
        self.assertEqual(header['kid'], 'key-123')
        self.assertEqual(header['typ'], 'JWT')
        self.assertEqual(header['alg'], 'HS256')
    
    def test_encode_with_datetime(self):
        """Test encoding with datetime objects"""
        exp = datetime.utcnow() + timedelta(hours=1)
        iat = datetime.utcnow()
        
        payload = {
            'user_id': 123,
            'exp': exp,
            'iat': iat
        }
        secret = 'secret-key'
        
        token = encode(payload, secret)
        decoded = decode(token, secret, algorithms=['HS256'])
        
        self.assertIsInstance(decoded['exp'], int)
        self.assertIsInstance(decoded['iat'], int)
    
    def test_encode_unsigned(self):
        """Test encoding unsigned token"""
        payload = {'user_id': 123}
        
        token = encode(payload, '', algorithm='none')
        
        self.assertTrue(token.endswith('.'))


class TestDecoding(unittest.TestCase):
    """Test JWT decoding"""
    
    def test_decode_basic(self):
        """Test basic token decoding"""
        payload = {'user_id': 123, 'username': 'testuser'}
        secret = 'secret-key'
        
        token = encode(payload, secret)
        decoded = decode(token, secret, algorithms=['HS256'])
        
        self.assertEqual(decoded['user_id'], 123)
        self.assertEqual(decoded['username'], 'testuser')
    
    def test_decode_without_verification(self):
        """Test decoding without verification"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        
        token = encode(payload, secret)
        decoded = decode(token, verify=False)
        
        self.assertEqual(decoded['user_id'], 123)
    
    def test_decode_invalid_signature(self):
        """Test decoding with invalid signature"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        wrong_secret = 'wrong-key'
        
        token = encode(payload, secret)
        
        with self.assertRaises(InvalidSignatureError):
            decode(token, wrong_secret, algorithms=['HS256'])
    
    def test_decode_invalid_algorithm(self):
        """Test decoding with disallowed algorithm"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        
        token = encode(payload, secret, algorithm='HS256')
        
        with self.assertRaises(InvalidTokenError):
            decode(token, secret, algorithms=['HS384'])
    
    def test_decode_malformed_token(self):
        """Test decoding malformed token"""
        with self.assertRaises(DecodeError):
            decode('invalid.token', 'secret', algorithms=['HS256'])
        
        with self.assertRaises(DecodeError):
            decode('invalid', 'secret', algorithms=['HS256'])


class TestClaims(unittest.TestCase):
    """Test JWT claims verification"""
    
    def test_expired_token(self):
        """Test expired token detection"""
        exp = datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        payload = {
            'user_id': 123,
            'exp': exp
        }
        secret = 'secret-key'
        
        token = encode(payload, secret)
        
        with self.assertRaises(ExpiredSignatureError):
            decode(token, secret, algorithms=['HS256'])
    
    def test_not_before(self):
        """Test not before (nbf) claim"""
        nbf = datetime.utcnow() + timedelta(hours=1)  # Valid in 1 hour
        payload = {
            'user_id': 123,
            'nbf': nbf
        }
        secret = 'secret-key'
        
        token = encode(payload, secret)
        
        with self.assertRaises(ImmatureSignatureError):
            decode(token, secret, algorithms=['HS256'])
    
    def test_audience_claim(self):
        """Test audience claim verification"""
        payload = {
            'user_id': 123,
            'aud': 'my-app'
        }
        secret = 'secret-key'
        
        token = encode(payload, secret)
        
        # Valid audience
        decoded = decode(token, secret, algorithms=['HS256'], audience='my-app')
        self.assertEqual(decoded['user_id'], 123)
        
        # Invalid audience
        with self.assertRaises(InvalidAudienceError):
            decode(token, secret, algorithms=['HS256'], audience='other-app')
    
    def test_audience_list(self):
        """Test audience with list"""
        payload = {
            'user_id': 123,
            'aud': ['app1', 'app2']
        }
        secret = 'secret-key'
        
        token = encode(payload, secret)
        
        # Valid audience (one of them)
        decoded = decode(token, secret, algorithms=['HS256'], audience='app1')
        self.assertEqual(decoded['user_id'], 123)
        
        # Valid audience (other one)
        decoded = decode(token, secret, algorithms=['HS256'], audience='app2')
        self.assertEqual(decoded['user_id'], 123)
        
        # Invalid audience
        with self.assertRaises(InvalidAudienceError):
            decode(token, secret, algorithms=['HS256'], audience='app3')
    
    def test_issuer_claim(self):
        """Test issuer claim verification"""
        payload = {
            'user_id': 123,
            'iss': 'my-service'
        }
        secret = 'secret-key'
        
        token = encode(payload, secret)
        
        # Valid issuer
        decoded = decode(token, secret, algorithms=['HS256'], issuer='my-service')
        self.assertEqual(decoded['user_id'], 123)
        
        # Invalid issuer
        with self.assertRaises(InvalidIssuerError):
            decode(token, secret, algorithms=['HS256'], issuer='other-service')
    
    def test_leeway(self):
        """Test leeway for time-based claims"""
        # Token that expired 5 seconds ago
        exp = datetime.utcnow() - timedelta(seconds=5)
        payload = {
            'user_id': 123,
            'exp': exp
        }
        secret = 'secret-key'
        
        token = encode(payload, secret)
        
        # Should fail without leeway
        with self.assertRaises(ExpiredSignatureError):
            decode(token, secret, algorithms=['HS256'])
        
        # Should succeed with 10 second leeway
        decoded = decode(token, secret, algorithms=['HS256'], leeway=10)
        self.assertEqual(decoded['user_id'], 123)
    
    def test_required_claims(self):
        """Test required claims"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        
        token = encode(payload, secret)
        
        options = {'require_exp': True}
        
        with self.assertRaises(MissingRequiredClaimError):
            decode(token, secret, algorithms=['HS256'], options=options)


class TestDecodeComplete(unittest.TestCase):
    """Test decode_complete function"""
    
    def test_decode_complete(self):
        """Test decoding complete token"""
        payload = {'user_id': 123, 'username': 'testuser'}
        secret = 'secret-key'
        
        token = encode(payload, secret)
        result = decode_complete(token, secret, algorithms=['HS256'])
        
        self.assertIn('header', result)
        self.assertIn('payload', result)
        self.assertIn('signature', result)
        
        self.assertEqual(result['header']['alg'], 'HS256')
        self.assertEqual(result['header']['typ'], 'JWT')
        self.assertEqual(result['payload']['user_id'], 123)


class TestGetUnverifiedHeader(unittest.TestCase):
    """Test get_unverified_header function"""
    
    def test_get_header(self):
        """Test getting header without verification"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        headers = {'kid': 'key-123'}
        
        token = encode(payload, secret, headers=headers)
        header = get_unverified_header(token)
        
        self.assertEqual(header['alg'], 'HS256')
        self.assertEqual(header['typ'], 'JWT')
        self.assertEqual(header['kid'], 'key-123')
    
    def test_get_header_malformed(self):
        """Test getting header from malformed token"""
        with self.assertRaises(DecodeError):
            get_unverified_header('invalid')


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions"""
    
    def test_create_token_with_expiration(self):
        """Test creating token with expiration"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        
        # With seconds
        token = create_token_with_expiration(payload, secret, expires_in=3600)
        decoded = decode(token, secret, algorithms=['HS256'])
        
        self.assertIn('exp', decoded)
        self.assertIn('iat', decoded)
        self.assertEqual(decoded['user_id'], 123)
        
        # With timedelta
        token = create_token_with_expiration(payload, secret, expires_in=timedelta(hours=1))
        decoded = decode(token, secret, algorithms=['HS256'])
        
        self.assertIn('exp', decoded)
        self.assertIn('iat', decoded)


class TestAlgorithms(unittest.TestCase):
    """Test different algorithms"""
    
    def test_hs256(self):
        """Test HS256 algorithm"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        
        token = encode(payload, secret, algorithm='HS256')
        decoded = decode(token, secret, algorithms=['HS256'])
        
        self.assertEqual(decoded['user_id'], 123)
    
    def test_hs384(self):
        """Test HS384 algorithm"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        
        token = encode(payload, secret, algorithm='HS384')
        decoded = decode(token, secret, algorithms=['HS384'])
        
        self.assertEqual(decoded['user_id'], 123)
    
    def test_hs512(self):
        """Test HS512 algorithm"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        
        token = encode(payload, secret, algorithm='HS512')
        decoded = decode(token, secret, algorithms=['HS512'])
        
        self.assertEqual(decoded['user_id'], 123)
    
    def test_algorithm_mismatch(self):
        """Test algorithm mismatch detection"""
        payload = {'user_id': 123}
        secret = 'secret-key'
        
        # Encode with HS256
        token = encode(payload, secret, algorithm='HS256')
        
        # Try to decode with HS384
        with self.assertRaises(InvalidTokenError):
            decode(token, secret, algorithms=['HS384'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases"""
    
    def test_empty_payload(self):
        """Test encoding empty payload"""
        payload = {}
        secret = 'secret-key'
        
        token = encode(payload, secret)
        decoded = decode(token, secret, algorithms=['HS256'])
        
        self.assertEqual(decoded, {})
    
    def test_large_payload(self):
        """Test encoding large payload"""
        payload = {f'key_{i}': f'value_{i}' for i in range(100)}
        secret = 'secret-key'
        
        token = encode(payload, secret)
        decoded = decode(token, secret, algorithms=['HS256'])
        
        self.assertEqual(len(decoded), 100)
    
    def test_special_characters(self):
        """Test payload with special characters"""
        payload = {
            'user': 'test@example.com',
            'message': 'Hello, World! 你好世界',
            'symbols': '!@#$%^&*()'
        }
        secret = 'secret-key'
        
        token = encode(payload, secret)
        decoded = decode(token, secret, algorithms=['HS256'])
        
        self.assertEqual(decoded['user'], 'test@example.com')
        self.assertEqual(decoded['message'], 'Hello, World! 你好世界')
        self.assertEqual(decoded['symbols'], '!@#$%^&*()')


if __name__ == '__main__':
    unittest.main()
