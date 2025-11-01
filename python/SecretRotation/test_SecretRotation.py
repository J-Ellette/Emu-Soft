"""
Tests for Secret Rotation Automation
"""

import unittest
import json
import os
import tempfile
import shutil
from SecretRotation import (
    SecretRotation, SecretType, RotationStrategy,
    SecretMetadata, RotationHistory
)


class TestSecretRotation(unittest.TestCase):
    """Test SecretRotation manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SecretRotation(storage_path=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_api_key(self):
        """Test API key generation"""
        api_key = self.manager.generate_api_key(length=32)
        self.assertEqual(len(api_key), 32)
        self.assertTrue(api_key.isalnum())
    
    def test_generate_password(self):
        """Test password generation"""
        password = self.manager.generate_password(length=16, use_special=True)
        self.assertGreaterEqual(len(password), 16)
        self.assertTrue(any(c.isupper() for c in password))
        self.assertTrue(any(c.islower() for c in password))
        self.assertTrue(any(c.isdigit() for c in password))
    
    def test_generate_token(self):
        """Test token generation"""
        token = self.manager.generate_token(length=32)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
    
    def test_generate_encryption_key(self):
        """Test encryption key generation"""
        key = self.manager.generate_encryption_key(key_size=32)
        self.assertEqual(len(key), 64)  # 32 bytes = 64 hex chars
        self.assertTrue(all(c in '0123456789abcdef' for c in key))
    
    def test_generate_signing_key(self):
        """Test signing key generation"""
        key = self.manager.generate_signing_key(length=64)
        self.assertIsInstance(key, str)
        self.assertGreater(len(key), 0)
    
    def test_add_secret_with_value(self):
        """Test adding a secret with a specific value"""
        value = self.manager.add_secret('my_api_key', 'test-key-123', SecretType.API_KEY)
        
        self.assertEqual(value, 'test-key-123')
        self.assertEqual(self.manager.get_secret('my_api_key'), 'test-key-123')
        self.assertIn('my_api_key', self.manager.metadata)
    
    def test_add_secret_auto_generate(self):
        """Test adding a secret with auto-generation"""
        value = self.manager.add_secret('my_password', secret_type=SecretType.PASSWORD, auto_generate=True)
        
        self.assertIsNotNone(value)
        self.assertEqual(self.manager.get_secret('my_password'), value)
    
    def test_add_secret_no_value_no_autogen(self):
        """Test that adding secret without value and auto_generate=False raises error"""
        with self.assertRaises(ValueError):
            self.manager.add_secret('test', value=None, auto_generate=False)
    
    def test_add_secret_with_rotation_interval(self):
        """Test adding a secret with rotation interval"""
        self.manager.add_secret(
            'my_key',
            'value',
            rotation_interval_days=30
        )
        
        meta = self.manager.get_metadata('my_key')
        self.assertEqual(meta.rotation_interval_days, 30)
        self.assertIsNotNone(meta.next_rotation)
    
    def test_add_secret_with_tags(self):
        """Test adding a secret with tags"""
        self.manager.add_secret(
            'my_key',
            'value',
            tags=['production', 'database']
        )
        
        meta = self.manager.get_metadata('my_key')
        self.assertEqual(meta.tags, ['production', 'database'])
    
    def test_rotate_secret_random(self):
        """Test rotating a secret with random strategy"""
        self.manager.add_secret('api_key', 'old-value', SecretType.API_KEY)
        old_value = self.manager.get_secret('api_key')
        
        new_value = self.manager.rotate_secret('api_key', strategy=RotationStrategy.RANDOM)
        
        self.assertNotEqual(new_value, old_value)
        self.assertEqual(self.manager.get_secret('api_key'), new_value)
        
        meta = self.manager.get_metadata('api_key')
        self.assertEqual(meta.rotation_count, 1)
    
    def test_rotate_secret_with_new_value(self):
        """Test rotating a secret with provided value"""
        self.manager.add_secret('api_key', 'old-value')
        
        new_value = self.manager.rotate_secret('api_key', new_value='new-value')
        
        self.assertEqual(new_value, 'new-value')
        self.assertEqual(self.manager.get_secret('api_key'), 'new-value')
    
    def test_rotate_secret_derived(self):
        """Test rotating a secret with derived strategy"""
        self.manager.add_secret('api_key', 'old-value')
        old_value = self.manager.get_secret('api_key')
        
        new_value = self.manager.rotate_secret('api_key', strategy=RotationStrategy.DERIVED)
        
        self.assertNotEqual(new_value, old_value)
        self.assertEqual(self.manager.get_secret('api_key'), new_value)
    
    def test_rotate_nonexistent_secret(self):
        """Test rotating a nonexistent secret raises error"""
        with self.assertRaises(ValueError):
            self.manager.rotate_secret('nonexistent')
    
    def test_rotation_callback(self):
        """Test rotation callback execution"""
        callback_data = {}
        
        def callback(name, old_val, new_val):
            callback_data['name'] = name
            callback_data['old'] = old_val
            callback_data['new'] = new_val
        
        self.manager.add_secret('api_key', 'old-value')
        self.manager.register_rotation_callback('api_key', callback)
        
        self.manager.rotate_secret('api_key', new_value='new-value')
        
        self.assertEqual(callback_data['name'], 'api_key')
        self.assertEqual(callback_data['old'], 'old-value')
        self.assertEqual(callback_data['new'], 'new-value')
    
    def test_get_secret(self):
        """Test getting a secret"""
        self.manager.add_secret('test', 'value')
        
        self.assertEqual(self.manager.get_secret('test'), 'value')
        self.assertIsNone(self.manager.get_secret('nonexistent'))
    
    def test_get_metadata(self):
        """Test getting secret metadata"""
        self.manager.add_secret('test', 'value', SecretType.API_KEY)
        
        meta = self.manager.get_metadata('test')
        self.assertIsNotNone(meta)
        self.assertEqual(meta.name, 'test')
        self.assertEqual(meta.secret_type, SecretType.API_KEY)
    
    def test_list_secrets(self):
        """Test listing all secrets"""
        self.manager.add_secret('key1', 'val1', SecretType.API_KEY)
        self.manager.add_secret('key2', 'val2', SecretType.PASSWORD)
        self.manager.add_secret('key3', 'val3', SecretType.API_KEY)
        
        all_secrets = self.manager.list_secrets()
        self.assertEqual(len(all_secrets), 3)
        
        api_keys = self.manager.list_secrets(secret_type=SecretType.API_KEY)
        self.assertEqual(len(api_keys), 2)
        self.assertIn('key1', api_keys)
        self.assertIn('key3', api_keys)
    
    def test_check_rotation_needed(self):
        """Test checking which secrets need rotation"""
        # Add secret with rotation interval that's already past
        self.manager.add_secret('old_key', 'value', rotation_interval_days=-1)
        
        # Add secret with future rotation
        self.manager.add_secret('new_key', 'value', rotation_interval_days=30)
        
        needs_rotation = self.manager.check_rotation_needed()
        
        self.assertIn('old_key', needs_rotation)
        self.assertNotIn('new_key', needs_rotation)
    
    def test_rotate_all_due(self):
        """Test rotating all due secrets"""
        self.manager.add_secret('key1', 'val1', rotation_interval_days=-1)
        self.manager.add_secret('key2', 'val2', rotation_interval_days=-1)
        
        results = self.manager.rotate_all_due()
        
        self.assertTrue(results['key1'])
        self.assertTrue(results['key2'])
    
    def test_delete_secret(self):
        """Test deleting a secret"""
        self.manager.add_secret('test', 'value')
        
        self.assertTrue(self.manager.delete_secret('test'))
        self.assertIsNone(self.manager.get_secret('test'))
        self.assertFalse(self.manager.delete_secret('nonexistent'))
    
    def test_export_secrets(self):
        """Test exporting secrets to file"""
        self.manager.add_secret('key1', 'val1', SecretType.API_KEY, tags=['prod'])
        self.manager.add_secret('key2', 'val2', SecretType.PASSWORD)
        
        export_path = os.path.join(self.temp_dir, 'export.json')
        self.manager.export_secrets(export_path, include_metadata=True)
        
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        self.assertIn('secrets', data)
        self.assertIn('metadata', data)
        self.assertEqual(data['secrets']['key1'], 'val1')
    
    def test_import_secrets(self):
        """Test importing secrets from file"""
        data = {
            'secrets': {
                'key1': 'val1',
                'key2': 'val2'
            },
            'metadata': {
                'key1': {
                    'name': 'key1',
                    'secret_type': 'api_key',
                    'created_at': '2024-01-01T00:00:00',
                    'rotation_count': 0,
                    'tags': ['test']
                }
            }
        }
        
        import_path = os.path.join(self.temp_dir, 'import.json')
        with open(import_path, 'w') as f:
            json.dump(data, f)
        
        self.manager.import_secrets(import_path)
        
        self.assertEqual(self.manager.get_secret('key1'), 'val1')
        self.assertEqual(self.manager.get_secret('key2'), 'val2')
        self.assertEqual(self.manager.get_metadata('key1').secret_type, SecretType.API_KEY)
    
    def test_get_rotation_history(self):
        """Test getting rotation history"""
        self.manager.add_secret('key1', 'val1')
        self.manager.rotate_secret('key1')
        self.manager.rotate_secret('key1')
        
        history = self.manager.get_rotation_history('key1')
        self.assertEqual(len(history), 2)
        
        all_history = self.manager.get_rotation_history()
        self.assertEqual(len(all_history), 2)
    
    def test_generate_env_file(self):
        """Test generating .env file"""
        self.manager.add_secret('DATABASE_URL', 'postgres://localhost/db')
        self.manager.add_secret('API_KEY', 'secret-key')
        
        env_path = os.path.join(self.temp_dir, '.env')
        self.manager.generate_env_file(env_path)
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        self.assertIn('DATABASE_URL=postgres://localhost/db', content)
        self.assertIn('API_KEY=secret-key', content)
    
    def test_generate_env_file_selective(self):
        """Test generating .env file with selected secrets"""
        self.manager.add_secret('KEY1', 'val1')
        self.manager.add_secret('KEY2', 'val2')
        self.manager.add_secret('KEY3', 'val3')
        
        env_path = os.path.join(self.temp_dir, '.env')
        self.manager.generate_env_file(env_path, secrets=['KEY1', 'KEY3'])
        
        with open(env_path, 'r') as f:
            content = f.read()
        
        self.assertIn('KEY1=val1', content)
        self.assertNotIn('KEY2=val2', content)
        self.assertIn('KEY3=val3', content)
    
    def test_get_statistics(self):
        """Test getting statistics"""
        self.manager.add_secret('key1', 'val1', SecretType.API_KEY)
        self.manager.add_secret('key2', 'val2', SecretType.PASSWORD)
        self.manager.add_secret('key3', 'val3', SecretType.API_KEY)
        self.manager.rotate_secret('key1')
        
        stats = self.manager.get_statistics()
        
        self.assertEqual(stats['total_secrets'], 3)
        self.assertEqual(stats['secrets_by_type']['api_key'], 2)
        self.assertEqual(stats['secrets_by_type']['password'], 1)
        self.assertEqual(stats['total_rotations'], 1)
    
    def test_validate_secret_strength_password(self):
        """Test validating password strength"""
        # Strong password
        result = self.manager.validate_secret_strength('Test1234!@#$', SecretType.PASSWORD)
        self.assertTrue(result['valid'])
        self.assertGreater(result['score'], 80)
        
        # Weak password
        result = self.manager.validate_secret_strength('short', SecretType.PASSWORD)
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['issues']), 0)
    
    def test_validate_secret_strength_api_key(self):
        """Test validating API key strength"""
        # Short API key
        result = self.manager.validate_secret_strength('short', SecretType.API_KEY)
        self.assertFalse(result['valid'])
        self.assertIn('Length too short', result['issues'][0])
        
        # Long enough API key
        result = self.manager.validate_secret_strength('a' * 20, SecretType.API_KEY)
        self.assertTrue(result['valid'])
    
    def test_rotation_history_recorded(self):
        """Test that rotation history is properly recorded"""
        self.manager.add_secret('key1', 'val1')
        self.manager.rotate_secret('key1')
        
        history = self.manager.get_rotation_history('key1')
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].secret_name, 'key1')
        self.assertEqual(history[0].rotation_count, 1)
        self.assertTrue(history[0].success)
    
    def test_metadata_updated_on_rotation(self):
        """Test that metadata is updated after rotation"""
        self.manager.add_secret('key1', 'val1', rotation_interval_days=30)
        
        meta_before = self.manager.get_metadata('key1')
        initial_rotation_count = meta_before.rotation_count
        
        self.manager.rotate_secret('key1')
        
        meta_after = self.manager.get_metadata('key1')
        self.assertEqual(meta_after.rotation_count, initial_rotation_count + 1)
        self.assertIsNotNone(meta_after.last_rotated)


if __name__ == '__main__':
    unittest.main()
