"""
Developed by PowerShield, as an alternative to Django REST Framework
"""

"""Enhanced serialization for API responses."""

import json
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime, date
from database.orm import Model


class APISerializer:
    """Base API serializer for converting data to/from JSON."""

    # Fields to include in serialization (None means all fields)
    fields: Optional[List[str]] = None
    # Fields to exclude from serialization
    exclude: Optional[List[str]] = None
    # Read-only fields (not used during deserialization)
    read_only_fields: Optional[List[str]] = None

    def __init__(
        self,
        instance: Optional[Any] = None,
        data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        many: bool = False,
    ) -> None:
        """Initialize the serializer.

        Args:
            instance: Object instance(s) to serialize
            data: Data to deserialize
            many: Whether to handle multiple instances
        """
        self.instance = instance
        self.data = data
        self.many = many
        self._validated_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
        self._errors: Dict[str, List[str]] = {}

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        """Convert an instance to a dictionary representation.

        Args:
            instance: Object to serialize

        Returns:
            Dictionary representation
        """
        result: Dict[str, Any] = {}

        # Get fields to serialize
        if hasattr(instance, "__dict__"):
            fields = self._get_field_names(instance)

            for field_name in fields:
                value = getattr(instance, field_name, None)
                result[field_name] = self._serialize_value(value)

        return result

    def _get_field_names(self, instance: Any) -> List[str]:
        """Get list of field names to serialize.

        Args:
            instance: Object instance

        Returns:
            List of field names
        """
        if hasattr(instance, "_fields"):
            all_fields = list(instance._fields)
        else:
            all_fields = [key for key in instance.__dict__.keys() if not key.startswith("_")]

        # Apply fields filter
        if self.fields:
            all_fields = [f for f in all_fields if f in self.fields]

        # Apply exclude filter
        if self.exclude:
            all_fields = [f for f in all_fields if f not in self.exclude]

        return all_fields

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a single value.

        Args:
            value: Value to serialize

        Returns:
            Serialized value
        """
        if value is None:
            return None
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif hasattr(value, "__dict__"):
            # Nested object
            return self.to_representation(value)
        else:
            return value

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            JSON string representation
        """
        if self.many and isinstance(self.instance, (list, tuple)):
            data = [self.to_representation(item) for item in self.instance]
        elif self.instance:
            data = self.to_representation(self.instance)
        else:
            data = {}

        return json.dumps(data, default=str)

    def to_dict(self) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        if self.many and isinstance(self.instance, (list, tuple)):
            return [self.to_representation(item) for item in self.instance]
        elif self.instance:
            return self.to_representation(self.instance)
        else:
            return {}

    def validate(self) -> bool:
        """Validate input data.

        Returns:
            True if valid, False otherwise
        """
        if not self.data:
            self._errors["data"] = ["No data provided"]
            return False

        self._errors = {}

        if self.many and isinstance(self.data, list):
            validated_items: List[Dict[str, Any]] = []
            for idx, item in enumerate(self.data):
                if self._validate_item(item):
                    validated_items.append(item)
                else:
                    self._errors[f"item_{idx}"] = ["Validation failed"]
            self._validated_data = validated_items
        else:
            if self._validate_item(self.data):  # type: ignore[arg-type]
                self._validated_data = self.data
            else:
                return False

        return len(self._errors) == 0

    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate a single item.

        Args:
            item: Item to validate

        Returns:
            True if valid
        """
        # Basic validation - can be overridden in subclasses
        if not isinstance(item, dict):
            return False
        return True

    @property
    def validated_data(self) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """Get validated data.

        Returns:
            Validated data or None
        """
        return self._validated_data

    @property
    def errors(self) -> Dict[str, List[str]]:
        """Get validation errors.

        Returns:
            Dictionary of errors
        """
        return self._errors


class ModelSerializer(APISerializer):
    """Serializer specifically for ORM Model instances."""

    model_class: Optional[Type[Model]] = None

    def to_representation(self, instance: Model) -> Dict[str, Any]:
        """Convert Model instance to dictionary.

        Args:
            instance: Model instance

        Returns:
            Dictionary representation
        """
        result: Dict[str, Any] = {}

        fields = self._get_field_names(instance)

        for field_name in fields:
            value = getattr(instance, field_name, None)
            result[field_name] = self._serialize_value(value)

        return result

    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate item against model fields.

        Args:
            item: Item to validate

        Returns:
            True if valid
        """
        if not super()._validate_item(item):
            return False

        # Can add model-specific validation here
        return True

    async def save(self) -> Optional[Union[Model, List[Model]]]:
        """Save validated data to database.

        Returns:
            Saved model instance(s) or None
        """
        if not self.validate():
            return None

        if not self.model_class:
            raise ValueError("model_class must be specified")

        if self.many and isinstance(self._validated_data, list):
            instances = []
            for item_data in self._validated_data:
                instance = await self._save_instance(item_data)
                if instance:
                    instances.append(instance)
            return instances
        elif self._validated_data:
            return await self._save_instance(self._validated_data)  # type: ignore[arg-type]

        return None

    async def _save_instance(self, data: Dict[str, Any]) -> Optional[Model]:
        """Save a single instance.

        Args:
            data: Data to save

        Returns:
            Saved model instance
        """
        if self.instance:
            # Update existing
            for key, value in data.items():
                if hasattr(self.instance, key):
                    if not self.read_only_fields or key not in self.read_only_fields:
                        setattr(self.instance, key, value)
            await self.instance.save()
            return self.instance
        else:
            # Create new - requires model_class
            if not self.model_class:
                return None
            instance = self.model_class(**data)
            await instance.save()
            return instance


def serialize(
    instance: Any,
    fields: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Convenience function to serialize an instance.

    Args:
        instance: Object to serialize
        fields: Fields to include
        exclude: Fields to exclude

    Returns:
        Dictionary representation
    """
    serializer = APISerializer(instance=instance)
    serializer.fields = fields
    serializer.exclude = exclude
    return serializer.to_dict()  # type: ignore[return-value]


def serialize_many(
    instances: List[Any],
    fields: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Convenience function to serialize multiple instances.

    Args:
        instances: Objects to serialize
        fields: Fields to include
        exclude: Fields to exclude

    Returns:
        List of dictionary representations
    """
    serializer = APISerializer(instance=instances, many=True)
    serializer.fields = fields
    serializer.exclude = exclude
    return serializer.to_dict()  # type: ignore[return-value]
