"""Configuration management for the admin interface.

This module provides a system for managing site-wide configuration
settings through the admin interface.
"""

from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import json


class ConfigType(str, Enum):
    """Configuration value types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"


class ConfigCategory(str, Enum):
    """Configuration categories."""

    GENERAL = "general"
    APPEARANCE = "appearance"
    SECURITY = "security"
    PERFORMANCE = "performance"
    EMAIL = "email"
    CACHE = "cache"
    MEDIA = "media"
    CUSTOM = "custom"


class ConfigSetting:
    """Represents a single configuration setting."""

    def __init__(
        self,
        key: str,
        label: str,
        value: Any,
        config_type: ConfigType = ConfigType.STRING,
        category: ConfigCategory = ConfigCategory.GENERAL,
        description: str = "",
        default: Any = None,
        required: bool = False,
        editable: bool = True,
        choices: Optional[List[Any]] = None,
        validation_func: Optional[Callable] = None,
    ) -> None:
        """Initialize a configuration setting.

        Args:
            key: Unique setting key
            label: Human-readable label
            value: Current value
            config_type: Type of the configuration value
            category: Setting category
            description: Description of the setting
            default: Default value
            required: Whether the setting is required
            editable: Whether the setting can be edited
            choices: List of valid choices (for select fields)
            validation_func: Optional custom validation function
        """
        self.key = key
        self.label = label
        self.value = value
        self.config_type = config_type
        self.category = category
        self.description = description
        self.default = default if default is not None else value
        self.required = required
        self.editable = editable
        self.choices = choices
        self.validation_func = validation_func

    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a value for this setting.

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required
        if self.required and (value is None or value == ""):
            return False, f"{self.label} is required"

        # Type validation
        try:
            if self.config_type == ConfigType.INTEGER:
                int(value)
            elif self.config_type == ConfigType.FLOAT:
                float(value)
            elif self.config_type == ConfigType.BOOLEAN:
                if not isinstance(value, bool):
                    if value not in ["true", "false", "1", "0", True, False]:
                        return False, f"{self.label} must be a boolean value"
            elif self.config_type == ConfigType.JSON:
                if isinstance(value, str):
                    json.loads(value)
            elif self.config_type == ConfigType.LIST:
                if not isinstance(value, (list, tuple)):
                    if isinstance(value, str):
                        # Try to parse as JSON
                        json.loads(value)
        except (ValueError, json.JSONDecodeError) as e:
            return False, f"{self.label} has invalid format: {str(e)}"

        # Check choices
        if self.choices and value not in self.choices:
            return False, f"{self.label} must be one of: {', '.join(map(str, self.choices))}"

        # Custom validation
        if self.validation_func:
            try:
                result = self.validation_func(value)
                if isinstance(result, tuple):
                    return result
                elif result is False:
                    return False, f"{self.label} failed custom validation"
            except Exception as e:
                return False, f"{self.label} validation error: {str(e)}"

        return True, None

    def format_value(self, value: Any) -> Any:
        """Format a value according to the setting type.

        Args:
            value: Value to format

        Returns:
            Formatted value
        """
        if self.config_type == ConfigType.INTEGER:
            return int(value)
        elif self.config_type == ConfigType.FLOAT:
            return float(value)
        elif self.config_type == ConfigType.BOOLEAN:
            if isinstance(value, bool):
                return value
            return value in ["true", "1", True]
        elif self.config_type == ConfigType.JSON:
            if isinstance(value, str):
                return json.loads(value)
            return value
        elif self.config_type == ConfigType.LIST:
            if isinstance(value, str):
                return json.loads(value)
            return value
        return str(value)


class ConfigurationManager:
    """Manages site-wide configuration settings."""

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._settings: Dict[str, ConfigSetting] = {}
        self._load_default_settings()

    def _load_default_settings(self) -> None:
        """Load default configuration settings."""
        # General settings
        self.register_setting(
            ConfigSetting(
                key="site_name",
                label="Site Name",
                value="MyCMS",
                category=ConfigCategory.GENERAL,
                description="The name of your website",
                required=True,
            )
        )

        self.register_setting(
            ConfigSetting(
                key="site_description",
                label="Site Description",
                value="A homegrown CMS",
                category=ConfigCategory.GENERAL,
                description="A brief description of your website",
            )
        )

        self.register_setting(
            ConfigSetting(
                key="items_per_page",
                label="Items Per Page",
                value=25,
                config_type=ConfigType.INTEGER,
                category=ConfigCategory.GENERAL,
                description="Default number of items to display per page",
            )
        )

        # Appearance settings
        self.register_setting(
            ConfigSetting(
                key="theme",
                label="Theme",
                value="default",
                category=ConfigCategory.APPEARANCE,
                description="Site theme",
                choices=["default", "dark", "light"],
            )
        )

        self.register_setting(
            ConfigSetting(
                key="date_format",
                label="Date Format",
                value="%Y-%m-%d",
                category=ConfigCategory.APPEARANCE,
                description="Format for displaying dates",
            )
        )

        # Security settings
        self.register_setting(
            ConfigSetting(
                key="session_timeout",
                label="Session Timeout",
                value=3600,
                config_type=ConfigType.INTEGER,
                category=ConfigCategory.SECURITY,
                description="Session timeout in seconds",
            )
        )

        self.register_setting(
            ConfigSetting(
                key="password_min_length",
                label="Minimum Password Length",
                value=8,
                config_type=ConfigType.INTEGER,
                category=ConfigCategory.SECURITY,
                description="Minimum required password length",
            )
        )

        # Performance settings
        self.register_setting(
            ConfigSetting(
                key="cache_enabled",
                label="Enable Caching",
                value=True,
                config_type=ConfigType.BOOLEAN,
                category=ConfigCategory.PERFORMANCE,
                description="Enable site-wide caching",
            )
        )

        self.register_setting(
            ConfigSetting(
                key="cache_timeout",
                label="Default Cache Timeout",
                value=300,
                config_type=ConfigType.INTEGER,
                category=ConfigCategory.PERFORMANCE,
                description="Default cache timeout in seconds",
            )
        )

    def register_setting(self, setting: ConfigSetting) -> None:
        """Register a configuration setting.

        Args:
            setting: Configuration setting to register
        """
        self._settings[setting.key] = setting

    def unregister_setting(self, key: str) -> bool:
        """Unregister a configuration setting.

        Args:
            key: Setting key

        Returns:
            True if unregistered, False if not found
        """
        if key in self._settings:
            del self._settings[key]
            return True
        return False

    def get_setting(self, key: str) -> Optional[ConfigSetting]:
        """Get a configuration setting.

        Args:
            key: Setting key

        Returns:
            ConfigSetting or None if not found
        """
        return self._settings.get(key)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        setting = self.get_setting(key)
        if setting:
            return setting.value
        return default

    def set_value(self, key: str, value: Any) -> tuple[bool, Optional[str]]:
        """Set a configuration value.

        Args:
            key: Setting key
            value: New value

        Returns:
            Tuple of (success, error_message)
        """
        setting = self.get_setting(key)
        if not setting:
            return False, f"Setting '{key}' not found"

        if not setting.editable:
            return False, f"Setting '{key}' is not editable"

        # Validate the value
        is_valid, error = setting.validate(value)
        if not is_valid:
            return False, error

        # Format and set the value
        try:
            formatted_value = setting.format_value(value)
            setting.value = formatted_value
            return True, None
        except Exception as e:
            return False, f"Error setting value: {str(e)}"

    def get_all_settings(self) -> List[ConfigSetting]:
        """Get all configuration settings.

        Returns:
            List of all settings
        """
        return list(self._settings.values())

    def get_settings_by_category(self, category: ConfigCategory) -> List[ConfigSetting]:
        """Get settings by category.

        Args:
            category: Category to filter by

        Returns:
            List of settings in the category
        """
        return [s for s in self._settings.values() if s.category == category]

    def get_categories(self) -> List[ConfigCategory]:
        """Get all categories that have settings.

        Returns:
            List of categories with settings
        """
        categories = set()
        for setting in self._settings.values():
            categories.add(setting.category)
        return sorted(list(categories), key=lambda c: c.value)

    def reset_to_default(self, key: str) -> bool:
        """Reset a setting to its default value.

        Args:
            key: Setting key

        Returns:
            True if reset, False if not found
        """
        setting = self.get_setting(key)
        if setting:
            setting.value = setting.default
            return True
        return False

    def export_settings(self) -> Dict[str, Any]:
        """Export all settings as a dictionary.

        Returns:
            Dictionary of setting key to value
        """
        return {key: setting.value for key, setting in self._settings.items()}

    def import_settings(self, settings_dict: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Import settings from a dictionary.

        Args:
            settings_dict: Dictionary of setting key to value

        Returns:
            Dictionary of setting key to error message (empty string if successful)
        """
        results = {}
        for key, value in settings_dict.items():
            success, error = self.set_value(key, value)
            if not success:
                results[key] = error
            else:
                results[key] = None
        return results


# Global configuration manager instance
config_manager = ConfigurationManager()
