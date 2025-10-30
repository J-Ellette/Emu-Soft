"""
Test suite for cryptography emulator
"""

import unittest
import time
import os
from cryptography_emulator import (
    Fernet, MultiFernet,
    Hash, HMAC,
    SHA1, SHA256, SHA384, SHA512, MD5, BLAKE2b, BLAKE2s,
    hashes_Hash,
    PBKDF2HMAC, Scrypt, HKDF,
    PKCS7,
    TOTP, HOTP,
    InvalidToken, InvalidSignature, InvalidKey, AlreadyFinalized,
    constant_time_bytes_eq
)


class TestConstantTimeComparison(unittest.TestCase):
    """Tests for constant time comparison"""
    
    def test_equal_bytes(self):
        """Test equal byte strings"""
        self.assertTrue(constant_time_bytes_eq(b'hello', b'hello'))
    
    def test_unequal_bytes(self):
        """Test unequal byte strings"""
        self.assertFalse(constant_time_bytes_eq(b'hello', b'world'))
    
    def test_different_lengths(self):
        """Test different length strings"""
        self.assertFalse(constant_time_bytes_eq(b'hello', b'hi'))


class TestFernet(unittest.TestCase):
    """Tests for Fernet encryption"""
    
    def test_generate_key(self):
        """Test key generation"""
        key = Fernet.generate_key()
        self.assertIsInstance(key, bytes)
        self.assertGreater(len(key), 0)
    
    def test_encrypt_decrypt(self):
        """Test basic encryption and decryption"""
        key = Fernet.generate_key()
        f = Fernet(key)
        
        plaintext = b'hello world'
        token = f.encrypt(plaintext)
        
        self.assertIsInstance(token, bytes)
        self.assertNotEqual(token, plaintext)
        
        decrypted = f.decrypt(token)
        self.assertEqual(decrypted, plaintext)
    
    def test_encrypt_empty(self):
        """Test encrypting empty data"""
        key = Fernet.generate_key()
        f = Fernet(key)
        
        token = f.encrypt(b'')
        decrypted = f.decrypt(token)
        
        self.assertEqual(decrypted, b'')
    
    def test_encrypt_large_data(self):
        """Test encrypting large data"""
        key = Fernet.generate_key()
        f = Fernet(key)
        
        plaintext = b'x' * 10000
        token = f.encrypt(plaintext)
        decrypted = f.decrypt(token)
        
        self.assertEqual(decrypted, plaintext)
    
    def test_decrypt_with_ttl(self):
        """Test decryption with TTL"""
        key = Fernet.generate_key()
        f = Fernet(key)
        
        plaintext = b'test data'
        token = f.encrypt(plaintext)
        
        # Should work with generous TTL
        decrypted = f.decrypt(token, ttl=60)
        self.assertEqual(decrypted, plaintext)
    
    def test_decrypt_expired(self):
        """Test decryption of expired token"""
        key = Fernet.generate_key()
        f = Fernet(key)
        
        # Create token with old timestamp
        plaintext = b'test data'
        old_time = int(time.time()) - 100
        token = f.encrypt_at_time(plaintext, old_time)
        
        # Should fail with short TTL
        with self.assertRaises(InvalidToken):
            f.decrypt(token, ttl=10)
    
    def test_decrypt_wrong_key(self):
        """Test decryption with wrong key"""
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        
        f1 = Fernet(key1)
        f2 = Fernet(key2)
        
        token = f1.encrypt(b'secret')
        
        with self.assertRaises(InvalidToken):
            f2.decrypt(token)
    
    def test_decrypt_tampered(self):
        """Test decryption of tampered token"""
        key = Fernet.generate_key()
        f = Fernet(key)
        
        token = f.encrypt(b'original')
        # Tamper with token
        tampered = token[:-5] + b'xxxxx'
        
        with self.assertRaises(InvalidToken):
            f.decrypt(tampered)
    
    def test_invalid_key(self):
        """Test invalid key format"""
        with self.assertRaises(InvalidKey):
            Fernet(b'not-a-valid-key')
    
    def test_decrypt_invalid_token(self):
        """Test decrypting invalid token"""
        key = Fernet.generate_key()
        f = Fernet(key)
        
        with self.assertRaises(InvalidToken):
            f.decrypt(b'invalid-token')


class TestMultiFernet(unittest.TestCase):
    """Tests for MultiFernet"""
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption with multiple keys"""
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        
        mf = MultiFernet([Fernet(key1), Fernet(key2)])
        
        plaintext = b'hello world'
        token = mf.encrypt(plaintext)
        decrypted = mf.decrypt(token)
        
        self.assertEqual(decrypted, plaintext)
    
    def test_decrypt_any_key(self):
        """Test decrypting with any available key"""
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        
        f1 = Fernet(key1)
        f2 = Fernet(key2)
        
        mf = MultiFernet([f1, f2])
        
        # Encrypt with second key
        token = f2.encrypt(b'test')
        
        # Should decrypt with MultiFernet
        decrypted = mf.decrypt(token)
        self.assertEqual(decrypted, b'test')
    
    def test_rotate(self):
        """Test key rotation"""
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        
        f1 = Fernet(key1)
        f2 = Fernet(key2)
        
        # Encrypt with old key
        token_old = f2.encrypt(b'data')
        
        # Rotate to new key
        mf = MultiFernet([f1, f2])
        token_new = mf.rotate(token_old)
        
        # Should be encrypted with first key now
        decrypted = f1.decrypt(token_new)
        self.assertEqual(decrypted, b'data')
    
    def test_empty_fernets(self):
        """Test MultiFernet with no keys"""
        with self.assertRaises(ValueError):
            MultiFernet([])


class TestHash(unittest.TestCase):
    """Tests for Hash"""
    
    def test_sha256(self):
        """Test SHA256 hashing"""
        h = Hash('sha256')
        h.update(b'hello')
        h.update(b' world')
        digest = h.finalize()
        
        self.assertIsInstance(digest, bytes)
        self.assertEqual(len(digest), 32)
    
    def test_multiple_algorithms(self):
        """Test different hash algorithms"""
        algorithms = ['sha1', 'sha256', 'sha512', 'md5']
        
        for algo in algorithms:
            h = Hash(algo)
            h.update(b'test data')
            digest = h.finalize()
            
            self.assertIsInstance(digest, bytes)
            self.assertGreater(len(digest), 0)
    
    def test_already_finalized(self):
        """Test that finalized hash cannot be updated"""
        h = Hash('sha256')
        h.update(b'data')
        h.finalize()
        
        with self.assertRaises(AlreadyFinalized):
            h.update(b'more data')
        
        with self.assertRaises(AlreadyFinalized):
            h.finalize()
    
    def test_copy(self):
        """Test copying hash context"""
        h1 = Hash('sha256')
        h1.update(b'hello')
        
        h2 = h1.copy()
        h1.update(b' world')
        h2.update(b' earth')
        
        digest1 = h1.finalize()
        digest2 = h2.finalize()
        
        self.assertNotEqual(digest1, digest2)
    
    def test_hashes_Hash(self):
        """Test hashes_Hash convenience function"""
        h = hashes_Hash(SHA256())
        h.update(b'test')
        digest = h.finalize()
        
        self.assertEqual(len(digest), 32)


class TestHMAC(unittest.TestCase):
    """Tests for HMAC"""
    
    def test_hmac_sha256(self):
        """Test HMAC with SHA256"""
        key = b'secret-key'
        h = HMAC(key, SHA256())
        h.update(b'message')
        signature = h.finalize()
        
        self.assertIsInstance(signature, bytes)
        self.assertEqual(len(signature), 32)
    
    def test_hmac_verify(self):
        """Test HMAC verification"""
        key = b'secret-key'
        message = b'test message'
        
        # Generate signature
        h1 = HMAC(key, SHA256())
        h1.update(message)
        signature = h1.finalize()
        
        # Verify signature
        h2 = HMAC(key, SHA256())
        h2.update(message)
        h2.verify(signature)  # Should not raise
    
    def test_hmac_verify_invalid(self):
        """Test HMAC verification with invalid signature"""
        key = b'secret-key'
        h = HMAC(key, SHA256())
        h.update(b'message')
        
        with self.assertRaises(InvalidSignature):
            h.verify(b'invalid-signature-bytes-here')
    
    def test_hmac_copy(self):
        """Test copying HMAC context"""
        key = b'key'
        h1 = HMAC(key, SHA256())
        h1.update(b'hello')
        
        h2 = h1.copy()
        h1.update(b' world')
        h2.update(b' earth')
        
        sig1 = h1.finalize()
        sig2 = h2.finalize()
        
        self.assertNotEqual(sig1, sig2)


class TestPBKDF2HMAC(unittest.TestCase):
    """Tests for PBKDF2HMAC"""
    
    def test_derive(self):
        """Test key derivation"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        
        key = kdf.derive(b'password')
        
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 32)
    
    def test_same_password_same_key(self):
        """Test that same password produces same key"""
        salt = os.urandom(16)
        
        kdf1 = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        key1 = kdf1.derive(b'password')
        
        kdf2 = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        key2 = kdf2.derive(b'password')
        
        self.assertEqual(key1, key2)
    
    def test_different_salt_different_key(self):
        """Test that different salt produces different key"""
        kdf1 = PBKDF2HMAC(SHA256(), 32, os.urandom(16), 100000)
        key1 = kdf1.derive(b'password')
        
        kdf2 = PBKDF2HMAC(SHA256(), 32, os.urandom(16), 100000)
        key2 = kdf2.derive(b'password')
        
        self.assertNotEqual(key1, key2)
    
    def test_verify(self):
        """Test key verification"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        key = kdf.derive(b'password')
        
        kdf2 = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        kdf2.verify(b'password', key)  # Should not raise
    
    def test_verify_wrong_password(self):
        """Test verification with wrong password"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        key = kdf.derive(b'password')
        
        kdf2 = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        with self.assertRaises(InvalidKey):
            kdf2.verify(b'wrong', key)
    
    def test_already_used(self):
        """Test that KDF can only be used once"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(SHA256(), 32, salt, 100000)
        kdf.derive(b'password')
        
        with self.assertRaises(AlreadyFinalized):
            kdf.derive(b'password')


class TestScrypt(unittest.TestCase):
    """Tests for Scrypt"""
    
    def test_derive(self):
        """Test Scrypt key derivation"""
        salt = os.urandom(16)
        kdf = Scrypt(salt, 32, n=2**14, r=8, p=1)
        
        key = kdf.derive(b'password')
        
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 32)
    
    def test_same_parameters_same_key(self):
        """Test consistency"""
        salt = os.urandom(16)
        
        kdf1 = Scrypt(salt, 32, n=2**14, r=8, p=1)
        key1 = kdf1.derive(b'password')
        
        kdf2 = Scrypt(salt, 32, n=2**14, r=8, p=1)
        key2 = kdf2.derive(b'password')
        
        self.assertEqual(key1, key2)
    
    def test_verify(self):
        """Test key verification"""
        salt = os.urandom(16)
        kdf = Scrypt(salt, 32, n=2**14, r=8, p=1)
        key = kdf.derive(b'password')
        
        kdf2 = Scrypt(salt, 32, n=2**14, r=8, p=1)
        kdf2.verify(b'password', key)  # Should not raise


class TestHKDF(unittest.TestCase):
    """Tests for HKDF"""
    
    def test_derive(self):
        """Test HKDF derivation"""
        salt = os.urandom(16)
        info = b'application context'
        
        kdf = HKDF(SHA256(), 32, salt, info)
        key = kdf.derive(b'input key material')
        
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 32)
    
    def test_same_inputs_same_output(self):
        """Test consistency"""
        salt = os.urandom(16)
        info = b'context'
        ikm = b'key material'
        
        kdf1 = HKDF(SHA256(), 32, salt, info)
        key1 = kdf1.derive(ikm)
        
        kdf2 = HKDF(SHA256(), 32, salt, info)
        key2 = kdf2.derive(ikm)
        
        self.assertEqual(key1, key2)
    
    def test_different_info_different_output(self):
        """Test that different info produces different keys"""
        salt = os.urandom(16)
        ikm = b'key material'
        
        kdf1 = HKDF(SHA256(), 32, salt, b'info1')
        key1 = kdf1.derive(ikm)
        
        kdf2 = HKDF(SHA256(), 32, salt, b'info2')
        key2 = kdf2.derive(ikm)
        
        self.assertNotEqual(key1, key2)
    
    def test_verify(self):
        """Test key verification"""
        salt = os.urandom(16)
        info = b'context'
        ikm = b'key material'
        
        kdf = HKDF(SHA256(), 32, salt, info)
        key = kdf.derive(ikm)
        
        kdf2 = HKDF(SHA256(), 32, salt, info)
        kdf2.verify(ikm, key)  # Should not raise


class TestPKCS7(unittest.TestCase):
    """Tests for PKCS7 padding"""
    
    def test_pad_unpad(self):
        """Test padding and unpadding"""
        padder = PKCS7(128)
        
        data = b'hello world'
        padded = padder.pad(data)
        
        self.assertGreater(len(padded), len(data))
        self.assertEqual(len(padded) % 16, 0)
        
        unpadded = padder.unpad(padded)
        self.assertEqual(unpadded, data)
    
    def test_pad_block_size(self):
        """Test padding when data is already block-aligned"""
        padder = PKCS7(128)
        
        data = b'x' * 16  # Exactly one block
        padded = padder.pad(data)
        
        # Should add full block of padding
        self.assertEqual(len(padded), 32)
        
        unpadded = padder.unpad(padded)
        self.assertEqual(unpadded, data)
    
    def test_unpad_invalid(self):
        """Test unpadding invalid data"""
        padder = PKCS7(128)
        
        # Invalid padding
        with self.assertRaises(ValueError):
            padder.unpad(b'invalid-padding-here')
    
    def test_empty_data(self):
        """Test padding empty data"""
        padder = PKCS7(128)
        
        padded = padder.pad(b'')
        self.assertEqual(len(padded), 16)
        
        unpadded = padder.unpad(padded)
        self.assertEqual(unpadded, b'')


class TestTOTP(unittest.TestCase):
    """Tests for TOTP"""
    
    def test_generate(self):
        """Test TOTP generation"""
        key = b'secret-key-12345'
        totp = TOTP(key)
        
        code = totp.generate()
        
        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
    
    def test_verify(self):
        """Test TOTP verification"""
        key = b'secret-key-12345'
        totp = TOTP(key)
        
        time_value = int(time.time())
        code = totp.generate(time_value)
        
        # Should verify with same time
        self.assertTrue(totp.verify(code, time_value))
    
    def test_verify_wrong_code(self):
        """Test verification with wrong code"""
        key = b'secret-key-12345'
        totp = TOTP(key)
        
        self.assertFalse(totp.verify('000000'))
    
    def test_time_window(self):
        """Test TOTP time window"""
        key = b'secret-key-12345'
        totp = TOTP(key, time_step=30)
        
        current_time = int(time.time())
        code = totp.generate(current_time)
        
        # Should work in adjacent windows
        self.assertTrue(totp.verify(code, current_time - 30))
        self.assertTrue(totp.verify(code, current_time))
        self.assertTrue(totp.verify(code, current_time + 30))
    
    def test_different_lengths(self):
        """Test TOTP with different code lengths"""
        key = b'secret-key'
        
        for length in [6, 7, 8]:
            totp = TOTP(key, length=length)
            code = totp.generate()
            
            self.assertEqual(len(code), length)
            self.assertTrue(code.isdigit())


class TestHOTP(unittest.TestCase):
    """Tests for HOTP"""
    
    def test_generate(self):
        """Test HOTP generation"""
        key = b'secret-key-12345'
        hotp = HOTP(key)
        
        code = hotp.generate(0)
        
        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
    
    def test_verify(self):
        """Test HOTP verification"""
        key = b'secret-key-12345'
        hotp = HOTP(key)
        
        code = hotp.generate(42)
        self.assertTrue(hotp.verify(code, 42))
    
    def test_verify_wrong_counter(self):
        """Test verification with wrong counter"""
        key = b'secret-key-12345'
        hotp = HOTP(key)
        
        code = hotp.generate(10)
        self.assertFalse(hotp.verify(code, 11))
    
    def test_sequential_codes(self):
        """Test that sequential counters produce different codes"""
        key = b'secret-key'
        hotp = HOTP(key)
        
        codes = [hotp.generate(i) for i in range(10)]
        
        # All codes should be different (very high probability)
        self.assertEqual(len(codes), len(set(codes)))


if __name__ == '__main__':
    unittest.main()
