# jsonschema Emulator - JSON Schema Validation

This module emulates the **jsonschema** library, which provides an implementation of JSON Schema validation for Python.

## What is jsonschema?

jsonschema is a Python library for validating JSON data against JSON Schema specifications. JSON Schema is a vocabulary that allows you to annotate and validate JSON documents. It's commonly used for:
- API request/response validation
- Configuration file validation
- Data structure validation
- API documentation
- Contract testing

## Features

This emulator implements JSON Schema Draft 7 validation with:

### Core Validation
- **Type validation** - string, integer, number, boolean, null, object, array
- **Multiple types** - Allow multiple valid types
- **Enum and const** - Restrict values to specific options
- **Format validation** - email, ipv4, ipv6, uri, date, date-time

### Object Validation
- **Properties** - Define expected object properties with schemas
- **Required properties** - Specify mandatory fields
- **Additional properties** - Control handling of extra properties
- **Pattern properties** - Match properties by regex pattern
- **Min/max properties** - Limit object property count

### Array Validation
- **Items schema** - Validate all array items against schema
- **Tuple validation** - Different schema per array position
- **Min/max items** - Limit array length
- **Unique items** - Enforce uniqueness

### String Validation
- **Min/max length** - String length constraints
- **Pattern matching** - Regex validation
- **Format validation** - Built-in format validators

### Number Validation
- **Minimum/maximum** - Inclusive bounds
- **Exclusive minimum/maximum** - Exclusive bounds
- **Multiple of** - Divisibility constraint

### Validator Classes
- `Draft7Validator` - JSON Schema Draft 7 validator
- `Draft4Validator` - Alias for Draft 7
- `Draft6Validator` - Alias for Draft 7

### Error Handling
- `ValidationError` - Validation failure with path tracking
- `SchemaError` - Invalid schema definition
- Detailed error messages with field paths

## Usage Examples

### Basic Validation

```python
from jsonschema_emulator import validate, ValidationError

# Simple type validation
schema = {"type": "string"}
validate("hello", schema)  # OK

try:
    validate(123, schema)  # Raises ValidationError
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Using Validator Objects

```python
from jsonschema_emulator import Draft7Validator

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0}
    },
    "required": ["name"]
}

validator = Draft7Validator(schema)

# Validate and raise exception on failure
validator.validate({"name": "Alice", "age": 30})  # OK

# Check validity without exception
is_valid = validator.is_valid({"name": "Bob"})  # True
is_valid = validator.is_valid({"age": 30})  # False (missing required 'name')
```

### Object Schema with Required Fields

```python
schema = {
    "type": "object",
    "properties": {
        "username": {"type": "string", "minLength": 3},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 13}
    },
    "required": ["username", "email"]
}

# Valid data
data = {
    "username": "alice",
    "email": "alice@example.com",
    "age": 25
}
validate(data, schema)  # OK

# Invalid - missing required field
try:
    validate({"username": "bob"}, schema)
except ValidationError as e:
    print(e)  # "Required property 'email' is missing"
```

### Array Validation

```python
# Array of specific type
schema = {
    "type": "array",
    "items": {"type": "integer"},
    "minItems": 1,
    "maxItems": 5
}

validate([1, 2, 3], schema)  # OK

# Tuple validation - different type per position
schema = {
    "type": "array",
    "items": [
        {"type": "string"},
        {"type": "integer"},
        {"type": "boolean"}
    ]
}

validate(["Alice", 30, True], schema)  # OK
```

### String Validation

```python
# Pattern matching
schema = {
    "type": "string",
    "pattern": "^[A-Z][a-z]+$"  # Capitalized word
}
validate("Alice", schema)  # OK

# Format validation
schema = {
    "type": "string",
    "format": "email"
}
validate("user@example.com", schema)  # OK

# Length constraints
schema = {
    "type": "string",
    "minLength": 3,
    "maxLength": 20
}
validate("Alice", schema)  # OK
```

### Number Validation

```python
# Range validation
schema = {
    "type": "integer",
    "minimum": 0,
    "maximum": 100
}
validate(50, schema)  # OK

# Exclusive bounds
schema = {
    "type": "number",
    "exclusiveMinimum": 0,
    "exclusiveMaximum": 1
}
validate(0.5, schema)  # OK

# Multiple of
schema = {
    "type": "integer",
    "multipleOf": 5
}
validate(15, schema)  # OK
```

### Nested Objects

```python
schema = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"}
                    },
                    "required": ["city"]
                }
            },
            "required": ["name"]
        }
    }
}

data = {
    "user": {
        "name": "Alice",
        "address": {
            "street": "123 Main St",
            "city": "NYC"
        }
    }
}
validate(data, schema)  # OK
```

### Enum Validation

```python
schema = {
    "type": "string",
    "enum": ["red", "green", "blue"]
}

validate("red", schema)  # OK
validate("yellow", schema)  # ValidationError
```

### Additional Properties

```python
# Disallow additional properties
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "additionalProperties": False
}

validate({"name": "Alice"}, schema)  # OK
validate({"name": "Alice", "age": 30}, schema)  # ValidationError

# Additional properties with schema
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "additionalProperties": {"type": "integer"}
}

validate({"name": "Alice", "age": 30}, schema)  # OK
validate({"name": "Alice", "age": "30"}, schema)  # ValidationError
```

### Iterating Over Errors

```python
schema = {"type": "string"}
validator = Draft7Validator(schema)

for error in validator.iter_errors(123):
    print(f"Error: {error.message}")
    print(f"Path: {'.'.join(str(p) for p in error.path)}")
```

### Error Path Tracking

```python
schema = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "age": {"type": "integer"}
            }
        }
    }
}

try:
    validate({"user": {"age": "not a number"}}, schema)
except ValidationError as e:
    print(e.path)  # ['user', 'age']
    print(str(e))  # "Value is not of type integer at path: user.age"
```

### Multiple Type Validation

```python
schema = {
    "type": ["string", "integer"]
}

validate("hello", schema)  # OK
validate(42, schema)  # OK
validate(3.14, schema)  # ValidationError
```

### Pattern Properties

```python
schema = {
    "type": "object",
    "patternProperties": {
        "^num_": {"type": "number"},
        "^str_": {"type": "string"}
    }
}

validate({
    "num_value": 42,
    "num_count": 10,
    "str_name": "Alice"
}, schema)  # OK
```

## Testing

Run the comprehensive test suite:

```bash
python test_jsonschema_emulator.py
```

Tests cover:
- All basic types (string, integer, number, boolean, null, array, object)
- Enum and const validation
- Object validation (properties, required, additionalProperties, min/max properties)
- Array validation (items, min/max items, unique items)
- String validation (length, pattern, format)
- Number validation (minimum, maximum, exclusive bounds, multipleOf)
- Complex nested schemas
- Error handling and path tracking
- Convenience functions

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for jsonschema:

```python
# Instead of:
# from jsonschema import validate, Draft7Validator, ValidationError

# Use:
from jsonschema_emulator import validate, Draft7Validator, ValidationError
```

## Use Cases

Perfect for:
- **API Validation**: Validate API requests and responses
- **Configuration**: Validate configuration files and settings
- **Testing**: Ensure data structures meet requirements
- **Documentation**: Define and enforce data contracts
- **Data Quality**: Validate incoming data from external sources
- **Type Safety**: Add runtime type checking to dynamic data

## Supported Format Validators

- `email` - Email addresses
- `ipv4` - IPv4 addresses
- `ipv6` - IPv6 addresses (basic validation)
- `uri` - URIs
- `date` - Date strings (YYYY-MM-DD)
- `date-time` - ISO 8601 datetime strings

## Compatibility

Emulates core features of:
- jsonschema Draft 7 specification
- Common validation patterns
- Error reporting with path tracking

## Limitations

This emulator implements the most commonly used features of JSON Schema. Some advanced features not included:
- $ref references
- allOf, anyOf, oneOf combinators
- not keyword
- Schema composition and $id
- Custom format validators

For most use cases, the implemented features provide comprehensive validation capabilities.

## License

Part of the Emu-Soft project. See main repository LICENSE.
