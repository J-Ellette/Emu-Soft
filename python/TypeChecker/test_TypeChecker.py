"""
Developed by PowerShield, as an alternative to mypy
"""

"""
Tests for MyPy Emulator
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from TypeChecker import MypyEmulator, TypeChecker, TypeInferenceEngine
import tempfile
import os


def test_basic_type_inference():
    """Test basic type inference from literals"""
    engine = TypeInferenceEngine()
    
    import ast
    
    # Test integer
    node = ast.parse("42").body[0].value
    assert engine.infer_from_literal(node) == 'int'
    
    # Test string
    node = ast.parse("'hello'").body[0].value
    assert engine.infer_from_literal(node) == 'str'
    
    print("✓ Basic type inference works")


def test_annotated_assignment():
    """Test type checking with annotated assignments"""
    checker = TypeChecker()
    
    # Create temp file with annotated assignment
    code = """
x: int = 5
y: str = "hello"
z: int = "wrong"  # This should error
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = checker.check_file(temp_file)
        
        # Should have one error (z assignment)
        assert len(result.errors) >= 1
        assert 'Type mismatch' in result.errors[0]
        assert not result.success
        
        print("✓ Annotated assignment checking works")
    finally:
        os.unlink(temp_file)


def test_function_type_checking():
    """Test function signature type checking"""
    checker = TypeChecker()
    
    code = """
def add(a: int, b: int) -> int:
    return a + b

def greet(name: str) -> str:
    return f"Hello, {name}"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = checker.check_file(temp_file)
        
        # Should have no errors
        assert result.success
        print("✓ Function type checking works")
    finally:
        os.unlink(temp_file)


def test_type_compatibility():
    """Test type compatibility checking"""
    checker = TypeChecker()
    
    # Compatible types
    assert checker._is_compatible('int', 'int')
    assert checker._is_compatible('str', 'Any')
    assert checker._is_compatible('Any', 'str')
    
    # Numeric compatibility
    assert checker._is_compatible('int', 'float')
    
    # Optional types
    assert checker._is_compatible('None', 'Optional[str]')
    assert checker._is_compatible('str', 'Optional[str]')
    
    print("✓ Type compatibility checking works")


def test_strict_mode():
    """Test strict mode warnings"""
    checker = TypeChecker(strict=True)
    
    code = """
def no_annotations(x, y):
    return x + y
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = checker.check_file(temp_file)
        
        # Should have warnings in strict mode
        assert len(result.warnings) > 0
        
        print("✓ Strict mode works")
    finally:
        os.unlink(temp_file)


def test_emulator_interface():
    """Test MypyEmulator interface"""
    emulator = MypyEmulator(verbose=False)
    
    # Create multiple test files
    files = []
    
    # File 1: Valid types
    code1 = """
x: int = 5
y: str = "hello"
"""
    
    # File 2: Type error
    code2 = """
a: int = "wrong"
"""
    
    for code in [code1, code2]:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            files.append(f.name)
    
    try:
        results = emulator.check_files(files)
        
        # Should check both files
        assert len(results) == 2
        
        # First should succeed, second should fail
        assert results[0].success
        assert not results[1].success
        
        # Generate report
        report = emulator.generate_report(results)
        assert report['total_files'] == 2
        assert report['successful'] == 1
        assert report['failed'] == 1
        
        print("✓ Emulator interface works")
    finally:
        for f in files:
            os.unlink(f)


def test_complex_types():
    """Test complex type annotations"""
    checker = TypeChecker()
    
    code = """
from typing import List, Dict, Optional, Union

numbers: List[int] = [1, 2, 3]
mapping: Dict[str, int] = {"a": 1, "b": 2}
maybe_str: Optional[str] = None
multi: Union[int, str] = 5
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = checker.check_file(temp_file)
        
        # Should handle complex types without crashing
        assert result is not None
        
        print("✓ Complex type handling works")
    finally:
        os.unlink(temp_file)


def test_error_reporting():
    """Test error reporting format"""
    checker = TypeChecker()
    
    code = """
x: int = 5
x = "string"  # Type error - reassignment
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = checker.check_file(temp_file)
        
        # Should have error with line number
        assert len(result.errors) > 0
        assert 'Line' in result.errors[0]
        
        print("✓ Error reporting works")
    finally:
        os.unlink(temp_file)


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("MyPy Emulator Tests")
    print("="*60)
    
    tests = [
        test_basic_type_inference,
        test_annotated_assignment,
        test_function_type_checking,
        test_type_compatibility,
        test_strict_mode,
        test_emulator_interface,
        test_complex_types,
        test_error_reporting,
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
