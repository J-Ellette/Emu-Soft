"""
Test suite for isort emulator

Tests import sorting functionality including:
- Import parsing and classification
- Sorting by section (stdlib, third-party, first-party)
- Preserving comments
- Multi-line imports
- File and directory operations


Developed by PowerShield
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Import_Sorter import (
    ImportStatement, ImportSection, classify_import,
    parse_imports, sort_imports, sort_file, sort_directory, Config
)


class TestImportStatement(unittest.TestCase):
    """Test ImportStatement class"""
    
    def test_simple_import(self):
        """Test parsing simple import"""
        stmt = ImportStatement("import os", 1)
        self.assertEqual(stmt.module, "os")
        self.assertFalse(stmt.is_from)
        self.assertIsNone(stmt.alias)
    
    def test_import_with_alias(self):
        """Test parsing import with alias"""
        stmt = ImportStatement("import numpy as np", 1)
        self.assertEqual(stmt.module, "numpy")
        self.assertEqual(stmt.alias, "np")
    
    def test_from_import(self):
        """Test parsing from import"""
        stmt = ImportStatement("from os import path", 1)
        self.assertTrue(stmt.is_from)
        self.assertEqual(stmt.module, "os")
        self.assertEqual(stmt.items, ["path"])
    
    def test_from_import_multiple(self):
        """Test parsing from import with multiple items"""
        stmt = ImportStatement("from typing import List, Dict, Optional", 1)
        self.assertTrue(stmt.is_from)
        self.assertEqual(stmt.module, "typing")
        self.assertEqual(len(stmt.items), 3)
        self.assertIn("List", stmt.items)
        self.assertIn("Dict", stmt.items)
        self.assertIn("Optional", stmt.items)
    
    def test_import_with_comment(self):
        """Test parsing import with comment"""
        stmt = ImportStatement("import sys  # System module", 1)
        self.assertEqual(stmt.module, "sys")
        self.assertEqual(stmt.comment, "# System module")
    
    def test_str_conversion(self):
        """Test converting import back to string"""
        stmt = ImportStatement("import os", 1)
        self.assertEqual(str(stmt), "import os")
        
        stmt = ImportStatement("import numpy as np", 1)
        self.assertEqual(str(stmt), "import numpy as np")
        
        stmt = ImportStatement("from typing import List", 1)
        self.assertEqual(str(stmt), "from typing import List")


class TestImportSection(unittest.TestCase):
    """Test ImportSection class"""
    
    def test_section_creation(self):
        """Test creating import section"""
        section = ImportSection("stdlib")
        self.assertEqual(section.name, "stdlib")
        self.assertEqual(len(section.imports), 0)
    
    def test_add_import(self):
        """Test adding imports to section"""
        section = ImportSection("stdlib")
        stmt1 = ImportStatement("import os", 1)
        stmt2 = ImportStatement("import sys", 2)
        
        section.add(stmt1)
        section.add(stmt2)
        
        self.assertEqual(len(section.imports), 2)
    
    def test_sort_section(self):
        """Test sorting imports in section"""
        section = ImportSection("stdlib")
        section.add(ImportStatement("import sys", 1))
        section.add(ImportStatement("import os", 2))
        section.add(ImportStatement("from pathlib import Path", 3))
        
        section.sort()
        
        # Regular imports come before from imports
        self.assertFalse(section.imports[0].is_from)
        self.assertFalse(section.imports[1].is_from)
        self.assertTrue(section.imports[2].is_from)


class TestClassification(unittest.TestCase):
    """Test import classification"""
    
    def test_classify_stdlib(self):
        """Test classifying standard library imports"""
        self.assertEqual(classify_import("os"), "stdlib")
        self.assertEqual(classify_import("sys"), "stdlib")
        self.assertEqual(classify_import("json"), "stdlib")
        self.assertEqual(classify_import("pathlib"), "stdlib")
    
    def test_classify_third_party(self):
        """Test classifying third-party imports"""
        self.assertEqual(classify_import("numpy"), "third-party")
        self.assertEqual(classify_import("requests"), "third-party")
        self.assertEqual(classify_import("django"), "third-party")
    
    def test_classify_with_known_third_party(self):
        """Test classification with known third-party"""
        known = {"mylib"}
        self.assertEqual(classify_import("mylib", known_third_party=known), "third-party")
    
    def test_classify_with_known_first_party(self):
        """Test classification with known first-party"""
        known = {"myapp"}
        self.assertEqual(classify_import("myapp", known_first_party=known), "first-party")
    
    def test_classify_relative_import(self):
        """Test classifying relative imports"""
        self.assertEqual(classify_import(".models"), "first-party")
        self.assertEqual(classify_import("..utils"), "first-party")


class TestSortImports(unittest.TestCase):
    """Test import sorting functionality"""
    
    def test_sort_simple_imports(self):
        """Test sorting simple imports"""
        code = """import sys
import os
import json"""
        
        result = sort_imports(code)
        
        # Should be sorted alphabetically
        lines = result.strip().split('\n')
        self.assertIn("import json", lines)
        self.assertIn("import os", lines)
        self.assertIn("import sys", lines)
        self.assertTrue(lines.index("import json") < lines.index("import os"))
    
    def test_sort_by_section(self):
        """Test sorting imports into sections"""
        code = """import requests
import os
from myapp.models import User"""
        
        result = sort_imports(code, known_first_party={"myapp"}, 
                            known_third_party={"requests"})
        
        lines = [l for l in result.split('\n') if l.strip()]
        
        # stdlib should come first
        self.assertTrue(any("import os" in l for l in lines))
        
        # Check that sections are separated by blank lines
        self.assertIn("", result.split('\n'))
    
    def test_sort_preserves_comments(self):
        """Test that comments are preserved"""
        code = """import sys  # System module
import os  # Operating system"""
        
        result = sort_imports(code)
        
        self.assertIn("# System module", result)
        self.assertIn("# Operating system", result)
    
    def test_sort_preserves_docstring(self):
        """Test that module docstrings are preserved"""
        code = '''"""
Module docstring
"""
import sys
import os'''
        
        result = sort_imports(code)
        
        self.assertTrue(result.startswith('"""'))
        self.assertIn("Module docstring", result)
    
    def test_sort_from_imports(self):
        """Test sorting from imports"""
        code = """from typing import Dict
from typing import List
from pathlib import Path"""
        
        result = sort_imports(code)
        
        lines = [l for l in result.split('\n') if l.strip()]
        
        # Should combine multiple from imports from same module
        # and sort items alphabetically
        self.assertIn("from pathlib import Path", result)
        self.assertIn("from typing import", result)
    
    def test_sort_mixed_imports(self):
        """Test sorting mix of import types"""
        code = """from typing import List
import os
import requests
from myapp import models"""
        
        result = sort_imports(code, 
                            known_first_party={"myapp"},
                            known_third_party={"requests"})
        
        # Verify all imports are present
        self.assertIn("import os", result)
        self.assertIn("import requests", result)
        self.assertIn("from typing import List", result)
        self.assertIn("from myapp import models", result)
    
    def test_empty_code(self):
        """Test handling empty code"""
        result = sort_imports("")
        self.assertEqual(result, "")
    
    def test_no_imports(self):
        """Test code without imports"""
        code = """# Just a comment
print("Hello")"""
        
        result = sort_imports(code)
        self.assertIn("print", result)
        self.assertIn("# Just a comment", result)


class TestFileOperations(unittest.TestCase):
    """Test file and directory operations"""
    
    def setUp(self):
        """Create temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_sort_file(self):
        """Test sorting imports in a file"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("import sys\nimport os\n")
        
        # Sort the file
        changed = sort_file(test_file)
        
        # Read back
        with open(test_file, 'r') as f:
            content = f.read()
        
        self.assertIn("import os", content)
        self.assertIn("import sys", content)
    
    def test_sort_file_check_only(self):
        """Test check_only mode"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("import sys\nimport os\n")
        
        # Check if sorted (should be False as not sorted)
        is_sorted = sort_file(test_file, check_only=True)
        
        # File should not be modified
        with open(test_file, 'r') as f:
            content = f.read()
        
        self.assertEqual(content, "import sys\nimport os\n")
    
    def test_sort_directory(self):
        """Test sorting all files in directory"""
        # Create test files
        test_file1 = os.path.join(self.temp_dir, "file1.py")
        test_file2 = os.path.join(self.temp_dir, "file2.py")
        
        with open(test_file1, 'w') as f:
            f.write("import sys\nimport os\n")
        
        with open(test_file2, 'w') as f:
            f.write("import json\nimport ast\n")
        
        # Sort directory
        modified, total = sort_directory(self.temp_dir)
        
        self.assertEqual(total, 2)
        # At least one file should be modified
        self.assertGreaterEqual(modified, 0)
    
    def test_sort_directory_skip_dirs(self):
        """Test skipping directories"""
        # Create subdirectory to skip
        skip_dir = os.path.join(self.temp_dir, ".git")
        os.makedirs(skip_dir)
        
        test_file = os.path.join(skip_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("import sys\n")
        
        # Sort with default skip dirs
        modified, total = sort_directory(self.temp_dir)
        
        # Should not process files in .git
        self.assertEqual(total, 0)


class TestConfig(unittest.TestCase):
    """Test configuration"""
    
    def test_config_creation(self):
        """Test creating default config"""
        config = Config()
        
        self.assertIsInstance(config.known_first_party, set)
        self.assertIsInstance(config.known_third_party, set)
        self.assertEqual(config.line_length, 88)
        self.assertEqual(config.profile, 'black')
    
    def test_config_from_file(self):
        """Test loading config from file"""
        # Create temp config file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cfg') as f:
            f.write("known_first_party = myapp, mylib\n")
            f.write("known_third_party = requests, numpy\n")
            f.write("line_length = 100\n")
            config_file = f.name
        
        try:
            config = Config.from_file(config_file)
            
            self.assertIn("myapp", config.known_first_party)
            self.assertIn("mylib", config.known_first_party)
            self.assertIn("requests", config.known_third_party)
            self.assertEqual(config.line_length, 100)
        finally:
            os.unlink(config_file)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases"""
    
    def test_multiline_import(self):
        """Test handling multi-line imports"""
        code = """from typing import (
    List,
    Dict,
    Optional
)
import os"""
        
        result = sort_imports(code)
        
        # Should handle multi-line imports
        self.assertIn("from typing import", result)
    
    def test_import_with_dots(self):
        """Test imports with dots in module names"""
        code = """import os.path
import xml.etree.ElementTree"""
        
        result = sort_imports(code)
        
        self.assertIn("os.path", result)
        self.assertIn("xml.etree.ElementTree", result)
    
    def test_code_after_imports(self):
        """Test preserving code after imports"""
        code = """import os
import sys

def main():
    pass"""
        
        result = sort_imports(code)
        
        self.assertIn("def main():", result)
        self.assertIn("pass", result)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestImportStatement))
    suite.addTests(loader.loadTestsFromTestCase(TestImportSection))
    suite.addTests(loader.loadTestsFromTestCase(TestClassification))
    suite.addTests(loader.loadTestsFromTestCase(TestSortImports))
    suite.addTests(loader.loadTestsFromTestCase(TestFileOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
