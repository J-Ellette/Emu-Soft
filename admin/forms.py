"""Form handling for admin interface.

This module provides form handling capabilities for the admin interface,
including field validation and data processing.
"""

from typing import Any, Dict, Optional, Type
from mycms.core.database.orm import Model, Field as OrmField


class ValidationError(Exception):
    """Exception raised for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            field: Field name that failed validation
        """
        self.message = message
        self.field = field
        super().__init__(message)


class Field:
    """Base form field class."""

    def __init__(
        self,
        label: Optional[str] = None,
        required: bool = True,
        initial: Any = None,
        help_text: Optional[str] = None,
        widget: Optional[str] = None,
    ) -> None:
        """Initialize a form field.

        Args:
            label: Field label for display
            required: Whether field is required
            initial: Initial/default value
            help_text: Help text for the field
            widget: HTML widget type (input, textarea, select, etc.)
        """
        self.label = label
        self.required = required
        self.initial = initial
        self.help_text = help_text
        self.widget = widget or "input"
        self.name: Optional[str] = None

    def clean(self, value: Any) -> Any:
        """Validate and clean the field value.

        Args:
            value: Raw value to validate

        Returns:
            Cleaned value

        Raises:
            ValidationError: If validation fails
        """
        if self.required and (value is None or value == ""):
            raise ValidationError(f"{self.label or self.name} is required", self.name)
        return value

    def render(self, value: Any = None) -> str:
        """Render the field as HTML.

        Args:
            value: Current field value

        Returns:
            HTML string
        """
        value = value if value is not None else self.initial
        value_attr = f'value="{value}"' if value is not None else ""
        required_attr = "required" if self.required else ""

        if self.widget == "textarea":
            return f'<textarea name="{self.name}" {required_attr}>{value or ""}</textarea>'
        elif self.widget == "checkbox":
            checked = "checked" if value else ""
            return f'<input type="checkbox" name="{self.name}" {checked}>'
        else:
            return f'<input type="text" name="{self.name}" {value_attr} {required_attr}>'


class CharField(Field):
    """Character field for text input."""

    def __init__(
        self, max_length: Optional[int] = None, min_length: Optional[int] = None, **kwargs: Any
    ) -> None:
        """Initialize CharField.

        Args:
            max_length: Maximum length
            min_length: Minimum length
            **kwargs: Additional field options
        """
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length

    def clean(self, value: Any) -> str:
        """Validate and clean the value.

        Args:
            value: Raw value

        Returns:
            Cleaned string value

        Raises:
            ValidationError: If validation fails
        """
        value = super().clean(value)
        if value is None or value == "":
            return value if not self.required else ""

        value = str(value)

        if self.min_length and len(value) < self.min_length:
            raise ValidationError(
                f"{self.label or self.name} must be at least {self.min_length} characters",
                self.name,
            )

        if self.max_length and len(value) > self.max_length:
            raise ValidationError(
                f"{self.label or self.name} must be no more than {self.max_length} characters",
                self.name,
            )

        return value


class IntegerField(Field):
    """Integer field for numeric input."""

    def __init__(
        self, min_value: Optional[int] = None, max_value: Optional[int] = None, **kwargs: Any
    ) -> None:
        """Initialize IntegerField.

        Args:
            min_value: Minimum value
            max_value: Maximum value
            **kwargs: Additional field options
        """
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def clean(self, value: Any) -> Optional[int]:
        """Validate and clean the value.

        Args:
            value: Raw value

        Returns:
            Cleaned integer value

        Raises:
            ValidationError: If validation fails
        """
        value = super().clean(value)
        if value is None or value == "":
            return None if not self.required else value

        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{self.label or self.name} must be a valid integer", self.name)

        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"{self.label or self.name} must be at least {self.min_value}", self.name
            )

        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"{self.label or self.name} must be no more than {self.max_value}", self.name
            )

        return value

    def render(self, value: Any = None) -> str:
        """Render as number input.

        Args:
            value: Current value

        Returns:
            HTML string
        """
        value = value if value is not None else self.initial
        value_attr = f'value="{value}"' if value is not None else ""
        required_attr = "required" if self.required else ""
        return f'<input type="number" name="{self.name}" {value_attr} {required_attr}>'


class BooleanField(Field):
    """Boolean field for checkbox input."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize BooleanField.

        Args:
            **kwargs: Additional field options
        """
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", "checkbox")
        super().__init__(**kwargs)

    def clean(self, value: Any) -> bool:
        """Validate and clean the value.

        Args:
            value: Raw value

        Returns:
            Boolean value
        """
        if value in (True, "True", "true", "1", "on", "yes"):
            return True
        return False


class EmailField(CharField):
    """Email field with email validation."""

    def clean(self, value: Any) -> str:
        """Validate and clean email.

        Args:
            value: Raw value

        Returns:
            Cleaned email string

        Raises:
            ValidationError: If validation fails
        """
        value = super().clean(value)
        if value and "@" not in value:
            raise ValidationError(
                f"{self.label or self.name} must be a valid email address", self.name
            )
        return value


class PasswordField(CharField):
    """Password field with masked input."""

    def render(self, value: Any = None) -> str:
        """Render as password input.

        Args:
            value: Current value (ignored for security)

        Returns:
            HTML string
        """
        required_attr = "required" if self.required else ""
        return f'<input type="password" name="{self.name}" {required_attr}>'


class TextAreaField(CharField):
    """Text area field for long text input."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize TextAreaField.

        Args:
            **kwargs: Additional field options
        """
        kwargs.setdefault("widget", "textarea")
        super().__init__(**kwargs)


class Form:
    """Base form class for handling user input."""

    def __init__(
        self, data: Optional[Dict[str, Any]] = None, instance: Optional[Model] = None
    ) -> None:
        """Initialize form.

        Args:
            data: Form data from request
            instance: Model instance to populate form with
        """
        self.data = data or {}
        self.instance = instance
        self.errors: Dict[str, str] = {}
        self.cleaned_data: Dict[str, Any] = {}

        # Collect fields from class
        self._fields: Dict[str, Field] = {}
        for name in dir(self.__class__):
            attr = getattr(self.__class__, name)
            if isinstance(attr, Field):
                field = attr
                field.name = name
                self._fields[name] = field

    def is_valid(self) -> bool:
        """Validate all fields.

        Returns:
            True if all fields are valid, False otherwise
        """
        self.errors.clear()
        self.cleaned_data.clear()

        for field_name, field in self._fields.items():
            value = self.data.get(field_name)
            try:
                cleaned_value = field.clean(value)
                self.cleaned_data[field_name] = cleaned_value
            except ValidationError as e:
                self.errors[field_name] = e.message

        return len(self.errors) == 0

    def save(self) -> Optional[Model]:
        """Save the form data to the model instance.

        Returns:
            Saved model instance or None if no instance
        """
        if not self.is_valid():
            raise ValueError("Cannot save invalid form")

        if self.instance:
            for field_name, value in self.cleaned_data.items():
                if hasattr(self.instance, field_name):
                    setattr(self.instance, field_name, value)
            return self.instance

        return None

    def render(self) -> str:
        """Render the form as HTML.

        Returns:
            HTML string with all fields
        """
        html_parts = []
        for field_name, field in self._fields.items():
            error = self.errors.get(field_name, "")
            error_html = f'<div class="error">{error}</div>' if error else ""

            # Get current value
            if self.instance and hasattr(self.instance, field_name):
                value = getattr(self.instance, field_name)
            else:
                value = self.data.get(field_name)

            field_html = f"""
            <div class="form-field">
                <label for="{field_name}">{field.label or field_name}:</label>
                {field.render(value)}
                {error_html}
                {f'<div class="help-text">{field.help_text}</div>' if field.help_text else ''}
            </div>
            """
            html_parts.append(field_html)

        return "\n".join(html_parts)


class ModelForm(Form):
    """Form class that automatically generates fields from a model."""

    model: Optional[Type[Model]] = None

    def __init__(
        self, data: Optional[Dict[str, Any]] = None, instance: Optional[Model] = None
    ) -> None:
        """Initialize model form.

        Args:
            data: Form data from request
            instance: Model instance to populate form with
        """
        super().__init__(data, instance)

        # Auto-generate fields from model if not already defined
        if self.model and not self._fields:
            self._generate_fields_from_model()

    def _generate_fields_from_model(self) -> None:
        """Generate form fields from model definition."""
        if not self.model:
            return

        for field_name, orm_field in self.model._fields.items():
            # Skip primary key fields
            if orm_field.primary_key:
                continue

            # Create appropriate form field based on ORM field type
            form_field = self._create_form_field(orm_field)
            form_field.name = field_name
            self._fields[field_name] = form_field

    def _create_form_field(self, orm_field: OrmField) -> Field:
        """Create a form field from an ORM field.

        Args:
            orm_field: ORM field instance

        Returns:
            Form field instance
        """
        from mycms.core.database.orm import CharField as OrmCharField
        from mycms.core.database.orm import IntegerField as OrmIntField
        from mycms.core.database.orm import BooleanField as OrmBoolField
        from mycms.core.database.orm import TextField as OrmTextField

        required = not orm_field.null

        if isinstance(orm_field, OrmCharField):
            return CharField(required=required)
        elif isinstance(orm_field, OrmIntField):
            return IntegerField(required=required)
        elif isinstance(orm_field, OrmBoolField):
            return BooleanField(required=required)
        elif isinstance(orm_field, OrmTextField):
            return TextAreaField(required=required)
        else:
            return Field(required=required)

    async def save(self) -> Model:
        """Save the form data to the model instance.

        Returns:
            Saved model instance

        Raises:
            ValueError: If form is invalid or no instance
        """
        if not self.is_valid():
            raise ValueError("Cannot save invalid form")

        if not self.instance and self.model:
            self.instance = self.model()

        if self.instance:
            for field_name, value in self.cleaned_data.items():
                if hasattr(self.instance, field_name):
                    setattr(self.instance, field_name, value)
            await self.instance.save()
            return self.instance

        raise ValueError("No model instance to save")
