#!/usr/bin/env python3
"""
Tests for pdoc Emulator
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdoc_emulator_tool.pdoc_emulator import (
    DocItem,
    PythonInspector,
    HTMLGenerator,
    PdocEmulator
)


# Sample module for testing
class TestClass:
    """A test class for documentation."""
    
    def __init__(self, value: int):
        """
        Initialize TestClass.
        
        Args:
            value: An integer value
        """
        self.value = value
    
    def test_method(self, x: int) -> int:
        """
        A test method.
        
        Args:
            x: Input value
        
        Returns:
            Result value
        """
        return self.value + x
    
    def _private_method(self):
        """Private method."""
        pass


def test_function(a: int, b: str = "default") -> str:
    """
    A test function.
    
    Args:
        a: First parameter
        b: Second parameter with default
    
    Returns:
        A string result
    """
    return f"{a}: {b}"


class TestDocItem:
    """Test DocItem class"""
    
    @staticmethod
    def test_creation():
        """Test DocItem creation"""
        item = DocItem(
            name="test",
            type="function",
            qualname="module.test",
            docstring="Test docstring"
        )
        
        assert item.name == "test"
        assert item.type == "function"
        assert item.qualname == "module.test"
        assert item.docstring == "Test docstring"
        print("✓ DocItem creation works")
    
    @staticmethod
    def test_anchor():
        """Test anchor generation"""
        item = DocItem(
            name="test",
            type="function",
            qualname="module.submodule.test"
        )
        
        anchor = item.get_anchor()
        assert anchor == "module-submodule-test"
        print("✓ Anchor generation works")
    
    @staticmethod
    def test_with_members():
        """Test DocItem with members"""
        parent = DocItem(name="Parent", type="class", qualname="module.Parent")
        child = DocItem(name="method", type="method", qualname="module.Parent.method")
        parent.members.append(child)
        
        assert len(parent.members) == 1
        assert parent.members[0].name == "method"
        print("✓ DocItem with members works")


class TestPythonInspector:
    """Test PythonInspector"""
    
    @staticmethod
    def test_inspect_function():
        """Test function inspection"""
        inspector = PythonInspector()
        
        # Inspect the test_function
        item = inspector._inspect_function("test_function", test_function, "test.test_function", False)
        
        assert item.name == "test_function"
        assert item.type == "function"
        assert item.docstring is not None
        assert "test function" in item.docstring.lower()
        assert item.signature is not None
        print("✓ Function inspection works")
    
    @staticmethod
    def test_inspect_class():
        """Test class inspection"""
        inspector = PythonInspector()
        
        # Inspect the TestClass
        item = inspector._inspect_class("TestClass", TestClass, "test.TestClass", False)
        
        assert item.name == "TestClass"
        assert item.type == "class"
        assert item.docstring is not None
        assert len(item.members) > 0  # Should have methods
        print("✓ Class inspection works")
    
    @staticmethod
    def test_private_filtering():
        """Test that private members are filtered by default"""
        inspector = PythonInspector(show_private=False)
        
        # Inspect TestClass
        item = inspector._inspect_class("TestClass", TestClass, "test.TestClass", False)
        
        # Check that _private_method is not included
        method_names = [m.name for m in item.members]
        assert '_private_method' not in method_names
        print("✓ Private member filtering works")
    
    @staticmethod
    def test_show_private():
        """Test showing private members when requested"""
        inspector = PythonInspector(show_private=True)
        
        # Inspect TestClass
        item = inspector._inspect_class("TestClass", TestClass, "test.TestClass", False)
        
        # Check that _private_method is included
        method_names = [m.name for m in item.members]
        assert '_private_method' in method_names
        print("✓ Show private members works")


class TestHTMLGenerator:
    """Test HTML generation"""
    
    @staticmethod
    def test_format_docstring():
        """Test docstring formatting"""
        generator = HTMLGenerator()
        
        docstring = "First paragraph.\n\nSecond paragraph."
        html = generator._format_docstring(docstring)
        
        assert '<p>First paragraph.</p>' in html
        assert '<p>Second paragraph.</p>' in html
        print("✓ Docstring formatting works")
    
    @staticmethod
    def test_generate_function_html():
        """Test function HTML generation"""
        generator = HTMLGenerator()
        
        item = DocItem(
            name="test_func",
            type="function",
            qualname="module.test_func",
            docstring="Test function",
            signature="test_func(x, y)"
        )
        
        html = generator.generate_html(item)
        
        assert 'test_func' in html
        assert 'Test function' in html
        assert 'test_func(x, y)' in html
        print("✓ Function HTML generation works")
    
    @staticmethod
    def test_generate_class_html():
        """Test class HTML generation"""
        generator = HTMLGenerator()
        
        method = DocItem(
            name="method",
            type="method",
            qualname="module.TestClass.method",
            docstring="Test method"
        )
        
        cls = DocItem(
            name="TestClass",
            type="class",
            qualname="module.TestClass",
            docstring="Test class",
            signature="class TestClass",
            members=[method]
        )
        
        html = generator.generate_html(cls)
        
        assert 'TestClass' in html
        assert 'Test class' in html
        assert 'method' in html
        print("✓ Class HTML generation works")
    
    @staticmethod
    def test_generate_toc():
        """Test table of contents generation"""
        generator = HTMLGenerator()
        
        func1 = DocItem(name="func1", type="function", qualname="module.func1")
        cls1 = DocItem(name="Class1", type="class", qualname="module.Class1")
        
        module = DocItem(
            name="module",
            type="module",
            qualname="module",
            members=[cls1, func1]
        )
        
        toc = generator._generate_toc(module)
        
        assert 'Contents' in toc
        assert 'Classes' in toc
        assert 'Functions' in toc
        assert 'Class1' in toc
        assert 'func1' in toc
        print("✓ TOC generation works")
    
    @staticmethod
    def test_generate_page():
        """Test full page generation"""
        generator = HTMLGenerator()
        
        item = DocItem(
            name="test",
            type="function",
            qualname="module.test",
            docstring="Test"
        )
        
        html = generator.generate_page(item, "Test Documentation")
        
        assert '<!DOCTYPE html>' in html
        assert '<title>Test Documentation</title>' in html
        assert 'API Documentation' in html
        print("✓ Full page generation works")


class TestPdocEmulator:
    """Test PdocEmulator integration"""
    
    @staticmethod
    def test_document_module():
        """Test documenting a real module"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'docs.html'
            
            emulator = PdocEmulator()
            
            # Document the os module (part of stdlib)
            success = emulator.document_module('os', str(output_file))
            
            assert success
            assert output_file.exists()
            
            # Check content
            with open(output_file, 'r') as f:
                content = f.read()
                assert '<!DOCTYPE html>' in content
                assert 'os' in content
            
            print("✓ Module documentation works")
    
    @staticmethod
    def test_document_builtin():
        """Test documenting a simpler module"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'json_docs.html'
            
            emulator = PdocEmulator()
            
            # Document the json module
            success = emulator.document_module('json', str(output_file))
            
            assert success
            assert output_file.exists()
            
            # Check content
            with open(output_file, 'r') as f:
                content = f.read()
                assert 'json' in content or 'JSON' in content
            
            print("✓ Built-in module documentation works")


def run_all_tests():
    """Run all tests"""
    print("Testing pdoc Emulator\n")
    print("=" * 50)
    
    # DocItem tests
    print("\nTesting DocItem:")
    TestDocItem.test_creation()
    TestDocItem.test_anchor()
    TestDocItem.test_with_members()
    
    # PythonInspector tests
    print("\nTesting PythonInspector:")
    TestPythonInspector.test_inspect_function()
    TestPythonInspector.test_inspect_class()
    TestPythonInspector.test_private_filtering()
    TestPythonInspector.test_show_private()
    
    # HTMLGenerator tests
    print("\nTesting HTMLGenerator:")
    TestHTMLGenerator.test_format_docstring()
    TestHTMLGenerator.test_generate_function_html()
    TestHTMLGenerator.test_generate_class_html()
    TestHTMLGenerator.test_generate_toc()
    TestHTMLGenerator.test_generate_page()
    
    # Integration tests
    print("\nTesting PdocEmulator:")
    TestPdocEmulator.test_document_module()
    TestPdocEmulator.test_document_builtin()
    
    print("\n" + "=" * 50)
    print("All tests passed! ✓")


if __name__ == '__main__':
    run_all_tests()
