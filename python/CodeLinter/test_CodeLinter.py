"""
Tests for Flake8 Emulator
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from CodeLinter import Flake8Emulator, Flake8Linter
import tempfile


def test_line_length():
    """Test line length checking"""
    linter = Flake8Linter(max_line_length=79)
    
    code = """
short_line = 1
this_is_a_very_long_line_that_exceeds_the_maximum_allowed_length_and_should_trigger_an_error = 2
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = linter.lint_file(temp_file)
        
        # Should have E501 error
        e501_issues = [i for i in result.issues if i.code == 'E501']
        assert len(e501_issues) > 0
        
        print("✓ Line length checking works")
    finally:
        os.unlink(temp_file)


def test_trailing_whitespace():
    """Test trailing whitespace detection"""
    linter = Flake8Linter()
    
    code = "x = 1   \ny = 2\n"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = linter.lint_file(temp_file)
        
        # Should have W291 warning
        w291_issues = [i for i in result.issues if i.code == 'W291']
        assert len(w291_issues) > 0
        
        print("✓ Trailing whitespace detection works")
    finally:
        os.unlink(temp_file)


def test_unused_import():
    """Test unused import detection"""
    linter = Flake8Linter()
    
    code = """
import os
import sys

print("Hello")
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = linter.lint_file(temp_file)
        
        # Should have F401 errors for unused imports
        f401_issues = [i for i in result.issues if i.code == 'F401']
        assert len(f401_issues) >= 1
        
        print("✓ Unused import detection works")
    finally:
        os.unlink(temp_file)


def test_unused_variable():
    """Test unused variable detection"""
    linter = Flake8Linter()
    
    code = """
def test_func():
    unused_var = 42
    used_var = 10
    return used_var
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = linter.lint_file(temp_file)
        
        # Should have F841 error for unused variable
        f841_issues = [i for i in result.issues if i.code == 'F841']
        assert len(f841_issues) > 0
        
        print("✓ Unused variable detection works")
    finally:
        os.unlink(temp_file)


def test_complexity():
    """Test cyclomatic complexity checking"""
    linter = Flake8Linter(max_complexity=5)
    
    code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    if x > 40:
                        return "very large"
                    return "large"
                return "medium"
            return "small"
        return "tiny"
    return "negative"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = linter.lint_file(temp_file)
        
        # Should have C901 error for high complexity
        c901_issues = [i for i in result.issues if i.code == 'C901']
        assert len(c901_issues) > 0
        
        print("✓ Complexity checking works")
    finally:
        os.unlink(temp_file)


def test_whitespace_rules():
    """Test whitespace rules"""
    linter = Flake8Linter()
    
    code = """
x = ( 1, 2, 3 )
y = [1, 2 ]
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = linter.lint_file(temp_file)
        
        # Should have E201/E202 errors
        whitespace_issues = [i for i in result.issues if i.code in ('E201', 'E202')]
        assert len(whitespace_issues) > 0
        
        print("✓ Whitespace rules work")
    finally:
        os.unlink(temp_file)


def test_clean_code():
    """Test that clean code passes"""
    linter = Flake8Linter()
    
    code = """
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = linter.lint_file(temp_file)
        
        # Clean code should have minimal or no issues
        assert result.lines_checked > 0
        
        print("✓ Clean code checking works")
    finally:
        os.unlink(temp_file)


def test_emulator_interface():
    """Test Flake8Emulator interface"""
    emulator = Flake8Emulator(verbose=False)
    
    files = []
    
    # Create test files
    code1 = "x = 1\n"
    code2 = "import unused\nx = 1\n"
    
    for code in [code1, code2]:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            files.append(f.name)
    
    try:
        results = emulator.check_files(files)
        
        # Should check both files
        assert len(results) == 2
        
        # Generate report
        report = emulator.generate_report(results)
        assert report['total_files'] == 2
        
        print("✓ Emulator interface works")
    finally:
        for f in files:
            os.unlink(f)


def test_syntax_error_handling():
    """Test handling of syntax errors"""
    linter = Flake8Linter()
    
    code = """
def broken(
    # missing closing paren
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = linter.lint_file(temp_file)
        
        # Should have E999 error for syntax error
        e999_issues = [i for i in result.issues if i.code == 'E999']
        assert len(e999_issues) > 0
        
        print("✓ Syntax error handling works")
    finally:
        os.unlink(temp_file)


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("Flake8 Emulator Tests")
    print("="*60)
    
    tests = [
        test_line_length,
        test_trailing_whitespace,
        test_unused_import,
        test_unused_variable,
        test_complexity,
        test_whitespace_rules,
        test_clean_code,
        test_emulator_interface,
        test_syntax_error_handling,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("="*60)
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
