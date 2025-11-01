# SchemReg - Event Schema Registry

Schema registry for managing event schemas with version control and compatibility checking.

## Features

- Schema versioning
- Compatibility checking (backward, forward, full)
- Schema validation
- Multiple subjects support

## Usage

```python
from SchemReg import SchemReg, CompatibilityMode

registry = SchemReg()

# Register schema
schema = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'age': {'type': 'integer'}
    },
    'required': ['name']
}

version = registry.register_schema('user', schema)

# Validate data
valid = registry.validate('user', {'name': 'John', 'age': 30})
```

## API Reference

- `register_schema(subject, schema, created_by)` - Register schema
- `get_schema(subject, version)` - Get schema
- `validate(subject, data, version)` - Validate data
- `list_subjects()` - List subjects
- `set_compatibility(subject, mode)` - Set compatibility mode

## Testing

```bash
python test_SchemReg.py
```

## License

Part of the Emu-Soft project.
