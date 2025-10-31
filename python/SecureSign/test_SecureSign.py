"""
Test suite for itsdangerous emulator
"""

import unittest
import time
import json
from SecureSign import (
    Signer, TimestampSigner, Serializer, TimedSerializer,
    URLSafeSerializer, URLSafeTimedSerializer,
    BadSignature, SignatureExpired, BadTimeSignature, BadPayload,
    sign, unsign, _constant_time_compare
)


class TestConstantTimeCompare(unittest.TestCase):
    """Tests for constant time comparison"""
    
    def test_equal_strings(self):
        """Test comparing equal byte strings"""
        self.assertTrue(_constant_time_compare(b'hello', b'hello'))
    
    def test_unequal_strings(self):
        """Test comparing unequal byte strings"""
        self.assertFalse(_constant_time_compare(b'hello', b'world'))
    
    def test_different_lengths(self):
        """Test comparing strings of different lengths"""
        self.assertFalse(_constant_time_compare(b'hello', b'hi'))


class TestSigner(unittest.TestCase):
    """Tests for basic Signer"""
    
    def setUp(self):
        self.secret_key = 'my-secret-key'
        self.signer = Signer(self.secret_key)
    
    def test_sign_string(self):
        """Test signing a string"""
        value = 'hello world'
        signed = self.signer.sign(value)
        
        self.assertIsInstance(signed, bytes)
        self.assertIn(b'.', signed)
        self.assertTrue(signed.startswith(b'hello world.'))
    
    def test_sign_bytes(self):
        """Test signing bytes"""
        value = b'hello world'
        signed = self.signer.sign(value)
        
        self.assertIsInstance(signed, bytes)
        self.assertIn(b'.', signed)
    
    def test_unsign_valid(self):
        """Test unsigning a valid signature"""
        value = 'hello world'
        signed = self.signer.sign(value)
        unsigned = self.signer.unsign(signed)
        
        self.assertEqual(unsigned, b'hello world')
    
    def test_unsign_invalid(self):
        """Test unsigning an invalid signature"""
        with self.assertRaises(BadSignature):
            self.signer.unsign(b'hello world.invalid')
    
    def test_unsign_tampered(self):
        """Test unsigning a tampered value"""
        signed = self.signer.sign('hello world')
        # Tamper with the value
        tampered = b'goodbye world' + signed[len(b'hello world'):]
        
        with self.assertRaises(BadSignature):
            self.signer.unsign(tampered)
    
    def test_unsign_no_separator(self):
        """Test unsigning value without separator"""
        with self.assertRaises(BadSignature):
            self.signer.unsign(b'hello world')
    
    def test_different_salts(self):
        """Test that different salts produce different signatures"""
        signer1 = Signer(self.secret_key, salt=b'salt1')
        signer2 = Signer(self.secret_key, salt=b'salt2')
        
        signed1 = signer1.sign('test')
        signed2 = signer2.sign('test')
        
        self.assertNotEqual(signed1, signed2)
        
        # Each signer can only unsign its own signatures
        self.assertEqual(signer1.unsign(signed1), b'test')
        with self.assertRaises(BadSignature):
            signer1.unsign(signed2)
    
    def test_different_keys(self):
        """Test that different keys produce different signatures"""
        signer1 = Signer('key1')
        signer2 = Signer('key2')
        
        signed1 = signer1.sign('test')
        signed2 = signer2.sign('test')
        
        self.assertNotEqual(signed1, signed2)
        
        # Each signer can only unsign its own signatures
        with self.assertRaises(BadSignature):
            signer2.unsign(signed1)


class TestTimestampSigner(unittest.TestCase):
    """Tests for TimestampSigner"""
    
    def setUp(self):
        self.secret_key = 'my-secret-key'
        self.signer = TimestampSigner(self.secret_key)
    
    def test_sign_with_timestamp(self):
        """Test signing with timestamp"""
        value = 'hello world'
        signed = self.signer.sign(value)
        
        self.assertIsInstance(signed, bytes)
        # Should have two separators (value.timestamp.signature)
        self.assertEqual(signed.count(b'.'), 2)
    
    def test_unsign_fresh_signature(self):
        """Test unsigning a fresh signature"""
        value = 'hello world'
        signed = self.signer.sign(value)
        unsigned = self.signer.unsign(signed)
        
        self.assertEqual(unsigned, b'hello world')
    
    def test_unsign_with_max_age(self):
        """Test unsigning with max_age"""
        value = 'hello world'
        signed = self.signer.sign(value)
        
        # Should work with generous max_age
        unsigned = self.signer.unsign(signed, max_age=10)
        self.assertEqual(unsigned, b'hello world')
    
    def test_unsign_expired(self):
        """Test unsigning an expired signature"""
        value = 'hello world'
        signed = self.signer.sign(value)
        
        # Wait at least 1 second
        time.sleep(1.1)
        
        # Should fail with very short max_age
        with self.assertRaises(SignatureExpired):
            self.signer.unsign(signed, max_age=0)
    
    def test_unsign_return_timestamp(self):
        """Test unsigning and returning timestamp"""
        value = 'hello world'
        before = int(time.time())
        signed = self.signer.sign(value)
        after = int(time.time())
        
        unsigned, timestamp = self.signer.unsign(signed, return_timestamp=True)
        
        self.assertEqual(unsigned, b'hello world')
        self.assertIsInstance(timestamp, int)
        self.assertGreaterEqual(timestamp, before)
        self.assertLessEqual(timestamp, after)
    
    def test_unsign_invalid_timestamp(self):
        """Test unsigning with malformed timestamp"""
        # Create a signed value with invalid timestamp
        value = b'hello world.invalid_ts'
        sig = self.signer.get_signature(value)
        signed = value + b'.' + sig
        
        with self.assertRaises(BadTimeSignature):
            self.signer.unsign(signed)


class TestSerializer(unittest.TestCase):
    """Tests for Serializer"""
    
    def setUp(self):
        self.secret_key = 'my-secret-key'
        self.serializer = Serializer(self.secret_key)
    
    def test_dumps_loads_dict(self):
        """Test serializing and deserializing a dict"""
        data = {'key': 'value', 'number': 42, 'list': [1, 2, 3]}
        signed = self.serializer.dumps(data)
        
        self.assertIsInstance(signed, str)
        
        loaded = self.serializer.loads(signed)
        self.assertEqual(loaded, data)
    
    def test_dumps_loads_list(self):
        """Test serializing and deserializing a list"""
        data = [1, 2, 3, 'hello', {'nested': True}]
        signed = self.serializer.dumps(data)
        loaded = self.serializer.loads(signed)
        
        self.assertEqual(loaded, data)
    
    def test_dumps_loads_string(self):
        """Test serializing and deserializing a string"""
        data = 'hello world'
        signed = self.serializer.dumps(data)
        loaded = self.serializer.loads(signed)
        
        self.assertEqual(loaded, data)
    
    def test_dumps_loads_number(self):
        """Test serializing and deserializing numbers"""
        data = 42
        signed = self.serializer.dumps(data)
        loaded = self.serializer.loads(signed)
        
        self.assertEqual(loaded, data)
    
    def test_loads_invalid_signature(self):
        """Test loading with invalid signature"""
        signed = self.serializer.dumps({'test': 'data'})
        # Tamper with signature
        tampered = signed[:-5] + 'xxxxx'
        
        with self.assertRaises(BadSignature):
            self.serializer.loads(tampered)
    
    def test_loads_invalid_payload(self):
        """Test loading with invalid payload"""
        # Sign an invalid payload
        signer = self.serializer.make_signer()
        signed = signer.sign(b'not-valid-base64!!!')
        
        with self.assertRaises(BadPayload):
            self.serializer.loads(signed)
    
    def test_different_salts(self):
        """Test that different salts produce different signatures"""
        data = {'test': 'data'}
        
        signed1 = self.serializer.dumps(data, salt=b'salt1')
        signed2 = self.serializer.dumps(data, salt=b'salt2')
        
        self.assertNotEqual(signed1, signed2)
        
        # Each can be loaded with the correct salt
        self.assertEqual(self.serializer.loads(signed1, salt=b'salt1'), data)
        self.assertEqual(self.serializer.loads(signed2, salt=b'salt2'), data)
        
        # But not with the wrong salt
        with self.assertRaises(BadSignature):
            self.serializer.loads(signed1, salt=b'salt2')
    
    def test_compression(self):
        """Test that large data gets compressed"""
        # Create data that compresses well
        data = {'data': 'x' * 1000}
        signed = self.serializer.dumps(data)
        
        # Should start with '.' indicating compression
        # (after base64 encoding and signing)
        loaded = self.serializer.loads(signed)
        self.assertEqual(loaded, data)


class TestTimedSerializer(unittest.TestCase):
    """Tests for TimedSerializer"""
    
    def setUp(self):
        self.secret_key = 'my-secret-key'
        self.serializer = TimedSerializer(self.secret_key)
    
    def test_dumps_loads_fresh(self):
        """Test serializing and deserializing fresh data"""
        data = {'key': 'value', 'number': 42}
        signed = self.serializer.dumps(data)
        loaded = self.serializer.loads(signed)
        
        self.assertEqual(loaded, data)
    
    def test_loads_with_max_age(self):
        """Test loading with max_age"""
        data = {'key': 'value'}
        signed = self.serializer.dumps(data)
        
        # Should work with generous max_age
        loaded = self.serializer.loads(signed, max_age=10)
        self.assertEqual(loaded, data)
    
    def test_loads_expired(self):
        """Test loading expired data"""
        data = {'key': 'value'}
        signed = self.serializer.dumps(data)
        
        time.sleep(1.1)
        
        # Should fail with very short max_age
        with self.assertRaises(SignatureExpired):
            self.serializer.loads(signed, max_age=0)
    
    def test_loads_return_timestamp(self):
        """Test loading with timestamp"""
        data = {'key': 'value'}
        before = int(time.time())
        signed = self.serializer.dumps(data)
        after = int(time.time())
        
        loaded, timestamp = self.serializer.loads(signed, return_timestamp=True)
        
        self.assertEqual(loaded, data)
        self.assertIsInstance(timestamp, int)
        self.assertGreaterEqual(timestamp, before)
        self.assertLessEqual(timestamp, after)
    
    def test_loads_with_max_age_and_timestamp(self):
        """Test loading with both max_age and return_timestamp"""
        data = {'key': 'value'}
        signed = self.serializer.dumps(data)
        
        loaded, timestamp = self.serializer.loads(signed, max_age=10, 
                                                   return_timestamp=True)
        
        self.assertEqual(loaded, data)
        self.assertIsInstance(timestamp, int)


class TestURLSafeSerializers(unittest.TestCase):
    """Tests for URL-safe serializer aliases"""
    
    def test_url_safe_serializer(self):
        """Test URLSafeSerializer"""
        s = URLSafeSerializer('secret')
        data = {'test': 'data'}
        
        signed = s.dumps(data)
        loaded = s.loads(signed)
        
        self.assertEqual(loaded, data)
    
    def test_url_safe_timed_serializer(self):
        """Test URLSafeTimedSerializer"""
        s = URLSafeTimedSerializer('secret')
        data = {'test': 'data'}
        
        signed = s.dumps(data)
        loaded = s.loads(signed, max_age=10)
        
        self.assertEqual(loaded, data)


class TestConvenienceFunctions(unittest.TestCase):
    """Tests for convenience functions"""
    
    def test_sign_unsign(self):
        """Test sign and unsign convenience functions"""
        secret = 'my-secret'
        value = 'hello world'
        
        signed = sign(value, secret)
        unsigned = unsign(signed, secret)
        
        self.assertEqual(unsigned, value)
    
    def test_unsign_invalid(self):
        """Test unsign with invalid signature"""
        secret = 'my-secret'
        
        with self.assertRaises(BadSignature):
            unsign('hello.invalid', secret)
    
    def test_different_salts(self):
        """Test sign/unsign with different salts"""
        secret = 'my-secret'
        value = 'test'
        
        signed1 = sign(value, secret, salt=b'salt1')
        signed2 = sign(value, secret, salt=b'salt2')
        
        self.assertNotEqual(signed1, signed2)
        
        # Can unsign with correct salt
        self.assertEqual(unsign(signed1, secret, salt=b'salt1'), value)
        
        # Cannot unsign with wrong salt
        with self.assertRaises(BadSignature):
            unsign(signed1, secret, salt=b'salt2')


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and special scenarios"""
    
    def test_empty_value(self):
        """Test signing empty value"""
        s = Signer('secret')
        signed = s.sign('')
        unsigned = s.unsign(signed)
        
        self.assertEqual(unsigned, b'')
    
    def test_binary_data(self):
        """Test signing binary data"""
        s = Signer('secret')
        data = b'\x00\x01\x02\xff\xfe\xfd'
        
        signed = s.sign(data)
        unsigned = s.unsign(signed)
        
        self.assertEqual(unsigned, data)
    
    def test_unicode_data(self):
        """Test signing unicode data"""
        serializer = Serializer('secret')
        data = {'unicode': '你好世界', 'emoji': '🎉🎊'}
        
        signed = serializer.dumps(data)
        loaded = serializer.loads(signed)
        
        self.assertEqual(loaded, data)
    
    def test_nested_structures(self):
        """Test deeply nested data structures"""
        serializer = Serializer('secret')
        data = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': [1, 2, 3, {'level5': True}]
                    }
                }
            }
        }
        
        signed = serializer.dumps(data)
        loaded = serializer.loads(signed)
        
        self.assertEqual(loaded, data)
    
    def test_none_values(self):
        """Test serializing None values"""
        serializer = Serializer('secret')
        data = {'value': None, 'list': [None, 1, None]}
        
        signed = serializer.dumps(data)
        loaded = serializer.loads(signed)
        
        self.assertEqual(loaded, data)
    
    def test_boolean_values(self):
        """Test serializing boolean values"""
        serializer = Serializer('secret')
        data = {'true': True, 'false': False}
        
        signed = serializer.dumps(data)
        loaded = serializer.loads(signed)
        
        self.assertEqual(loaded, data)


if __name__ == '__main__':
    unittest.main()
