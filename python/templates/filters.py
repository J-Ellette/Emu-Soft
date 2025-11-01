"""
Developed by PowerShield, as an alternative to Django Templates
"""

"""Template filters for transforming values in templates."""

import html
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from urllib.parse import quote


class TemplateFilters:
    """Collection of template filters for data transformation.

    Filters can be used in templates to modify variable output.
    Example: {{ variable|escape }} or {{ date|date_format:"Y-m-d" }}
    """

    def __init__(self) -> None:
        """Initialize the filter collection."""
        self._filters: Dict[str, Callable] = {
            "escape": self.escape,
            "safe": self.safe,
            "upper": self.upper,
            "lower": self.lower,
            "title": self.title,
            "capitalize": self.capitalize,
            "length": self.length,
            "default": self.default,
            "date_format": self.date_format,
            "truncate": self.truncate,
            "urlencode": self.urlencode,
            "join": self.join,
            "first": self.first,
            "last": self.last,
            "striptags": self.striptags,
        }

    def register(self, name: str, func: Callable) -> None:
        """Register a custom filter.

        Args:
            name: Name of the filter
            func: Filter function that takes a value and optional args
        """
        self._filters[name] = func

    def get_filter(self, name: str) -> Optional[Callable]:
        """Get a filter by name.

        Args:
            name: Name of the filter

        Returns:
            The filter function, or None if not found
        """
        return self._filters.get(name)

    def apply(self, value: Any, filter_name: str, *args: Any, **kwargs: Any) -> Any:
        """Apply a filter to a value.

        Args:
            value: The value to filter
            filter_name: Name of the filter
            *args: Positional arguments for the filter
            **kwargs: Keyword arguments for the filter

        Returns:
            The filtered value

        Raises:
            ValueError: If filter is not found
        """
        filter_func = self.get_filter(filter_name)
        if filter_func is None:
            raise ValueError(f"Unknown filter: {filter_name}")
        return filter_func(value, *args, **kwargs)

    @staticmethod
    def escape(value: Any) -> str:
        """Escape HTML special characters.

        Args:
            value: Value to escape

        Returns:
            HTML-escaped string
        """
        return html.escape(str(value))

    @staticmethod
    def safe(value: Any) -> str:
        """Mark a string as safe (don't escape).

        Args:
            value: Value to mark as safe

        Returns:
            The value as a string (unescaped)
        """
        return str(value)

    @staticmethod
    def upper(value: Any) -> str:
        """Convert string to uppercase.

        Args:
            value: Value to convert

        Returns:
            Uppercase string
        """
        return str(value).upper()

    @staticmethod
    def lower(value: Any) -> str:
        """Convert string to lowercase.

        Args:
            value: Value to convert

        Returns:
            Lowercase string
        """
        return str(value).lower()

    @staticmethod
    def title(value: Any) -> str:
        """Convert string to title case.

        Args:
            value: Value to convert

        Returns:
            Title case string
        """
        return str(value).title()

    @staticmethod
    def capitalize(value: Any) -> str:
        """Capitalize the first character of a string.

        Args:
            value: Value to capitalize

        Returns:
            Capitalized string
        """
        return str(value).capitalize()

    @staticmethod
    def length(value: Any) -> int:
        """Get the length of a value.

        Args:
            value: Value to get length of

        Returns:
            Length of the value
        """
        try:
            return len(value)
        except TypeError:
            return 0

    @staticmethod
    def default(value: Any, default_value: Any = "") -> Any:
        """Return a default value if the value is empty or None.

        Args:
            value: Value to check
            default_value: Default value to return

        Returns:
            The value or the default
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return default_value
        return value

    @staticmethod
    def date_format(value: Any, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format a datetime object.

        Args:
            value: Datetime object or string
            format_string: Format string (default: "%Y-%m-%d %H:%M:%S")

        Returns:
            Formatted date string
        """
        if isinstance(value, datetime):
            return value.strftime(format_string)
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.strftime(format_string)
            except (ValueError, AttributeError):
                return str(value)
        return str(value)

    @staticmethod
    def truncate(value: Any, length: int = 100, suffix: str = "...") -> str:
        """Truncate a string to a maximum length.

        Args:
            value: Value to truncate
            length: Maximum length (default: 100)
            suffix: Suffix to add if truncated (default: "...")

        Returns:
            Truncated string
        """
        text = str(value)
        if len(text) <= length:
            return text
        return text[: length - len(suffix)] + suffix

    @staticmethod
    def urlencode(value: Any) -> str:
        """URL-encode a string.

        Args:
            value: Value to encode

        Returns:
            URL-encoded string
        """
        return quote(str(value))

    @staticmethod
    def join(value: Any, separator: str = ", ") -> str:
        """Join a list of values with a separator.

        Args:
            value: List of values to join
            separator: Separator string (default: ", ")

        Returns:
            Joined string
        """
        if isinstance(value, (list, tuple)):
            return separator.join(str(v) for v in value)
        return str(value)

    @staticmethod
    def first(value: Any) -> Any:
        """Get the first item from a list.

        Args:
            value: List or iterable

        Returns:
            First item, or empty string if not available
        """
        try:
            if isinstance(value, (list, tuple)) and value:
                return value[0]
        except (IndexError, TypeError):
            pass
        return ""

    @staticmethod
    def last(value: Any) -> Any:
        """Get the last item from a list.

        Args:
            value: List or iterable

        Returns:
            Last item, or empty string if not available
        """
        try:
            if isinstance(value, (list, tuple)) and value:
                return value[-1]
        except (IndexError, TypeError):
            pass
        return ""

    @staticmethod
    def striptags(value: Any) -> str:
        """Remove HTML tags from a string (basic implementation).

        Args:
            value: Value with HTML tags

        Returns:
            String with HTML tags removed
        """
        import re

        text = str(value)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        return text
