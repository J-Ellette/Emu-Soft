"""
Developed by PowerShield, as an alternative to marshmallow


Marshmallow Emulator - Object Serialization/Deserialization Library

This module emulates the marshmallow library functionality for serializing and
deserializing complex objects to and from primitive Python types.

Key Features:
- Schema definition for data structures
- Field types with validation
- Data serialization (dump) and deserialization (load)
- Nested schemas and field relationships
- Data validation with error reporting
- Post-load and pre-dump hooks
- Missing and default value handling
- Required field validation
"""

from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Type, Union
from collections import OrderedDict
import re


# Exceptions
class ValidationError(Exception):
    """Raised when validation fails."""
    
    def __init__(self, message: Union[str, Dict, List], field_name: str = '_schema', data: Any = None):
        self.messages = self._normalize_messages(message, field_name)
        self.field_name = field_name
        self.data = data
        super().__init__(str(self.messages))
    
    def _normalize_messages(self, message, field_name):
        """Normalize message to dict format."""
        if isinstance(message, dict):
            return message
        elif isinstance(message, list):
            return {field_name: message}
        else:
            return {field_name: [message]}


# Fields
class Field:
    """Base field class."""
    
    default_error_messages = {
        'required': 'Missing data for required field.',
        'null': 'Field may not be null.',
        'validator_failed': 'Invalid value.',
    }
    
    def __init__(
        self,
        *,
        required: bool = False,
        allow_none: bool = False,
        load_default: Any = None,
        dump_default: Any = None,
        missing: Any = None,
        default: Any = None,
        data_key: Optional[str] = None,
        attribute: Optional[str] = None,
        validate: Optional[Union[Callable, List[Callable]]] = None,
        error_messages: Optional[Dict] = None,
        **kwargs
    ):
        self.required = required
        self.allow_none = allow_none
        
        # Handle default values (marshmallow 3.x uses load_default/dump_default)
        self.load_default = load_default if load_default is not None else (missing if missing is not None else default)
        self.dump_default = dump_default if dump_default is not None else default
        
        self.data_key = data_key  # Key in data dict
        self.attribute = attribute  # Attribute name on object
        self.validate = validate if isinstance(validate, list) else ([validate] if validate else [])
        
        self.error_messages = {**self.default_error_messages, **(error_messages or {})}
        self.parent = None
        self.name = None
    
    def serialize(self, attr: str, obj: Any, accessor: Optional[Callable] = None):
        """Serialize object attribute (dump)."""
        if accessor:
            value = accessor(obj, attr, None)
        else:
            value = getattr(obj, attr, None)
        
        if value is None:
            if self.allow_none:
                return None
            if self.dump_default is not None:
                return self.dump_default
            return None
        
        return self._serialize(value, attr, obj)
    
    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs):
        """Actual serialization logic. Override in subclasses."""
        return value
    
    def deserialize(self, value: Any, attr: Optional[str] = None, data: Optional[Dict] = None, **kwargs):
        """Deserialize data (load)."""
        if value is None:
            if self.allow_none:
                return None
            if not self.required:
                return self.load_default
            raise ValidationError(self.error_messages['required'])
        
        output = self._deserialize(value, attr, data, **kwargs)
        self._run_validators(output)
        return output
    
    def _deserialize(self, value: Any, attr: Optional[str], data: Optional[Dict], **kwargs):
        """Actual deserialization logic. Override in subclasses."""
        return value
    
    def _run_validators(self, value: Any):
        """Run field validators."""
        for validator in self.validate:
            if callable(validator):
                result = validator(value)
                if result is False:
                    raise ValidationError(self.error_messages['validator_failed'])


class String(Field):
    """String field."""
    
    def _serialize(self, value, attr, obj, **kwargs):
        return str(value)
    
    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, str):
            raise ValidationError(f"Not a valid string.")
        return value


class Integer(Field):
    """Integer field."""
    
    def _serialize(self, value, attr, obj, **kwargs):
        return int(value)
    
    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Not a valid integer.")


class Float(Field):
    """Float field."""
    
    def _serialize(self, value, attr, obj, **kwargs):
        return float(value)
    
    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Not a valid float.")


class Boolean(Field):
    """Boolean field."""
    
    truthy = {True, 'true', 'True', '1', 1, 'yes', 'Yes'}
    falsy = {False, 'false', 'False', '0', 0, 'no', 'No', ''}
    
    def _serialize(self, value, attr, obj, **kwargs):
        return bool(value)
    
    def _deserialize(self, value, attr, data, **kwargs):
        if value in self.truthy:
            return True
        elif value in self.falsy:
            return False
        else:
            raise ValidationError(f"Not a valid boolean.")


class DateTime(Field):
    """DateTime field."""
    
    def __init__(self, format: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.format = format or '%Y-%m-%dT%H:%M:%S'
    
    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, datetime):
            return value.strftime(self.format)
        return value
    
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.strptime(value, self.format)
        except (TypeError, ValueError):
            raise ValidationError(f"Not a valid datetime.")


class Date(Field):
    """Date field."""
    
    def __init__(self, format: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.format = format or '%Y-%m-%d'
    
    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, date):
            return value.strftime(self.format)
        return value
    
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, date):
            return value
        try:
            return datetime.strptime(value, self.format).date()
        except (TypeError, ValueError):
            raise ValidationError(f"Not a valid date.")


class Email(String):
    """Email field with validation."""
    
    email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        if not self.email_regex.match(value):
            raise ValidationError(f"Not a valid email address.")
        return value


class URL(String):
    """URL field with validation."""
    
    url_regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        if not self.url_regex.match(value):
            raise ValidationError(f"Not a valid URL.")
        return value


class List(Field):
    """List field."""
    
    def __init__(self, inner: Optional[Field] = None, **kwargs):
        super().__init__(**kwargs)
        self.inner = inner or Field()
    
    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, (list, tuple)):
            raise ValidationError(f"Not a valid list.")
        return [self.inner._serialize(item, attr, obj) for item in value]
    
    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, (list, tuple)):
            raise ValidationError(f"Not a valid list.")
        return [self.inner._deserialize(item, attr, data) for item in value]


class Dict(Field):
    """Dictionary field."""
    
    def __init__(self, keys: Optional[Field] = None, values: Optional[Field] = None, **kwargs):
        super().__init__(**kwargs)
        self.keys = keys
        self.values = values
    
    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, dict):
            raise ValidationError(f"Not a valid dict.")
        
        result = {}
        for k, v in value.items():
            key = self.keys._serialize(k, attr, obj) if self.keys else k
            val = self.values._serialize(v, attr, obj) if self.values else v
            result[key] = val
        return result
    
    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, dict):
            raise ValidationError(f"Not a valid dict.")
        
        result = {}
        for k, v in value.items():
            key = self.keys._deserialize(k, attr, data) if self.keys else k
            val = self.values._deserialize(v, attr, data) if self.values else v
            result[key] = val
        return result


class Nested(Field):
    """Nested schema field."""
    
    def __init__(self, nested: Union[Type['Schema'], str], many: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.nested = nested
        self.many = many
        self._nested_schema = None
    
    def _get_schema(self):
        """Get or create nested schema instance."""
        if self._nested_schema is None:
            if isinstance(self.nested, str):
                # Handle string references (circular dependencies)
                # For simplicity, we'll just raise an error
                raise ValueError(f"String schema references not supported: {self.nested}")
            elif isinstance(self.nested, type):
                self._nested_schema = self.nested()
            else:
                self._nested_schema = self.nested
        return self._nested_schema
    
    def _serialize(self, value, attr, obj, **kwargs):
        schema = self._get_schema()
        if self.many:
            return [schema.dump(item) for item in value]
        return schema.dump(value)
    
    def _deserialize(self, value, attr, data, **kwargs):
        schema = self._get_schema()
        if self.many:
            return [schema.load(item) for item in value]
        return schema.load(value)


class Method(Field):
    """Method field that calls a method on the Schema."""
    
    def __init__(self, serialize: Optional[str] = None, deserialize: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.serialize_method_name = serialize
        self.deserialize_method_name = deserialize
    
    def serialize(self, attr: str, obj: Any, accessor: Optional[Callable] = None):
        """Override serialize to call method directly."""
        if self.serialize_method_name:
            method = getattr(self.parent, self.serialize_method_name, None)
            if method:
                return method(obj)
        return None
    
    def _deserialize(self, value, attr, data, **kwargs):
        if self.deserialize_method_name:
            method = getattr(self.parent, self.deserialize_method_name, None)
            if method:
                return method(value)
        return value


class Function(Field):
    """Function field that calls a function."""
    
    def __init__(self, serialize: Optional[Callable] = None, deserialize: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.serialize_func = serialize
        self.deserialize_func = deserialize
    
    def serialize(self, attr: str, obj: Any, accessor: Optional[Callable] = None):
        """Override serialize to call function directly."""
        if self.serialize_func:
            return self.serialize_func(obj)
        return None
    
    def _deserialize(self, value, attr, data, **kwargs):
        if self.deserialize_func:
            return self.deserialize_func(value)
        return value


# Schema Meta
class SchemaMeta(type):
    """Metaclass for Schema."""
    
    def __new__(mcs, name, bases, namespace):
        # Collect fields from class definition
        fields = {}
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                fields[key] = value
                value.name = key
        
        namespace['_declared_fields'] = fields
        return super().__new__(mcs, name, bases, namespace)


# Schema
class Schema(metaclass=SchemaMeta):
    """Base schema class for serialization/deserialization."""
    
    class Meta:
        """Schema configuration."""
        ordered = False
        unknown = 'exclude'  # 'exclude', 'include', or 'raise'
    
    def __init__(self, *, many: bool = False, unknown: Optional[str] = None, **kwargs):
        self.many = many
        self.unknown = unknown or getattr(self.Meta, 'unknown', 'exclude')
        self.fields = self._init_fields()
        
        # Set parent reference for all fields
        for field_name, field_obj in self.fields.items():
            field_obj.parent = self
            field_obj.name = field_name
    
    def _init_fields(self):
        """Initialize schema fields."""
        fields = {}
        
        # Collect fields from base classes
        for base in reversed(self.__class__.__mro__):
            if hasattr(base, '_declared_fields'):
                fields.update(base._declared_fields.copy())
        
        # Create ordered dict if needed
        if getattr(self.Meta, 'ordered', False):
            return OrderedDict(fields)
        return fields
    
    def dump(self, obj: Any, *, many: Optional[bool] = None) -> Union[Dict, List[Dict]]:
        """Serialize object to dict."""
        many = self.many if many is None else many
        
        if many:
            return [self._serialize(item) for item in obj]
        return self._serialize(obj)
    
    def _serialize(self, obj: Any) -> Dict:
        """Serialize single object."""
        result = {}
        
        for field_name, field_obj in self.fields.items():
            # Determine the attribute name to access
            attr = field_obj.attribute or field_name
            
            # Determine the key to use in output
            key = field_obj.data_key or field_name
            
            try:
                value = field_obj.serialize(attr, obj)
                if value is not None or field_obj.allow_none:
                    result[key] = value
            except AttributeError:
                # Attribute doesn't exist
                if field_obj.dump_default is not None:
                    result[key] = field_obj.dump_default
        
        # Call post_dump hook
        result = self.post_dump(result, obj)
        
        return result
    
    def dumps(self, obj: Any, *, many: Optional[bool] = None) -> str:
        """Serialize object to JSON string."""
        import json
        return json.dumps(self.dump(obj, many=many))
    
    def load(self, data: Union[Dict, List[Dict]], *, many: Optional[bool] = None) -> Any:
        """Deserialize data to object."""
        many = self.many if many is None else many
        
        if many:
            return [self._deserialize(item) for item in data]
        return self._deserialize(data)
    
    def _deserialize(self, data: Dict) -> Dict:
        """Deserialize single data dict."""
        if not isinstance(data, dict):
            raise ValidationError("Invalid input type.")
        
        result = {}
        errors = {}
        
        # Call pre_load hook
        data = self.pre_load(data)
        
        # Process each field
        for field_name, field_obj in self.fields.items():
            # Determine the key to look for in data
            key = field_obj.data_key or field_name
            
            # Get value from data
            if key in data:
                value = data[key]
            elif field_obj.required:
                errors[field_name] = [field_obj.error_messages['required']]
                continue
            elif field_obj.load_default is not None:
                value = field_obj.load_default
            else:
                continue
            
            # Deserialize value
            try:
                result[field_name] = field_obj.deserialize(value, key, data)
            except ValidationError as ve:
                errors[field_name] = ve.messages.get(ve.field_name, [str(ve)])
        
        # Handle unknown fields
        if self.unknown == 'raise':
            known_keys = {field_obj.data_key or field_name for field_name, field_obj in self.fields.items()}
            unknown_keys = set(data.keys()) - known_keys
            if unknown_keys:
                errors['_schema'] = [f'Unknown field: {k}' for k in unknown_keys]
        elif self.unknown == 'include':
            known_keys = {field_obj.data_key or field_name for field_name, field_obj in self.fields.items()}
            for key in data:
                if key not in known_keys:
                    result[key] = data[key]
        
        if errors:
            raise ValidationError(errors)
        
        # Call post_load hook
        result = self.post_load(result)
        
        return result
    
    def loads(self, json_data: str, *, many: Optional[bool] = None) -> Any:
        """Deserialize JSON string to object."""
        import json
        data = json.loads(json_data)
        return self.load(data, many=many)
    
    def validate(self, data: Dict, *, many: Optional[bool] = None) -> Dict:
        """Validate data and return errors."""
        try:
            self.load(data, many=many)
            return {}
        except ValidationError as ve:
            return ve.messages
    
    # Hooks (can be overridden in subclasses)
    def pre_load(self, data: Dict, **kwargs) -> Dict:
        """Pre-process data before loading."""
        return data
    
    def post_load(self, data: Dict, **kwargs) -> Any:
        """Post-process data after loading."""
        return data
    
    def post_dump(self, data: Dict, obj: Any, **kwargs) -> Dict:
        """Post-process data after dumping."""
        return data


# Decorators for hooks
def pre_load(fn):
    """Decorator to register pre_load hook."""
    fn._marshmallow_hook = 'pre_load'
    return fn


def post_load(fn):
    """Decorator to register post_load hook."""
    fn._marshmallow_hook = 'post_load'
    return fn


def post_dump(fn):
    """Decorator to register post_dump hook."""
    fn._marshmallow_hook = 'post_dump'
    return fn


# Validators
def validate_length(min: Optional[int] = None, max: Optional[int] = None, equal: Optional[int] = None):
    """Validator for length."""
    def validator(value):
        length = len(value)
        if equal is not None and length != equal:
            raise ValidationError(f'Length must be {equal}.')
        if min is not None and length < min:
            raise ValidationError(f'Length must be at least {min}.')
        if max is not None and length > max:
            raise ValidationError(f'Length must be at most {max}.')
        return True
    return validator


def validate_range(min: Optional[float] = None, max: Optional[float] = None):
    """Validator for numeric range."""
    def validator(value):
        if min is not None and value < min:
            raise ValidationError(f'Value must be at least {min}.')
        if max is not None and value > max:
            raise ValidationError(f'Value must be at most {max}.')
        return True
    return validator


def validate_oneof(choices: List[Any]):
    """Validator for one-of choices."""
    def validator(value):
        if value not in choices:
            raise ValidationError(f'Value must be one of {choices}.')
        return True
    return validator


def validate_regexp(regex: str, flags: int = 0):
    """Validator for regex pattern."""
    pattern = re.compile(regex, flags)
    def validator(value):
        if not pattern.match(str(value)):
            raise ValidationError(f'Value does not match pattern {regex}.')
        return True
    return validator


# Expose common classes at module level
__all__ = [
    'Schema',
    'Field',
    'String',
    'Integer',
    'Float',
    'Boolean',
    'DateTime',
    'Date',
    'Email',
    'URL',
    'List',
    'Dict',
    'Nested',
    'Method',
    'Function',
    'ValidationError',
    'pre_load',
    'post_load',
    'post_dump',
    'validate_length',
    'validate_range',
    'validate_oneof',
    'validate_regexp',
]
