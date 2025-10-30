# MyPy Emulator

A lightweight emulation of MyPy's static type checking functionality for Python code.

## Features

- **Type Inference Engine**: Automatically infers types from literals and expressions
- **Type Annotation Checking**: Validates type annotations against actual values
- **Function Signature Checking**: Checks parameter and return type annotations
- **Type Compatibility**: Handles Union, Optional, and generic types
- **Strict Mode**: Optional strict mode for enforcing type annotations
- **Error Reporting**: Clear error messages with line numbers
- **Multiple File Support**: Check single files or entire directories

## What It Emulates

This tool emulates core functionality of [MyPy](https://github.com/python/mypy), the popular static type checker for Python.

### Core Components Implemented

1. **Type Inference Engine**
   - Infers types from literal values (int, str, list, dict, etc.)
   - Handles binary operations
   - Tracks variable types through assignments

2. **Type Checker**
   - Validates annotated assignments
   - Checks function signatures
   - Detects type mismatches
   - Handles complex types (Optional, Union, List, Dict, etc.)

3. **Constraint Solver**
   - Type compatibility checking
   - Numeric type coercion
   - Union and Optional type handling

4. **Error Reporting**
   - Line-specific error messages
   - Clear descriptions of type mismatches
   - Warning system for missing annotations

## Usage

### As a Module

```python
from mypy_emulator import MypyEmulator

# Create emulator instance
emulator = MypyEmulator(strict=False, verbose=True)

# Check single file
results = emulator.check_files(['my_script.py'])

# Check multiple files
results = emulator.check_files(['file1.py', 'file2.py', 'file3.py'])

# Check entire directory
results = emulator.check_directory('src/', pattern='*.py')

# Generate report
report = emulator.generate_report(results)
print(f"Total errors: {report['total_errors']}")
print(f"Total warnings: {report['total_warnings']}")
```

### Command Line

```bash
# Check single file
python mypy_emulator.py script.py

# Check multiple files
python mypy_emulator.py file1.py file2.py file3.py

# Strict mode (warns about missing annotations)
python mypy_emulator.py --strict script.py

# Verbose output
python mypy_emulator.py -v script.py
```

## Examples

### Valid Type Usage

```python
# Proper type annotations
x: int = 5
y: str = "hello"
z: list = [1, 2, 3]

def add(a: int, b: int) -> int:
    return a + b

# Complex types
from typing import List, Dict, Optional

numbers: List[int] = [1, 2, 3]
mapping: Dict[str, int] = {"a": 1}
maybe_value: Optional[str] = None
```

### Type Errors

```python
# Type mismatch - will generate error
x: int = "wrong"  # Error: Type mismatch

# Incompatible reassignment
y: str = "hello"
y = 42  # Error: Type mismatch

# Wrong return type
def get_number() -> int:
    return "not a number"  # Error: Type mismatch
```

### Strict Mode

```python
# In strict mode, missing annotations generate warnings

def no_types(x, y):  # Warning: missing annotations
    return x + y
```

## API Reference

### MypyEmulator

Main interface for type checking.

**Constructor:**
- `strict` (bool): Enable strict mode (warns about missing annotations)
- `verbose` (bool): Enable verbose output

**Methods:**
- `check_files(file_paths: List[str]) -> List[TypeCheckResult]`: Check multiple files
- `check_directory(directory: str, pattern: str = "*.py") -> List[TypeCheckResult]`: Check directory
- `generate_report(results: List[TypeCheckResult]) -> Dict`: Generate summary report

### TypeCheckResult

Result of type checking a file.

**Attributes:**
- `file_path` (str): Path to checked file
- `errors` (List[str]): Type errors found
- `warnings` (List[str]): Warnings (e.g., missing annotations)
- `checked_lines` (int): Number of lines checked
- `success` (bool): True if no errors

### TypeChecker

Core type checking engine.

**Methods:**
- `check_file(file_path: str) -> TypeCheckResult`: Check a single file
- `_is_compatible(actual: str, expected: str) -> bool`: Check type compatibility

### TypeInferenceEngine

Engine for inferring types from code.

**Methods:**
- `infer_from_literal(node: ast.AST) -> str`: Infer type from literal
- `infer_from_operation(node: ast.BinOp) -> str`: Infer type from operation
- `parse_annotation(annotation: ast.AST) -> str`: Parse type annotation

## Limitations

This is an educational emulation with some limitations compared to full MyPy:

1. **Limited Type System**: Doesn't support all advanced type features (Protocols, TypeVars, Generics)
2. **No Incremental Checking**: Checks entire files each time
3. **Basic Inference**: Type inference is simplified
4. **No Third-Party Stubs**: Doesn't use type stubs for external libraries
5. **Limited Error Recovery**: May not catch all edge cases

## Testing

Run the test suite:

```bash
python test_mypy_emulator.py
```

Tests cover:
- Type inference from literals
- Annotated assignment checking
- Function signature validation
- Type compatibility rules
- Strict mode warnings
- Error reporting format
- Complex type handling

## Complexity

**Implementation Complexity**: High

This emulator involves:
- Abstract Syntax Tree (AST) parsing and analysis
- Type inference algorithms
- Constraint solving for type compatibility
- Symbol table management
- Error reporting and diagnostics

The type system is one of the more complex aspects of static analysis, requiring deep understanding of Python's type system and AST manipulation.

## Dependencies

- Python 3.6+ (uses built-in `ast` module)
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
