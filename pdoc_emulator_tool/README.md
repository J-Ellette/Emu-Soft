# pdoc Emulator

A pure Python implementation that emulates pdoc functionality for generating API documentation from Python source code without external dependencies.

## What This Emulates

**Emulates:** pdoc (Automatic API documentation generator)
**Original:** https://pdoc.dev/

## Overview

This module automatically generates API documentation by introspecting Python modules, classes, and functions, extracting their docstrings, and creating professional HTML documentation.

## Features

- **Automatic API Documentation**
  - Extract documentation from any Python module
  - Document classes, functions, and methods
  - Signature extraction
  - Source code viewing
  - Docstring parsing

- **Introspection-Based**
  - Uses Python's `inspect` module
  - No parsing required - works with any Python code
  - Handles complex inheritance
  - Extracts type hints and signatures

- **HTML Generation**
  - Clean, modern design
  - Responsive layout
  - Syntax highlighting
  - Collapsible source code
  - Table of contents
  - Anchor links

- **Configuration Options**
  - Show/hide private members
  - Show/hide source code
  - Customizable output

## Usage

### Command Line

Generate documentation for a module:

```bash
python pdoc_emulator.py mymodule
```

Save to file:

```bash
python pdoc_emulator.py mymodule docs/mymodule.html
```

Document a package:

```bash
python pdoc_emulator.py mypackage.submodule docs/submodule.html
```

### Python API

Use programmatically:

```python
from pdoc_emulator_tool.pdoc_emulator import PdocEmulator

# Create emulator
emulator = PdocEmulator()

# Generate documentation
emulator.document_module('mymodule', 'docs/mymodule.html')
```

With options:

```python
# Show private members and exclude source code
emulator = PdocEmulator(show_private=True, show_source=False)
emulator.document_module('mymodule', 'docs/mymodule.html')
```

## Examples

### Example 1: Document Your Module

Create a module:

```python
# mymodule.py
"""
My Module - A sample module.

This module demonstrates documentation generation.
"""

def greet(name: str) -> str:
    """
    Greet a person by name.
    
    Args:
        name: The person's name
    
    Returns:
        A greeting message
    """
    return f"Hello, {name}!"


class Calculator:
    """A simple calculator class."""
    
    def add(self, a: int, b: int) -> int:
        """
        Add two numbers.
        
        Args:
            a: First number
            b: Second number
        
        Returns:
            Sum of a and b
        """
        return a + b
```

Generate docs:

```bash
python pdoc_emulator.py mymodule docs/mymodule.html
```

### Example 2: Document Standard Library

```bash
# Document the json module
python pdoc_emulator.py json docs/json.html

# Document the pathlib module
python pdoc_emulator.py pathlib docs/pathlib.html
```

## Output

The generated HTML includes:

- **Module Overview**: Name, source file, module docstring
- **Table of Contents**: Quick navigation to classes and functions
- **Classes**: With inheritance, methods, and docstrings
- **Functions**: With signatures and docstrings
- **Methods**: Organized under their classes
- **Source Code**: Collapsible view of implementation
- **Anchors**: Direct links to specific items

## Configuration

### Constructor Options

```python
PdocEmulator(
    show_private=False,    # Show private members (starting with _)
    show_source=True       # Include source code in output
)
```

### Private Members

By default, private members (starting with `_`) are hidden:

```python
# Hidden by default
emulator = PdocEmulator()

# Show private members
emulator = PdocEmulator(show_private=True)
```

### Source Code

Source code is shown by default in collapsible sections:

```python
# Show source (default)
emulator = PdocEmulator(show_source=True)

# Hide source
emulator = PdocEmulator(show_source=False)
```

## Docstring Formats

Works with any docstring format:

### Google Style

```python
def function(arg1, arg2):
    """
    Summary line.
    
    Args:
        arg1: First argument
        arg2: Second argument
    
    Returns:
        Return value description
    """
    pass
```

### NumPy Style

```python
def function(arg1, arg2):
    """
    Summary line.
    
    Parameters
    ----------
    arg1 : type
        First argument
    arg2 : type
        Second argument
    
    Returns
    -------
    type
        Return value description
    """
    pass
```

### reStructuredText Style

```python
def function(arg1, arg2):
    """
    Summary line.
    
    :param arg1: First argument
    :param arg2: Second argument
    :return: Return value description
    """
    pass
```

## Testing

Run the test suite:

```bash
python test_pdoc_emulator.py
```

Test coverage:
- DocItem tests (3 tests)
- PythonInspector tests (4 tests)
- HTMLGenerator tests (5 tests)
- Integration tests (2 tests)

## Use Cases

- **API Documentation**: Auto-generate docs for libraries
- **Code Review**: Share documentation with team
- **Learning**: Understand code structure
- **Onboarding**: Help new developers understand code
- **Reference**: Quick lookup of function signatures
- **Export**: Create offline documentation

## Benefits

### Self-Contained

No external dependencies beyond Python standard library. Easy to install and use anywhere.

### Automatic

No manual documentation writing. Just add docstrings and generate.

### Fast

Quick documentation generation using introspection. No parsing or compilation needed.

### Professional

Clean, modern HTML output with responsive design.

## Advanced Usage

### Inspect Without Generating HTML

```python
from pdoc_emulator_tool.pdoc_emulator import PythonInspector

inspector = PythonInspector()
doc_item = inspector.inspect_module('mymodule')

print(f"Module: {doc_item.name}")
print(f"Docstring: {doc_item.docstring}")
print(f"Members: {len(doc_item.members)}")
```

### Custom HTML Generation

```python
from pdoc_emulator_tool.pdoc_emulator import HTMLGenerator, DocItem

generator = HTMLGenerator()

item = DocItem(
    name='my_function',
    type='function',
    qualname='module.my_function',
    docstring='My function docs',
    signature='my_function(x, y)'
)

html = generator.generate_html(item)
page = generator.generate_page(item, 'My Documentation')
```

### Inspect Classes Only

```python
inspector = PythonInspector()
doc_item = inspector.inspect_module('mymodule')

classes = [m for m in doc_item.members if m.type == 'class']
for cls in classes:
    print(f"Class: {cls.name}")
    print(f"Methods: {len(cls.members)}")
```

## Integration

### With CI/CD

GitHub Actions example:

```yaml
- name: Generate API Documentation
  run: |
    python -m pdoc_emulator_tool.pdoc_emulator mypackage docs/api.html
    
- name: Deploy Documentation
  run: |
    # Deploy docs/ directory
```

### With Make

Add to Makefile:

```makefile
.PHONY: api-docs
api-docs:
	python -m pdoc_emulator_tool.pdoc_emulator mypackage docs/api.html

.PHONY: docs-clean
docs-clean:
	rm -rf docs/*.html
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- id: generate-api-docs
  name: Generate API Documentation
  entry: python -m pdoc_emulator_tool.pdoc_emulator mypackage docs/api.html
  language: system
  pass_filenames: false
```

## Command-Line Interface

### Basic Usage

```bash
python pdoc_emulator.py <module_name> [output_file]
```

### Examples

Print to stdout:
```bash
python pdoc_emulator.py mymodule
```

Save to file:
```bash
python pdoc_emulator.py mymodule docs.html
```

Document package:
```bash
python pdoc_emulator.py mypackage.submodule output.html
```

## Limitations

Compared to full pdoc:

- **No live reload**: No development server
- **Single file output**: No multi-page sites
- **Basic themes**: Only one built-in theme
- **No plugins**: No extension system
- **Simplified parsing**: Basic docstring formatting
- **No search**: No built-in search functionality
- **No cross-linking**: Between modules limited
- **No inheritance diagrams**: No visual class hierarchies

These limitations keep the implementation simple while providing core documentation generation capabilities.

## Performance

- **Fast Generation**: Direct introspection is quick
- **Low Memory**: Efficient memory usage
- **No Compilation**: No parsing or AST building needed
- **Scalable**: Handles modules with many classes

## How It Works

1. **Import Module**: Import the target module
2. **Introspect**: Use Python's `inspect` module
3. **Extract Info**: Get docstrings, signatures, source
4. **Build Structure**: Create documentation tree
5. **Generate HTML**: Convert to styled HTML
6. **Write Output**: Save to file

## Troubleshooting

### "Error inspecting module"

- Ensure the module is importable
- Check that module is in Python path
- Verify no import errors in the module

### "Module not found"

Add the module's directory to `sys.path`:

```python
import sys
sys.path.insert(0, '/path/to/module')
```

Or use environment variable:

```bash
export PYTHONPATH=/path/to/module
python pdoc_emulator.py mymodule
```

### No documentation generated

- Check that functions/classes have docstrings
- Ensure module imports successfully
- Verify output path is writable

## Best Practices

### 1. Write Good Docstrings

Always document public APIs:

```python
def public_function(x):
    """Document this - it's public!"""
    pass

def _private_function(x):
    """Optional - it's private"""
    pass
```

### 2. Use Type Hints

Type hints appear in signatures:

```python
def calculate(x: int, y: int) -> int:
    """Type hints make better docs!"""
    return x + y
```

### 3. Consistent Format

Choose one docstring format and use it consistently.

### 4. Document Parameters

Always document function parameters:

```python
def process(data, options=None):
    """
    Process data.
    
    Args:
        data: Input data to process
        options: Optional processing options
    """
    pass
```

### 5. Add Examples

Include usage examples in docstrings:

```python
def add(a, b):
    """
    Add two numbers.
    
    Example:
        >>> add(2, 3)
        5
    """
    return a + b
```

## Contributing

This is part of the Emu-Soft repository's collection of emulated tools. Improvements welcome!

## License

Part of the Emu-Soft project. See project license for terms.
