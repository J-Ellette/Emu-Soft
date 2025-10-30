"""
Tests for bcrypt emulator
"""

import unittest
from bcrypt_emulator import (
    gensalt, hashpw, checkpw, kdf,
    hash_password, verify_password,
    BcryptError, InvalidSaltError,
    BCRYPT_PREFIX, DEFAULT_ROUNDS
)


class TestSaltGeneration(unittest.TestCase):
    """Test salt generation"""
    
    def test_gensalt_default(self):
        """Test generating salt with default rounds"""
        salt = gensalt()
        
        self.assertIsInstance(salt, bytes)
        self.assertTrue(salt.startswith(BCRYPT_PREFIX))
        
        # Format: $2b$12$...
        parts = salt.split(b'$')
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[2], b'12')  # Default rounds
    
    def test_gensalt_custom_rounds(self):
        """Test generating salt with custom rounds"""
        for rounds in [4, 8, 10, 14]:
            salt = gensalt(rounds)
            
            parts = salt.split(b'$')
            rounds_str = f"{rounds:02d}".encode('ascii')
            self.assertEqual(parts[2], rounds_str)
    
    def test_gensalt_invalid_rounds(self):
        """Test invalid rounds values"""
        with self.assertRaises(ValueError):
            gensalt(rounds=3)  # Too low
        
        with self.assertRaises(ValueError):
            gensalt(rounds=32)  # Too high
    
    def test_gensalt_uniqueness(self):
        """Test that generated salts are unique"""
        salt1 = gensalt()
        salt2 = gensalt()
        
        self.assertNotEqual(salt1, salt2)


class TestPasswordHashing(unittest.TestCase):
    """Test password hashing"""
    
    def test_hashpw_basic(self):
        """Test basic password hashing"""
        password = "my_secure_password"
        salt = gensalt()
        
        hashed = hashpw(password, salt)
        
        self.assertIsInstance(hashed, bytes)
        self.assertTrue(hashed.startswith(BCRYPT_PREFIX))
    
    def test_hashpw_with_bytes(self):
        """Test hashing with bytes password"""
        password = b"my_secure_password"
        salt = gensalt()
        
        hashed = hashpw(password, salt)
        
        self.assertIsInstance(hashed, bytes)
    
    def test_hashpw_deterministic(self):
        """Test that same password and salt produce same hash"""
        password = "my_password"
        salt = gensalt()
        
        hash1 = hashpw(password, salt)
        hash2 = hashpw(password, salt)
        
        self.assertEqual(hash1, hash2)
    
    def test_hashpw_different_salts(self):
        """Test that different salts produce different hashes"""
        password = "my_password"
        salt1 = gensalt()
        salt2 = gensalt()
        
        hash1 = hashpw(password, salt1)
        hash2 = hashpw(password, salt2)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_hashpw_invalid_salt(self):
        """Test hashing with invalid salt"""
        password = "my_password"
        
        with self.assertRaises(InvalidSaltError):
            hashpw(password, b"invalid_salt")
    
    def test_hashpw_different_passwords(self):
        """Test that different passwords produce different hashes"""
        salt = gensalt()
        
        hash1 = hashpw("password1", salt)
        hash2 = hashpw("password2", salt)
        
        self.assertNotEqual(hash1, hash2)


class TestPasswordVerification(unittest.TestCase):
    """Test password verification"""
    
    def test_checkpw_correct_password(self):
        """Test verifying correct password"""
        password = "my_secure_password"
        salt = gensalt()
        hashed = hashpw(password, salt)
        
        self.assertTrue(checkpw(password, hashed))
    
    def test_checkpw_incorrect_password(self):
        """Test verifying incorrect password"""
        password = "my_secure_password"
        wrong_password = "wrong_password"
        salt = gensalt()
        hashed = hashpw(password, salt)
        
        self.assertFalse(checkpw(wrong_password, hashed))
    
    def test_checkpw_with_bytes(self):
        """Test verifying with bytes"""
        password = b"my_secure_password"
        salt = gensalt()
        hashed = hashpw(password, salt)
        
        self.assertTrue(checkpw(password, hashed))
    
    def test_checkpw_empty_password(self):
        """Test verifying empty password"""
        password = ""
        salt = gensalt()
        hashed = hashpw(password, salt)
        
        self.assertTrue(checkpw(password, hashed))
        self.assertFalse(checkpw("nonempty", hashed))
    
    def test_checkpw_invalid_hash(self):
        """Test verifying with invalid hash"""
        password = "my_password"
        
        self.assertFalse(checkpw(password, b"invalid_hash"))
    
    def test_checkpw_case_sensitive(self):
        """Test that password verification is case-sensitive"""
        password = "MyPassword"
        salt = gensalt()
        hashed = hashpw(password, salt)
        
        self.assertTrue(checkpw("MyPassword", hashed))
        self.assertFalse(checkpw("mypassword", hashed))
        self.assertFalse(checkpw("MYPASSWORD", hashed))


class TestRounds(unittest.TestCase):
    """Test different cost factors (rounds)"""
    
    def test_different_rounds(self):
        """Test hashing with different rounds"""
        password = "test_password"
        
        for rounds in [4, 6, 8, 10]:
            salt = gensalt(rounds)
            hashed = hashpw(password, salt)
            
            self.assertTrue(checkpw(password, hashed))
            
            # Verify rounds in hash
            parts = hashed.split(b'$')
            rounds_str = f"{rounds:02d}".encode('ascii')
            self.assertEqual(parts[2], rounds_str)
    
    def test_rounds_affect_hash(self):
        """Test that different rounds produce different hashes"""
        password = "test_password"
        
        # Generate salts with same random part but different rounds
        # (In practice, different rounds will have different salts)
        hash1 = hashpw(password, gensalt(4))
        hash2 = hashpw(password, gensalt(6))
        
        self.assertNotEqual(hash1, hash2)


class TestKeyDerivation(unittest.TestCase):
    """Test key derivation function"""
    
    def test_kdf_basic(self):
        """Test basic key derivation"""
        password = "my_password"
        salt = b"random_salt_16_b"
        
        key = kdf(password, salt, desired_key_bytes=32)
        
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 32)
    
    def test_kdf_deterministic(self):
        """Test that KDF is deterministic"""
        password = "my_password"
        salt = b"random_salt_16_b"
        
        key1 = kdf(password, salt, desired_key_bytes=32)
        key2 = kdf(password, salt, desired_key_bytes=32)
        
        self.assertEqual(key1, key2)
    
    def test_kdf_different_lengths(self):
        """Test deriving keys of different lengths"""
        password = "my_password"
        salt = b"random_salt_16_b"
        
        key16 = kdf(password, salt, desired_key_bytes=16)
        key32 = kdf(password, salt, desired_key_bytes=32)
        key64 = kdf(password, salt, desired_key_bytes=64)
        
        self.assertEqual(len(key16), 16)
        self.assertEqual(len(key32), 32)
        self.assertEqual(len(key64), 64)
    
    def test_kdf_different_passwords(self):
        """Test that different passwords produce different keys"""
        salt = b"random_salt_16_b"
        
        key1 = kdf("password1", salt, desired_key_bytes=32)
        key2 = kdf("password2", salt, desired_key_bytes=32)
        
        self.assertNotEqual(key1, key2)
    
    def test_kdf_different_salts(self):
        """Test that different salts produce different keys"""
        password = "my_password"
        
        key1 = kdf(password, b"salt1_16_bytes_x", desired_key_bytes=32)
        key2 = kdf(password, b"salt2_16_bytes_x", desired_key_bytes=32)
        
        self.assertNotEqual(key1, key2)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def test_hash_password(self):
        """Test hash_password convenience function"""
        password = "my_password"
        
        hashed = hash_password(password)
        
        self.assertIsInstance(hashed, str)
        self.assertTrue(hashed.startswith('$2b$'))
    
    def test_verify_password(self):
        """Test verify_password convenience function"""
        password = "my_password"
        
        hashed = hash_password(password)
        
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))
    
    def test_hash_verify_workflow(self):
        """Test complete hash and verify workflow"""
        password = "secure_password_123"
        
        # Hash
        hashed = hash_password(password, rounds=8)
        
        # Verify correct password
        self.assertTrue(verify_password(password, hashed))
        
        # Verify incorrect password
        self.assertFalse(verify_password("wrong_password", hashed))


class TestSpecialCases(unittest.TestCase):
    """Test special cases and edge cases"""
    
    def test_long_password(self):
        """Test hashing long password"""
        password = "a" * 1000
        salt = gensalt()
        
        hashed = hashpw(password, salt)
        self.assertTrue(checkpw(password, hashed))
    
    def test_unicode_password(self):
        """Test hashing password with unicode characters"""
        password = "пароль密码🔐"
        salt = gensalt()
        
        hashed = hashpw(password, salt)
        self.assertTrue(checkpw(password, hashed))
    
    def test_special_characters(self):
        """Test password with special characters"""
        password = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        salt = gensalt()
        
        hashed = hashpw(password, salt)
        self.assertTrue(checkpw(password, hashed))
    
    def test_whitespace_password(self):
        """Test password with whitespace"""
        password = "pass word with spaces\t\n"
        salt = gensalt()
        
        hashed = hashpw(password, salt)
        self.assertTrue(checkpw(password, hashed))


class TestSecurity(unittest.TestCase):
    """Test security properties"""
    
    def test_timing_attack_resistance(self):
        """Test that verification doesn't leak timing information"""
        # This is a basic test - real timing attack testing requires more sophisticated methods
        password = "correct_password"
        salt = gensalt()
        hashed = hashpw(password, salt)
        
        # All these should return False without leaking information
        wrong_passwords = [
            "wrong",
            "wrong_password",
            "correct_passwor",  # Off by one
            "Correct_password",  # Case difference
            "",
        ]
        
        for wrong in wrong_passwords:
            self.assertFalse(checkpw(wrong, hashed))
    
    def test_salt_randomness(self):
        """Test that salts are sufficiently random"""
        salts = [gensalt() for _ in range(10)]
        
        # All salts should be unique
        self.assertEqual(len(salts), len(set(salts)))
    
    def test_hash_format(self):
        """Test that hash format is correct"""
        password = "test"
        salt = gensalt()
        hashed = hashpw(password, salt)
        
        # Format: $2b$12$salt22chars...hash31chars...
        parts = hashed.split(b'$')
        
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[1], b'2b')
        self.assertEqual(len(parts[2]), 2)  # Rounds (2 digits)
        self.assertGreaterEqual(len(parts[3]), 22 + 31)  # Salt + hash


if __name__ == '__main__':
    unittest.main()
