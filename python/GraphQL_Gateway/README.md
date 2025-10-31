# graphene Emulator - GraphQL Framework for Python

This module emulates the **graphene** library, which is a Python library for building GraphQL APIs. It provides an elegant way to define GraphQL schemas using Python classes and allows for easy integration with various web frameworks.

## What is graphene?

graphene is a library for building GraphQL schemas and types in Python. It is designed to be:
- Pythonic and easy to use
- Type-safe and well-defined
- Framework-agnostic
- Highly performant

GraphQL is a query language for APIs that allows clients to request exactly the data they need, making it more efficient than traditional REST APIs.

## Features

This emulator implements core graphene functionality:

### Type System
- **Scalar Types**: String, Int, Float, Boolean, ID, DateTime
- **Object Types**: Define custom types with fields
- **List Types**: Support for lists of any type
- **NonNull Types**: Mark fields as required

### Schema Definition
- **Query Types**: Define read operations
- **Mutation Types**: Define write operations
- **Field Resolvers**: Custom logic for field resolution
- **Arguments**: Pass parameters to fields

### Execution
- **Query Execution**: Execute GraphQL queries
- **Mutation Execution**: Execute GraphQL mutations
- **Error Handling**: Comprehensive error reporting

## Usage Examples

### Basic Schema Definition

```python
from GraphQL_Gateway import ObjectType, String, Int, Field, Schema

class User(ObjectType):
    id = Field(String)
    name = Field(String)
    age = Field(Int)

class Query(ObjectType):
    user = Field(User)
    
    def resolve_user(root, info):
        return {
            'id': '1',
            'name': 'John Doe',
            'age': 30
        }

# Set the resolver
Query._fields['user'].resolver = Query.resolve_user

# Create schema
schema = Schema(query=Query)

# Execute query
result = schema.execute('{ user }')
print(result.data)
# Output: {'user': {'id': '1', 'name': 'John Doe', 'age': 30}}
```

### Query with Arguments

```python
from GraphQL_Gateway import ObjectType, String, Field, Schema

class Query(ObjectType):
    greeting = Field(String)
    
    def resolve_greeting(root, info, name="World"):
        return f"Hello, {name}!"

Query._fields['greeting'].resolver = Query.resolve_greeting

schema = Schema(query=Query)

# Query with argument
result = schema.execute('{ greeting(name: "Alice") }')
print(result.data)
# Output: {'greeting': 'Hello, Alice!'}
```

### Working with Lists

```python
from GraphQL_Gateway import ObjectType, String, Int, Field, List, Schema

class Book(ObjectType):
    title = Field(String)
    author = Field(String)
    year = Field(Int)

class Query(ObjectType):
    books = Field(List(Book))
    
    def resolve_books(root, info):
        return [
            {'title': '1984', 'author': 'George Orwell', 'year': 1949},
            {'title': 'Brave New World', 'author': 'Aldous Huxley', 'year': 1932},
            {'title': 'Fahrenheit 451', 'author': 'Ray Bradbury', 'year': 1953}
        ]

Query._fields['books'].resolver = Query.resolve_books

schema = Schema(query=Query)

result = schema.execute('{ books }')
print(result.data)
# Output: {'books': [{'title': '1984', ...}, ...]}
```

### Mutations

```python
from GraphQL_Gateway import ObjectType, String, Field, Schema

# Storage for demo
users = []

class User(ObjectType):
    id = Field(String)
    name = Field(String)
    email = Field(String)

class Mutation(ObjectType):
    create_user = Field(User)
    
    def resolve_create_user(root, info, name="", email=""):
        user = {
            'id': str(len(users) + 1),
            'name': name,
            'email': email
        }
        users.append(user)
        return user

Mutation._fields['create_user'].resolver = Mutation.resolve_create_user

schema = Schema(mutation=Mutation)

result = schema.execute('mutation { create_user(name: "Alice", email: "alice@example.com") }')
print(result.data)
# Output: {'create_user': {'id': '1', 'name': 'Alice', 'email': 'alice@example.com'}}
```

### Complete Blog API Example

```python
from GraphQL_Gateway import ObjectType, String, Int, Field, List, Schema

# In-memory storage
posts_db = []
comments_db = []

class Comment(ObjectType):
    id = Field(String)
    text = Field(String)
    author = Field(String)

class Post(ObjectType):
    id = Field(String)
    title = Field(String)
    content = Field(String)
    author = Field(String)
    comments = Field(List(Comment))

class Query(ObjectType):
    post = Field(Post)
    posts = Field(List(Post))
    
    def resolve_post(root, info, id=None):
        for post in posts_db:
            if post['id'] == id:
                return post
        return None
    
    def resolve_posts(root, info):
        return posts_db

class Mutation(ObjectType):
    create_post = Field(Post)
    add_comment = Field(Comment)
    
    def resolve_create_post(root, info, title="", content="", author=""):
        post = {
            'id': str(len(posts_db) + 1),
            'title': title,
            'content': content,
            'author': author,
            'comments': []
        }
        posts_db.append(post)
        return post
    
    def resolve_add_comment(root, info, post_id="", text="", author=""):
        comment = {
            'id': str(len(comments_db) + 1),
            'text': text,
            'author': author
        }
        comments_db.append(comment)
        
        # Add to post
        for post in posts_db:
            if post['id'] == post_id:
                post['comments'].append(comment)
        
        return comment

# Set resolvers
Query._fields['post'].resolver = Query.resolve_post
Query._fields['posts'].resolver = Query.resolve_posts
Mutation._fields['create_post'].resolver = Mutation.resolve_create_post
Mutation._fields['add_comment'].resolver = Mutation.resolve_add_comment

schema = Schema(query=Query, mutation=Mutation)

# Create a post
result = schema.execute('''
    mutation {
        create_post(
            title: "GraphQL is awesome",
            content: "Learn GraphQL today!",
            author: "John Doe"
        )
    }
''')

print(result.data)

# Query all posts
result = schema.execute('{ posts }')
print(result.data)
```

### Working with DateTime

```python
from GraphQL_Gateway import ObjectType, String, DateTime, Field, Schema
from datetime import datetime

class Event(ObjectType):
    name = Field(String)
    scheduled_at = Field(DateTime)

class Query(ObjectType):
    event = Field(Event)
    
    def resolve_event(root, info):
        return {
            'name': 'Conference',
            'scheduled_at': datetime(2024, 12, 25, 10, 0)
        }

Query._fields['event'].resolver = Query.resolve_event

schema = Schema(query=Query)

result = schema.execute('{ event }')
print(result.data)
# Output: {'event': {'name': 'Conference', 'scheduled_at': '2024-12-25T10:00:00'}}
```

### Error Handling

```python
from GraphQL_Gateway import ObjectType, String, Field, Schema

class Query(ObjectType):
    risky_operation = Field(String)
    
    def resolve_risky_operation(root, info):
        raise Exception("Something went wrong!")

Query._fields['risky_operation'].resolver = Query.resolve_risky_operation

schema = Schema(query=Query)

result = schema.execute('{ risky_operation }')

if result.errors:
    print("Errors occurred:")
    for error in result.errors:
        print(f"  - {error}")
```

## Testing

Run the comprehensive test suite:

```bash
python test_GraphQL_Gateway.py
```

Tests cover:
- Scalar types (String, Int, Float, Boolean, ID, DateTime)
- Field definitions and resolvers
- Object types
- Queries with and without arguments
- List types
- Mutations
- Schema creation and execution
- Error handling
- Complete API examples

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for graphene in development and testing:

```python
# Instead of:
# import graphene

# Use:
import GraphQL_Gateway as graphene

# The rest of your code remains unchanged
class Query(graphene.ObjectType):
    hello = graphene.Field(graphene.String)
```

## Use Cases

Perfect for:
- **Learning GraphQL**: Understand GraphQL concepts without setup
- **Development**: Build GraphQL APIs locally
- **Testing**: Test GraphQL schemas without external dependencies
- **Prototyping**: Quickly prototype GraphQL APIs
- **Education**: Teach GraphQL in workshops and courses
- **CI/CD**: Run GraphQL tests in pipelines

## Limitations

This is an emulator for development and testing purposes:
- Simplified query parsing (basic field selection)
- No support for fragments
- No support for directives
- No support for subscriptions
- Limited introspection support
- No query validation beyond basic checks

## Supported Features

### Type System
- ✅ String scalar
- ✅ Int scalar
- ✅ Float scalar
- ✅ Boolean scalar
- ✅ ID scalar
- ✅ DateTime scalar
- ✅ Object types
- ✅ List types
- ✅ NonNull types

### Schema Features
- ✅ Query types
- ✅ Mutation types
- ✅ Field definitions
- ✅ Field resolvers
- ✅ Field arguments
- ✅ Custom types

### Execution
- ✅ Query execution
- ✅ Mutation execution
- ✅ Error handling
- ✅ Result formatting

## Real-World GraphQL Concepts

This emulator teaches the following GraphQL concepts:

1. **Type System**: Strong typing for API contracts
2. **Schema-First Design**: Define your API structure upfront
3. **Resolver Pattern**: Separate data fetching logic
4. **Query Language**: Client-specified data requirements
5. **Mutations**: Structured write operations
6. **Arguments**: Parameterized field requests

## Compatibility

Emulates core features of:
- graphene 2.x and 3.x API patterns
- GraphQL specification basics
- Common GraphQL schema patterns

## License

Part of the Emu-Soft project. See main repository LICENSE.
