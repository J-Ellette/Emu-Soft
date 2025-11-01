"""Tests for SchemReg"""
import unittest
from SchemReg import SchemReg, CompatibilityMode

class TestSchemReg(unittest.TestCase):
    def setUp(self):
        self.registry = SchemReg()
    
    def test_register_schema(self):
        schema = {'type': 'object', 'properties': {'name': {'type': 'string'}}}
        version = self.registry.register_schema('user', schema)
        self.assertEqual(version, 1)
    
    def test_get_schema(self):
        schema = {'type': 'object', 'properties': {'id': {'type': 'integer'}}}
        self.registry.register_schema('event', schema)
        retrieved = self.registry.get_schema('event')
        self.assertEqual(retrieved, schema)
    
    def test_backward_compatibility(self):
        schema1 = {'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}}}
        schema2 = {'properties': {'name': {'type': 'string'}}}
        
        self.registry.register_schema('user', schema1)
        with self.assertRaises(ValueError):
            self.registry.register_schema('user', schema2)
    
    def test_list_subjects(self):
        self.registry.register_schema('user', {})
        self.registry.register_schema('order', {})
        subjects = self.registry.list_subjects()
        self.assertEqual(len(subjects), 2)
        self.assertIn('user', subjects)
    
    def test_validate(self):
        schema = {
            'type': 'object',
            'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}},
            'required': ['name']
        }
        self.registry.register_schema('user', schema)
        
        self.assertTrue(self.registry.validate('user', {'name': 'John', 'age': 30}))
        self.assertFalse(self.registry.validate('user', {'age': 30}))

if __name__ == '__main__':
    unittest.main()
