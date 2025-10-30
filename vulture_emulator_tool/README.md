# vulture Emulator

A pure Python implementation that emulates the core functionality of vulture for finding dead code in Python projects without external dependencies.

## Overview

This module provides dead code detection by analyzing Python source files with AST (Abstract Syntax Tree) parsing. It helps identify unused imports, functions, classes, variables, and attributes that can be safely removed to improve code quality and maintainability.

## Features

- **Dead Code Detection**
  - Unused imports
  - Unused functions and methods
  - Unused classes
  - Unused variables
  - Unused attributes

- **Confidence Scoring**
  - Each finding has a confidence score (0-100%)
  - Higher scores indicate higher confidence that code is truly unused
  - Configurable minimum confidence threshold

- **Smart Analysis**
  - Recognizes special methods (`__init__`, `__str__`, etc.)
  - Lower confidence for test functions (often called by frameworks)
  - Ignores private variables (starting with `_`)
  - Detects usage across function and class scopes

- **Whitelist Support**
  - Exclude specific names from analysis
  - Useful for framework callbacks, plugin systems, etc.
  - Easy whitelist file format

- **Flexible Reporting**
  - Detailed per-file breakdown
  - Summary statistics by type
  - Sorted output by file and line number
  - Exit code indicates presence of dead code

## Usage

### Basic Analysis

Analyze a single file:

```python
from vulture_emulator import VultureAnalyzer

analyzer = VultureAnalyzer()
unused = analyzer.analyze(['myfile.py'])

for item in unused:
    print(item)
```

### Analyze Directory

Analyze entire project:

```python
from vulture_emulator import VultureAnalyzer

analyzer = VultureAnalyzer()
unused = analyzer.analyze(['.'])  # Current directory

print(analyzer.report(unused))
```

### Command-Line Usage

Analyze files or directories:

```bash
# Analyze current directory
python vulture_emulator.py .

# Analyze specific files
python vulture_emulator.py file1.py file2.py

# Analyze with higher confidence threshold
python vulture_emulator.py . --min-confidence 80

# Use whitelist
python vulture_emulator.py . --whitelist .vulture_whitelist

# Verbose output
python vulture_emulator.py . --verbose
```

## Confidence Levels

Different types of unused code have different confidence levels:

- **Imports**: 90% - High confidence (rarely have side effects)
- **Functions**: 80% - High confidence (60% for test functions)
- **Classes**: 70% - Medium confidence (may be used externally)
- **Variables**: 60% - Medium confidence (may be used in templates/configs)

The default minimum confidence is 60%, which includes all findings.

## Whitelist

Create a `.vulture_whitelist` file to exclude specific names:

```
# Framework callbacks
on_load
on_unload

# Plugin system
register_plugin
unregister_plugin

# External API
public_api_method
```

Use with:

```bash
python vulture_emulator.py . --whitelist .vulture_whitelist
```

Generate whitelist template from current findings:

```bash
python vulture_emulator.py . --make-whitelist > .vulture_whitelist
```

## Examples

### Example 1: Find Unused Imports

```python
# before.py
import os
import sys
import json

print("Hello")
```

Running vulture:

```bash
python vulture_emulator.py before.py
```

Output:
```
before.py:1: unused import 'os' (confidence: 90%)
before.py:2: unused import 'sys' (confidence: 90%)
before.py:3: unused import 'json' (confidence: 90%)

============================================================
Total: 3 unused code items found
  import: 3
```

### Example 2: Find Unused Functions

```python
# module.py
def used_function():
    return 42

def unused_function():
    return 0

result = used_function()
```

Running vulture:

```bash
python vulture_emulator.py module.py
```

Output:
```
module.py:4: unused function 'unused_function' (confidence: 80%)

============================================================
Total: 1 unused code items found
  function: 1
```

### Example 3: Find Unused Classes

```python
# models.py
class UsedModel:
    pass

class UnusedModel:
    pass

obj = UsedModel()
```

Running vulture:

```bash
python vulture_emulator.py models.py
```

Output:
```
models.py:4: unused class 'UnusedModel' (confidence: 70%)

============================================================
Total: 1 unused code items found
  class: 1
```

### Example 4: With Confidence Threshold

```python
# code.py
import os  # 90% confidence
def my_func():  # 80% confidence
    pass
my_var = 10  # 60% confidence
```

High confidence only:

```bash
python vulture_emulator.py code.py --min-confidence 80
```

Output will include `os` and `my_func` but not `my_var`.

## Python API

### Basic Usage

```python
from vulture_emulator import VultureAnalyzer

analyzer = VultureAnalyzer()
unused = analyzer.analyze(['src/'])

for item in unused:
    print(f"{item.filename}:{item.line} - {item.name} ({item.type})")
```

### Advanced Usage

```python
from vulture_emulator import VultureAnalyzer

# Create analyzer with custom settings
analyzer = VultureAnalyzer()
analyzer.min_confidence = 80

# Load whitelist
analyzer.load_whitelist('.vulture_whitelist')

# Analyze
unused = analyzer.analyze(['src/', 'tests/'])

# Generate report
report = analyzer.report(unused, verbose=True)
print(report)

# Check if any dead code found
if unused:
    print(f"Found {len(unused)} issues")
    exit(1)
else:
    print("No dead code found!")
    exit(0)
```

### Custom Analysis

```python
from vulture_emulator import VultureAnalyzer

analyzer = VultureAnalyzer()

# Analyze specific file
unused = analyzer.analyze_file('mymodule.py')

# Filter by type
unused_imports = [item for item in unused if item.type == 'import']
unused_functions = [item for item in unused if item.type == 'function']

print(f"Unused imports: {len(unused_imports)}")
print(f"Unused functions: {len(unused_functions)}")
```

## Command-Line Options

### Basic Commands

```bash
# Analyze paths
python vulture_emulator.py path1 path2 ...

# Set minimum confidence
python vulture_emulator.py . --min-confidence 70

# Use whitelist
python vulture_emulator.py . --whitelist .vulture_whitelist

# Verbose output (group by file)
python vulture_emulator.py . --verbose

# Exclude directories
python vulture_emulator.py . --exclude tests --exclude docs

# Generate whitelist template
python vulture_emulator.py . --make-whitelist > .vulture_whitelist
```

### Exit Codes

- `0`: No dead code found
- `1`: Dead code found (useful for CI/CD)

## Integration Examples

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- id: vulture
  name: Check for Dead Code
  entry: python -m vulture_emulator_tool.vulture_emulator
  language: system
  pass_filenames: false
  args: ['.', '--min-confidence', '80']
```

### CI/CD Pipeline

```bash
#!/bin/bash
# Run vulture and fail if dead code found
python -m vulture_emulator_tool.vulture_emulator src/ --min-confidence 80
if [ $? -ne 0 ]; then
    echo "Dead code detected! Please remove unused code."
    exit 1
fi
```

### Makefile

```makefile
.PHONY: check-deadcode
check-deadcode:
	python -m vulture_emulator_tool.vulture_emulator src/ --min-confidence 80
```

## Special Cases

### Framework Callbacks

Many frameworks call functions indirectly (Django views, Flask routes, etc.). Add these to whitelist:

```
# Django views
index
detail
create
update
delete

# Flask routes
home
api_endpoint
```

### Test Functions

Test functions (starting with `test_`) automatically get lower confidence (60%) because test frameworks call them indirectly.

### Private Variables

Variables starting with underscore (`_private`) are automatically excluded from analysis.

### Magic Methods

Python magic methods (`__init__`, `__str__`, etc.) are automatically marked as used.

## Best Practices

### 1. Start with High Confidence

Begin with high confidence threshold to find obvious dead code:

```bash
python vulture_emulator.py . --min-confidence 85
```

### 2. Review Before Deleting

Always review findings before deleting code. Some code may be:
- Called via `getattr()` or reflection
- Used by external modules
- Framework callbacks
- Plugin entry points

### 3. Use Whitelist

Maintain a whitelist for intentionally unused code:

```bash
# Generate initial whitelist
python vulture_emulator.py . --make-whitelist > .vulture_whitelist

# Edit to keep only intentional exceptions
vim .vulture_whitelist

# Run with whitelist
python vulture_emulator.py . --whitelist .vulture_whitelist
```

### 4. Run in CI/CD

Add to CI pipeline to prevent dead code accumulation:

```yaml
# GitHub Actions example
- name: Check for dead code
  run: python -m vulture_emulator_tool.vulture_emulator src/ --min-confidence 80
```

### 5. Exclude Generated Code

Exclude auto-generated code and vendored dependencies:

```bash
python vulture_emulator.py . --exclude migrations --exclude vendor
```

### 6. Periodic Cleanup

Run vulture periodically (weekly/monthly) to identify accumulating dead code.

## Testing

Run the test suite:

```bash
python test_vulture_emulator.py
```

The test suite includes:
- UnusedItem tests (2 tests)
- CodeUsageAnalyzer tests (6 tests)
- VultureAnalyzer tests (13 tests)
- Integration tests (1 test)

## Use Cases

This emulator is ideal for:

- **Code Cleanup**: Remove unused code to reduce maintenance burden
- **Refactoring**: Identify safe-to-delete code during refactoring
- **Code Review**: Check for dead code in pull requests
- **CI/CD**: Prevent dead code from being merged
- **Legacy Code**: Find unused code in old codebases
- **Import Cleanup**: Remove unused imports
- **Codebase Health**: Monitor code quality metrics

## Limitations

Compared to the full vulture tool:

- No complex control flow analysis
- No decorator-based usage detection
- Simplified attribute tracking
- No class hierarchy analysis
- No dynamic code execution analysis
- No configuration file support (beyond whitelist)

These limitations keep the implementation simple while covering the most common dead code patterns.

## Performance

- **Fast Analysis**: Uses AST parsing (no code execution)
- **Memory Efficient**: Processes files individually
- **Scalable**: Handles large codebases efficiently
- **Skip Optimization**: Automatically skips common non-code directories

## How It Works

1. **Parse**: Parse Python file into AST (Abstract Syntax Tree)
2. **Collect Definitions**: Find all imports, functions, classes, variables
3. **Track Usage**: Find all places where names are used
4. **Compare**: Identify definitions that have no corresponding usage
5. **Score**: Assign confidence based on item type and context
6. **Filter**: Apply confidence threshold and whitelist
7. **Report**: Generate sorted, grouped report

## Contributing

This is part of the Emu-Soft repository's collection of emulated tools. Improvements and bug fixes are welcome!

## License

This implementation is part of the Emu-Soft project and follows the same license terms.
