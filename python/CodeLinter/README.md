# Flake8 Emulator

A lightweight emulation of Flake8's Python linting functionality for code style and quality checking.

## Features

- **Style Checking**: PEP 8 style guide enforcement
- **Error Detection**: Syntax errors and common mistakes
- **Code Quality**: Unused imports, unused variables
- **Complexity Analysis**: Cyclomatic complexity checking
- **Whitespace Rules**: Indentation, trailing whitespace, line length
- **Multiple File Support**: Lint single files or entire directories
- **Configurable**: Adjust line length and complexity thresholds

## What It Emulates

This tool emulates core functionality of [Flake8](https://github.com/PyCQA/flake8), the popular Python linting tool that combines PyFlakes, pycodestyle, and McCabe complexity checking.

### Error Codes Implemented

#### E-codes (PEP 8 errors)
- **E101**: Indentation contains mixed spaces and tabs
- **E201**: Whitespace after '('
- **E202**: Whitespace before ')'
- **E501**: Line too long (configurable, default 79 characters)
- **E701**: Multiple statements on one line (colon)
- **E702**: Multiple statements on one line (semicolon)
- **E999**: Syntax error

#### W-codes (PEP 8 warnings)
- **W291**: Trailing whitespace
- **W292**: No newline at end of file

#### F-codes (PyFlakes)
- **F401**: Module imported but unused
- **F841**: Local variable assigned but never used

#### C-codes (McCabe complexity)
- **C901**: Function is too complex (configurable threshold)

## Usage

### As a Module

```python
from flake8_emulator import Flake8Emulator

# Create emulator instance
emulator = Flake8Emulator(
    max_line_length=79,
    max_complexity=10,
    verbose=True
)

# Lint single file
results = emulator.check_files(['my_script.py'])

# Lint multiple files
results = emulator.check_files(['file1.py', 'file2.py', 'file3.py'])

# Lint entire directory
results = emulator.check_directory('src/', pattern='*.py')

# Generate report
report = emulator.generate_report(results)
print(f"Total issues: {report['total_issues']}")
print(f"Clean files: {report['clean_files']}")
```

### Command Line

```bash
# Lint single file
python flake8_emulator.py script.py

# Lint multiple files
python flake8_emulator.py file1.py file2.py file3.py

# Custom line length
python flake8_emulator.py --max-line-length=100 script.py

# Custom complexity threshold
python flake8_emulator.py --max-complexity=15 script.py

# Verbose output
python flake8_emulator.py -v script.py
```

## Examples

### Line Length (E501)

```python
# Error: Line too long
this_is_a_very_long_line_that_exceeds_the_maximum_allowed_length_of_79_characters = 1

# OK: Within limit
short_line = 1
```

### Trailing Whitespace (W291)

```python
# Warning: Trailing whitespace
x = 1   

# OK: No trailing whitespace
x = 1
```

### Unused Import (F401)

```python
# Error: Unused import
import os
import sys

print("Hello")  # Neither os nor sys is used

# OK: Import is used
import os
print(os.getcwd())
```

### Unused Variable (F841)

```python
# Error: Unused variable
def my_function():
    unused = 42  # Never used
    used = 10
    return used

# OK: All variables used
def my_function():
    value = 42
    return value
```

### Complexity (C901)

```python
# Error: Too complex (default max is 10)
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    if x > 40:
                        if x > 50:
                            return "very large"
    return "small"

# OK: Lower complexity
def simple_function(x):
    if x > 50:
        return "very large"
    elif x > 30:
        return "large"
    return "small"
```

### Whitespace (E201, E202)

```python
# Error: Extra whitespace
x = ( 1, 2, 3 )
y = [1, 2 ]

# OK: Proper spacing
x = (1, 2, 3)
y = [1, 2]
```

## API Reference

### Flake8Emulator

Main interface for linting.

**Constructor:**
- `max_line_length` (int): Maximum line length (default: 79)
- `max_complexity` (int): Maximum cyclomatic complexity (default: 10)
- `verbose` (bool): Enable verbose output

**Methods:**
- `check_files(file_paths: List[str]) -> List[LintResult]`: Lint multiple files
- `check_directory(directory: str, pattern: str = "*.py") -> List[LintResult]`: Lint directory
- `generate_report(results: List[LintResult]) -> Dict`: Generate summary report

### LintResult

Result of linting a file.

**Attributes:**
- `file_path` (str): Path to linted file
- `issues` (List[LintIssue]): Issues found
- `lines_checked` (int): Number of lines checked
- `success` (bool): True if no errors

### LintIssue

Represents a single linting issue.

**Attributes:**
- `file_path` (str): File containing the issue
- `line_no` (int): Line number
- `column` (int): Column number
- `code` (str): Error code (e.g., "E501")
- `message` (str): Error message
- `severity` (str): "warning" or "error"

## Rule System

The emulator uses a plugin-like rule system:

### Line-Based Rules
Check individual lines of code:
- Indentation rules
- Whitespace rules
- Line length rules

### File-Based Rules
Check entire file properties:
- Newline at end of file

### AST-Based Rules
Use Python's AST for deeper analysis:
- Unused imports
- Unused variables
- Cyclomatic complexity

## Limitations

This is an educational emulation with some limitations:

1. **Limited Rule Set**: Implements most common rules but not all 300+ Flake8 rules
2. **No Plugin System**: Doesn't support external plugins like real Flake8
3. **Simplified Parsing**: Some edge cases may not be detected
4. **No Config Files**: Doesn't read .flake8 or setup.cfg configuration
5. **Basic Whitespace**: Some complex whitespace rules not implemented

## Testing

Run the test suite:

```bash
python test_flake8_emulator.py
```

Tests cover:
- Line length checking
- Trailing whitespace detection
- Unused import detection
- Unused variable detection
- Complexity checking
- Whitespace rules
- Syntax error handling

## Complexity

**Implementation Complexity**: Medium

This emulator involves:
- AST parsing for code analysis
- Pattern matching with regular expressions
- Rule engine architecture
- Symbol table tracking for unused detection
- Cyclomatic complexity calculation

The linting system requires understanding Python's style guidelines, AST structure, and common code smells.

## Dependencies

- Python 3.6+ (uses built-in `ast` and `re` modules)
- No external dependencies required

## Integration

Can be integrated into:
- Pre-commit hooks
- CI/CD pipelines
- IDE linting tools
- Code review automation

## License

Part of the Emu-Soft project - see main repository LICENSE.
