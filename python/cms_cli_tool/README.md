# CMS CLI - Development Scaffolding Tool

Command-line interface for scaffolding CMS components including plugins, themes, and content types.

## What This Provides

**Purpose:** Development scaffolding and code generation
**Similar to:** Django's `manage.py`, Rails generators, Yeoman

## Features

- Plugin scaffolding with complete structure
- Theme generation with templates and static assets
- Content type creation with field definitions
- Component validation
- File structure generation
- Boilerplate code creation

## Core Components

- **cli.py**: Main implementation
  - `CLI`: Main command-line interface
  - `PluginScaffolder`: Plugin structure generator
  - `ThemeScaffolder`: Theme structure generator
  - `ContentTypeScaffolder`: Content type generator
  - `Validator`: Component name and code validation

## Commands

### Create Plugin

```bash
python cli.py create-plugin my_plugin \
    --display-name "My Plugin" \
    --description "A custom plugin" \
    --author "Your Name"
```

Generates:
- `plugins/my_plugin/__init__.py`
- `plugins/my_plugin/plugin.py` (main plugin class)
- `plugins/my_plugin/plugin.json` (configuration)
- `plugins/my_plugin/README.md`
- `plugins/my_plugin/tests/` (test structure)

### Create Theme

```bash
python cli.py create-theme my_theme \
    --display-name "My Theme" \
    --author "Your Name"
```

Generates:
- `themes/my_theme/theme.json`
- `themes/my_theme/templates/` (base.html, home.html)
- `themes/my_theme/static/` (css, js, images directories)
- `themes/my_theme/README.md`

### Create Content Type

```bash
python cli.py create-content-type product
```

Generates:
- `content/types/product.py` (CustomPostType class)

## Generated Structures

### Plugin Structure
```
plugins/my_plugin/
├── __init__.py
├── plugin.py
├── plugin.json
├── README.md
└── tests/
    ├── __init__.py
    └── test_my_plugin.py
```

### Theme Structure
```
themes/my_theme/
├── theme.json
├── README.md
├── templates/
│   ├── base.html
│   └── home.html
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    └── images/
```

## Validation

- Enforces snake_case naming conventions
- Validates Python identifier rules
- Checks for existing components
- Verifies Python syntax in generated code

## Implementation Notes

- Uses Python's built-in libraries (no external dependencies)
- Generates complete, working boilerplate code
- Includes documentation in generated files
- Creates test structures automatically
- Follows CMS architecture patterns

## Why This Was Created

This CLI tool was created as part of the CIV-ARCOS project to streamline CMS development, providing rapid scaffolding for common components and enforcing consistent project structure.
