"""Command-line interface for MyCMS development.

Provides CLI tools for scaffolding and managing CMS components:
- Plugin scaffolding
- Theme scaffolding
- Content type scaffolding
- Validation and testing
"""

import os
import sys
import argparse
from typing import Optional, Dict, Any
from pathlib import Path
import re
import json


class CLIError(Exception):
    """CLI-specific error."""

    pass


class Validator:
    """Validates scaffolded components."""

    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate component name.
        
        Args:
            name: Component name to validate
            
        Returns:
            True if valid
            
        Raises:
            CLIError if invalid
        """
        # Must be valid Python identifier
        if not re.match(r"^[a-z][a-z0-9_]*$", name):
            raise CLIError(
                f"Invalid name '{name}'. "
                "Must start with lowercase letter and contain only "
                "lowercase letters, numbers, and underscores."
            )
        return True

    @staticmethod
    def validate_python_code(code: str) -> bool:
        """Validate Python code syntax.
        
        Args:
            code: Python code to validate
            
        Returns:
            True if valid
            
        Raises:
            CLIError if invalid
        """
        try:
            compile(code, "<string>", "exec")
            return True
        except SyntaxError as e:
            raise CLIError(f"Invalid Python syntax: {e}")


class PluginScaffolder:
    """Scaffolds new plugin structures."""

    def __init__(self, base_dir: str = ".") -> None:
        """Initialize plugin scaffolder.
        
        Args:
            base_dir: Base directory for plugin creation
        """
        self.base_dir = Path(base_dir)

    def create_plugin(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: str = "",
        author: str = "",
    ) -> Path:
        """Create a new plugin structure.
        
        Args:
            name: Plugin identifier (snake_case)
            display_name: Human-readable name
            description: Plugin description
            author: Plugin author
            
        Returns:
            Path to created plugin directory
            
        Raises:
            CLIError if creation fails
        """
        # Validate name
        Validator.validate_name(name)
        
        # Create plugin directory
        plugin_dir = self.base_dir / "plugins" / name
        if plugin_dir.exists():
            raise CLIError(f"Plugin directory already exists: {plugin_dir}")
        
        plugin_dir.mkdir(parents=True)
        
        # Create plugin files
        self._create_init_file(plugin_dir, name, display_name, description, author)
        self._create_plugin_file(plugin_dir, name, display_name or name.title())
        self._create_config_file(plugin_dir, name, display_name, description, author)
        self._create_readme(plugin_dir, name, display_name or name.title(), description)
        self._create_tests(plugin_dir, name)
        
        return plugin_dir

    def _create_init_file(
        self,
        plugin_dir: Path,
        name: str,
        display_name: Optional[str],
        description: str,
        author: str,
    ) -> None:
        """Create __init__.py file."""
        content = f'''"""
{display_name or name.title()} Plugin

{description}

Author: {author}
"""

from .plugin import {self._to_class_name(name)}

__version__ = "1.0.0"
__all__ = ["{self._to_class_name(name)}"]
'''
        
        init_file = plugin_dir / "__init__.py"
        init_file.write_text(content)

    def _create_plugin_file(
        self, plugin_dir: Path, name: str, display_name: str
    ) -> None:
        """Create main plugin.py file."""
        class_name = self._to_class_name(name)
        
        content = f'''"""Main plugin implementation for {display_name}."""

from mycms.plugins.base import Plugin, PluginConfig
from typing import Dict, Any


class {class_name}(Plugin):
    """
    {display_name} plugin.
    
    This plugin provides [describe functionality here].
    """

    async def on_load(self) -> bool:
        """Called when the plugin is loaded.
        
        Perform any initialization required for the plugin.
        
        Returns:
            True if load was successful
        """
        print(f"Loading {{self.config.display_name}}...")
        
        # TODO: Add initialization logic here
        # - Register hooks
        # - Set up database tables
        # - Load configuration
        
        return True

    async def on_enable(self) -> bool:
        """Called when the plugin is enabled.
        
        Activate the plugin's functionality.
        
        Returns:
            True if enable was successful
        """
        print(f"Enabling {{self.config.display_name}}...")
        
        # TODO: Add enable logic here
        # - Register routes
        # - Start background tasks
        # - Connect to external services
        
        return True

    async def on_disable(self) -> None:
        """Called when the plugin is disabled.
        
        Deactivate the plugin's functionality.
        """
        print(f"Disabling {{self.config.display_name}}...")
        
        # TODO: Add disable logic here
        # - Unregister routes
        # - Stop background tasks
        # - Disconnect from external services

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded.
        
        Clean up any resources used by the plugin.
        """
        print(f"Unloading {{self.config.display_name}}...")
        
        # TODO: Add cleanup logic here
        # - Close connections
        # - Remove temporary files
        # - Clean up cache

    # Add your custom methods here
    def process_content(self, content: str) -> str:
        """Example method: Process content.
        
        Args:
            content: Content to process
            
        Returns:
            Processed content
        """
        # TODO: Implement your logic
        return content
'''
        
        plugin_file = plugin_dir / "plugin.py"
        plugin_file.write_text(content)

    def _create_config_file(
        self,
        plugin_dir: Path,
        name: str,
        display_name: Optional[str],
        description: str,
        author: str,
    ) -> None:
        """Create plugin.json config file."""
        config = {
            "name": name,
            "display_name": display_name or name.title(),
            "description": description,
            "version": "1.0.0",
            "author": author,
            "dependencies": [],
            "settings": {
                "example_setting": "default_value"
            }
        }
        
        config_file = plugin_dir / "plugin.json"
        config_file.write_text(json.dumps(config, indent=2))

    def _create_readme(
        self, plugin_dir: Path, name: str, display_name: str, description: str
    ) -> None:
        """Create README.md file."""
        content = f'''# {display_name}

{description}

## Installation

1. Copy this plugin to your `plugins/{name}` directory
2. Enable the plugin in the admin interface

## Configuration

Configure the plugin settings in `plugin.json`:

```json
{{
  "example_setting": "your_value"
}}
```

## Usage

[Add usage instructions here]

## Development

To develop this plugin:

1. Make changes to `plugin.py`
2. Test your changes: `pytest tests/`
3. Update version in `plugin.json`

## License

[Add your license here]
'''
        
        readme_file = plugin_dir / "README.md"
        readme_file.write_text(content)

    def _create_tests(self, plugin_dir: Path, name: str) -> None:
        """Create test file."""
        class_name = self._to_class_name(name)
        
        content = f'''"""Tests for {name} plugin."""

import pytest
from mycms.plugins.base import PluginConfig
from .plugin import {class_name}


@pytest.fixture
def plugin():
    """Create plugin instance for testing."""
    config = PluginConfig(
        name="{name}",
        display_name="{name.title()}",
        description="Test plugin"
    )
    return {class_name}(config)


@pytest.mark.asyncio
async def test_plugin_load(plugin):
    """Test plugin loading."""
    result = await plugin.on_load()
    assert result is True


@pytest.mark.asyncio
async def test_plugin_enable(plugin):
    """Test plugin enabling."""
    await plugin.on_load()
    result = await plugin.on_enable()
    assert result is True


@pytest.mark.asyncio
async def test_plugin_disable(plugin):
    """Test plugin disabling."""
    await plugin.on_load()
    await plugin.on_enable()
    await plugin.on_disable()
    # Add assertions for disable behavior


# Add more tests for your plugin functionality
def test_process_content(plugin):
    """Test content processing."""
    content = "test content"
    result = plugin.process_content(content)
    assert result == content  # Update assertion for your logic
'''
        
        tests_dir = plugin_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").touch()
        
        test_file = tests_dir / f"test_{name}.py"
        test_file.write_text(content)

    @staticmethod
    def _to_class_name(name: str) -> str:
        """Convert snake_case to PascalCase."""
        return "".join(word.capitalize() for word in name.split("_"))


class ThemeScaffolder:
    """Scaffolds new theme structures."""

    def __init__(self, base_dir: str = ".") -> None:
        """Initialize theme scaffolder.
        
        Args:
            base_dir: Base directory for theme creation
        """
        self.base_dir = Path(base_dir)

    def create_theme(
        self,
        name: str,
        display_name: Optional[str] = None,
        author: str = "",
    ) -> Path:
        """Create a new theme structure.
        
        Args:
            name: Theme identifier
            display_name: Human-readable name
            author: Theme author
            
        Returns:
            Path to created theme directory
        """
        # Validate name
        Validator.validate_name(name)
        
        # Create theme directory
        theme_dir = self.base_dir / "themes" / name
        if theme_dir.exists():
            raise CLIError(f"Theme directory already exists: {theme_dir}")
        
        theme_dir.mkdir(parents=True)
        
        # Create theme files
        self._create_theme_config(theme_dir, name, display_name, author)
        self._create_templates(theme_dir)
        self._create_static_dirs(theme_dir)
        self._create_readme(theme_dir, name, display_name or name.title())
        
        return theme_dir

    def _create_theme_config(
        self,
        theme_dir: Path,
        name: str,
        display_name: Optional[str],
        author: str,
    ) -> None:
        """Create theme.json config file."""
        config = {
            "name": name,
            "display_name": display_name or name.title(),
            "version": "1.0.0",
            "author": author,
            "description": "A custom theme for MyCMS",
            "template_dir": "templates",
            "static_dir": "static",
            "settings": {
                "primary_color": "#007bff",
                "font_family": "Arial, sans-serif"
            }
        }
        
        config_file = theme_dir / "theme.json"
        config_file.write_text(json.dumps(config, indent=2))

    def _create_templates(self, theme_dir: Path) -> None:
        """Create template files."""
        templates_dir = theme_dir / "templates"
        templates_dir.mkdir()
        
        # Base template
        base_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title|default:"MyCMS" }}</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a>
            <!-- Add more navigation -->
        </nav>
    </header>
    
    <main>
        {{ content|safe }}
    </main>
    
    <footer>
        <p>&copy; 2025 MyCMS</p>
    </footer>
</body>
</html>
'''
        (templates_dir / "base.html").write_text(base_content)
        
        # Home template
        home_content = '''{{ extends "base.html" }}

<h1>Welcome to {{ site_name|default:"MyCMS" }}</h1>

<div class="content-grid">
    {{ for post in posts }}
    <article class="post-card">
        <h2>{{ post.title }}</h2>
        <p>{{ post.excerpt }}</p>
        <a href="/posts/{{ post.id }}">Read more</a>
    </article>
    {{ endfor }}
</div>
'''
        (templates_dir / "home.html").write_text(home_content)

    def _create_static_dirs(self, theme_dir: Path) -> None:
        """Create static asset directories."""
        static_dir = theme_dir / "static"
        static_dir.mkdir()
        
        # Create CSS directory with example file
        css_dir = static_dir / "css"
        css_dir.mkdir()
        
        css_content = '''/* Theme Styles */

:root {
    --primary-color: #007bff;
    --font-family: Arial, sans-serif;
}

body {
    font-family: var(--font-family);
    margin: 0;
    padding: 0;
    line-height: 1.6;
}

header {
    background-color: var(--primary-color);
    color: white;
    padding: 1rem;
}

main {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

footer {
    background-color: #333;
    color: white;
    text-align: center;
    padding: 1rem;
    margin-top: 2rem;
}
'''
        (css_dir / "style.css").write_text(css_content)
        
        # Create JS and images directories
        (static_dir / "js").mkdir()
        (static_dir / "images").mkdir()

    def _create_readme(
        self, theme_dir: Path, name: str, display_name: str
    ) -> None:
        """Create README.md file."""
        content = f'''# {display_name} Theme

A custom theme for MyCMS.

## Installation

1. Copy this theme to your `themes/{name}` directory
2. Activate the theme in the admin interface

## Customization

### Colors

Edit `theme.json` to change theme colors:

```json
{{
  "settings": {{
    "primary_color": "#your-color",
    "font_family": "Your Font"
  }}
}}
```

### Templates

Templates are in the `templates/` directory:
- `base.html` - Base template
- `home.html` - Homepage template

### Styles

CSS files are in `static/css/`:
- `style.css` - Main stylesheet

## Development

To develop this theme:

1. Make changes to templates and static files
2. Refresh your browser to see changes
3. Use the live reload server for automatic updates

## License

[Add your license here]
'''
        (theme_dir / "README.md").write_text(content)


class ContentTypeScaffolder:
    """Scaffolds new content type structures."""

    def __init__(self, base_dir: str = ".") -> None:
        """Initialize content type scaffolder.
        
        Args:
            base_dir: Base directory for content type creation
        """
        self.base_dir = Path(base_dir)

    def create_content_type(
        self,
        name: str,
        fields: Optional[Dict[str, str]] = None,
    ) -> Path:
        """Create a new content type.
        
        Args:
            name: Content type name
            fields: Dictionary of field_name: field_type
            
        Returns:
            Path to created file
        """
        # Validate name
        Validator.validate_name(name)
        
        # Default fields if none provided
        if fields is None:
            fields = {
                "title": "CharField",
                "content": "TextField",
                "published": "BooleanField",
            }
        
        # Create content types directory if needed
        content_dir = self.base_dir / "content" / "types"
        content_dir.mkdir(parents=True, exist_ok=True)
        
        # Create content type file
        file_path = content_dir / f"{name}.py"
        if file_path.exists():
            raise CLIError(f"Content type already exists: {file_path}")
        
        class_name = "".join(word.capitalize() for word in name.split("_"))
        
        # Generate field definitions
        field_defs = []
        for field_name, field_type in fields.items():
            field_defs.append(f"    {field_name} = {field_type}()")
        
        content = f'''"""Custom content type: {class_name}."""

from mycms.content.custom_post_types import CustomPostType
from mycms.content.custom_fields import (
    CharField,
    TextField,
    BooleanField,
    DateTimeField,
    IntegerField,
)


class {class_name}(CustomPostType):
    """
    {class_name} content type.
    
    Custom content type for managing {name.replace("_", " ")} content.
    """
    
    # Define fields
{chr(10).join(field_defs)}
    
    class Meta:
        """Meta information for this content type."""
        
        verbose_name = "{name.replace("_", " ").title()}"
        verbose_name_plural = "{name.replace("_", " ").title()}s"
        supports = ["editor", "thumbnail", "author", "comments"]
        
    def get_absolute_url(self) -> str:
        """Get the URL for this content item.
        
        Returns:
            URL path
        """
        return f"/{name}/{{self.id}}/"
    
    def save(self) -> None:
        """Custom save logic."""
        # Add any pre-save logic here
        super().save()
        # Add any post-save logic here
'''
        
        file_path.write_text(content)
        return file_path


class CLI:
    """Main CLI interface for MyCMS development tools."""

    def __init__(self) -> None:
        """Initialize CLI."""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description="MyCMS Development CLI",
            prog="mycms",
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Command to run")
        
        # Plugin command
        plugin_parser = subparsers.add_parser(
            "create-plugin",
            help="Create a new plugin",
        )
        plugin_parser.add_argument("name", help="Plugin name (snake_case)")
        plugin_parser.add_argument(
            "--display-name",
            help="Human-readable name",
        )
        plugin_parser.add_argument(
            "--description",
            default="",
            help="Plugin description",
        )
        plugin_parser.add_argument(
            "--author",
            default="",
            help="Plugin author",
        )
        
        # Theme command
        theme_parser = subparsers.add_parser(
            "create-theme",
            help="Create a new theme",
        )
        theme_parser.add_argument("name", help="Theme name (snake_case)")
        theme_parser.add_argument(
            "--display-name",
            help="Human-readable name",
        )
        theme_parser.add_argument(
            "--author",
            default="",
            help="Theme author",
        )
        
        # Content type command
        content_parser = subparsers.add_parser(
            "create-content-type",
            help="Create a new content type",
        )
        content_parser.add_argument("name", help="Content type name (snake_case)")
        
        return parser

    def run(self, args: Optional[list[str]] = None) -> int:
        """Run CLI.
        
        Args:
            args: Command line arguments (defaults to sys.argv)
            
        Returns:
            Exit code
        """
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return 0
        
        try:
            if parsed_args.command == "create-plugin":
                self._create_plugin(parsed_args)
            elif parsed_args.command == "create-theme":
                self._create_theme(parsed_args)
            elif parsed_args.command == "create-content-type":
                self._create_content_type(parsed_args)
            
            return 0
            
        except CLIError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1

    def _create_plugin(self, args: argparse.Namespace) -> None:
        """Create plugin command."""
        scaffolder = PluginScaffolder()
        plugin_dir = scaffolder.create_plugin(
            name=args.name,
            display_name=args.display_name,
            description=args.description,
            author=args.author,
        )
        print(f"✓ Created plugin: {plugin_dir}")
        print(f"  Next steps:")
        print(f"    1. cd {plugin_dir}")
        print(f"    2. Edit plugin.py to add your functionality")
        print(f"    3. Run tests: pytest tests/")

    def _create_theme(self, args: argparse.Namespace) -> None:
        """Create theme command."""
        scaffolder = ThemeScaffolder()
        theme_dir = scaffolder.create_theme(
            name=args.name,
            display_name=args.display_name,
            author=args.author,
        )
        print(f"✓ Created theme: {theme_dir}")
        print(f"  Next steps:")
        print(f"    1. cd {theme_dir}")
        print(f"    2. Edit templates and static files")
        print(f"    3. Activate theme in admin interface")

    def _create_content_type(self, args: argparse.Namespace) -> None:
        """Create content type command."""
        scaffolder = ContentTypeScaffolder()
        file_path = scaffolder.create_content_type(name=args.name)
        print(f"✓ Created content type: {file_path}")
        print(f"  Next steps:")
        print(f"    1. Edit {file_path} to customize fields")
        print(f"    2. Register content type in your application")


def main() -> int:
    """Main entry point for CLI."""
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
