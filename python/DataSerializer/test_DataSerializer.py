"""
Developed by PowerShield, as an alternative to Marshmallow
"""

"""
Tests for Marshmallow Emulator

Comprehensive test suite for object serialization/deserialization.
"""

import unittest
from datetime import datetime, date
from DataSerializer import (
    Schema,
    Field,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    Email,
    URL,
    List,
    Dict,
    Nested,
    Method,
    Function,
    ValidationError,
    pre_load,
    post_load,
    post_dump,
    validate_length,
    validate_range,
    validate_oneof,
)


class TestBasicFields(unittest.TestCase):
    """Test basic field types."""
    
    def test_string_field(self):
        """Test String field."""
        field = String()
        
        # Serialize
        self.assertEqual(field._serialize(123, 'test', None), '123')
        
        # Deserialize
        self.assertEqual(field._deserialize('hello', 'test', {}), 'hello')
        
        # Invalid
        with self.assertRaises(ValidationError):
            field._deserialize(123, 'test', {})
    
    def test_integer_field(self):
        """Test Integer field."""
        field = Integer()
        
        # Serialize
        self.assertEqual(field._serialize('42', 'test', None), 42)
        
        # Deserialize
        self.assertEqual(field._deserialize(42, 'test', {}), 42)
        self.assertEqual(field._deserialize('42', 'test', {}), 42)
        
        # Invalid
        with self.assertRaises(ValidationError):
            field._deserialize('not a number', 'test', {})
    
    def test_float_field(self):
        """Test Float field."""
        field = Float()
        
        # Serialize
        self.assertEqual(field._serialize(42, 'test', None), 42.0)
        
        # Deserialize
        self.assertEqual(field._deserialize(3.14, 'test', {}), 3.14)
        self.assertEqual(field._deserialize('3.14', 'test', {}), 3.14)
    
    def test_boolean_field(self):
        """Test Boolean field."""
        field = Boolean()
        
        # Serialize
        self.assertTrue(field._serialize(1, 'test', None))
        self.assertFalse(field._serialize(0, 'test', None))
        
        # Deserialize
        self.assertTrue(field._deserialize(True, 'test', {}))
        self.assertTrue(field._deserialize('true', 'test', {}))
        self.assertTrue(field._deserialize(1, 'test', {}))
        self.assertFalse(field._deserialize(False, 'test', {}))
        self.assertFalse(field._deserialize('false', 'test', {}))
        self.assertFalse(field._deserialize(0, 'test', {}))


class TestDateTimeFields(unittest.TestCase):
    """Test date and time fields."""
    
    def test_datetime_field(self):
        """Test DateTime field."""
        field = DateTime()
        
        dt = datetime(2023, 10, 30, 12, 30, 45)
        
        # Serialize
        serialized = field._serialize(dt, 'test', None)
        self.assertEqual(serialized, '2023-10-30T12:30:45')
        
        # Deserialize
        deserialized = field._deserialize('2023-10-30T12:30:45', 'test', {})
        self.assertEqual(deserialized, dt)
    
    def test_date_field(self):
        """Test Date field."""
        field = Date()
        
        d = date(2023, 10, 30)
        
        # Serialize
        serialized = field._serialize(d, 'test', None)
        self.assertEqual(serialized, '2023-10-30')
        
        # Deserialize
        deserialized = field._deserialize('2023-10-30', 'test', {})
        self.assertEqual(deserialized, d)


class TestValidationFields(unittest.TestCase):
    """Test fields with validation."""
    
    def test_email_field(self):
        """Test Email field."""
        field = Email()
        
        # Valid
        self.assertEqual(field._deserialize('test@example.com', 'test', {}), 'test@example.com')
        
        # Invalid
        with self.assertRaises(ValidationError):
            field._deserialize('not-an-email', 'test', {})
    
    def test_url_field(self):
        """Test URL field."""
        field = URL()
        
        # Valid
        self.assertEqual(field._deserialize('https://example.com', 'test', {}), 'https://example.com')
        self.assertEqual(field._deserialize('http://localhost:8000/path', 'test', {}), 'http://localhost:8000/path')
        
        # Invalid
        with self.assertRaises(ValidationError):
            field._deserialize('not a url', 'test', {})


class TestCollectionFields(unittest.TestCase):
    """Test collection fields."""
    
    def test_list_field(self):
        """Test List field."""
        field = List(Integer())
        
        # Serialize
        result = field._serialize([1, 2, 3], 'test', None)
        self.assertEqual(result, [1, 2, 3])
        
        # Deserialize
        result = field._deserialize([1, 2, 3], 'test', {})
        self.assertEqual(result, [1, 2, 3])
        
        result = field._deserialize(['1', '2', '3'], 'test', {})
        self.assertEqual(result, [1, 2, 3])
    
    def test_dict_field(self):
        """Test Dict field."""
        field = Dict(keys=String(), values=Integer())
        
        # Serialize
        result = field._serialize({'a': 1, 'b': 2}, 'test', None)
        self.assertEqual(result, {'a': 1, 'b': 2})
        
        # Deserialize
        result = field._deserialize({'a': '1', 'b': '2'}, 'test', {})
        self.assertEqual(result, {'a': 1, 'b': 2})


class TestBasicSchema(unittest.TestCase):
    """Test basic schema operations."""
    
    def test_simple_schema_dump(self):
        """Test dumping simple objects."""
        
        class UserSchema(Schema):
            name = String()
            age = Integer()
        
        class User:
            def __init__(self, name, age):
                self.name = name
                self.age = age
        
        user = User('Alice', 30)
        schema = UserSchema()
        
        result = schema.dump(user)
        self.assertEqual(result, {'name': 'Alice', 'age': 30})
    
    def test_simple_schema_load(self):
        """Test loading simple data."""
        
        class UserSchema(Schema):
            name = String()
            age = Integer()
        
        schema = UserSchema()
        data = {'name': 'Bob', 'age': 25}
        
        result = schema.load(data)
        self.assertEqual(result, {'name': 'Bob', 'age': 25})
    
    def test_many_dump(self):
        """Test dumping multiple objects."""
        
        class UserSchema(Schema):
            name = String()
        
        class User:
            def __init__(self, name):
                self.name = name
        
        users = [User('Alice'), User('Bob'), User('Charlie')]
        schema = UserSchema()
        
        result = schema.dump(users, many=True)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['name'], 'Alice')
    
    def test_many_load(self):
        """Test loading multiple objects."""
        
        class UserSchema(Schema):
            name = String()
        
        schema = UserSchema()
        data = [{'name': 'Alice'}, {'name': 'Bob'}]
        
        result = schema.load(data, many=True)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Alice')


class TestFieldOptions(unittest.TestCase):
    """Test field options."""
    
    def test_required_field(self):
        """Test required field validation."""
        
        class UserSchema(Schema):
            name = String(required=True)
            age = Integer()
        
        schema = UserSchema()
        
        # Missing required field
        with self.assertRaises(ValidationError) as cm:
            schema.load({'age': 30})
        
        self.assertIn('name', cm.exception.messages)
    
    def test_default_values(self):
        """Test default values."""
        
        class UserSchema(Schema):
            name = String()
            role = String(load_default='user')
        
        schema = UserSchema()
        
        # Load without role
        result = schema.load({'name': 'Alice'})
        self.assertEqual(result['role'], 'user')
    
    def test_allow_none(self):
        """Test allow_none option."""
        
        class UserSchema(Schema):
            name = String()
            bio = String(allow_none=True)
        
        schema = UserSchema()
        
        result = schema.load({'name': 'Alice', 'bio': None})
        self.assertIsNone(result['bio'])
    
    def test_data_key(self):
        """Test data_key option."""
        
        class UserSchema(Schema):
            user_name = String(data_key='username')
        
        class User:
            def __init__(self, user_name):
                self.user_name = user_name
        
        schema = UserSchema()
        
        # Load
        result = schema.load({'username': 'alice'})
        self.assertEqual(result['user_name'], 'alice')
        
        # Dump
        user = User('bob')
        result = schema.dump(user)
        self.assertEqual(result['username'], 'bob')


class TestNestedSchema(unittest.TestCase):
    """Test nested schemas."""
    
    def test_nested_schema(self):
        """Test nested schema field."""
        
        class AddressSchema(Schema):
            street = String()
            city = String()
        
        class UserSchema(Schema):
            name = String()
            address = Nested(AddressSchema)
        
        class Address:
            def __init__(self, street, city):
                self.street = street
                self.city = city
        
        class User:
            def __init__(self, name, address):
                self.name = name
                self.address = address
        
        # Dump
        user = User('Alice', Address('123 Main St', 'NYC'))
        schema = UserSchema()
        result = schema.dump(user)
        
        self.assertEqual(result['name'], 'Alice')
        self.assertEqual(result['address']['street'], '123 Main St')
        self.assertEqual(result['address']['city'], 'NYC')
        
        # Load
        data = {
            'name': 'Bob',
            'address': {'street': '456 Oak Ave', 'city': 'LA'}
        }
        result = schema.load(data)
        self.assertEqual(result['name'], 'Bob')
        self.assertEqual(result['address']['street'], '456 Oak Ave')
    
    def test_nested_many(self):
        """Test nested schema with many=True."""
        
        class TagSchema(Schema):
            name = String()
        
        class ArticleSchema(Schema):
            title = String()
            tags = Nested(TagSchema, many=True)
        
        class Tag:
            def __init__(self, name):
                self.name = name
        
        class Article:
            def __init__(self, title, tags):
                self.title = title
                self.tags = tags
        
        # Dump
        article = Article('Test', [Tag('python'), Tag('testing')])
        schema = ArticleSchema()
        result = schema.dump(article)
        
        self.assertEqual(len(result['tags']), 2)
        self.assertEqual(result['tags'][0]['name'], 'python')


class TestValidators(unittest.TestCase):
    """Test field validators."""
    
    def test_validate_length(self):
        """Test length validator."""
        
        class UserSchema(Schema):
            username = String(validate=validate_length(min=3, max=20))
        
        schema = UserSchema()
        
        # Valid
        result = schema.load({'username': 'alice'})
        self.assertEqual(result['username'], 'alice')
        
        # Too short
        with self.assertRaises(ValidationError):
            schema.load({'username': 'ab'})
        
        # Too long
        with self.assertRaises(ValidationError):
            schema.load({'username': 'a' * 21})
    
    def test_validate_range(self):
        """Test range validator."""
        
        class ProductSchema(Schema):
            price = Float(validate=validate_range(min=0, max=1000))
        
        schema = ProductSchema()
        
        # Valid
        result = schema.load({'price': 99.99})
        self.assertEqual(result['price'], 99.99)
        
        # Too low
        with self.assertRaises(ValidationError):
            schema.load({'price': -1})
        
        # Too high
        with self.assertRaises(ValidationError):
            schema.load({'price': 1001})
    
    def test_validate_oneof(self):
        """Test one-of validator."""
        
        class UserSchema(Schema):
            role = String(validate=validate_oneof(['admin', 'user', 'guest']))
        
        schema = UserSchema()
        
        # Valid
        result = schema.load({'role': 'admin'})
        self.assertEqual(result['role'], 'admin')
        
        # Invalid
        with self.assertRaises(ValidationError):
            schema.load({'role': 'superuser'})


class TestHooks(unittest.TestCase):
    """Test schema hooks."""
    
    def test_post_load_hook(self):
        """Test post_load hook."""
        
        class User:
            def __init__(self, name, email):
                self.name = name
                self.email = email
        
        class UserSchema(Schema):
            name = String()
            email = Email()
            
            def post_load(self, data, **kwargs):
                return User(**data)
        
        schema = UserSchema()
        result = schema.load({'name': 'Alice', 'email': 'alice@example.com'})
        
        self.assertIsInstance(result, User)
        self.assertEqual(result.name, 'Alice')
    
    def test_pre_load_hook(self):
        """Test pre_load hook."""
        
        class UserSchema(Schema):
            name = String()
            
            def pre_load(self, data, **kwargs):
                # Uppercase the name before processing
                if 'name' in data:
                    data['name'] = data['name'].upper()
                return data
        
        schema = UserSchema()
        result = schema.load({'name': 'alice'})
        
        self.assertEqual(result['name'], 'ALICE')
    
    def test_post_dump_hook(self):
        """Test post_dump hook."""
        
        class User:
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
        
        class UserSchema(Schema):
            first_name = String()
            last_name = String()
            
            def post_dump(self, data, obj, **kwargs):
                # Add full_name field
                data['full_name'] = f"{data['first_name']} {data['last_name']}"
                return data
        
        user = User('Alice', 'Smith')
        schema = UserSchema()
        result = schema.dump(user)
        
        self.assertEqual(result['full_name'], 'Alice Smith')


class TestMethodField(unittest.TestCase):
    """Test Method field."""
    
    def test_method_serialize(self):
        """Test Method field serialization."""
        
        class User:
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
        
        class UserSchema(Schema):
            first_name = String()
            last_name = String()
            full_name = Method(serialize='get_full_name')
            
            def get_full_name(self, obj):
                return f"{obj.first_name} {obj.last_name}"
        
        user = User('Alice', 'Smith')
        schema = UserSchema()
        result = schema.dump(user)
        
        self.assertEqual(result['full_name'], 'Alice Smith')


class TestFunctionField(unittest.TestCase):
    """Test Function field."""
    
    def test_function_serialize(self):
        """Test Function field serialization."""
        
        class User:
            def __init__(self, name):
                self.name = name
        
        class UserSchema(Schema):
            name = String()
            name_length = Function(serialize=lambda obj: len(obj.name))
        
        user = User('Alice')
        schema = UserSchema()
        result = schema.dump(user)
        
        self.assertEqual(result['name_length'], 5)


class TestValidation(unittest.TestCase):
    """Test validation methods."""
    
    def test_validate_method(self):
        """Test validate method."""
        
        class UserSchema(Schema):
            name = String(required=True)
            age = Integer()
        
        schema = UserSchema()
        
        # Valid data
        errors = schema.validate({'name': 'Alice', 'age': 30})
        self.assertEqual(errors, {})
        
        # Invalid data
        errors = schema.validate({'age': 30})
        self.assertIn('name', errors)


class TestUnknownFields(unittest.TestCase):
    """Test handling of unknown fields."""
    
    def test_unknown_exclude(self):
        """Test excluding unknown fields."""
        
        class UserSchema(Schema):
            name = String()
            
            class Meta:
                unknown = 'exclude'
        
        schema = UserSchema()
        result = schema.load({'name': 'Alice', 'extra': 'ignored'})
        
        self.assertNotIn('extra', result)
    
    def test_unknown_include(self):
        """Test including unknown fields."""
        
        class UserSchema(Schema):
            name = String()
            
            class Meta:
                unknown = 'include'
        
        schema = UserSchema()
        result = schema.load({'name': 'Alice', 'extra': 'included'})
        
        self.assertIn('extra', result)
        self.assertEqual(result['extra'], 'included')
    
    def test_unknown_raise(self):
        """Test raising error on unknown fields."""
        
        class UserSchema(Schema):
            name = String()
            
            class Meta:
                unknown = 'raise'
        
        schema = UserSchema()
        
        with self.assertRaises(ValidationError):
            schema.load({'name': 'Alice', 'extra': 'error'})


if __name__ == '__main__':
    unittest.main()
