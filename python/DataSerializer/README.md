# Marshmallow Emulator - Object Serialization/Deserialization Library

This module emulates the **marshmallow** library, which is a popular Python library for serializing and deserializing complex data types to and from native Python datatypes.

## What is Marshmallow?

Marshmallow is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, to and from native Python datatypes. It's commonly used for:
- API serialization/deserialization
- Data validation
- Converting database models to JSON
- Form data processing
- Configuration file parsing

## Features

This emulator implements:

### Schema Definition
- Declarative schema classes
- Field-based data structure definition
- Schema inheritance
- Ordered fields support

### Field Types
- `String` - Text data
- `Integer` - Whole numbers
- `Float` - Decimal numbers
- `Boolean` - True/False values
- `DateTime` - Date and time with formatting
- `Date` - Date values
- `Email` - Email addresses with validation
- `URL` - URLs with validation
- `List` - Lists/arrays with typed elements
- `Dict` - Dictionaries with typed keys/values
- `Nested` - Nested schemas for complex objects
- `Method` - Computed fields using schema methods
- `Function` - Computed fields using functions

### Data Operations
- `dump()` - Serialize objects to dicts (object → dict)
- `load()` - Deserialize dicts to objects (dict → object)
- `dumps()` - Serialize to JSON string
- `loads()` - Deserialize from JSON string
- `validate()` - Validate data without loading
- Many mode for lists of objects

### Validation
- Required field validation
- Type validation
- Custom validators (`validate_length`, `validate_range`, `validate_oneof`, `validate_regexp`)
- Field-level validation
- Schema-level validation

### Field Options
- `required` - Field must be present
- `allow_none` - Allow None values
- `load_default` / `dump_default` - Default values
- `data_key` - Different key name in data
- `attribute` - Different attribute name on object
- `validate` - Custom validators

### Hooks
- `pre_load` - Process data before deserialization
- `post_load` - Process data after deserialization
- `post_dump` - Process data after serialization

### Schema Options
- `unknown` - Handle unknown fields ('exclude', 'include', 'raise')
- `ordered` - Maintain field order
- `many` - Serialize/deserialize lists

## Usage Examples

### Basic Schema

```python
from marshmallow_emulator import Schema, String, Integer, Email

class UserSchema(Schema):
    name = String(required=True)
    email = Email(required=True)
    age = Integer()

# Serialize (dump)
class User:
    def __init__(self, name, email, age):
        self.name = name
        self.email = email
        self.age = age

user = User('Alice', 'alice@example.com', 30)
schema = UserSchema()
result = schema.dump(user)
print(result)
# {'name': 'Alice', 'email': 'alice@example.com', 'age': 30}

# Deserialize (load)
data = {'name': 'Bob', 'email': 'bob@example.com', 'age': 25}
result = schema.load(data)
print(result)
# {'name': 'Bob', 'email': 'bob@example.com', 'age': 25}
```

### Nested Schemas

```python
from marshmallow_emulator import Schema, String, Nested

class AddressSchema(Schema):
    street = String()
    city = String()
    country = String()

class UserSchema(Schema):
    name = String()
    address = Nested(AddressSchema)

# With objects
class Address:
    def __init__(self, street, city, country):
        self.street = street
        self.city = city
        self.country = country

class User:
    def __init__(self, name, address):
        self.name = name
        self.address = address

user = User('Alice', Address('123 Main St', 'NYC', 'USA'))
schema = UserSchema()
result = schema.dump(user)
# {
#     'name': 'Alice',
#     'address': {'street': '123 Main St', 'city': 'NYC', 'country': 'USA'}
# }
```

### Validation

```python
from marshmallow_emulator import Schema, String, Integer, ValidationError, validate_range

class ProductSchema(Schema):
    name = String(required=True)
    price = Integer(validate=validate_range(min=0, max=10000))

schema = ProductSchema()

# Valid data
data = {'name': 'Widget', 'price': 99}
result = schema.load(data)

# Invalid - missing required field
try:
    schema.load({'price': 99})
except ValidationError as e:
    print(e.messages)
    # {'name': ['Missing data for required field.']}

# Invalid - out of range
try:
    schema.load({'name': 'Widget', 'price': -5})
except ValidationError as e:
    print(e.messages)
```

### Many Objects

```python
class UserSchema(Schema):
    name = String()
    email = Email()

# Dump many
users = [User('Alice', 'alice@example.com'), User('Bob', 'bob@example.com')]
schema = UserSchema()
result = schema.dump(users, many=True)
# [{'name': 'Alice', 'email': 'alice@example.com'}, ...]

# Load many
data = [{'name': 'Alice', 'email': 'alice@example.com'}]
result = schema.load(data, many=True)
```

### Custom Fields with Method

```python
class UserSchema(Schema):
    first_name = String()
    last_name = String()
    full_name = Method(serialize='get_full_name')
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

user = User('Alice', 'Smith')
schema = UserSchema()
result = schema.dump(user)
# {'first_name': 'Alice', 'last_name': 'Smith', 'full_name': 'Alice Smith'}
```

### Post-Load Hook

```python
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

class UserSchema(Schema):
    name = String()
    email = Email()
    
    def post_load(self, data, **kwargs):
        # Convert dict to User object
        return User(**data)

schema = UserSchema()
user = schema.load({'name': 'Alice', 'email': 'alice@example.com'})
# Returns User object instead of dict
```

### Data Key Mapping

```python
class UserSchema(Schema):
    username = String(data_key='user_name')  # Different name in data
    email_address = String(data_key='email', attribute='email')

# When loading
data = {'user_name': 'alice', 'email': 'alice@example.com'}
result = schema.load(data)
# {'username': 'alice', 'email_address': 'alice@example.com'}
```

## Testing

Run the comprehensive test suite:

```bash
python test_marshmallow_emulator.py
```

Tests cover:
- All field types
- Schema serialization and deserialization
- Validation and error handling
- Nested schemas
- Custom validators
- Hooks
- Many mode
- Unknown field handling

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for marshmallow in development and testing:

```python
# Instead of:
# from marshmallow import Schema, fields

# Use:
from marshmallow_emulator import Schema, String as fields.String
# Or import fields directly with appropriate names
```

## Use Cases

Perfect for:
- **API Development**: Serialize/deserialize API requests and responses
- **Data Validation**: Validate complex data structures
- **Testing**: Test data transformations without external dependencies
- **Configuration**: Parse and validate configuration files
- **ORM Integration**: Convert database models to JSON
- **Form Processing**: Validate and process form data

## Compatibility

Emulates core features of:
- marshmallow 3.x API
- Common field types and validators
- Schema hooks and options

## License

Part of the Emu-Soft project. See main repository LICENSE.
