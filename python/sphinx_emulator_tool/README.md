# Sphinx Emulator

A pure Python implementation that emulates the core functionality of Sphinx for generating documentation from Python source code without external dependencies.

## Overview

This module provides documentation generation by extracting docstrings from Python modules and generating HTML documentation. It supports multiple docstring formats and creates professional-looking documentation websites.

## Features

- **Automatic API Documentation**
  - Extract documentation from Python modules
  - Support for modules, classes, functions, and methods
  - Automatic signature extraction
  - Cross-referenced documentation

- **Multiple Docstring Formats**
  - Sphinx/reStructuredText style (`:param`, `:return:`)
  - Google style (`Args:`, `Returns:`)
  - NumPy style (`Parameters`, `Returns` with underlines)
  - Plain docstrings

- **HTML Generation**
  - Professional HTML output
  - Built-in CSS styling
  - Responsive design
  - Syntax highlighting for signatures
  - Organized by type (module, class, function)

- **Documentation Structure**
  - Index page with overview
  - Individual pages for each module
  - Hierarchical organization
  - Navigation between pages

- **Configuration**
  - Simple `conf.py` configuration file
  - Project metadata (name, author, version)
  - Theme support (basic)

## Usage

### Quickstart

Create a new documentation project interactively:

```bash
python sphinx_emulator.py quickstart
```

This will ask for:
- Project name
- Author name
- Version
- Source directory
- Build directory

And create a `conf.py` configuration file.

### Build Documentation

Build documentation from Python source files:

```bash
python sphinx_emulator.py build source_dir build_dir
```

Example:

```bash
python sphinx_emulator.py build . _build
```

This will:
1. Scan the source directory for Python files
2. Extract docstrings from all modules, classes, and functions
3. Generate HTML files in the build directory
4. Create an index page linking to all modules

### Python API

Use the builder programmatically:

```python
from sphinx_emulator import SphinxBuilder

# Create builder
builder = SphinxBuilder(
    source_dir='./src',
    build_dir='./_build'
)

# Build documentation
success = builder.build()

if success:
    print("Documentation built successfully!")
```

## Configuration

Create a `conf.py` file in your source directory:

```python
# Configuration file for Sphinx documentation

project = 'My Project'
author = 'John Doe'
version = '1.0'
release = '1.0.0'

# Theme
html_theme = 'default'
```

## Docstring Formats

### Sphinx/reStructuredText Style

```python
def my_function(x, y):
    """
    Calculate the sum of two numbers.
    
    :param x: First number
    :param y: Second number
    :return: The sum of x and y
    :raises ValueError: If inputs are invalid
    """
    return x + y
```

### Google Style

```python
def my_function(x, y):
    """Calculate the sum of two numbers.
    
    Args:
        x: First number
        y: Second number
    
    Returns:
        The sum of x and y
    
    Raises:
        ValueError: If inputs are invalid
    """
    return x + y
```

### NumPy Style

```python
def my_function(x, y):
    """Calculate the sum of two numbers.
    
    Parameters
    ----------
    x : int
        First number
    y : int
        Second number
    
    Returns
    -------
    int
        The sum of x and y
    """
    return x + y
```

## Examples

### Example 1: Simple Module

Create a Python module:

```python
# mymodule.py
"""
My Module - A sample module.

This module demonstrates documentation generation.
"""

def greet(name):
    """
    Greet a person by name.
    
    :param name: The person's name
    :return: A greeting message
    """
    return f"Hello, {name}!"

class Person:
    """Represents a person."""
    
    def __init__(self, name, age):
        """
        Initialize a Person.
        
        :param name: Person's name
        :param age: Person's age
        """
        self.name = name
        self.age = age
    
    def introduce(self):
        """
        Introduce the person.
        
        :return: Introduction string
        """
        return f"I'm {self.name}, {self.age} years old."
```

Build documentation:

```bash
python sphinx_emulator.py build . _build
```

Open `_build/index.html` in a browser to view the documentation.

### Example 2: Multi-Module Project

Project structure:
```
myproject/
├── conf.py
├── module1.py
├── module2.py
└── package/
    ├── __init__.py
    └── submodule.py
```

Build:
```bash
python sphinx_emulator.py build myproject _build
```

## Output Structure

After building, the output directory contains:

```
_build/
├── index.html          # Main index page
├── module1.html        # Documentation for module1
├── module2.html        # Documentation for module2
└── package.html        # Documentation for package
```

Each HTML file contains:
- Module docstring
- All classes with their methods
- All functions
- Complete documentation with parameters, returns, and exceptions

## HTML Output

The generated HTML includes:

- **Clean, Modern Design**: Professional appearance
- **Syntax Highlighting**: Code blocks with monospace font
- **Type Indicators**: Visual distinction between modules, classes, functions
- **Hierarchical Structure**: Nested documentation for classes and methods
- **Responsive Layout**: Works on all screen sizes
- **Easy Navigation**: Links between related documentation

## Command-Line Interface

### Build Command

```bash
python sphinx_emulator.py build <source> <build>
```

Arguments:
- `source`: Source directory containing Python files
- `build`: Output directory for HTML files

### Quickstart Command

```bash
python sphinx_emulator.py quickstart
```

Interactive setup that creates:
- `conf.py` configuration file
- Source and build directory structure

## Advanced Usage

### Custom Configuration

Load custom configuration:

```python
from sphinx_emulator import SphinxBuilder

builder = SphinxBuilder('src', '_build')

# Load configuration
builder.load_config('conf.py')

# Override settings
builder.project_name = 'Custom Name'
builder.version = '2.0'
builder.theme = 'custom'

# Build
builder.build()
```

### Extract Documentation Only

Extract documentation without building HTML:

```python
from sphinx_emulator import PythonDocExtractor

extractor = PythonDocExtractor()
items = extractor.extract_from_file('mymodule.py')

for item in items:
    print(f"{item.type}: {item.name}")
    print(f"Docstring: {item.docstring}")
```

### Parse Docstrings

Parse docstrings in different formats:

```python
from sphinx_emulator import DocstringParser

docstring = """
Summary line.

:param x: First parameter
:return: Result
"""

parsed = DocstringParser.parse(docstring)
print(f"Summary: {parsed['summary']}")
print(f"Parameters: {parsed['params']}")
print(f"Returns: {parsed['returns']}")
```

### Custom HTML Generation

Generate custom HTML:

```python
from sphinx_emulator import HTMLGenerator, DocItem

generator = HTMLGenerator(theme='custom')

item = DocItem(
    name='my_function',
    type='function',
    docstring='My function docstring',
    signature='my_function(x, y)'
)

html = generator.generate_html(item)
page = generator.generate_page(item, 'My Function Documentation')
```

## Testing

Run the test suite:

```bash
python test_sphinx_emulator.py
```

The test suite includes:
- DocItem tests (3 tests)
- DocstringParser tests (5 tests)
- PythonDocExtractor tests (4 tests)
- HTMLGenerator tests (4 tests)
- SphinxBuilder tests (6 tests)
- Integration tests (1 test)

## Use Cases

This emulator is ideal for:

- **Project Documentation**: Generate API documentation for Python projects
- **Code Understanding**: Create readable documentation from source code
- **Internal Tools**: Document internal libraries and utilities
- **Learning**: Understand code structure through generated docs
- **Code Review**: Share documentation with team members
- **Legacy Code**: Document undocumented codebases
- **Quick Reference**: Create searchable documentation

## Benefits

### Self-Contained

No external dependencies beyond Python standard library. Easy to install and use.

### Fast

Quick documentation generation for small to medium projects. Processes files individually for efficiency.

### Flexible

Supports multiple docstring formats. Works with any Python codebase.

### Professional

Clean, modern HTML output that looks professional and is easy to read.

## Best Practices

### 1. Write Good Docstrings

```python
def process_data(data, options=None):
    """
    Process the input data according to options.
    
    Args:
        data: Input data to process
        options: Optional processing options
    
    Returns:
        Processed data
    
    Raises:
        ValueError: If data format is invalid
    """
    pass
```

### 2. Document All Public APIs

Document all modules, classes, and functions that are part of your public API.

### 3. Use Consistent Style

Choose one docstring format and use it consistently throughout your project.

### 4. Keep Documentation Up to Date

Rebuild documentation after significant code changes.

### 5. Include Examples

Add usage examples in docstrings:

```python
def add(x, y):
    """
    Add two numbers.
    
    Example:
        >>> add(2, 3)
        5
    """
    return x + y
```

### 6. Organize Source Files

Keep source files organized in a clear directory structure for better documentation organization.

## Limitations

Compared to full Sphinx:

- No extension system
- No advanced directives (toctree, code-block, etc.)
- No theme customization (single basic theme)
- No search functionality (basic HTML only)
- Simplified docstring parsing
- No intersphinx (cross-project references)
- No autodoc configuration options
- No PDF or other format output

These limitations keep the implementation simple while covering core documentation generation needs.

## Performance

- **Fast Extraction**: AST-based extraction is quick
- **Incremental**: Processes one file at a time
- **Memory Efficient**: Low memory footprint
- **Scalable**: Handles projects with hundreds of files

## Integration

### With pre-commit

Add to `.pre-commit-config.yaml`:

```yaml
- id: docs
  name: Build Documentation
  entry: python -m sphinx_emulator_tool.sphinx_emulator build . _build
  language: system
  pass_filenames: false
```

### With Make

Add to `Makefile`:

```makefile
.PHONY: docs
docs:
	python -m sphinx_emulator_tool.sphinx_emulator build . _build
	
.PHONY: docs-clean
docs-clean:
	rm -rf _build
```

### With CI/CD

GitHub Actions example:

```yaml
- name: Build Documentation
  run: |
    python -m sphinx_emulator_tool.sphinx_emulator build . _build
    
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./_build
```

## How It Works

1. **Scan**: Find all Python files in source directory
2. **Parse**: Parse each file with AST (Abstract Syntax Tree)
3. **Extract**: Extract docstrings from modules, classes, functions
4. **Parse Docstrings**: Parse docstrings to extract parameters, returns, etc.
5. **Generate HTML**: Create HTML pages for each module
6. **Create Index**: Generate index page with links to all modules
7. **Write Files**: Save all HTML files to build directory

## Contributing

This is part of the Emu-Soft repository's collection of emulated tools. Improvements and bug fixes are welcome!

## License

This implementation is part of the Emu-Soft project and follows the same license terms.
