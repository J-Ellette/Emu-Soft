"""
Tests for Multi-Environment Config Validator
"""

import unittest
import json
import os
import tempfile
from MultiEnv import MultiEnv, DriftSeverity, ValidationRule, DriftReport


class TestMultiEnv(unittest.TestCase):
    """Test MultiEnv configuration validator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = MultiEnv()
    
    def test_add_environment(self):
        """Test adding an environment"""
        config = {'key1': 'value1', 'key2': 'value2'}
        self.validator.add_environment('dev', config)
        
        self.assertIn('dev', self.validator.environments)
        self.assertEqual(self.validator.environments['dev']['config'], config)
    
    def test_add_environment_empty_name(self):
        """Test that empty environment name raises error"""
        with self.assertRaises(ValueError):
            self.validator.add_environment('', {})
    
    def test_load_from_json_file(self):
        """Test loading configuration from JSON file"""
        config = {'database': 'localhost', 'port': 5432}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            filepath = f.name
        
        try:
            self.validator.load_from_file('staging', filepath, format='json')
            self.assertIn('staging', self.validator.environments)
            self.assertEqual(self.validator.environments['staging']['config'], config)
        finally:
            os.unlink(filepath)
    
    def test_load_from_env_file(self):
        """Test loading configuration from .env file"""
        env_content = """
DATABASE_URL=postgres://localhost/mydb
API_KEY=secret123
PORT=8080
# This is a comment
DEBUG=true
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            filepath = f.name
        
        try:
            self.validator.load_from_file('production', filepath, format='env')
            config = self.validator.environments['production']['config']
            self.assertEqual(config['DATABASE_URL'], 'postgres://localhost/mydb')
            self.assertEqual(config['API_KEY'], 'secret123')
            self.assertEqual(config['PORT'], '8080')
        finally:
            os.unlink(filepath)
    
    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises error"""
        with self.assertRaises(FileNotFoundError):
            self.validator.load_from_file('dev', '/nonexistent/file.json')
    
    def test_validation_required_key(self):
        """Test validation of required keys"""
        self.validator.add_environment('dev', {'key1': 'value1'})
        
        rule = ValidationRule(key='key2', required=True)
        self.validator.add_validation_rule(rule)
        
        errors = self.validator.validate_environment('dev')
        self.assertEqual(len(errors), 1)
        self.assertIn('Required key', errors[0])
    
    def test_validation_allowed_values(self):
        """Test validation of allowed values"""
        self.validator.add_environment('dev', {'environment': 'testing'})
        
        rule = ValidationRule(
            key='environment',
            allowed_values=['dev', 'staging', 'production']
        )
        self.validator.add_validation_rule(rule)
        
        errors = self.validator.validate_environment('dev')
        self.assertEqual(len(errors), 1)
        self.assertIn('invalid value', errors[0])
    
    def test_validation_value_type(self):
        """Test validation of value types"""
        self.validator.add_environment('dev', {'port': '8080'})
        
        rule = ValidationRule(key='port', value_type=int)
        self.validator.add_validation_rule(rule)
        
        errors = self.validator.validate_environment('dev')
        self.assertEqual(len(errors), 1)
        self.assertIn('wrong type', errors[0])
    
    def test_validation_pattern(self):
        """Test validation with regex pattern"""
        self.validator.add_environment('dev', {'version': '2.0.0'})
        
        rule = ValidationRule(key='version', pattern=r'^\d+\.\d+\.\d+$')
        self.validator.add_validation_rule(rule)
        
        errors = self.validator.validate_environment('dev')
        self.assertEqual(len(errors), 0)
    
    def test_validation_pattern_mismatch(self):
        """Test validation with pattern mismatch"""
        self.validator.add_environment('dev', {'email': 'invalid-email'})
        
        rule = ValidationRule(key='email', pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
        self.validator.add_validation_rule(rule)
        
        errors = self.validator.validate_environment('dev')
        self.assertEqual(len(errors), 1)
        self.assertIn("doesn't match pattern", errors[0])
    
    def test_validation_environment_specific(self):
        """Test environment-specific validation rules"""
        self.validator.add_environment('dev', {})
        self.validator.add_environment('production', {})
        
        rule = ValidationRule(key='ssl_enabled', required=True, environments=['production'])
        self.validator.add_validation_rule(rule)
        
        dev_errors = self.validator.validate_environment('dev')
        prod_errors = self.validator.validate_environment('production')
        
        self.assertEqual(len(dev_errors), 0)
        self.assertEqual(len(prod_errors), 1)
    
    def test_validate_all(self):
        """Test validating all environments"""
        self.validator.add_environment('dev', {'key1': 'value1'})
        self.validator.add_environment('staging', {})
        
        rule = ValidationRule(key='key1', required=True)
        self.validator.add_validation_rule(rule)
        
        results = self.validator.validate_all()
        self.assertIn('staging', results)
        self.assertNotIn('dev', results)
    
    def test_drift_detection_missing_keys(self):
        """Test drift detection for missing keys"""
        self.validator.add_environment('dev', {'key1': 'value1', 'key2': 'value2'})
        self.validator.add_environment('staging', {'key1': 'value1'})
        
        drifts = self.validator.detect_drift()
        
        # Should detect key2 missing in staging
        key2_drifts = [d for d in drifts if d.key == 'key2']
        self.assertEqual(len(key2_drifts), 1)
        self.assertEqual(key2_drifts[0].severity, DriftSeverity.WARNING)
    
    def test_drift_detection_different_values(self):
        """Test drift detection for different values"""
        self.validator.add_environment('dev', {'database': 'localhost'})
        self.validator.add_environment('production', {'database': 'prod-server'})
        
        drifts = self.validator.detect_drift()
        
        db_drifts = [d for d in drifts if d.key == 'database']
        self.assertEqual(len(db_drifts), 1)
        self.assertIn('differs', db_drifts[0].message)
    
    def test_drift_severity_critical(self):
        """Test critical severity for sensitive keys"""
        self.validator.add_environment('dev', {'api_key': 'dev-key'})
        self.validator.add_environment('prod', {'api_key': 'prod-key'})
        
        drifts = self.validator.detect_drift()
        
        api_key_drifts = [d for d in drifts if d.key == 'api_key']
        self.assertEqual(len(api_key_drifts), 1)
        self.assertEqual(api_key_drifts[0].severity, DriftSeverity.CRITICAL)
    
    def test_drift_summary(self):
        """Test drift summary generation"""
        self.validator.add_environment('dev', {'database': 'localhost', 'api_key': 'dev-key'})
        self.validator.add_environment('prod', {'database': 'prod-db', 'api_key': 'prod-key'})
        
        summary = self.validator.get_drift_summary()
        
        self.assertIn('total', summary)
        self.assertIn('critical', summary)
        self.assertIn('error', summary)
        self.assertEqual(summary['total'], 2)
    
    def test_compare_environments(self):
        """Test comparing two environments"""
        self.validator.add_environment('dev', {
            'key1': 'value1',
            'key2': 'value2',
            'common': 'same'
        })
        self.validator.add_environment('staging', {
            'key1': 'different',
            'key3': 'value3',
            'common': 'same'
        })
        
        comparison = self.validator.compare_environments('dev', 'staging')
        
        self.assertEqual(len(comparison['differences']), 1)
        self.assertIn('key2', comparison['only_in_dev'])
        self.assertIn('key3', comparison['only_in_staging'])
        self.assertIn('common', comparison['identical'])
    
    def test_compare_nonexistent_environment(self):
        """Test comparing with nonexistent environment raises error"""
        self.validator.add_environment('dev', {})
        
        with self.assertRaises(ValueError):
            self.validator.compare_environments('dev', 'nonexistent')
    
    def test_generate_text_report(self):
        """Test generating text report"""
        self.validator.add_environment('dev', {'key1': 'value1'})
        self.validator.add_environment('prod', {'key1': 'value2'})
        
        report = self.validator.generate_report(format='text')
        
        self.assertIn('Multi-Environment Configuration Drift Report', report)
        self.assertIn('dev', report)
        self.assertIn('prod', report)
    
    def test_generate_json_report(self):
        """Test generating JSON report"""
        self.validator.add_environment('dev', {'key1': 'value1'})
        self.validator.add_environment('prod', {'key1': 'value2'})
        
        report = self.validator.generate_report(format='json')
        data = json.loads(report)
        
        self.assertIn('summary', data)
        self.assertIn('drifts', data)
        self.assertIn('environments', data)
    
    def test_export_baseline(self):
        """Test exporting environment as baseline"""
        config = {'key1': 'value1', 'key2': 'value2'}
        self.validator.add_environment('production', config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            self.validator.export_baseline('production', filepath)
            
            with open(filepath, 'r') as f:
                baseline = json.load(f)
            
            self.assertEqual(baseline['environment'], 'production')
            self.assertEqual(baseline['config'], config)
            self.assertIn('exported_at', baseline)
        finally:
            os.unlink(filepath)
    
    def test_compute_config_hash(self):
        """Test computing configuration hash"""
        config = {'key1': 'value1', 'key2': 'value2'}
        self.validator.add_environment('dev', config)
        
        hash1 = self.validator.compute_config_hash('dev')
        self.assertEqual(len(hash1), 64)  # SHA-256 produces 64 hex chars
        
        # Same config should produce same hash
        self.validator.add_environment('staging', config)
        hash2 = self.validator.compute_config_hash('staging')
        self.assertEqual(hash1, hash2)
    
    def test_get_environment_keys(self):
        """Test getting all keys in an environment"""
        config = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        self.validator.add_environment('dev', config)
        
        keys = self.validator.get_environment_keys('dev')
        self.assertEqual(set(keys), {'key1', 'key2', 'key3'})
    
    def test_get_common_keys(self):
        """Test getting keys common to all environments"""
        self.validator.add_environment('dev', {'key1': 'val1', 'key2': 'val2', 'key3': 'val3'})
        self.validator.add_environment('staging', {'key1': 'val1', 'key2': 'val2', 'key4': 'val4'})
        self.validator.add_environment('prod', {'key1': 'val1', 'key2': 'val2', 'key5': 'val5'})
        
        common = self.validator.get_common_keys()
        self.assertEqual(set(common), {'key1', 'key2'})
    
    def test_get_unique_keys(self):
        """Test getting keys unique to one environment"""
        self.validator.add_environment('dev', {'key1': 'val1', 'key2': 'val2', 'dev_only': 'val'})
        self.validator.add_environment('staging', {'key1': 'val1', 'key2': 'val2'})
        
        unique = self.validator.get_unique_keys('dev')
        self.assertIn('dev_only', unique)
        self.assertNotIn('key1', unique)
    
    def test_no_drift_with_single_environment(self):
        """Test that no drift is detected with single environment"""
        self.validator.add_environment('dev', {'key1': 'value1'})
        
        drifts = self.validator.detect_drift()
        self.assertEqual(len(drifts), 0)
    
    def test_no_drift_with_identical_environments(self):
        """Test no drift when environments are identical"""
        config = {'key1': 'value1', 'key2': 'value2'}
        self.validator.add_environment('dev', config.copy())
        self.validator.add_environment('staging', config.copy())
        
        drifts = self.validator.detect_drift()
        self.assertEqual(len(drifts), 0)


if __name__ == '__main__':
    unittest.main()
