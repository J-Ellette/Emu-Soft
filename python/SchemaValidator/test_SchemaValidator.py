"""
Tests for jsonschema emulator
"""

import unittest
from SchemaValidator import (
    Draft7Validator,
    ValidationError,
    SchemaError,
    validate,
    is_valid
)


class TestBasicTypes(unittest.TestCase):
    """Test basic type validation"""
    
    def test_string_type(self):
        schema = {"type": "string"}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate("hello")
        self.assertTrue(validator.is_valid("hello"))
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate(123)
        self.assertFalse(validator.is_valid(123))
    
    def test_integer_type(self):
        schema = {"type": "integer"}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate(42)
        self.assertTrue(validator.is_valid(0))
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate(3.14)
        self.assertFalse(validator.is_valid("42"))
    
    def test_number_type(self):
        schema = {"type": "number"}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate(42)
        validator.validate(3.14)
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate("42")
    
    def test_boolean_type(self):
        schema = {"type": "boolean"}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate(True)
        validator.validate(False)
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate(1)
    
    def test_null_type(self):
        schema = {"type": "null"}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate(None)
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate(0)
    
    def test_array_type(self):
        schema = {"type": "array"}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate([])
        validator.validate([1, 2, 3])
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate({})
    
    def test_object_type(self):
        schema = {"type": "object"}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate({})
        validator.validate({"key": "value"})
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate([])
    
    def test_multiple_types(self):
        schema = {"type": ["string", "number"]}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate("hello")
        validator.validate(42)
        validator.validate(3.14)
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate(None)


class TestEnumConst(unittest.TestCase):
    """Test enum and const validation"""
    
    def test_enum(self):
        schema = {"enum": ["red", "green", "blue"]}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate("red")
        validator.validate("green")
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate("yellow")
    
    def test_const(self):
        schema = {"const": 42}
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate(42)
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate(43)


class TestObjectValidation(unittest.TestCase):
    """Test object/dictionary validation"""
    
    def test_required_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate({"name": "Alice"})
        validator.validate({"name": "Bob", "age": 30})
        
        # Invalid - missing required
        with self.assertRaises(ValidationError) as cm:
            validator.validate({"age": 30})
        self.assertIn("name", str(cm.exception))
    
    def test_properties_validation(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            }
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate({"name": "Alice", "age": 30})
        
        # Invalid - wrong type
        with self.assertRaises(ValidationError):
            validator.validate({"name": "Alice", "age": "30"})
        
        # Invalid - fails constraint
        with self.assertRaises(ValidationError):
            validator.validate({"name": "Alice", "age": -1})
    
    def test_additional_properties_false(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "additionalProperties": False
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate({"name": "Alice"})
        
        # Invalid - additional property
        with self.assertRaises(ValidationError) as cm:
            validator.validate({"name": "Alice", "age": 30})
        self.assertIn("age", str(cm.exception))
    
    def test_additional_properties_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "additionalProperties": {"type": "integer"}
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate({"name": "Alice", "age": 30})
        
        # Invalid - additional property wrong type
        with self.assertRaises(ValidationError):
            validator.validate({"name": "Alice", "age": "30"})
    
    def test_min_max_properties(self):
        schema = {
            "type": "object",
            "minProperties": 1,
            "maxProperties": 3
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate({"a": 1})
        validator.validate({"a": 1, "b": 2, "c": 3})
        
        # Invalid - too few
        with self.assertRaises(ValidationError):
            validator.validate({})
        
        # Invalid - too many
        with self.assertRaises(ValidationError):
            validator.validate({"a": 1, "b": 2, "c": 3, "d": 4})
    
    def test_pattern_properties(self):
        schema = {
            "type": "object",
            "patternProperties": {
                "^num_": {"type": "number"},
                "^str_": {"type": "string"}
            }
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate({"num_value": 42, "str_value": "hello"})
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate({"num_value": "not a number"})


class TestArrayValidation(unittest.TestCase):
    """Test array/list validation"""
    
    def test_items_schema(self):
        schema = {
            "type": "array",
            "items": {"type": "integer"}
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate([1, 2, 3])
        validator.validate([])
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate([1, "two", 3])
    
    def test_items_tuple(self):
        schema = {
            "type": "array",
            "items": [
                {"type": "string"},
                {"type": "integer"},
                {"type": "boolean"}
            ]
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate(["hello", 42, True])
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate([42, "hello", True])
    
    def test_min_max_items(self):
        schema = {
            "type": "array",
            "minItems": 1,
            "maxItems": 3
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate([1])
        validator.validate([1, 2, 3])
        
        # Invalid - too few
        with self.assertRaises(ValidationError):
            validator.validate([])
        
        # Invalid - too many
        with self.assertRaises(ValidationError):
            validator.validate([1, 2, 3, 4])
    
    def test_unique_items(self):
        schema = {
            "type": "array",
            "uniqueItems": True
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate([1, 2, 3])
        
        # Invalid - duplicates
        with self.assertRaises(ValidationError):
            validator.validate([1, 2, 2, 3])


class TestStringValidation(unittest.TestCase):
    """Test string validation"""
    
    def test_min_max_length(self):
        schema = {
            "type": "string",
            "minLength": 2,
            "maxLength": 10
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate("ab")
        validator.validate("abcdefghij")
        
        # Invalid - too short
        with self.assertRaises(ValidationError):
            validator.validate("a")
        
        # Invalid - too long
        with self.assertRaises(ValidationError):
            validator.validate("abcdefghijk")
    
    def test_pattern(self):
        schema = {
            "type": "string",
            "pattern": "^[a-z]+$"
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate("hello")
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate("Hello123")
    
    def test_format_email(self):
        schema = {
            "type": "string",
            "format": "email"
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate("user@example.com")
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate("not-an-email")
    
    def test_format_ipv4(self):
        schema = {
            "type": "string",
            "format": "ipv4"
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate("192.168.1.1")
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate("256.1.1.1")
    
    def test_format_date(self):
        schema = {
            "type": "string",
            "format": "date"
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate("2023-12-25")
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate("12/25/2023")


class TestNumberValidation(unittest.TestCase):
    """Test number validation"""
    
    def test_minimum_maximum(self):
        schema = {
            "type": "number",
            "minimum": 0,
            "maximum": 100
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate(0)
        validator.validate(50)
        validator.validate(100)
        
        # Invalid - too small
        with self.assertRaises(ValidationError):
            validator.validate(-1)
        
        # Invalid - too large
        with self.assertRaises(ValidationError):
            validator.validate(101)
    
    def test_exclusive_minimum_maximum(self):
        schema = {
            "type": "number",
            "exclusiveMinimum": 0,
            "exclusiveMaximum": 100
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate(0.1)
        validator.validate(99.9)
        
        # Invalid - equal to bounds
        with self.assertRaises(ValidationError):
            validator.validate(0)
        
        with self.assertRaises(ValidationError):
            validator.validate(100)
    
    def test_multiple_of(self):
        schema = {
            "type": "number",
            "multipleOf": 5
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate(0)
        validator.validate(5)
        validator.validate(10)
        
        # Invalid
        with self.assertRaises(ValidationError):
            validator.validate(7)


class TestComplexSchemas(unittest.TestCase):
    """Test complex nested schemas"""
    
    def test_nested_objects(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    },
                    "required": ["name"]
                }
            },
            "required": ["user"]
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate({"user": {"name": "Alice", "age": 30}})
        validator.validate({"user": {"name": "Bob"}})
        
        # Invalid - missing required nested field
        with self.assertRaises(ValidationError):
            validator.validate({"user": {"age": 30}})
        
        # Invalid - missing required top-level field
        with self.assertRaises(ValidationError):
            validator.validate({})
    
    def test_array_of_objects(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                },
                "required": ["id"]
            }
        }
        validator = Draft7Validator(schema)
        
        # Valid
        validator.validate([
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ])
        
        # Invalid - missing required field
        with self.assertRaises(ValidationError):
            validator.validate([
                {"id": 1, "name": "Alice"},
                {"name": "Bob"}
            ])


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def test_validate_function(self):
        schema = {"type": "string"}
        
        # Valid
        validate("hello", schema)
        
        # Invalid
        with self.assertRaises(ValidationError):
            validate(123, schema)
    
    def test_is_valid_function(self):
        schema = {"type": "string"}
        
        # Valid
        self.assertTrue(is_valid("hello", schema))
        
        # Invalid
        self.assertFalse(is_valid(123, schema))


class TestValidatorMethods(unittest.TestCase):
    """Test validator methods"""
    
    def test_iter_errors(self):
        schema = {"type": "string"}
        validator = Draft7Validator(schema)
        
        errors = list(validator.iter_errors(123))
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ValidationError)
    
    def test_validation_error_path(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer"}
                    }
                }
            }
        }
        validator = Draft7Validator(schema)
        
        try:
            validator.validate({"user": {"age": "not a number"}})
            self.fail("Should have raised ValidationError")
        except ValidationError as e:
            self.assertEqual(e.path, ["user", "age"])


def run_tests():
    """Run all tests"""
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBasicTypes))
    suite.addTests(loader.loadTestsFromTestCase(TestEnumConst))
    suite.addTests(loader.loadTestsFromTestCase(TestObjectValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestArrayValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestStringValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestNumberValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestComplexSchemas))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestValidatorMethods))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
