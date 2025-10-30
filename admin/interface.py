"""Admin interface core logic.

This module provides the core admin interface functionality including
model registration, admin site management, and model admin classes.
"""

from typing import Any, Dict, List, Optional, Type
from database.orm import Model
from admin.forms import ModelForm


class ModelAdmin:
    """Base class for model admin configuration.

    This class defines how a model should be displayed and managed
    in the admin interface.
    """

    # Fields to display in list view
    list_display: List[str] = []

    # Fields to allow searching on
    search_fields: List[str] = []

    # Fields to filter by
    list_filter: List[str] = []

    # Number of items per page
    list_per_page: int = 25

    # Fields to display in the form
    fields: Optional[List[str]] = None

    # Fields to exclude from the form
    exclude: Optional[List[str]] = None

    # Form class to use
    form_class: Optional[Type[ModelForm]] = None

    def __init__(self, model: Type[Model], admin_site: "AdminSite") -> None:
        """Initialize the model admin.

        Args:
            model: Model class to manage
            admin_site: Admin site instance
        """
        self.model = model
        self.admin_site = admin_site

    def get_list_display(self) -> List[str]:
        """Get the list of fields to display in the list view.

        Returns:
            List of field names
        """
        if self.list_display:
            return self.list_display

        # Default to showing all non-relationship fields
        fields = []
        for field_name in self.model._fields.keys():
            fields.append(field_name)
        return fields[:5]  # Limit to first 5 fields by default

    def get_search_fields(self) -> List[str]:
        """Get the list of fields to search on.

        Returns:
            List of field names
        """
        return self.search_fields

    def get_list_filter(self) -> List[str]:
        """Get the list of fields to filter by.

        Returns:
            List of field names
        """
        return self.list_filter

    def get_form_class(self) -> Type[ModelForm]:
        """Get the form class to use for this model.

        Returns:
            Form class
        """
        if self.form_class:
            return self.form_class

        # Create a default ModelForm class
        class DefaultModelForm(ModelForm):
            model = self.model

        return DefaultModelForm

    def get_form_fields(self) -> Optional[List[str]]:
        """Get the list of fields to include in the form.

        Returns:
            List of field names or None for all fields
        """
        if self.fields:
            return self.fields

        # Get all fields except those excluded
        if self.exclude:
            all_fields = list(self.model._fields.keys())
            return [f for f in all_fields if f not in self.exclude]

        return None

    async def get_queryset(
        self, search: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[Model]:
        """Get the queryset for the list view.

        Args:
            search: Search query
            filters: Filter parameters

        Returns:
            List of model instances
        """
        # For now, just return all items
        # In a real implementation, this would filter and search
        instances = await self.model.all()

        # Apply filters if provided
        if filters:
            # Simple exact match filtering
            filtered = []
            for instance in instances:
                match = True
                for field_name, value in filters.items():
                    if hasattr(instance, field_name):
                        if getattr(instance, field_name) != value:
                            match = False
                            break
                if match:
                    filtered.append(instance)
            instances = filtered

        # Apply search if provided
        if search and self.search_fields:
            searched = []
            for instance in instances:
                for field_name in self.search_fields:
                    if hasattr(instance, field_name):
                        value = str(getattr(instance, field_name, "")).lower()
                        if search.lower() in value:
                            searched.append(instance)
                            break
            instances = searched

        return instances

    async def get_object(self, pk: int) -> Optional[Model]:
        """Get a single object by primary key.

        Args:
            pk: Primary key value

        Returns:
            Model instance or None
        """
        pk_field = self._get_primary_key_field()
        return await self.model.get(**{pk_field: pk})

    def _get_primary_key_field(self) -> str:
        """Get the primary key field name.

        Returns:
            Primary key field name
        """
        for field_name, field in self.model._fields.items():
            if field.primary_key:
                return field_name
        return "id"  # Default to 'id'

    def has_add_permission(self) -> bool:
        """Check if the current user can add new objects.

        Returns:
            True if user can add, False otherwise
        """
        return True  # Default to True, override for custom logic

    def has_change_permission(self) -> bool:
        """Check if the current user can change objects.

        Returns:
            True if user can change, False otherwise
        """
        return True  # Default to True, override for custom logic

    def has_delete_permission(self) -> bool:
        """Check if the current user can delete objects.

        Returns:
            True if user can delete, False otherwise
        """
        return True  # Default to True, override for custom logic

    def has_view_permission(self) -> bool:
        """Check if the current user can view objects.

        Returns:
            True if user can view, False otherwise
        """
        return True  # Default to True, override for custom logic


class AdminSite:
    """Main admin site class for managing registered models.

    This class acts as a registry for models and their admin classes,
    and provides methods for generating admin URLs and views.
    """

    def __init__(self, name: str = "admin") -> None:
        """Initialize the admin site.

        Args:
            name: Name of the admin site (used in URLs)
        """
        self.name = name
        self._registry: Dict[Type[Model], ModelAdmin] = {}

    def register(self, model: Type[Model], admin_class: Optional[Type[ModelAdmin]] = None) -> None:
        """Register a model with the admin site.

        Args:
            model: Model class to register
            admin_class: Optional ModelAdmin class (uses default if not provided)
        """
        if admin_class is None:
            admin_class = ModelAdmin

        admin_instance = admin_class(model, self)
        self._registry[model] = admin_instance

    def unregister(self, model: Type[Model]) -> None:
        """Unregister a model from the admin site.

        Args:
            model: Model class to unregister
        """
        if model in self._registry:
            del self._registry[model]

    def is_registered(self, model: Type[Model]) -> bool:
        """Check if a model is registered.

        Args:
            model: Model class to check

        Returns:
            True if registered, False otherwise
        """
        return model in self._registry

    def get_model_admin(self, model: Type[Model]) -> Optional[ModelAdmin]:
        """Get the ModelAdmin instance for a model.

        Args:
            model: Model class

        Returns:
            ModelAdmin instance or None
        """
        return self._registry.get(model)

    def get_registered_models(self) -> List[Type[Model]]:
        """Get list of all registered models.

        Returns:
            List of model classes
        """
        return list(self._registry.keys())

    def get_registry(self) -> Dict[Type[Model], ModelAdmin]:
        """Get the complete registry.

        Returns:
            Dictionary mapping models to their admin instances
        """
        return self._registry.copy()

    def get_model_name(self, model: Type[Model]) -> str:
        """Get a URL-safe name for a model.

        Args:
            model: Model class

        Returns:
            URL-safe model name
        """
        return model.__name__.lower()

    def get_app_list(self) -> List[Dict[str, Any]]:
        """Get list of apps and their models for the dashboard.

        Returns:
            List of app dictionaries
        """
        # For now, treat all models as belonging to one app
        # In the future, this could be enhanced to support multiple apps
        models_info = []
        for model, admin in self._registry.items():
            models_info.append(
                {
                    "name": model.__name__,
                    "url_name": self.get_model_name(model),
                    "admin": admin,
                    "perms": {
                        "add": admin.has_add_permission(),
                        "change": admin.has_change_permission(),
                        "delete": admin.has_delete_permission(),
                        "view": admin.has_view_permission(),
                    },
                }
            )

        return [{"name": "Content", "models": models_info}] if models_info else []


# Global admin site instance
site = AdminSite()
