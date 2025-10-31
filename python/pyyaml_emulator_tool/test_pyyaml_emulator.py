"""
Tests for PyYAML emulator
"""

import unittest
from io import StringIO
from pyyaml_emulator import (
    load,
    safe_load,
    dump,
    safe_dump,
    YAMLError,
    ParserError
)


class TestScalarParsing(unittest.TestCase):
    """Test parsing of scalar values"""
    
    def test_string(self):
        result = load("name: Alice")
        self.assertEqual(result, {"name": "Alice"})
    
    def test_integer(self):
        result = load("age: 30")
        self.assertEqual(result, {"age": 30})
    
    def test_float(self):
        result = load("price: 19.99")
        self.assertEqual(result, {"price": 19.99})
    
    def test_boolean_true(self):
        result = load("enabled: true")
        self.assertEqual(result, {"enabled": True})
        
        result = load("enabled: True")
        self.assertEqual(result, {"enabled": True})
    
    def test_boolean_false(self):
        result = load("enabled: false")
        self.assertEqual(result, {"enabled": False})
    
    def test_null(self):
        result = load("value: null")
        self.assertEqual(result, {"value": None})
        
        result = load("value: ~")
        self.assertEqual(result, {"value": None})
    
    def test_quoted_string(self):
        result = load('message: "Hello, World!"')
        self.assertEqual(result, {"message": "Hello, World!"})
        
        result = load("message: 'Hello, World!'")
        self.assertEqual(result, {"message": "Hello, World!"})
    
    def test_string_with_colon(self):
        result = load('url: "http://example.com"')
        self.assertEqual(result, {"url": "http://example.com"})


class TestMappingParsing(unittest.TestCase):
    """Test parsing of mappings/dictionaries"""
    
    def test_simple_mapping(self):
        yaml = """
name: Alice
age: 30
city: NYC
"""
        result = load(yaml)
        self.assertEqual(result, {
            "name": "Alice",
            "age": 30,
            "city": "NYC"
        })
    
    def test_nested_mapping(self):
        yaml = """
user:
  name: Alice
  age: 30
"""
        result = load(yaml)
        self.assertEqual(result, {
            "user": {
                "name": "Alice",
                "age": 30
            }
        })
    
    def test_deeply_nested_mapping(self):
        yaml = """
company:
  department:
    team:
      name: Engineering
"""
        result = load(yaml)
        self.assertEqual(result, {
            "company": {
                "department": {
                    "team": {
                        "name": "Engineering"
                    }
                }
            }
        })
    
    def test_empty_mapping(self):
        result = load("{}")
        self.assertEqual(result, {})


class TestListParsing(unittest.TestCase):
    """Test parsing of lists/sequences"""
    
    def test_simple_list(self):
        yaml = """
- apple
- banana
- cherry
"""
        result = load(yaml)
        self.assertEqual(result, ["apple", "banana", "cherry"])
    
    def test_list_of_numbers(self):
        yaml = """
- 1
- 2
- 3
"""
        result = load(yaml)
        self.assertEqual(result, [1, 2, 3])
    
    def test_list_in_mapping(self):
        yaml = """
fruits:
  - apple
  - banana
  - cherry
"""
        result = load(yaml)
        self.assertEqual(result, {
            "fruits": ["apple", "banana", "cherry"]
        })
    
    def test_list_of_mappings(self):
        yaml = """
- name: Alice
  age: 30
- name: Bob
  age: 25
"""
        result = load(yaml)
        self.assertEqual(result, [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ])
    
    def test_nested_list(self):
        yaml = """
items:
  - item1
  - item2
"""
        result = load(yaml)
        self.assertEqual(result, {
            "items": ["item1", "item2"]
        })
    
    def test_inline_list(self):
        result = load("numbers: [1, 2, 3]")
        self.assertEqual(result, {"numbers": [1, 2, 3]})
        
        result = load("names: [Alice, Bob, Charlie]")
        self.assertEqual(result, {"names": ["Alice", "Bob", "Charlie"]})


class TestComplexStructures(unittest.TestCase):
    """Test parsing of complex nested structures"""
    
    def test_mixed_structure(self):
        yaml = """
name: MyApp
version: 1.0
authors:
  - Alice
  - Bob
config:
  debug: true
  port: 8000
"""
        result = load(yaml)
        self.assertEqual(result, {
            "name": "MyApp",
            "version": 1.0,
            "authors": ["Alice", "Bob"],
            "config": {
                "debug": True,
                "port": 8000
            }
        })
    
    def test_list_with_nested_mappings(self):
        yaml = """
users:
  - name: Alice
    email: alice@example.com
    active: true
  - name: Bob
    email: bob@example.com
    active: false
"""
        result = load(yaml)
        self.assertEqual(result, {
            "users": [
                {"name": "Alice", "email": "alice@example.com", "active": True},
                {"name": "Bob", "email": "bob@example.com", "active": False}
            ]
        })


class TestComments(unittest.TestCase):
    """Test handling of comments"""
    
    def test_comment_line(self):
        yaml = """
# This is a comment
name: Alice
"""
        result = load(yaml)
        self.assertEqual(result, {"name": "Alice"})
    
    def test_inline_comment(self):
        yaml = """
name: Alice  # This is her name
age: 30  # This is her age
"""
        result = load(yaml)
        self.assertEqual(result, {"name": "Alice", "age": 30})
    
    def test_multiple_comments(self):
        yaml = """
# Configuration file
# Author: Alice

name: MyApp  # Application name
version: 1.0  # Version number
"""
        result = load(yaml)
        self.assertEqual(result, {"name": "MyApp", "version": 1.0})


class TestInlineStructures(unittest.TestCase):
    """Test inline/flow style structures"""
    
    def test_inline_mapping(self):
        result = load("person: {name: Alice, age: 30}")
        self.assertEqual(result, {"person": {"name": "Alice", "age": 30}})
    
    def test_inline_list(self):
        result = load("colors: [red, green, blue]")
        self.assertEqual(result, {"colors": ["red", "green", "blue"]})
    
    def test_mixed_inline(self):
        result = load("data: {items: [1, 2, 3], count: 3}")
        self.assertEqual(result, {"data": {"items": [1, 2, 3], "count": 3}})


class TestDumping(unittest.TestCase):
    """Test YAML dumping/serialization"""
    
    def test_dump_simple_mapping(self):
        data = {"name": "Alice", "age": 30}
        result = dump(data)
        self.assertIn("name: Alice", result)
        self.assertIn("age: 30", result)
    
    def test_dump_list(self):
        data = ["apple", "banana", "cherry"]
        result = dump(data)
        self.assertIn("- apple", result)
        self.assertIn("- banana", result)
        self.assertIn("- cherry", result)
    
    def test_dump_nested_mapping(self):
        data = {
            "user": {
                "name": "Alice",
                "age": 30
            }
        }
        result = dump(data)
        self.assertIn("user:", result)
        self.assertIn("name: Alice", result)
        self.assertIn("age: 30", result)
    
    def test_dump_boolean(self):
        data = {"enabled": True, "disabled": False}
        result = dump(data)
        self.assertIn("enabled: true", result)
        self.assertIn("disabled: false", result)
    
    def test_dump_null(self):
        data = {"value": None}
        result = dump(data)
        self.assertIn("value: null", result)
    
    def test_dump_numbers(self):
        data = {"integer": 42, "float": 3.14}
        result = dump(data)
        self.assertIn("integer: 42", result)
        self.assertIn("float: 3.14", result)
    
    def test_dump_quoted_string(self):
        data = {"message": "Hello: World"}
        result = dump(data)
        # String with colon should be quoted
        self.assertIn('"Hello: World"', result)
    
    def test_dump_list_of_mappings(self):
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = dump(data)
        self.assertIn("- name: Alice", result)
        self.assertIn("  age: 30", result)
    
    def test_dump_to_stream(self):
        data = {"name": "Alice"}
        stream = StringIO()
        dump(data, stream)
        result = stream.getvalue()
        self.assertIn("name: Alice", result)


class TestRoundTrip(unittest.TestCase):
    """Test that data survives load->dump->load round trip"""
    
    def test_simple_mapping_roundtrip(self):
        original = {"name": "Alice", "age": 30, "active": True}
        yaml = dump(original)
        loaded = load(yaml)
        self.assertEqual(original, loaded)
    
    def test_list_roundtrip(self):
        original = [1, 2, 3, 4, 5]
        yaml = dump(original)
        loaded = load(yaml)
        self.assertEqual(original, loaded)
    
    def test_nested_roundtrip(self):
        original = {
            "user": {
                "name": "Alice",
                "age": 30
            },
            "items": [1, 2, 3]
        }
        yaml = dump(original)
        loaded = load(yaml)
        self.assertEqual(original, loaded)


class TestSafeFunctions(unittest.TestCase):
    """Test safe_load and safe_dump functions"""
    
    def test_safe_load(self):
        yaml = "name: Alice"
        result = safe_load(yaml)
        self.assertEqual(result, {"name": "Alice"})
    
    def test_safe_dump(self):
        data = {"name": "Alice"}
        result = safe_dump(data)
        self.assertIn("name: Alice", result)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios"""
    
    def test_empty_string(self):
        result = load("")
        self.assertIsNone(result)
    
    def test_only_comments(self):
        yaml = """
# Just a comment
# Another comment
"""
        result = load(yaml)
        self.assertIsNone(result)
    
    def test_empty_values(self):
        yaml = """
empty:
nothing: ~
"""
        result = load(yaml)
        self.assertEqual(result, {"empty": None, "nothing": None})
    
    def test_numbers_as_strings(self):
        result = load('version: "1.0"')
        self.assertEqual(result, {"version": "1.0"})
        self.assertIsInstance(result["version"], str)
    
    def test_special_characters_in_string(self):
        yaml = 'message: "Hello\\nWorld"'
        result = load(yaml)
        self.assertEqual(result, {"message": "Hello\nWorld"})


class TestFileIO(unittest.TestCase):
    """Test file-like object handling"""
    
    def test_load_from_stringio(self):
        stream = StringIO("name: Alice\nage: 30")
        result = load(stream)
        self.assertEqual(result, {"name": "Alice", "age": 30})
    
    def test_dump_to_stringio(self):
        data = {"name": "Alice", "age": 30}
        stream = StringIO()
        dump(data, stream)
        result = stream.getvalue()
        self.assertIn("name: Alice", result)
        self.assertIn("age: 30", result)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestScalarParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestMappingParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestListParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestComplexStructures))
    suite.addTests(loader.loadTestsFromTestCase(TestComments))
    suite.addTests(loader.loadTestsFromTestCase(TestInlineStructures))
    suite.addTests(loader.loadTestsFromTestCase(TestDumping))
    suite.addTests(loader.loadTestsFromTestCase(TestRoundTrip))
    suite.addTests(loader.loadTestsFromTestCase(TestSafeFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestFileIO))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
