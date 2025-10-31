"""
Tests for vulture emulator

This test suite validates the dead code finder functionality.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from DeadCodeFinder import VultureAnalyzer, UnusedItem, CodeUsageAnalyzer
import ast


class TestUnusedItem(unittest.TestCase):
    """Test UnusedItem class"""
    
    def test_unused_item_creation(self):
        """Test creating an unused item"""
        item = UnusedItem(
            filename='test.py',
            line=10,
            name='unused_func',
            type='function',
            confidence=80
        )
        
        self.assertEqual(item.filename, 'test.py')
        self.assertEqual(item.line, 10)
        self.assertEqual(item.name, 'unused_func')
        self.assertEqual(item.type, 'function')
        self.assertEqual(item.confidence, 80)
    
    def test_unused_item_str(self):
        """Test string representation"""
        item = UnusedItem(
            filename='test.py',
            line=10,
            name='unused_func',
            type='function',
            confidence=80
        )
        
        string = str(item)
        self.assertIn('test.py', string)
        self.assertIn('10', string)
        self.assertIn('unused_func', string)
        self.assertIn('function', string)
        self.assertIn('80', string)


class TestCodeUsageAnalyzer(unittest.TestCase):
    """Test CodeUsageAnalyzer class"""
    
    def test_import_detection(self):
        """Test detecting imports"""
        code = """
import os
import sys
"""
        tree = ast.parse(code)
        analyzer = CodeUsageAnalyzer('test.py')
        analyzer.visit(tree)
        
        self.assertIn('os', analyzer.imports)
        self.assertIn('sys', analyzer.imports)
    
    def test_function_detection(self):
        """Test detecting function definitions"""
        code = """
def my_function():
    pass

def another_function():
    pass
"""
        tree = ast.parse(code)
        analyzer = CodeUsageAnalyzer('test.py')
        analyzer.visit(tree)
        
        self.assertIn('my_function', analyzer.functions)
        self.assertIn('another_function', analyzer.functions)
    
    def test_class_detection(self):
        """Test detecting class definitions"""
        code = """
class MyClass:
    pass

class AnotherClass:
    pass
"""
        tree = ast.parse(code)
        analyzer = CodeUsageAnalyzer('test.py')
        analyzer.visit(tree)
        
        self.assertIn('MyClass', analyzer.classes)
        self.assertIn('AnotherClass', analyzer.classes)
    
    def test_variable_detection(self):
        """Test detecting variable assignments"""
        code = """
my_var = 10
another_var = "hello"
"""
        tree = ast.parse(code)
        analyzer = CodeUsageAnalyzer('test.py')
        analyzer.visit(tree)
        
        self.assertIn('my_var', analyzer.variables)
        self.assertIn('another_var', analyzer.variables)
    
    def test_usage_detection(self):
        """Test detecting name usages"""
        code = """
import os

def my_function():
    return os.path.exists('test')
"""
        tree = ast.parse(code)
        analyzer = CodeUsageAnalyzer('test.py')
        analyzer.visit(tree)
        
        self.assertIn('os', analyzer.usages)
    
    def test_special_methods_marked_as_used(self):
        """Test that special methods are marked as used"""
        code = """
class MyClass:
    def __init__(self):
        pass
    
    def __str__(self):
        return "MyClass"
"""
        tree = ast.parse(code)
        analyzer = CodeUsageAnalyzer('test.py')
        analyzer.visit(tree)
        
        self.assertIn('__init__', analyzer.usages)
        self.assertIn('__str__', analyzer.usages)


class TestVultureAnalyzer(unittest.TestCase):
    """Test VultureAnalyzer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_analyzer_creation(self):
        """Test creating analyzer"""
        analyzer = VultureAnalyzer()
        
        self.assertEqual(len(analyzer.unused_items), 0)
        self.assertEqual(analyzer.min_confidence, 60)
    
    def test_analyze_unused_import(self):
        """Test detecting unused import"""
        code = """
import os
import sys

print("Hello")
"""
        
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        analyzer = VultureAnalyzer()
        unused = analyzer.analyze_file(test_file)
        
        # Should find unused imports
        self.assertTrue(any(item.name == 'os' and item.type == 'import' for item in unused))
        self.assertTrue(any(item.name == 'sys' and item.type == 'import' for item in unused))
    
    def test_analyze_unused_function(self):
        """Test detecting unused function"""
        code = """
def used_function():
    pass

def unused_function():
    pass

used_function()
"""
        
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        analyzer = VultureAnalyzer()
        unused = analyzer.analyze_file(test_file)
        
        # Should find unused function
        self.assertTrue(any(item.name == 'unused_function' and item.type == 'function' for item in unused))
        # Should not report used function
        self.assertFalse(any(item.name == 'used_function' for item in unused))
    
    def test_analyze_unused_class(self):
        """Test detecting unused class"""
        code = """
class UsedClass:
    pass

class UnusedClass:
    pass

obj = UsedClass()
"""
        
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        analyzer = VultureAnalyzer()
        unused = analyzer.analyze_file(test_file)
        
        # Should find unused class
        self.assertTrue(any(item.name == 'UnusedClass' and item.type == 'class' for item in unused))
        # Should not report used class
        self.assertFalse(any(item.name == 'UsedClass' for item in unused))
    
    def test_analyze_unused_variable(self):
        """Test detecting unused variable"""
        code = """
used_var = 10
unused_var = 20

print(used_var)
"""
        
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        analyzer = VultureAnalyzer()
        unused = analyzer.analyze_file(test_file)
        
        # Should find unused variable
        self.assertTrue(any(item.name == 'unused_var' and item.type == 'variable' for item in unused))
        # Should not report used variable
        self.assertFalse(any(item.name == 'used_var' for item in unused))
    
    def test_whitelist(self):
        """Test whitelist functionality"""
        code = """
import os

def my_function():
    pass
"""
        
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        whitelist_file = os.path.join(self.test_dir, '.whitelist')
        with open(whitelist_file, 'w') as f:
            f.write('os\n')
            f.write('my_function\n')
        
        analyzer = VultureAnalyzer()
        unused = analyzer.analyze([test_file], whitelist_path=whitelist_file)
        
        # Should not report whitelisted items
        self.assertFalse(any(item.name == 'os' for item in unused))
        self.assertFalse(any(item.name == 'my_function' for item in unused))
    
    def test_min_confidence_filter(self):
        """Test minimum confidence filtering"""
        code = """
import os

def my_function():
    pass

my_var = 10
"""
        
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        analyzer = VultureAnalyzer()
        analyzer.min_confidence = 80  # High confidence only
        unused = analyzer.analyze([test_file])
        
        # Should include imports (confidence 90) and functions (confidence 80)
        self.assertTrue(any(item.name == 'os' and item.type == 'import' for item in unused))
        self.assertTrue(any(item.name == 'my_function' and item.type == 'function' for item in unused))
        
        # Should not include variables (confidence 60)
        self.assertFalse(any(item.name == 'my_var' for item in unused))
    
    def test_analyze_directory(self):
        """Test analyzing a directory"""
        # Create test files
        file1 = os.path.join(self.test_dir, 'file1.py')
        with open(file1, 'w') as f:
            f.write('import os\n')
        
        file2 = os.path.join(self.test_dir, 'file2.py')
        with open(file2, 'w') as f:
            f.write('import sys\n')
        
        analyzer = VultureAnalyzer()
        unused = analyzer.analyze_directory(self.test_dir)
        
        # Should find unused imports in both files
        self.assertTrue(any(item.name == 'os' for item in unused))
        self.assertTrue(any(item.name == 'sys' for item in unused))
    
    def test_report_generation(self):
        """Test report generation"""
        items = [
            UnusedItem('test.py', 1, 'unused_func', 'function', 80),
            UnusedItem('test.py', 5, 'unused_var', 'variable', 70),
        ]
        
        analyzer = VultureAnalyzer()
        report = analyzer.report(items)
        
        self.assertIn('unused_func', report)
        self.assertIn('unused_var', report)
        self.assertIn('Total: 2', report)
    
    def test_report_empty(self):
        """Test report with no unused items"""
        analyzer = VultureAnalyzer()
        report = analyzer.report([])
        
        self.assertIn('No dead code found', report)
    
    def test_private_variables_ignored(self):
        """Test that private variables (starting with _) are ignored"""
        code = """
_private_var = 10
public_var = 20
"""
        
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        analyzer = VultureAnalyzer()
        unused = analyzer.analyze_file(test_file)
        
        # Should not report private variable
        self.assertFalse(any(item.name == '_private_var' for item in unused))
        # Should report public variable
        self.assertTrue(any(item.name == 'public_var' for item in unused))
    
    def test_test_functions_lower_confidence(self):
        """Test that test functions have lower confidence"""
        code = """
def test_something():
    pass

def regular_function():
    pass
"""
        
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        analyzer = VultureAnalyzer()
        unused = analyzer.analyze_file(test_file)
        
        # Both should be found
        test_func = next((item for item in unused if item.name == 'test_something'), None)
        regular_func = next((item for item in unused if item.name == 'regular_function'), None)
        
        self.assertIsNotNone(test_func)
        self.assertIsNotNone(regular_func)
        
        # Test function should have lower confidence
        self.assertLess(test_func.confidence, regular_func.confidence)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_analysis(self):
        """Test full analysis workflow"""
        code = """
import os
import sys
from typing import List

def used_function(x: int) -> int:
    return x * 2

def unused_function():
    pass

class UsedClass:
    def __init__(self):
        pass

class UnusedClass:
    pass

result = used_function(5)
obj = UsedClass()
"""
        
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        analyzer = VultureAnalyzer()
        unused = analyzer.analyze([test_file])
        
        # Should find unused imports
        self.assertTrue(any(item.name == 'os' for item in unused))
        self.assertTrue(any(item.name == 'sys' for item in unused))
        self.assertTrue(any(item.name == 'List' for item in unused))
        
        # Should find unused function
        self.assertTrue(any(item.name == 'unused_function' for item in unused))
        
        # Should find unused class
        self.assertTrue(any(item.name == 'UnusedClass' for item in unused))
        
        # Should not find used items
        self.assertFalse(any(item.name == 'used_function' for item in unused))
        self.assertFalse(any(item.name == 'UsedClass' for item in unused))


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
