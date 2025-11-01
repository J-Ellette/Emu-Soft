"""
Developed by PowerShield, as an alternative to Vault
"""

#!/usr/bin/env python3
"""
Test suite for Vault Emulator

Tests core functionality including:
- Initialization and unsealing
- Secret storage (KV engine)
- Encryption as a service (Transit engine)
- Token management
- Policy-based access control
- Audit logging
"""

import unittest
import time
import base64
from SecretMan import SecretMan, Token, Policy


class TestVaultInit(unittest.TestCase):
    """Test Vault initialization"""
    
    def test_initialize(self):
        """Test initializing Vault"""
        vault = SecretMan()
        result = vault.initialize(secret_shares=5, secret_threshold=3)
        
        self.assertTrue(vault.initialized)
        self.assertEqual(len(result['keys']), 5)
        self.assertIn('root_token', result)
    
    def test_cannot_initialize_twice(self):
        """Test that Vault cannot be initialized twice"""
        vault = SecretMan()
        vault.initialize()
        
        with self.assertRaises(Exception) as ctx:
            vault.initialize()
        
        self.assertIn("already initialized", str(ctx.exception))


class TestVaultSeal(unittest.TestCase):
    """Test Vault sealing/unsealing"""
    
    def test_unseal(self):
        """Test unsealing Vault"""
        vault = SecretMan()
        result = vault.initialize(secret_shares=5, secret_threshold=3)
        keys = result['keys']
        
        self.assertTrue(vault.sealed)
        
        # Unseal with threshold number of keys
        vault.unseal(keys[0])
        vault.unseal(keys[1])
        status = vault.unseal(keys[2])
        
        self.assertFalse(status['sealed'])
        self.assertFalse(vault.sealed)
    
    def test_seal(self):
        """Test sealing Vault"""
        vault = SecretMan()
        result = vault.initialize()
        
        # Unseal first
        for key in result['keys'][:3]:
            vault.unseal(key)
        
        self.assertFalse(vault.sealed)
        
        # Seal
        vault.seal()
        self.assertTrue(vault.sealed)
    
    def test_status(self):
        """Test getting Vault status"""
        vault = SecretMan()
        status = vault.status()
        
        self.assertFalse(status['initialized'])
        self.assertTrue(status['sealed'])


class TestSecretsKV(unittest.TestCase):
    """Test KV secrets engine"""
    
    def setUp(self):
        """Set up Vault for testing"""
        self.vault = SecretMan()
        result = self.vault.initialize()
        self.root_token = result['root_token']
        
        # Unseal
        for key in result['keys'][:3]:
            self.vault.unseal(key)
    
    def test_write_secret(self):
        """Test writing a secret"""
        result = self.vault.write_secret(
            self.root_token,
            "secret/myapp",
            {"username": "admin", "password": "secret"}
        )
        
        self.assertIn('data', result)
        self.assertEqual(result['data']['version'], 1)
    
    def test_read_secret(self):
        """Test reading a secret"""
        # Write first
        self.vault.write_secret(
            self.root_token,
            "secret/myapp",
            {"username": "admin", "password": "secret"}
        )
        
        # Read
        result = self.vault.read_secret(self.root_token, "secret/myapp")
        
        self.assertEqual(result['data']['data']['username'], "admin")
        self.assertEqual(result['data']['data']['password'], "secret")
    
    def test_secret_versioning(self):
        """Test secret versioning"""
        # Write version 1
        self.vault.write_secret(self.root_token, "secret/app", {"key": "v1"})
        
        # Write version 2
        self.vault.write_secret(self.root_token, "secret/app", {"key": "v2"})
        
        # Read latest (v2)
        result = self.vault.read_secret(self.root_token, "secret/app")
        self.assertEqual(result['data']['data']['key'], "v2")
        self.assertEqual(result['data']['metadata']['version'], 2)
        
        # Read v1
        result = self.vault.read_secret(self.root_token, "secret/app", version=1)
        self.assertEqual(result['data']['data']['key'], "v1")
    
    def test_delete_secret(self):
        """Test deleting a secret"""
        self.vault.write_secret(self.root_token, "secret/temp", {"data": "test"})
        
        # Delete
        self.vault.delete_secret(self.root_token, "secret/temp")
        
        # Should still be able to read (soft delete)
        result = self.vault.read_secret(self.root_token, "secret/temp")
        self.assertIsNotNone(result['data']['metadata'].get('created_time'))
    
    def test_sealed_vault_blocks_operations(self):
        """Test that sealed Vault blocks operations"""
        self.vault.seal()
        
        with self.assertRaises(Exception) as ctx:
            self.vault.write_secret(self.root_token, "secret/test", {"key": "value"})
        
        self.assertIn("sealed", str(ctx.exception))


class TestTransitEngine(unittest.TestCase):
    """Test Transit encryption engine"""
    
    def setUp(self):
        """Set up Vault for testing"""
        self.vault = SecretMan()
        result = self.vault.initialize()
        self.root_token = result['root_token']
        
        # Unseal
        for key in result['keys'][:3]:
            self.vault.unseal(key)
    
    def test_create_encryption_key(self):
        """Test creating encryption key"""
        result = self.vault.create_encryption_key(self.root_token, "mykey")
        
        self.assertIn("mykey", self.vault.encryption_keys)
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption"""
        self.vault.create_encryption_key(self.root_token, "testkey")
        
        # Encrypt
        plaintext = "Hello, World!"
        encrypted = self.vault.encrypt(self.root_token, "testkey", plaintext)
        ciphertext = encrypted['data']['ciphertext']
        
        self.assertIn("vault:v1:", ciphertext)
        
        # Decrypt
        decrypted = self.vault.decrypt(self.root_token, "testkey", ciphertext)
        decrypted_text = base64.b64decode(decrypted['data']['plaintext']).decode('utf-8')
        
        self.assertEqual(decrypted_text, plaintext)
    
    def test_encrypt_without_key(self):
        """Test encryption without key fails"""
        with self.assertRaises(Exception) as ctx:
            self.vault.encrypt(self.root_token, "nonexistent", "data")
        
        self.assertIn("not found", str(ctx.exception))


class TestTokenManagement(unittest.TestCase):
    """Test token management"""
    
    def setUp(self):
        """Set up Vault for testing"""
        self.vault = SecretMan()
        result = self.vault.initialize()
        self.root_token = result['root_token']
        
        # Unseal
        for key in result['keys'][:3]:
            self.vault.unseal(key)
    
    def test_create_token(self):
        """Test creating a new token"""
        result = self.vault.create_token(
            self.root_token,
            policies=["default"],
            ttl=3600
        )
        
        token_id = result['auth']['client_token']
        self.assertIn(token_id, self.vault.tokens)
    
    def test_token_expiry(self):
        """Test token expiration"""
        result = self.vault.create_token(
            self.root_token,
            policies=["default"],
            ttl=1  # 1 second
        )
        
        token_id = result['auth']['client_token']
        
        # Token should be valid
        token = self.vault._check_token(token_id)
        self.assertIsNotNone(token)
        
        # Wait for expiry
        time.sleep(1.1)
        
        # Token should be expired
        token = self.vault._check_token(token_id)
        self.assertIsNone(token)
    
    def test_renew_token(self):
        """Test renewing a token"""
        result = self.vault.create_token(
            self.root_token,
            policies=["default"],
            ttl=3600
        )
        
        token_id = result['auth']['client_token']
        
        # Renew
        renew_result = self.vault.renew_token(token_id, increment=7200)
        
        self.assertEqual(renew_result['auth']['lease_duration'], 7200)
    
    def test_revoke_token(self):
        """Test revoking a token"""
        result = self.vault.create_token(self.root_token, policies=["default"])
        token_id = result['auth']['client_token']
        
        # Revoke
        self.vault.revoke_token(self.root_token, token_id)
        
        # Token should not exist
        self.assertNotIn(token_id, self.vault.tokens)


class TestPolicyManagement(unittest.TestCase):
    """Test policy management"""
    
    def setUp(self):
        """Set up Vault for testing"""
        self.vault = SecretMan()
        result = self.vault.initialize()
        self.root_token = result['root_token']
        
        # Unseal
        for key in result['keys'][:3]:
            self.vault.unseal(key)
    
    def test_write_policy(self):
        """Test writing a policy"""
        rules = [
            {
                "path": "secret/myapp/*",
                "capabilities": ["read", "list"]
            }
        ]
        
        self.vault.write_policy(self.root_token, "myapp-read", rules)
        
        self.assertIn("myapp-read", self.vault.policies)
    
    def test_read_policy(self):
        """Test reading a policy"""
        rules = [{"path": "secret/*", "capabilities": ["read"]}]
        self.vault.write_policy(self.root_token, "test-policy", rules)
        
        result = self.vault.read_policy(self.root_token, "test-policy")
        
        self.assertEqual(result['data']['name'], "test-policy")
        self.assertEqual(len(result['data']['rules']), 1)
    
    def test_list_policies(self):
        """Test listing policies"""
        result = self.vault.list_policies(self.root_token)
        
        self.assertIn("root", result['data']['policies'])
    
    def test_policy_allows(self):
        """Test policy permission checking"""
        policy = Policy(name="test")
        policy.rules.append({
            "path": "secret/app",
            "capabilities": ["read", "list"]
        })
        
        self.assertTrue(policy.allows("secret/app", "read"))
        self.assertFalse(policy.allows("secret/app", "write"))
        self.assertFalse(policy.allows("secret/other", "read"))


class TestAccessControl(unittest.TestCase):
    """Test policy-based access control"""
    
    def setUp(self):
        """Set up Vault for testing"""
        self.vault = SecretMan()
        result = self.vault.initialize()
        self.root_token = result['root_token']
        
        # Unseal
        for key in result['keys'][:3]:
            self.vault.unseal(key)
    
    def test_permission_denied(self):
        """Test that restricted token cannot access secrets"""
        # Create policy with no permissions
        self.vault.write_policy(self.root_token, "noaccess", [])
        
        # Create token with restricted policy
        result = self.vault.create_token(self.root_token, policies=["noaccess"])
        restricted_token = result['auth']['client_token']
        
        # Try to write secret
        with self.assertRaises(Exception) as ctx:
            self.vault.write_secret(restricted_token, "secret/test", {"key": "value"})
        
        self.assertIn("Permission denied", str(ctx.exception))
    
    def test_policy_enforcement(self):
        """Test that policy grants correct permissions"""
        # Create policy that allows read on secret/app/*
        rules = [
            {
                "path": "secret/app",
                "capabilities": ["create", "read"]
            }
        ]
        self.vault.write_policy(self.root_token, "app-access", rules)
        
        # Create token with this policy
        result = self.vault.create_token(self.root_token, policies=["app-access"])
        app_token = result['auth']['client_token']
        
        # Should be able to write to secret/app
        self.vault.write_secret(app_token, "secret/app", {"key": "value"})
        
        # Should be able to read from secret/app
        result = self.vault.read_secret(app_token, "secret/app")
        self.assertEqual(result['data']['data']['key'], "value")


class TestAuditLog(unittest.TestCase):
    """Test audit logging"""
    
    def setUp(self):
        """Set up Vault for testing"""
        self.vault = SecretMan()
        result = self.vault.initialize()
        self.root_token = result['root_token']
        
        # Unseal
        for key in result['keys'][:3]:
            self.vault.unseal(key)
    
    def test_audit_logging(self):
        """Test that operations are logged"""
        # Perform operations
        self.vault.write_secret(self.root_token, "secret/test", {"key": "value"})
        self.vault.read_secret(self.root_token, "secret/test")
        
        # Get audit log
        log = self.vault.get_audit_log(self.root_token, limit=10)
        
        self.assertGreater(len(log), 0)
        self.assertTrue(any(entry.operation == "write" for entry in log))
        self.assertTrue(any(entry.operation == "read" for entry in log))


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
