# Black Code Formatter Emulator

A pure Python implementation of AST-based Python code formatting.

## What This Emulates

**Emulates:** Black (The uncompromising Python code formatter)
**Original:** https://github.com/psf/black

## Features

- AST parsing and manipulation
- Style rules engine for consistent formatting
- Code regeneration from AST
- Line length enforcement (default 88 characters)
- String normalization
- Import statement formatting
- Consistent code style application

## Core Components

- **formatter.py**: Main implementation
  - `FormatOptions`: Configuration for formatting behavior
  - `CodeFormatter`: AST-based formatter implementing Black-like rules
  - Style enforcement methods
  - Code regeneration from modified AST

## Usage

```python
from formatter import CodeFormatter, FormatOptions

# Create formatter with options
options = FormatOptions(
    line_length=88,
    string_normalization=True,
    magic_trailing_comma=True
)
formatter = CodeFormatter(options)

# Format Python code
source_code = "def hello( x,y ):return x+y"
formatted = formatter.format_code(source_code)
print(formatted)
# Output: def hello(x, y):\n    return x + y
```

## Configuration Options

- `line_length`: Maximum line length (default: 88)
- `string_normalization`: Normalize string quotes (default: True)
- `skip_string_normalization`: Disable string normalization
- `magic_trailing_comma`: Use trailing commas (default: True)
- `target_version`: Python version target (default: "py38")

## Testing

Run the test suite:

```bash
python test_formatter.py
```

## Implementation Notes

- Uses Python's `ast` module for parsing
- Implements subset of Black's formatting rules
- Focuses on most common formatting patterns
- No external dependencies required
- Deterministic formatting output

## Formatting Rules

- Consistent indentation (4 spaces)
- Line length enforcement
- String quote normalization
- Whitespace around operators
- Trailing comma handling
- Import statement organization

## Why This Was Created

This emulator was created as part of the CIV-ARCOS project to provide code formatting capabilities without external dependencies, ensuring consistent code style across the project while maintaining self-containment.
