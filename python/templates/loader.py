"""
Developed by PowerShield, as an alternative to Django Templates
"""

"""Template loader for loading templates from the filesystem."""

from pathlib import Path
from typing import Optional, List


class TemplateLoader:
    """Loads templates from the filesystem.

    The loader searches for templates in configured directories
    and provides caching for loaded templates.
    """

    def __init__(self, template_dirs: Optional[List[str]] = None) -> None:
        """Initialize the template loader.

        Args:
            template_dirs: List of directories to search for templates
        """
        self.template_dirs = [Path(d) for d in (template_dirs or [])]
        self._cache: dict[str, str] = {}

    def add_directory(self, directory: str) -> None:
        """Add a directory to the template search path.

        Args:
            directory: Path to the template directory
        """
        path = Path(directory)
        if path not in self.template_dirs:
            self.template_dirs.append(path)

    def find_template(self, template_name: str) -> Optional[Path]:
        """Find a template file in the configured directories.

        Args:
            template_name: Name of the template file

        Returns:
            Path to the template file, or None if not found
        """
        for directory in self.template_dirs:
            template_path = directory / template_name
            if template_path.exists() and template_path.is_file():
                return template_path
        return None

    def load(self, template_name: str, use_cache: bool = True) -> str:
        """Load a template from the filesystem.

        Args:
            template_name: Name of the template file
            use_cache: Whether to use cached templates (default: True)

        Returns:
            Template content as a string

        Raises:
            FileNotFoundError: If template is not found
        """
        # Check cache first
        if use_cache and template_name in self._cache:
            return self._cache[template_name]

        # Find and load the template
        template_path = self.find_template(template_name)
        if template_path is None:
            raise FileNotFoundError(f"Template not found: {template_name}")

        # Read template content
        content = template_path.read_text(encoding="utf-8")

        # Cache the template
        if use_cache:
            self._cache[template_name] = content

        return content

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._cache.clear()

    def __repr__(self) -> str:
        """Return string representation of the loader."""
        return f"<TemplateLoader dirs={len(self.template_dirs)}>"
