"""
Tests for graphene emulator

Comprehensive test suite for GraphQL framework emulator functionality.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from graphene_emulator import (
    Field, Argument, ObjectType, Interface, Query, Mutation, Schema,
    String, Int, Float, Boolean, ID, DateTime, List, NonNull,
    ResolveInfo, ExecutionResult, GraphQLError, ValidationError,
    resolve_only_args
)


class TestScalarTypes(unittest.TestCase):
    """Test GraphQL scalar types."""
    
    def test_string_scalar(self):
        """Test String scalar type."""
        self.assertEqual(String.serialize(123), "123")
        self.assertEqual(String.parse_value("hello"), "hello")
    
    def test_int_scalar(self):
        """Test Int scalar type."""
        self.assertEqual(Int.serialize("42"), 42)
        self.assertEqual(Int.parse_value(42), 42)
    
    def test_float_scalar(self):
        """Test Float scalar type."""
        self.assertEqual(Float.serialize("3.14"), 3.14)
        self.assertEqual(Float.parse_value(3.14), 3.14)
    
    def test_boolean_scalar(self):
        """Test Boolean scalar type."""
        self.assertTrue(Boolean.serialize(1))
        self.assertFalse(Boolean.parse_value(0))
    
    def test_id_scalar(self):
        """Test ID scalar type."""
        self.assertEqual(ID.serialize(123), "123")
        self.assertEqual(ID.parse_value("abc-123"), "abc-123")


class TestFields(unittest.TestCase):
    """Test Field functionality."""
    
    def test_field_creation(self):
        """Test creating a field."""
        field = Field(String, required=True, description="A test field")
        
        self.assertEqual(field.type, String)
        self.assertTrue(field.required)
        self.assertEqual(field.description, "A test field")
    
    def test_field_with_resolver(self):
        """Test field with custom resolver."""
        def custom_resolver(root, info):
            return "custom_value"
        
        field = Field(String, resolver=custom_resolver)
        
        info = ResolveInfo("test", Query, String, None)
        result = field.resolve(None, info)
        
        self.assertEqual(result, "custom_value")
    
    def test_field_default_resolver(self):
        """Test field default resolver."""
        class TestObj:
            name = "test_name"
        
        field = Field(String)
        
        info = ResolveInfo("name", Query, String, None)
        info.field_name = "name"
        result = field.resolve(TestObj(), info)
        
        self.assertEqual(result, "test_name")


class TestObjectType(unittest.TestCase):
    """Test ObjectType functionality."""
    
    def test_object_type_definition(self):
        """Test defining an object type."""
        class User(ObjectType):
            id = Field(ID)
            name = Field(String)
            email = Field(String)
            age = Field(Int)
        
        fields = User.get_fields()
        
        self.assertIn('id', fields)
        self.assertIn('name', fields)
        self.assertIn('email', fields)
        self.assertIn('age', fields)
    
    def test_object_type_instance(self):
        """Test creating an instance of object type."""
        class User(ObjectType):
            id = Field(ID)
            name = Field(String)
        
        user = User(id="123", name="John Doe")
        
        self.assertEqual(user.id, "123")
        self.assertEqual(user.name, "John Doe")


class TestQuery(unittest.TestCase):
    """Test Query functionality."""
    
    def test_simple_query(self):
        """Test a simple query."""
        class Query(ObjectType):
            hello = Field(String)
            
            def resolve_hello(root, info):
                return "Hello, World!"
        
        # Set resolver
        Query._fields['hello'].resolver = Query.resolve_hello
        
        schema = Schema(query=Query)
        
        result = schema.execute('{ hello }')
        
        self.assertIsNotNone(result.data)
        self.assertEqual(result.data.get('hello'), "Hello, World!")
        self.assertEqual(len(result.errors), 0)
    
    def test_query_with_multiple_fields(self):
        """Test query with multiple fields."""
        class Query(ObjectType):
            name = Field(String)
            age = Field(Int)
            
            def resolve_name(root, info):
                return "Alice"
            
            def resolve_age(root, info):
                return 30
        
        Query._fields['name'].resolver = Query.resolve_name
        Query._fields['age'].resolver = Query.resolve_age
        
        schema = Schema(query=Query)
        
        result = schema.execute('{ name, age }')
        
        self.assertEqual(result.data.get('name'), "Alice")
        self.assertEqual(result.data.get('age'), 30)
    
    def test_query_with_arguments(self):
        """Test query with field arguments."""
        class Query(ObjectType):
            greeting = Field(String)
            
            def resolve_greeting(root, info, name="World"):
                return f"Hello, {name}!"
        
        Query._fields['greeting'].resolver = Query.resolve_greeting
        
        schema = Schema(query=Query)
        
        result = schema.execute('{ greeting(name: "Alice") }')
        
        self.assertEqual(result.data.get('greeting'), "Hello, Alice!")


class TestList(unittest.TestCase):
    """Test List type functionality."""
    
    def test_list_type(self):
        """Test list field type."""
        class Query(ObjectType):
            numbers = Field(List(Int))
            
            def resolve_numbers(root, info):
                return [1, 2, 3, 4, 5]
        
        Query._fields['numbers'].resolver = Query.resolve_numbers
        
        schema = Schema(query=Query)
        
        result = schema.execute('{ numbers }')
        
        self.assertEqual(result.data.get('numbers'), [1, 2, 3, 4, 5])
    
    def test_list_of_objects(self):
        """Test list of object types."""
        class User(ObjectType):
            id = Field(ID)
            name = Field(String)
        
        class Query(ObjectType):
            users = Field(List(User))
            
            def resolve_users(root, info):
                return [
                    {'id': '1', 'name': 'Alice'},
                    {'id': '2', 'name': 'Bob'}
                ]
        
        Query._fields['users'].resolver = Query.resolve_users
        
        schema = Schema(query=Query)
        
        result = schema.execute('{ users }')
        
        users = result.data.get('users')
        self.assertEqual(len(users), 2)


class TestMutation(unittest.TestCase):
    """Test Mutation functionality."""
    
    def test_simple_mutation(self):
        """Test a simple mutation."""
        class Mutation(ObjectType):
            create_user = Field(String)
            
            def resolve_create_user(root, info, name="User"):
                return f"Created user: {name}"
        
        Mutation._fields['create_user'].resolver = Mutation.resolve_create_user
        
        schema = Schema(mutation=Mutation)
        
        result = schema.execute('mutation { create_user(name: "Alice") }')
        
        self.assertEqual(result.data.get('create_user'), "Created user: Alice")


class TestSchema(unittest.TestCase):
    """Test Schema functionality."""
    
    def test_schema_creation(self):
        """Test creating a schema."""
        class Query(ObjectType):
            hello = Field(String)
        
        schema = Schema(query=Query)
        
        self.assertIsNotNone(schema.query)
        self.assertEqual(schema.query, Query)
    
    def test_schema_with_mutation(self):
        """Test schema with mutation."""
        class Query(ObjectType):
            hello = Field(String)
        
        class Mutation(ObjectType):
            update = Field(String)
        
        schema = Schema(query=Query, mutation=Mutation)
        
        self.assertIsNotNone(schema.query)
        self.assertIsNotNone(schema.mutation)
    
    def test_execution_result(self):
        """Test ExecutionResult."""
        result = ExecutionResult(data={'hello': 'world'}, errors=[])
        
        result_dict = result.to_dict()
        
        self.assertIn('data', result_dict)
        self.assertEqual(result_dict['data']['hello'], 'world')
    
    def test_execution_with_errors(self):
        """Test execution with errors."""
        result = ExecutionResult(data=None, errors=['Error 1', 'Error 2'])
        
        result_dict = result.to_dict()
        
        self.assertIn('errors', result_dict)
        self.assertEqual(len(result_dict['errors']), 2)


class TestCompleteExample(unittest.TestCase):
    """Test a complete GraphQL API example."""
    
    def test_blog_api(self):
        """Test a simple blog API."""
        # Define types
        class Post(ObjectType):
            id = Field(ID)
            title = Field(String)
            content = Field(String)
            author = Field(String)
        
        # Define Query
        class Query(ObjectType):
            post = Field(Post)
            posts = Field(List(Post))
            
            def resolve_post(root, info, id=None):
                return {
                    'id': id or '1',
                    'title': 'First Post',
                    'content': 'Content here',
                    'author': 'John Doe'
                }
            
            def resolve_posts(root, info):
                return [
                    {'id': '1', 'title': 'Post 1', 'content': 'Content 1', 'author': 'Alice'},
                    {'id': '2', 'title': 'Post 2', 'content': 'Content 2', 'author': 'Bob'}
                ]
        
        Query._fields['post'].resolver = Query.resolve_post
        Query._fields['posts'].resolver = Query.resolve_posts
        
        # Create schema
        schema = Schema(query=Query)
        
        # Test single post query
        result = schema.execute('{ post(id: "123") }')
        self.assertIsNotNone(result.data)
        
        # Test posts list query
        result = schema.execute('{ posts }')
        posts = result.data.get('posts')
        self.assertEqual(len(posts), 2)


class TestErrorHandling(unittest.TestCase):
    """Test error handling."""
    
    def test_graphql_error(self):
        """Test GraphQLError exception."""
        with self.assertRaises(GraphQLError):
            raise GraphQLError("Test error")
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        with self.assertRaises(ValidationError):
            raise ValidationError("Validation failed")


if __name__ == '__main__':
    unittest.main()
