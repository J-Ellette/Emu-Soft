"""
Developed by PowerShield, as an alternative to jsonschema


jsonschema Emulator - JSON Schema Validation
Emulates the jsonschema library for validating JSON data against JSON schemas
"""

import re
from typing import Any, Dict, List, Optional, Union


class ValidationError(Exception):
    """Exception raised when validation fails"""
    def __init__(self, message: str, path: List[str] = None):
        super().__init__(message)
        self.message = message
        self.path = path or []
        self.instance = None
        self.schema = None
    
    def __str__(self):
        if self.path:
            path_str = ".".join(str(p) for p in self.path)
            return f"{self.message} at path: {path_str}"
        return self.message


class SchemaError(Exception):
    """Exception raised when the schema itself is invalid"""
    pass


class Draft7Validator:
    """
    JSON Schema Draft 7 validator
    Implements validation against JSON Schema specification
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize validator with a JSON schema
        
        Args:
            schema: JSON schema dictionary
        """
        self.schema = schema
        self._validate_schema(schema)
    
    def _validate_schema(self, schema: Dict[str, Any]) -> None:
        """Validate that the schema itself is valid"""
        if not isinstance(schema, dict):
            raise SchemaError("Schema must be a dictionary")
    
    def validate(self, instance: Any) -> None:
        """
        Validate an instance against the schema
        Raises ValidationError if validation fails
        
        Args:
            instance: The data to validate
        """
        self._validate_with_path(instance, self.schema, [])
    
    def is_valid(self, instance: Any) -> bool:
        """
        Check if an instance is valid against the schema
        Returns True/False without raising exceptions
        
        Args:
            instance: The data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.validate(instance)
            return True
        except ValidationError:
            return False
    
    def iter_errors(self, instance: Any):
        """
        Iterate over validation errors
        
        Args:
            instance: The data to validate
            
        Yields:
            ValidationError objects for each validation failure
        """
        try:
            self._validate_with_path(instance, self.schema, [])
        except ValidationError as e:
            yield e
    
    def _validate_with_path(self, instance: Any, schema: Dict[str, Any], path: List[str]) -> None:
        """
        Internal validation with path tracking
        
        Args:
            instance: The data to validate
            schema: The schema to validate against
            path: Current path in the data structure
        """
        # Type validation
        if "type" in schema:
            self._validate_type(instance, schema["type"], path)
        
        # Enum validation
        if "enum" in schema:
            if instance not in schema["enum"]:
                raise ValidationError(
                    f"Value {instance} is not in enum {schema['enum']}",
                    path
                )
        
        # Const validation
        if "const" in schema:
            if instance != schema["const"]:
                raise ValidationError(
                    f"Value {instance} does not match const {schema['const']}",
                    path
                )
        
        # Type-specific validations
        if isinstance(instance, dict):
            self._validate_object(instance, schema, path)
        elif isinstance(instance, list):
            self._validate_array(instance, schema, path)
        elif isinstance(instance, str):
            self._validate_string(instance, schema, path)
        elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
            self._validate_number(instance, schema, path)
    
    def _validate_type(self, instance: Any, expected_type: Union[str, List[str]], path: List[str]) -> None:
        """Validate instance type"""
        if isinstance(expected_type, list):
            valid = any(self._check_type(instance, t) for t in expected_type)
            if not valid:
                raise ValidationError(
                    f"Value is not of type {expected_type}",
                    path
                )
        else:
            if not self._check_type(instance, expected_type):
                raise ValidationError(
                    f"Value is not of type {expected_type}",
                    path
                )
    
    def _check_type(self, instance: Any, type_name: str) -> bool:
        """Check if instance matches type name"""
        type_map = {
            "null": lambda x: x is None,
            "boolean": lambda x: isinstance(x, bool),
            "object": lambda x: isinstance(x, dict),
            "array": lambda x: isinstance(x, list),
            "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
            "string": lambda x: isinstance(x, str),
        }
        
        checker = type_map.get(type_name)
        if checker is None:
            raise SchemaError(f"Unknown type: {type_name}")
        
        return checker(instance)
    
    def _validate_object(self, instance: Dict, schema: Dict[str, Any], path: List[str]) -> None:
        """Validate object/dictionary"""
        # Required properties
        if "required" in schema:
            for prop in schema["required"]:
                if prop not in instance:
                    raise ValidationError(
                        f"Required property '{prop}' is missing",
                        path
                    )
        
        # Properties validation
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if prop_name in instance:
                    self._validate_with_path(
                        instance[prop_name],
                        prop_schema,
                        path + [prop_name]
                    )
        
        # Pattern properties
        if "patternProperties" in schema:
            for pattern, prop_schema in schema["patternProperties"].items():
                for prop_name, value in instance.items():
                    if re.match(pattern, prop_name):
                        self._validate_with_path(
                            value,
                            prop_schema,
                            path + [prop_name]
                        )
        
        # Additional properties
        if "additionalProperties" in schema:
            known_props = set(schema.get("properties", {}).keys())
            pattern_props = schema.get("patternProperties", {})
            
            for prop_name, value in instance.items():
                if prop_name not in known_props:
                    # Check if it matches any pattern property
                    matches_pattern = any(
                        re.match(pattern, prop_name)
                        for pattern in pattern_props.keys()
                    )
                    
                    if not matches_pattern:
                        if schema["additionalProperties"] is False:
                            raise ValidationError(
                                f"Additional property '{prop_name}' is not allowed",
                                path
                            )
                        elif isinstance(schema["additionalProperties"], dict):
                            self._validate_with_path(
                                value,
                                schema["additionalProperties"],
                                path + [prop_name]
                            )
        
        # Min/max properties
        if "minProperties" in schema:
            if len(instance) < schema["minProperties"]:
                raise ValidationError(
                    f"Object has {len(instance)} properties, minimum is {schema['minProperties']}",
                    path
                )
        
        if "maxProperties" in schema:
            if len(instance) > schema["maxProperties"]:
                raise ValidationError(
                    f"Object has {len(instance)} properties, maximum is {schema['maxProperties']}",
                    path
                )
    
    def _validate_array(self, instance: List, schema: Dict[str, Any], path: List[str]) -> None:
        """Validate array/list"""
        # Items validation
        if "items" in schema:
            if isinstance(schema["items"], dict):
                # All items must match this schema
                for i, item in enumerate(instance):
                    self._validate_with_path(
                        item,
                        schema["items"],
                        path + [f"[{i}]"]
                    )
            elif isinstance(schema["items"], list):
                # Tuple validation - each position has its own schema
                for i, item_schema in enumerate(schema["items"]):
                    if i < len(instance):
                        self._validate_with_path(
                            instance[i],
                            item_schema,
                            path + [f"[{i}]"]
                        )
        
        # Min/max items
        if "minItems" in schema:
            if len(instance) < schema["minItems"]:
                raise ValidationError(
                    f"Array has {len(instance)} items, minimum is {schema['minItems']}",
                    path
                )
        
        if "maxItems" in schema:
            if len(instance) > schema["maxItems"]:
                raise ValidationError(
                    f"Array has {len(instance)} items, maximum is {schema['maxItems']}",
                    path
                )
        
        # Unique items
        if schema.get("uniqueItems", False):
            seen = []
            for item in instance:
                # Handle unhashable types
                item_str = str(item)
                if item_str in seen:
                    raise ValidationError(
                        "Array items must be unique",
                        path
                    )
                seen.append(item_str)
    
    def _validate_string(self, instance: str, schema: Dict[str, Any], path: List[str]) -> None:
        """Validate string"""
        # Min/max length
        if "minLength" in schema:
            if len(instance) < schema["minLength"]:
                raise ValidationError(
                    f"String length {len(instance)} is less than minimum {schema['minLength']}",
                    path
                )
        
        if "maxLength" in schema:
            if len(instance) > schema["maxLength"]:
                raise ValidationError(
                    f"String length {len(instance)} exceeds maximum {schema['maxLength']}",
                    path
                )
        
        # Pattern matching
        if "pattern" in schema:
            if not re.search(schema["pattern"], instance):
                raise ValidationError(
                    f"String does not match pattern {schema['pattern']}",
                    path
                )
        
        # Format validation
        if "format" in schema:
            self._validate_format(instance, schema["format"], path)
    
    def _validate_number(self, instance: Union[int, float], schema: Dict[str, Any], path: List[str]) -> None:
        """Validate number (integer or float)"""
        # Minimum
        if "minimum" in schema:
            if instance < schema["minimum"]:
                raise ValidationError(
                    f"Value {instance} is less than minimum {schema['minimum']}",
                    path
                )
        
        if "exclusiveMinimum" in schema:
            if instance <= schema["exclusiveMinimum"]:
                raise ValidationError(
                    f"Value {instance} is not greater than exclusive minimum {schema['exclusiveMinimum']}",
                    path
                )
        
        # Maximum
        if "maximum" in schema:
            if instance > schema["maximum"]:
                raise ValidationError(
                    f"Value {instance} exceeds maximum {schema['maximum']}",
                    path
                )
        
        if "exclusiveMaximum" in schema:
            if instance >= schema["exclusiveMaximum"]:
                raise ValidationError(
                    f"Value {instance} is not less than exclusive maximum {schema['exclusiveMaximum']}",
                    path
                )
        
        # Multiple of
        if "multipleOf" in schema:
            if instance % schema["multipleOf"] != 0:
                raise ValidationError(
                    f"Value {instance} is not a multiple of {schema['multipleOf']}",
                    path
                )
    
    def _validate_format(self, instance: str, format_name: str, path: List[str]) -> None:
        """Validate string format"""
        format_validators = {
            "email": self._validate_email,
            "ipv4": self._validate_ipv4,
            "ipv6": self._validate_ipv6,
            "uri": self._validate_uri,
            "date": self._validate_date,
            "date-time": self._validate_datetime,
        }
        
        validator = format_validators.get(format_name)
        if validator:
            if not validator(instance):
                raise ValidationError(
                    f"String does not match format '{format_name}'",
                    path
                )
    
    def _validate_email(self, value: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    def _validate_ipv4(self, value: str) -> bool:
        """IPv4 address validation"""
        parts = value.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def _validate_ipv6(self, value: str) -> bool:
        """Basic IPv6 address validation"""
        # Simplified validation
        parts = value.split(':')
        return 2 <= len(parts) <= 8 and all(len(p) <= 4 for p in parts)
    
    def _validate_uri(self, value: str) -> bool:
        """Basic URI validation"""
        pattern = r'^[a-zA-Z][a-zA-Z0-9+.-]*:'
        return bool(re.match(pattern, value))
    
    def _validate_date(self, value: str) -> bool:
        """Date format validation (YYYY-MM-DD)"""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(pattern, value))
    
    def _validate_datetime(self, value: str) -> bool:
        """DateTime format validation (ISO 8601)"""
        pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        return bool(re.match(pattern, value))


def validate(instance: Any, schema: Dict[str, Any]) -> None:
    """
    Validate an instance against a schema
    Convenience function
    
    Args:
        instance: The data to validate
        schema: The JSON schema
        
    Raises:
        ValidationError: If validation fails
    """
    validator = Draft7Validator(schema)
    validator.validate(instance)


def is_valid(instance: Any, schema: Dict[str, Any]) -> bool:
    """
    Check if an instance is valid against a schema
    Convenience function
    
    Args:
        instance: The data to validate
        schema: The JSON schema
        
    Returns:
        True if valid, False otherwise
    """
    try:
        validate(instance, schema)
        return True
    except ValidationError:
        return False


# Aliases for compatibility
Draft4Validator = Draft7Validator
Draft6Validator = Draft7Validator
