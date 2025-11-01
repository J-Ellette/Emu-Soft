"""
Developed by PowerShield, as an alternative to Sphinx
"""

"""
Tests for Sphinx emulator

This test suite validates the documentation generator functionality.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from APIDocBuilder import (
    DocItem, DocstringParser, PythonDocExtractor, 
    HTMLGenerator, SphinxBuilder
)


class TestDocItem(unittest.TestCase):
    """Test DocItem class"""
    
    def test_doc_item_creation(self):
        """Test creating a DocItem"""
        item = DocItem(
            name='my_function',
            type='function',
            docstring='This is a test function',
            signature='my_function(x, y)',
            source_file='test.py',
            line_number=10
        )
        
        self.assertEqual(item.name, 'my_function')
        self.assertEqual(item.type, 'function')
        self.assertEqual(item.docstring, 'This is a test function')
        self.assertEqual(item.signature, 'my_function(x, y)')
    
    def test_get_id_without_parent(self):
        """Test getting ID without parent"""
        item = DocItem(name='test', type='function')
        self.assertEqual(item.get_id(), 'test')
    
    def test_get_id_with_parent(self):
        """Test getting ID with parent"""
        item = DocItem(name='method', type='method', parent='MyClass')
        self.assertEqual(item.get_id(), 'MyClass.method')


class TestDocstringParser(unittest.TestCase):
    """Test DocstringParser class"""
    
    def test_parse_empty_docstring(self):
        """Test parsing empty docstring"""
        result = DocstringParser.parse(None)
        
        self.assertEqual(result['summary'], '')
        self.assertEqual(result['description'], '')
        self.assertEqual(len(result['params']), 0)
    
    def test_parse_simple_docstring(self):
        """Test parsing simple docstring"""
        docstring = "This is a simple docstring"
        result = DocstringParser.parse(docstring)
        
        self.assertEqual(result['summary'], "This is a simple docstring")
    
    def test_parse_sphinx_style(self):
        """Test parsing Sphinx/reST style docstring"""
        docstring = """
Summary line.

Description paragraph.

:param x: First parameter
:param y: Second parameter
:return: The result
:raises ValueError: If invalid input
"""
        result = DocstringParser.parse(docstring)
        
        self.assertIn('Summary line', result['summary'])
        self.assertEqual(len(result['params']), 2)
        self.assertEqual(result['params'][0]['name'], 'x')
        self.assertEqual(result['params'][1]['name'], 'y')
        self.assertIn('result', result['returns'])
    
    def test_parse_google_style(self):
        """Test parsing Google style docstring"""
        docstring = """Summary line.

Description paragraph.

Args:
    x: First parameter
    y: Second parameter

Returns:
    The result value

Raises:
    ValueError: If invalid input
"""
        result = DocstringParser.parse(docstring)
        
        self.assertIn('Summary', result['summary'])
        self.assertEqual(len(result['params']), 2)
        self.assertEqual(result['params'][0]['name'], 'x')
        self.assertIn('result', result['returns'])
    
    def test_parse_numpy_style(self):
        """Test parsing NumPy style docstring"""
        docstring = """Summary line.

Description paragraph.

Parameters
----------
x : int
    First parameter
y : str
    Second parameter

Returns
-------
The result value
"""
        result = DocstringParser.parse(docstring)
        
        self.assertIn('Summary', result['summary'])
        self.assertEqual(len(result['params']), 2)


class TestPythonDocExtractor(unittest.TestCase):
    """Test PythonDocExtractor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_extractor_creation(self):
        """Test creating extractor"""
        extractor = PythonDocExtractor()
        self.assertEqual(len(extractor.items), 0)
    
    def test_extract_module_docstring(self):
        """Test extracting module docstring"""
        code = '''"""
This is a module docstring.
"""
'''
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        extractor = PythonDocExtractor()
        items = extractor.extract_from_file(test_file)
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].type, 'module')
        self.assertIn('module docstring', items[0].docstring)
    
    def test_extract_function(self):
        """Test extracting function documentation"""
        code = '''
def my_function(x, y):
    """This is a function docstring."""
    return x + y
'''
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        extractor = PythonDocExtractor()
        items = extractor.extract_from_file(test_file)
        
        self.assertEqual(len(items), 1)
        self.assertEqual(len(items[0].members), 1)
        func = items[0].members[0]
        self.assertEqual(func.type, 'function')
        self.assertEqual(func.name, 'my_function')
        self.assertIn('function docstring', func.docstring)
    
    def test_extract_class(self):
        """Test extracting class documentation"""
        code = '''
class MyClass:
    """This is a class docstring."""
    
    def method(self):
        """This is a method docstring."""
        pass
'''
        test_file = os.path.join(self.test_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write(code)
        
        extractor = PythonDocExtractor()
        items = extractor.extract_from_file(test_file)
        
        self.assertEqual(len(items), 1)
        self.assertEqual(len(items[0].members), 1)
        cls = items[0].members[0]
        self.assertEqual(cls.type, 'class')
        self.assertEqual(cls.name, 'MyClass')
        self.assertIn('class docstring', cls.docstring)
        self.assertEqual(len(cls.members), 1)
        self.assertEqual(cls.members[0].type, 'method')


class TestHTMLGenerator(unittest.TestCase):
    """Test HTMLGenerator class"""
    
    def test_generator_creation(self):
        """Test creating HTML generator"""
        generator = HTMLGenerator()
        self.assertEqual(generator.theme, 'default')
    
    def test_generate_html_for_function(self):
        """Test generating HTML for a function"""
        item = DocItem(
            name='test_func',
            type='function',
            docstring='Test function',
            signature='test_func(x, y)'
        )
        
        generator = HTMLGenerator()
        html = generator.generate_html(item)
        
        self.assertIn('test_func', html)
        self.assertIn('Test function', html)
        self.assertIn('test_func(x, y)', html)
    
    def test_generate_html_for_class(self):
        """Test generating HTML for a class"""
        item = DocItem(
            name='TestClass',
            type='class',
            docstring='Test class'
        )
        
        generator = HTMLGenerator()
        html = generator.generate_html(item)
        
        self.assertIn('TestClass', html)
        self.assertIn('Test class', html)
        self.assertIn('class', html)
    
    def test_generate_page(self):
        """Test generating complete HTML page"""
        item = DocItem(
            name='test',
            type='module',
            docstring='Test module'
        )
        
        generator = HTMLGenerator()
        html = generator.generate_page(item, 'Test Documentation')
        
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Test Documentation', html)
        self.assertIn('test', html)
    
    def test_get_css(self):
        """Test getting CSS"""
        generator = HTMLGenerator()
        css = generator.get_css()
        
        self.assertIn('body', css)
        self.assertIn('font-family', css)


class TestSphinxBuilder(unittest.TestCase):
    """Test SphinxBuilder class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.test_dir, 'source')
        self.build_dir = os.path.join(self.test_dir, 'build')
        os.makedirs(self.source_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_builder_creation(self):
        """Test creating Sphinx builder"""
        builder = SphinxBuilder(self.source_dir, self.build_dir)
        
        self.assertEqual(builder.source_dir, self.source_dir)
        self.assertEqual(builder.build_dir, self.build_dir)
    
    def test_collect_python_files(self):
        """Test collecting Python files"""
        # Create test files
        test_file1 = os.path.join(self.source_dir, 'module1.py')
        test_file2 = os.path.join(self.source_dir, 'module2.py')
        
        Path(test_file1).touch()
        Path(test_file2).touch()
        
        builder = SphinxBuilder(self.source_dir, self.build_dir)
        files = builder.collect_python_files()
        
        self.assertEqual(len(files), 2)
    
    def test_load_config(self):
        """Test loading configuration"""
        config_content = """
project = 'Test Project'
author = 'Test Author'
version = '2.0'
"""
        config_path = os.path.join(self.source_dir, 'conf.py')
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        builder = SphinxBuilder(self.source_dir, self.build_dir)
        builder.load_config()
        
        self.assertEqual(builder.project_name, 'Test Project')
        self.assertEqual(builder.author, 'Test Author')
        self.assertEqual(builder.version, '2.0')
    
    def test_build_documentation(self):
        """Test building documentation"""
        # Create a simple Python module
        module_code = '''"""Test module docstring."""

def test_function():
    """Test function docstring."""
    pass
'''
        test_file = os.path.join(self.source_dir, 'test_module.py')
        with open(test_file, 'w') as f:
            f.write(module_code)
        
        builder = SphinxBuilder(self.source_dir, self.build_dir)
        success = builder.build()
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.build_dir))
        
        # Check that HTML files were generated
        index_path = os.path.join(self.build_dir, 'index.html')
        self.assertTrue(os.path.exists(index_path))
        
        # Check that module HTML was generated
        module_html = os.path.join(self.build_dir, 'test_module.html')
        self.assertTrue(os.path.exists(module_html))
    
    def test_generate_index(self):
        """Test generating index"""
        builder = SphinxBuilder(self.source_dir, self.build_dir)
        os.makedirs(builder.build_dir, exist_ok=True)
        
        # Add some items
        builder.all_items = [
            DocItem(name='module1', type='module', docstring='Module 1'),
            DocItem(name='class1', type='class', docstring='Class 1'),
        ]
        
        builder.generate_index()
        
        index_path = os.path.join(self.build_dir, 'index.html')
        self.assertTrue(os.path.exists(index_path))
        
        with open(index_path, 'r') as f:
            content = f.read()
        
        self.assertIn('module1', content)
        self.assertIn('class1', content)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.test_dir, 'source')
        self.build_dir = os.path.join(self.test_dir, 'build')
        os.makedirs(self.source_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_documentation_build(self):
        """Test complete documentation build process"""
        # Create configuration
        config = """
project = 'My Project'
author = 'Test Author'
version = '1.0'
"""
        with open(os.path.join(self.source_dir, 'conf.py'), 'w') as f:
            f.write(config)
        
        # Create Python modules
        module1 = '''"""
Module 1 documentation.

This module does amazing things.
"""

def function1(x):
    """
    Function 1 does something.
    
    :param x: The input value
    :return: The result
    """
    return x * 2

class Class1:
    """Class 1 documentation."""
    
    def method1(self):
        """Method 1 documentation."""
        pass
'''
        
        with open(os.path.join(self.source_dir, 'module1.py'), 'w') as f:
            f.write(module1)
        
        # Build documentation
        builder = SphinxBuilder(self.source_dir, self.build_dir)
        success = builder.build()
        
        self.assertTrue(success)
        
        # Verify files exist
        self.assertTrue(os.path.exists(os.path.join(self.build_dir, 'index.html')))
        self.assertTrue(os.path.exists(os.path.join(self.build_dir, 'module1.html')))
        
        # Verify content
        with open(os.path.join(self.build_dir, 'module1.html'), 'r') as f:
            content = f.read()
        
        self.assertIn('Module 1 documentation', content)
        self.assertIn('function1', content)
        self.assertIn('Class1', content)
        self.assertIn('method1', content)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
