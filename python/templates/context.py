"""
Developed by PowerShield, as an alternative to Django Templates
"""

"""Template context management for passing data to templates."""

from typing import Any, Dict, Optional


class Context:
    """Manages template context data with scoping support.

    The Context class provides a dictionary-like interface for storing
    and retrieving template variables with support for nested scopes.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Initialize a context with optional data.

        Args:
            data: Initial context data dictionary
        """
        self._stack: list[Dict[str, Any]] = [data or {}]

    def push(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Push a new scope onto the context stack.

        Args:
            data: Data for the new scope
        """
        self._stack.append(data or {})

    def pop(self) -> Dict[str, Any]:
        """Pop the current scope from the context stack.

        Returns:
            The popped scope data

        Raises:
            IndexError: If trying to pop the last scope
        """
        if len(self._stack) <= 1:
            raise IndexError("Cannot pop the last context scope")
        return self._stack.pop()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context, searching from top to bottom of stack.

        Args:
            key: The variable name to look up
            default: Default value if key is not found

        Returns:
            The value associated with the key, or default if not found
        """
        # Search from top of stack (most recent) to bottom
        for scope in reversed(self._stack):
            if key in scope:
                return scope[key]
        return default

    def set(self, key: str, value: Any) -> None:
        """Set a value in the current scope.

        Args:
            key: The variable name
            value: The value to set
        """
        self._stack[-1][key] = value

    def update(self, data: Dict[str, Any]) -> None:
        """Update the current scope with multiple values.

        Args:
            data: Dictionary of values to add to current scope
        """
        self._stack[-1].update(data)

    def flatten(self) -> Dict[str, Any]:
        """Flatten all scopes into a single dictionary.

        Later scopes override earlier ones.

        Returns:
            A flattened dictionary of all context data
        """
        result = {}
        for scope in self._stack:
            result.update(scope)
        return result

    def __getitem__(self, key: str) -> Any:
        """Get a value using dictionary-style access.

        Args:
            key: The variable name

        Returns:
            The value associated with the key

        Raises:
            KeyError: If key is not found in any scope
        """
        value = self.get(key)
        if value is None and key not in self.flatten():
            raise KeyError(f"Key '{key}' not found in context")
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a value using dictionary-style access.

        Args:
            key: The variable name
            value: The value to set
        """
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in any scope.

        Args:
            key: The variable name

        Returns:
            True if key exists, False otherwise
        """
        return key in self.flatten()

    def __repr__(self) -> str:
        """Return string representation of the context."""
        return f"<Context {self.flatten()}>"
