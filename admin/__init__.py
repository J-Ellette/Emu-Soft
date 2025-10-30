"""Admin interface package for a CMS.

This package provides a web-based admin interface for managing
CMS data and models, similar to Django admin but completely custom-built.
"""

from mycms.admin.interface import AdminSite, ModelAdmin
from mycms.admin.forms import Form, Field
from mycms.admin.dashboard import Dashboard
from mycms.admin.config_manager import ConfigurationManager, config_manager

__all__ = [
    "AdminSite",
    "ModelAdmin",
    "Form",
    "Field",
    "Dashboard",
    "ConfigurationManager",
    "config_manager",
]
