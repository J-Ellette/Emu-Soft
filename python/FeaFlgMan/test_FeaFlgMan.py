"""
Tests for Feature Flag Management System
"""

import unittest
import json
import os
import tempfile
import shutil
from FeaFlgMan import (
    FeaFlgMan, FlagStatus, RolloutStrategy,
    TargetingRule, FlagMetadata, FlagConfig
)


class TestFeaFlgMan(unittest.TestCase):
    """Test FeaFlgMan feature flag manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = FeaFlgMan(storage_path=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_flag(self):
        """Test creating a feature flag"""
        flag = self.manager.create_flag(
            'new_feature',
            description='A new feature',
            enabled=True,
            tags=['beta']
        )
        
        self.assertEqual(flag.name, 'new_feature')
        self.assertTrue(flag.enabled)
        self.assertIn('new_feature', self.manager.flags)
    
    def test_create_duplicate_flag(self):
        """Test that creating duplicate flag raises error"""
        self.manager.create_flag('test')
        
        with self.assertRaises(ValueError):
            self.manager.create_flag('test')
    
    def test_update_flag(self):
        """Test updating a flag"""
        self.manager.create_flag('test', enabled=False)
        self.manager.update_flag('test', enabled=True, rollout_percentage=50)
        
        flag = self.manager.get_flag('test')
        self.assertTrue(flag.enabled)
        self.assertEqual(flag.rollout_percentage, 50)
    
    def test_update_nonexistent_flag(self):
        """Test updating nonexistent flag raises error"""
        with self.assertRaises(ValueError):
            self.manager.update_flag('nonexistent', enabled=True)
    
    def test_add_targeting_rule(self):
        """Test adding targeting rule"""
        self.manager.create_flag('test')
        self.manager.add_targeting_rule(
            'test',
            rule_type='attribute',
            operator='equals',
            key='country',
            value='US'
        )
        
        flag = self.manager.get_flag('test')
        self.assertEqual(len(flag.targeting_rules), 1)
        self.assertEqual(flag.targeting_rules[0].key, 'country')
    
    def test_remove_targeting_rule(self):
        """Test removing targeting rule"""
        self.manager.create_flag('test')
        self.manager.add_targeting_rule('test', 'attribute', 'equals', 'country', 'US')
        self.manager.remove_targeting_rule('test', 0)
        
        flag = self.manager.get_flag('test')
        self.assertEqual(len(flag.targeting_rules), 0)
    
    def test_whitelist_management(self):
        """Test whitelist add/remove"""
        self.manager.create_flag('test')
        
        self.manager.add_to_whitelist('test', 'user123')
        flag = self.manager.get_flag('test')
        self.assertIn('user123', flag.whitelist_users)
        
        self.manager.remove_from_whitelist('test', 'user123')
        self.assertNotIn('user123', flag.whitelist_users)
    
    def test_is_enabled_all_users(self):
        """Test flag enabled for all users"""
        self.manager.create_flag(
            'test',
            enabled=True,
            rollout_strategy=RolloutStrategy.ALL_USERS
        )
        
        self.assertTrue(self.manager.is_enabled('test'))
        self.assertTrue(self.manager.is_enabled('test', user_id='user123'))
    
    def test_is_enabled_disabled_flag(self):
        """Test disabled flag returns False"""
        self.manager.create_flag('test', enabled=False)
        
        self.assertFalse(self.manager.is_enabled('test'))
    
    def test_is_enabled_whitelist(self):
        """Test whitelist rollout strategy"""
        self.manager.create_flag(
            'test',
            enabled=True,
            rollout_strategy=RolloutStrategy.WHITELIST
        )
        self.manager.add_to_whitelist('test', 'user123')
        
        self.assertTrue(self.manager.is_enabled('test', user_id='user123'))
        self.assertFalse(self.manager.is_enabled('test', user_id='user456'))
    
    def test_is_enabled_percentage(self):
        """Test percentage rollout strategy"""
        self.manager.create_flag(
            'test',
            enabled=True,
            rollout_strategy=RolloutStrategy.PERCENTAGE,
            rollout_percentage=50
        )
        
        # Test with multiple users to ensure consistency
        user_id = 'test_user'
        result1 = self.manager.is_enabled('test', user_id=user_id)
        result2 = self.manager.is_enabled('test', user_id=user_id)
        
        # Same user should always get same result
        self.assertEqual(result1, result2)
    
    def test_is_enabled_custom_evaluator(self):
        """Test custom evaluator"""
        self.manager.create_flag('test', enabled=True)
        
        def custom_eval(user_id, context):
            return context.get('premium', False)
        
        self.manager.register_custom_evaluator('test', custom_eval)
        
        self.assertTrue(self.manager.is_enabled('test', context={'premium': True}))
        self.assertFalse(self.manager.is_enabled('test', context={'premium': False}))
    
    def test_targeting_rules_equals(self):
        """Test targeting rule with equals operator"""
        self.manager.create_flag('test', enabled=True)
        self.manager.add_targeting_rule('test', 'attribute', 'equals', 'country', 'US')
        
        self.assertTrue(self.manager.is_enabled('test', context={'country': 'US'}))
        self.assertFalse(self.manager.is_enabled('test', context={'country': 'UK'}))
    
    def test_targeting_rules_contains(self):
        """Test targeting rule with contains operator"""
        self.manager.create_flag('test', enabled=True)
        self.manager.add_targeting_rule('test', 'attribute', 'contains', 'email', '@example.com')
        
        self.assertTrue(self.manager.is_enabled('test', context={'email': 'user@example.com'}))
        self.assertFalse(self.manager.is_enabled('test', context={'email': 'user@other.com'}))
    
    def test_targeting_rules_in(self):
        """Test targeting rule with 'in' operator"""
        self.manager.create_flag('test', enabled=True)
        self.manager.add_targeting_rule('test', 'attribute', 'in', 'role', ['admin', 'moderator'])
        
        self.assertTrue(self.manager.is_enabled('test', context={'role': 'admin'}))
        self.assertFalse(self.manager.is_enabled('test', context={'role': 'user'}))
    
    def test_list_flags(self):
        """Test listing flags"""
        self.manager.create_flag('flag1', tags=['beta'])
        self.manager.create_flag('flag2', tags=['prod'])
        self.manager.create_flag('flag3', tags=['beta'])
        
        all_flags = self.manager.list_flags()
        self.assertEqual(len(all_flags), 3)
        
        beta_flags = self.manager.list_flags(tag='beta')
        self.assertEqual(len(beta_flags), 2)
    
    def test_delete_flag(self):
        """Test deleting a flag"""
        self.manager.create_flag('test')
        
        self.assertTrue(self.manager.delete_flag('test'))
        self.assertIsNone(self.manager.get_flag('test'))
        self.assertFalse(self.manager.delete_flag('nonexistent'))
    
    def test_environment_management(self):
        """Test environment management"""
        self.manager.create_flag('test', enabled=True)
        
        self.manager.set_environment('production')
        self.assertEqual(self.manager.current_environment, 'production')
        
        self.manager.disable_for_environment('test', 'production')
        self.assertFalse(self.manager.is_enabled('test'))
        
        self.manager.set_environment('development')
        self.assertTrue(self.manager.is_enabled('test'))
    
    def test_get_flag_status(self):
        """Test getting flag status"""
        self.manager.create_flag('test', description='Test flag', enabled=True)
        
        status = self.manager.get_flag_status('test')
        
        self.assertTrue(status['exists'])
        self.assertEqual(status['name'], 'test')
        self.assertTrue(status['enabled'])
        self.assertEqual(status['description'], 'Test flag')
    
    def test_get_flag_status_with_user(self):
        """Test getting flag status for specific user"""
        self.manager.create_flag(
            'test',
            enabled=True,
            rollout_strategy=RolloutStrategy.WHITELIST
        )
        self.manager.add_to_whitelist('test', 'user123')
        
        status = self.manager.get_flag_status('test', user_id='user123')
        self.assertTrue(status['enabled_for_user'])
        
        status = self.manager.get_flag_status('test', user_id='user456')
        self.assertFalse(status['enabled_for_user'])
    
    def test_export_import_flags(self):
        """Test exporting and importing flags"""
        self.manager.create_flag('flag1', description='First flag', enabled=True)
        self.manager.create_flag('flag2', description='Second flag', enabled=False)
        self.manager.add_to_whitelist('flag1', 'user123')
        
        export_path = os.path.join(self.temp_dir, 'flags.json')
        self.manager.export_flags(export_path)
        
        # Create new manager and import
        manager2 = FeaFlgMan(storage_path=self.temp_dir)
        manager2.import_flags(export_path)
        
        self.assertIsNotNone(manager2.get_flag('flag1'))
        self.assertIsNotNone(manager2.get_flag('flag2'))
        self.assertIn('user123', manager2.get_flag('flag1').whitelist_users)
    
    def test_get_statistics(self):
        """Test getting statistics"""
        self.manager.create_flag('flag1', enabled=True)
        self.manager.create_flag('flag2', enabled=False)
        self.manager.create_flag('flag3', enabled=True, rollout_strategy=RolloutStrategy.PERCENTAGE)
        
        stats = self.manager.get_statistics()
        
        self.assertEqual(stats['total_flags'], 3)
        self.assertEqual(stats['enabled_flags'], 2)
        self.assertEqual(stats['disabled_flags'], 1)
    
    def test_nonexistent_flag_returns_false(self):
        """Test that checking nonexistent flag returns False"""
        self.assertFalse(self.manager.is_enabled('nonexistent'))
    
    def test_targeting_rule_greater_than(self):
        """Test targeting rule with greater_than operator"""
        self.manager.create_flag('test', enabled=True)
        self.manager.add_targeting_rule('test', 'attribute', 'greater_than', 'age', 18)
        
        self.assertTrue(self.manager.is_enabled('test', context={'age': 25}))
        self.assertFalse(self.manager.is_enabled('test', context={'age': 15}))
    
    def test_percentage_consistency(self):
        """Test that percentage rollout is consistent for same user"""
        self.manager.create_flag(
            'test',
            enabled=True,
            rollout_strategy=RolloutStrategy.PERCENTAGE,
            rollout_percentage=50
        )
        
        # Call multiple times with same user
        user_id = 'consistent_user'
        results = [self.manager.is_enabled('test', user_id=user_id) for _ in range(10)]
        
        # All results should be the same
        self.assertEqual(len(set(results)), 1)


if __name__ == '__main__':
    unittest.main()
