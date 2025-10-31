# MkDocs Emulator

A pure Python implementation that emulates MkDocs functionality for generating documentation websites from Markdown files without external dependencies.

## What This Emulates

**Emulates:** MkDocs (Markdown documentation generator)
**Original:** https://www.mkdocs.org/

## Overview

This module provides static site generation from Markdown files, creating professional documentation websites with navigation, themes, and cross-page linking.

## Features

- **Markdown to HTML Conversion**
  - Headers (h1-h6)
  - Bold and italic text
  - Links and images
  - Code blocks with syntax highlighting
  - Inline code
  - Lists (ordered and unordered)
  - Blockquotes
  - Horizontal rules
  - Tables

- **Site Structure**
  - Automatic page discovery
  - Navigation menu generation
  - Index page
  - Multi-page support
  - Hierarchical organization

- **Configuration**
  - Simple `mkdocs.yml` configuration
  - Project metadata (name, author, description)
  - Theme support
  - Directory customization

- **Themes**
  - Clean, modern design
  - Responsive layout
  - Professional styling
  - Mobile-friendly

## Usage

### Create a New Project

Create a new documentation project:

```bash
python mkdocs_emulator.py new my-docs
```

This creates:
- `my-docs/` directory
- `mkdocs.yml` configuration file
- `docs/` directory with `index.md`

### Build Documentation

Build your documentation site:

```bash
cd my-docs
python -m mkdocs_emulator_tool.mkdocs_emulator build
```

Or specify directories:

```bash
python -m mkdocs_emulator_tool.mkdocs_emulator build . site
```

This will:
1. Read configuration from `mkdocs.yml`
2. Discover all Markdown files in `docs/`
3. Convert Markdown to HTML
4. Generate navigation
5. Create HTML files in `site/` directory

### View Documentation

Open `site/index.html` in your browser to view the generated documentation.

## Configuration

Create a `mkdocs.yml` file:

```yaml
site_name: My Documentation
site_description: Documentation for my project
site_author: John Doe
theme: default
docs_dir: docs
site_dir: site
```

Configuration options:
- `site_name`: Name of your documentation site
- `site_description`: Description (used in meta tags)
- `site_author`: Author name (shown in footer)
- `theme`: Theme to use (currently 'default')
- `docs_dir`: Directory containing Markdown files (default: 'docs')
- `site_dir`: Output directory for HTML (default: 'site')

## Project Structure

```
my-docs/
├── mkdocs.yml          # Configuration file
├── docs/               # Markdown source files
│   ├── index.md        # Home page
│   ├── about.md        # About page
│   └── guide.md        # Guide page
└── site/               # Generated HTML (after build)
    ├── index.html
    ├── about.html
    └── guide.html
```

## Markdown Examples

### Headers

```markdown
# Header 1
## Header 2
### Header 3
```

### Text Formatting

```markdown
**bold text**
*italic text*
`inline code`
```

### Links and Images

```markdown
[Link text](https://example.com)
![Image alt text](image.png)
```

### Code Blocks

```markdown
```python
def hello():
    print("Hello, world!")
```
```

### Lists

```markdown
- Item 1
- Item 2
- Item 3

1. First
2. Second
3. Third
```

### Blockquotes

```markdown
> This is a blockquote
> It can span multiple lines
```

## Python API

Use the builder programmatically:

```python
from mkdocs_emulator_tool.mkdocs_emulator import MkDocsBuilder

# Create builder
builder = MkDocsBuilder()

# Build site
builder.build(source_dir='.', output_dir='site')
```

Create a new project:

```python
from mkdocs_emulator_tool.mkdocs_emulator import MkDocsBuilder

builder = MkDocsBuilder()
builder.new('my-project', output_dir='.')
```

## Command-Line Interface

### Build Command

```bash
python mkdocs_emulator.py build [source_dir] [output_dir]
```

Examples:
```bash
# Build from current directory to site/
python mkdocs_emulator.py build

# Specify source and output
python mkdocs_emulator.py build ./docs ./build

# Use custom directories
python mkdocs_emulator.py build /path/to/source /path/to/output
```

### New Command

```bash
python mkdocs_emulator.py new <project_name>
```

Examples:
```bash
# Create new project in current directory
python mkdocs_emulator.py new my-docs

# Project will be created at ./my-docs/
```

## Testing

Run the test suite:

```bash
python test_mkdocs_emulator.py
```

Test coverage:
- YAML parser (3 tests)
- Markdown converter (8 tests)
- Page management (2 tests)
- Site builder (5 tests)
- Integration tests (1 test)

## Use Cases

- **Project Documentation**: Create user guides and API docs
- **Internal Wikis**: Build internal knowledge bases
- **Tutorials**: Write step-by-step guides
- **README Sites**: Expand your README into a full site
- **Portfolio**: Showcase projects with documentation
- **Notes**: Personal documentation and notes

## Benefits

### Self-Contained

No external dependencies - uses only Python standard library. Easy to install and deploy.

### Fast

Quick build times for small to medium documentation sites. Processes files efficiently.

### Simple

Easy to learn and use. Just write Markdown and build. No complex configuration needed.

### Professional

Clean, modern HTML output. Responsive design looks good on all devices.

## Advanced Usage

### Custom Markdown Converter

Extend the Markdown converter:

```python
from mkdocs_emulator_tool.mkdocs_emulator import MarkdownConverter

# Convert Markdown to HTML
html = MarkdownConverter.convert("# Hello\n\nWorld")
print(html)
```

### Manual Page Creation

Create pages manually:

```python
from mkdocs_emulator_tool.mkdocs_emulator import MarkdownPage

page = MarkdownPage(
    title="My Page",
    path="mypage.md",
    content="# My Page\n\nContent here"
)
```

### Load Custom Config

```python
builder = MkDocsBuilder('custom-config.yml')
builder.load_config()
print(builder.config['site_name'])
```

## Integration

### With CI/CD

GitHub Actions example:

```yaml
- name: Build Documentation
  run: |
    python -m mkdocs_emulator_tool.mkdocs_emulator build
    
- name: Deploy
  run: |
    # Deploy site/ directory to hosting
```

### With Make

Add to Makefile:

```makefile
.PHONY: docs
docs:
	python -m mkdocs_emulator_tool.mkdocs_emulator build

.PHONY: docs-clean
docs-clean:
	rm -rf site/
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- id: build-docs
  name: Build Documentation
  entry: python -m mkdocs_emulator_tool.mkdocs_emulator build
  language: system
  pass_filenames: false
```

## Limitations

Compared to full MkDocs:

- **No plugins**: No extension system
- **Single theme**: Only one built-in theme
- **Basic Markdown**: Simplified Markdown parser
- **No search**: No built-in search functionality
- **No live reload**: No development server
- **No themes marketplace**: Cannot install external themes
- **Limited navigation**: Simple linear navigation only

These limitations keep the implementation focused and dependency-free while providing core documentation generation capabilities.

## Performance

- **Fast Builds**: Quick generation for most projects
- **Low Memory**: Efficient memory usage
- **Scalable**: Handles projects with dozens of pages
- **Incremental**: Processes one file at a time

## Examples

### Example 1: Simple Documentation

```markdown
# docs/index.md
# My Project

Welcome to my project documentation!

## Installation

Install with pip:

```bash
pip install my-project
```

## Usage

Import and use:

```python
from myproject import main
main()
```
```

Build:
```bash
python -m mkdocs_emulator_tool.mkdocs_emulator build
```

### Example 2: Multi-Page Documentation

Structure:
```
docs/
├── index.md
├── installation.md
├── usage.md
└── api.md
```

Each file contains documentation. Build generates linked pages.

## Best Practices

### 1. Clear Structure

Organize documentation logically:
```
docs/
├── index.md           # Overview
├── getting-started.md
├── tutorials/
│   ├── basic.md
│   └── advanced.md
└── reference/
    └── api.md
```

### 2. Good Markdown

Write clear, well-formatted Markdown:
- Use headers to organize content
- Add code examples
- Include images for clarity
- Use lists for steps

### 3. Update Regularly

Keep documentation in sync with code. Rebuild after changes.

### 4. Test Links

Check that all internal links work after building.

### 5. Consistent Style

Use consistent Markdown formatting throughout your docs.

## Troubleshooting

### "No Markdown pages found"

- Check that `docs/` directory exists
- Ensure files have `.md` extension
- Verify `docs_dir` in `mkdocs.yml`

### "Directory already exists"

When creating a new project, choose a unique name or remove the existing directory.

### Images Not Showing

Place images in the `docs/` directory and use relative paths:
```markdown
![Image](./images/screenshot.png)
```

## How It Works

1. **Parse Config**: Read `mkdocs.yml` configuration
2. **Discover Pages**: Find all `.md` files in `docs/`
3. **Convert Markdown**: Transform Markdown to HTML
4. **Generate Navigation**: Create menu from pages
5. **Apply Theme**: Add CSS and layout
6. **Write Output**: Save HTML files to `site/`

## Contributing

This is part of the Emu-Soft repository's collection of emulated tools. Improvements welcome!

## License

Part of the Emu-Soft project. See project license for terms.
