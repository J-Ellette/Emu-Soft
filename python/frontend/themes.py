"""
Developed by PowerShield, as an alternative to Django Frontend
"""

"""Theme management system for MyCMS.

Provides functionality to manage and switch between different visual themes
for the frontend presentation layer.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class Theme:
    """Represents a single theme with its configuration and assets.

    A theme consists of:
    - Template files (HTML)
    - Static assets (CSS, JS, images)
    - Configuration metadata (theme.json)
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        description: str,
        template_dir: str,
        static_dir: Optional[str] = None,
        author: Optional[str] = None,
        version: str = "1.0.0",
        responsive: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize a theme.

        Args:
            name: Internal theme identifier (e.g., 'default')
            display_name: Human-readable theme name
            description: Theme description
            template_dir: Path to theme templates directory
            static_dir: Optional path to static assets
            author: Theme author name
            version: Theme version
            responsive: Whether theme supports responsive design
            **kwargs: Additional theme metadata
        """
        self.name = name
        self.display_name = display_name
        self.description = description
        self.template_dir = template_dir
        self.static_dir = static_dir
        self.author = author
        self.version = version
        self.responsive = responsive
        self.metadata = kwargs

    def get_template_path(self, template_name: str) -> str:
        """Get full path to a template file.

        Args:
            template_name: Name of the template file

        Returns:
            Full path to the template file
        """
        return os.path.join(self.template_dir, template_name)

    def template_exists(self, template_name: str) -> bool:
        """Check if a template file exists in this theme.

        Args:
            template_name: Name of the template file

        Returns:
            True if template exists, False otherwise
        """
        return os.path.exists(self.get_template_path(template_name))

    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary representation.

        Returns:
            Dictionary with theme information
        """
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "template_dir": self.template_dir,
            "static_dir": self.static_dir,
            "author": self.author,
            "version": self.version,
            "responsive": self.responsive,
            **self.metadata,
        }


class ThemeManager:
    """Manages themes and theme switching for the CMS.

    Handles theme registration, activation, and discovery.
    """

    def __init__(self, themes_base_dir: Optional[str] = None) -> None:
        """Initialize the theme manager.

        Args:
            themes_base_dir: Base directory for themes (e.g., 'frontend/themes')
        """
        self.themes: Dict[str, Theme] = {}
        self.active_theme: Optional[str] = None
        self.themes_base_dir = themes_base_dir

        # Register default theme
        self._register_default_theme()

    def _register_default_theme(self) -> None:
        """Register the default theme that ships with MyCMS."""
        default_theme = Theme(
            name="default",
            display_name="MyCMS Default",
            description="The default theme for MyCMS with clean, modern design",
            template_dir="frontend/templates",
            author="MyCMS Team",
            version="1.0.0",
            responsive=True,
        )
        self.register_theme(default_theme)
        self.activate_theme("default")

    def register_theme(self, theme: Theme) -> None:
        """Register a theme with the manager.

        Args:
            theme: Theme instance to register
        """
        self.themes[theme.name] = theme

    def register_theme_from_config(self, config_path: str) -> None:
        """Register a theme from a theme.json configuration file.

        Args:
            config_path: Path to theme.json configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Theme config not found: {config_path}")

        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            # Get theme directory from config path
            theme_dir = os.path.dirname(config_path)

            # Create theme instance
            theme = Theme(
                name=config["name"],
                display_name=config.get("display_name", config["name"]),
                description=config.get("description", ""),
                template_dir=os.path.join(theme_dir, config.get("template_dir", "templates")),
                static_dir=(
                    os.path.join(theme_dir, config.get("static_dir", "static"))
                    if config.get("static_dir")
                    else None
                ),
                author=config.get("author"),
                version=config.get("version", "1.0.0"),
                responsive=config.get("responsive", True),
                **{
                    k: v
                    for k, v in config.items()
                    if k
                    not in [
                        "name",
                        "display_name",
                        "description",
                        "template_dir",
                        "static_dir",
                        "author",
                        "version",
                        "responsive",
                    ]
                },
            )

            self.register_theme(theme)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid theme config JSON: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required theme config field: {e}")

    def discover_themes(self) -> int:
        """Discover and register themes from the themes base directory.

        Returns:
            Number of themes discovered and registered
        """
        if not self.themes_base_dir or not os.path.exists(self.themes_base_dir):
            return 0

        count = 0
        themes_path = Path(self.themes_base_dir)

        # Look for theme.json in subdirectories
        for theme_dir in themes_path.iterdir():
            if theme_dir.is_dir():
                config_file = theme_dir / "theme.json"
                if config_file.exists():
                    try:
                        self.register_theme_from_config(str(config_file))
                        count += 1
                    except (ValueError, FileNotFoundError) as e:
                        # Log error but continue discovering
                        print(f"Error loading theme from {theme_dir}: {e}")

        return count

    def activate_theme(self, theme_name: str) -> bool:
        """Activate a theme by name.

        Args:
            theme_name: Name of the theme to activate

        Returns:
            True if theme was activated, False if theme not found
        """
        if theme_name in self.themes:
            self.active_theme = theme_name
            return True
        return False

    def get_active_theme(self) -> Optional[Theme]:
        """Get the currently active theme.

        Returns:
            Active theme instance, or None if no theme is active
        """
        if self.active_theme:
            return self.themes.get(self.active_theme)
        return None

    def get_theme(self, theme_name: str) -> Optional[Theme]:
        """Get a theme by name.

        Args:
            theme_name: Name of the theme

        Returns:
            Theme instance, or None if not found
        """
        return self.themes.get(theme_name)

    def list_themes(self) -> List[Theme]:
        """Get list of all registered themes.

        Returns:
            List of theme instances
        """
        return list(self.themes.values())

    def get_theme_template_dirs(self, theme_name: Optional[str] = None) -> List[str]:
        """Get template directories for a theme (includes fallback to default).

        Args:
            theme_name: Name of theme, or None for active theme

        Returns:
            List of template directories (theme dir, then default)
        """
        dirs = []

        # Get requested or active theme
        if theme_name:
            theme = self.get_theme(theme_name)
        else:
            theme = self.get_active_theme()

        if theme:
            dirs.append(theme.template_dir)

        # Add default theme as fallback if it's not the active theme
        default_theme = self.get_theme("default")
        if default_theme and (not theme or theme.name != "default"):
            dirs.append(default_theme.template_dir)

        return dirs


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance.

    Returns:
        Global ThemeManager instance
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def set_theme_manager(manager: ThemeManager) -> None:
    """Set the global theme manager instance.

    Args:
        manager: ThemeManager instance to set as global
    """
    global _theme_manager
    _theme_manager = manager
