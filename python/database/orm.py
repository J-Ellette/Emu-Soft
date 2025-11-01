"""
Developed by PowerShield, as an alternative to Django Database
"""

"""Basic ORM implementation for database models."""

from typing import Any, Dict, List, Optional, Type, TypeVar
from database.connection import db
from database.query import QueryBuilder

T = TypeVar("T", bound="Model")


class Field:
    """Base class for model fields."""

    def __init__(
        self,
        field_type: str,
        null: bool = False,
        default: Any = None,
        primary_key: bool = False,
        unique: bool = False,
    ) -> None:
        """Initialize a field.

        Args:
            field_type: SQL field type
            null: Whether field can be NULL
            default: Default value
            primary_key: Whether field is primary key
            unique: Whether field must be unique
        """
        self.field_type = field_type
        self.null = null
        self.default = default
        self.primary_key = primary_key
        self.unique = unique
        self.name: Optional[str] = None

    def __repr__(self) -> str:
        """Return string representation of the field."""
        return f"<Field {self.name} {self.field_type}>"


class CharField(Field):
    """Character field for strings."""

    def __init__(self, max_length: int = 255, **kwargs: Any) -> None:
        """Initialize a CharField.

        Args:
            max_length: Maximum string length
            **kwargs: Additional field options
        """
        super().__init__(f"VARCHAR({max_length})", **kwargs)


class IntegerField(Field):
    """Integer field."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize an IntegerField.

        Args:
            **kwargs: Additional field options
        """
        super().__init__("INTEGER", **kwargs)


class TextField(Field):
    """Text field for long strings."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a TextField.

        Args:
            **kwargs: Additional field options
        """
        super().__init__("TEXT", **kwargs)


class BooleanField(Field):
    """Boolean field."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a BooleanField.

        Args:
            **kwargs: Additional field options
        """
        super().__init__("BOOLEAN", **kwargs)


class DateTimeField(Field):
    """DateTime field."""

    def __init__(self, auto_now: bool = False, **kwargs: Any) -> None:
        """Initialize a DateTimeField.

        Args:
            auto_now: Automatically set to current time on update
            **kwargs: Additional field options
        """
        self.auto_now = auto_now
        super().__init__("TIMESTAMP", **kwargs)


class SlugField(Field):
    """Slug field for URL-friendly strings."""

    def __init__(self, max_length: int = 255, **kwargs: Any) -> None:
        """Initialize a SlugField.

        Args:
            max_length: Maximum string length
            **kwargs: Additional field options
        """
        super().__init__(f"VARCHAR({max_length})", **kwargs)


class ForeignKey(Field):
    """Foreign key field for relationships."""

    def __init__(self, to: str, on_delete: str = "CASCADE", **kwargs: Any) -> None:
        """Initialize a ForeignKey.

        Args:
            to: Referenced table name
            on_delete: Action on delete (CASCADE, SET NULL, etc.)
            **kwargs: Additional field options
        """
        self.to = to
        self.on_delete = on_delete
        super().__init__("INTEGER", **kwargs)


class ModelMeta(type):
    """Metaclass for Model to collect fields."""

    def __new__(mcs: Type["ModelMeta"], name: str, bases: tuple, namespace: dict) -> "ModelMeta":
        """Create a new Model class.

        Args:
            name: Class name
            bases: Base classes
            namespace: Class namespace

        Returns:
            New Model class
        """
        # Collect fields from the class
        fields = {}
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                value.name = key
                fields[key] = value
                # Remove field from class namespace
                del namespace[key]

        namespace["_fields"] = fields
        namespace["_table_name"] = namespace.get("_table_name", name.lower() + "s")

        return super().__new__(mcs, name, bases, namespace)


class Model(metaclass=ModelMeta):
    """Base class for ORM models.

    Models should inherit from this class and define fields as class attributes.
    """

    _fields: Dict[str, Field] = {}
    _table_name: str = ""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a model instance.

        Args:
            **kwargs: Field values
        """
        for field_name in self._fields:
            value = kwargs.get(field_name)
            setattr(self, field_name, value)

    @classmethod
    def query(cls) -> QueryBuilder:
        """Create a query builder for this model.

        Returns:
            QueryBuilder instance
        """
        return QueryBuilder(cls._table_name)

    @classmethod
    async def all(cls: Type[T]) -> List[T]:
        """Get all records from the database.

        Returns:
            List of model instances
        """
        query, params = cls.query().build()
        rows = await db.fetch_all(query, *params)
        return [cls(**row) for row in rows]

    @classmethod
    async def filter(cls: Type[T], **kwargs: Any) -> List[T]:
        """Filter records by field values.

        Args:
            **kwargs: Field name and value pairs

        Returns:
            List of matching model instances
        """
        query_builder = cls.query()
        for field_name, value in kwargs.items():
            query_builder.where(field_name, "=", value)

        query, params = query_builder.build()
        rows = await db.fetch_all(query, *params)
        return [cls(**row) for row in rows]

    @classmethod
    async def get(cls: Type[T], **kwargs: Any) -> Optional[T]:
        """Get a single record by field values.

        Args:
            **kwargs: Field name and value pairs

        Returns:
            Model instance or None if not found
        """
        query_builder = cls.query().limit(1)
        for field_name, value in kwargs.items():
            query_builder.where(field_name, "=", value)

        query, params = query_builder.build()
        row = await db.fetch_one(query, *params)
        return cls(**row) if row else None

    async def save(self: T) -> T:
        """Save the model instance to the database.

        Returns:
            Self after saving
        """
        # Get field values
        values = {}
        for field_name in self._fields:
            value = getattr(self, field_name, None)
            if value is not None:
                values[field_name] = value

        # Check if this is an insert or update
        pk_field = self._get_primary_key_field()
        pk_value = getattr(self, pk_field, None) if pk_field else None

        if pk_value is None:
            # Insert
            query, params = self.query().insert(values).build()
            row = await db.fetch_one(query, *params)
            if row:
                for field_name, value in row.items():
                    setattr(self, field_name, value)
        else:
            # Update
            query_builder = self.query().update(values)
            query_builder.where(pk_field, "=", pk_value)
            query, params = query_builder.build()
            row = await db.fetch_one(query, *params)
            if row:
                for field_name, value in row.items():
                    setattr(self, field_name, value)

        return self

    async def delete(self) -> None:
        """Delete the model instance from the database."""
        pk_field = self._get_primary_key_field()
        if not pk_field:
            raise ValueError("Cannot delete model without primary key")

        pk_value = getattr(self, pk_field, None)
        if pk_value is None:
            raise ValueError("Cannot delete model without primary key value")

        query_builder = self.query().delete()
        query_builder.where(pk_field, "=", pk_value)
        query, params = query_builder.build()
        await db.execute(query, *params)

    def _get_primary_key_field(self) -> Optional[str]:
        """Get the primary key field name.

        Returns:
            Primary key field name or None
        """
        for field_name, field in self._fields.items():
            if field.primary_key:
                return field_name
        return None

    def __repr__(self) -> str:
        """Return string representation of the model."""
        pk_field = self._get_primary_key_field()
        pk_value = getattr(self, pk_field, None) if pk_field else None
        return f"<{self.__class__.__name__} {pk_field}={pk_value}>"
