# factory_boy Emulator

A pure Python implementation that emulates factory_boy functionality for creating test fixtures without external dependencies.

## What This Emulates

**Emulates:** factory_boy (Test fixture replacement tool)
**Original:** https://factoryboy.readthedocs.io/

## Overview

This module provides a flexible way to create test fixtures using the Factory pattern. Instead of manually creating test objects with repetitive setup code, factory_boy allows you to define factories that can generate objects with sensible defaults and customizable attributes.

## Features

- **Factory Pattern**
  - Define reusable factories for your models
  - Override attributes when needed
  - Create single or batch instances
  - Build vs Create modes

- **Sequences**
  - Auto-incrementing values for unique fields
  - Customizable sequence functions
  - Resetable counters

- **Faker Integration**
  - Generate realistic fake data
  - Multiple provider types (names, emails, addresses, etc.)
  - Customizable parameters

- **Lazy Attributes**
  - Compute attributes based on other attributes
  - Delayed evaluation during object creation

- **SubFactories**
  - Create related objects automatically
  - Support for complex object graphs
  - Nested factory relationships

- **Stubs**
  - Create dictionary-like objects for testing
  - Useful when you don't need full model instances

## Usage

### Basic Factory

```python
from factory_boy_emulator_tool.factory_boy_emulator import Factory, Sequence

class User:
    def __init__(self, username, email, is_active=True):
        self.username = username
        self.email = email
        self.is_active = is_active

class UserFactory(Factory):
    class Meta:
        model = User
    
    username = Sequence(lambda n: f"user{n}")
    email = Sequence(lambda n: f"user{n}@example.com")
    is_active = True

# Create a user
user = UserFactory.create()
print(user.username)  # "user0"
print(user.email)     # "user0@example.com"
```

### Using Faker

```python
from factory_boy_emulator_tool.factory_boy_emulator import Factory, Faker

class UserFactory(Factory):
    class Meta:
        model = User
    
    username = Faker('name')
    email = Faker('email')
    address = Faker('address')
    phone = Faker('phone_number')
    company = Faker('company')

user = UserFactory.create()
print(user.username)  # "John Smith"
print(user.email)     # "abcdefgh@example.com"
```

### Overriding Attributes

```python
# Override specific attributes
user = UserFactory.create(username='custom_user', is_active=False)
print(user.username)   # "custom_user"
print(user.is_active)  # False
```

### Batch Creation

```python
# Create multiple instances
users = UserFactory.create_batch(10)
print(len(users))  # 10

# All users have unique usernames due to Sequence
for i, user in enumerate(users):
    print(f"User {i}: {user.username}")
```

### SubFactories (Related Objects)

```python
from factory_boy_emulator_tool.factory_boy_emulator import SubFactory

class Post:
    def __init__(self, title, content, author):
        self.title = title
        self.content = content
        self.author = author

class PostFactory(Factory):
    class Meta:
        model = Post
    
    title = Sequence(lambda n: f"Post {n}")
    content = Faker('text')
    author = SubFactory(UserFactory)

# Creates a post with an automatically created user
post = PostFactory.create()
print(post.title)           # "Post 0"
print(post.author.username) # "user0"
```

### Lazy Attributes

```python
from factory_boy_emulator_tool.factory_boy_emulator import LazyAttribute

class UserFactory(Factory):
    class Meta:
        model = User
    
    first_name = 'John'
    last_name = 'Doe'
    # Email is computed from other attributes
    email = LazyAttribute(lambda stub: f"{stub.first_name.lower()}.{stub.last_name.lower()}@example.com")

user = UserFactory.create()
print(user.email)  # "john.doe@example.com"

user = UserFactory.create(first_name='Jane')
print(user.email)  # "jane.doe@example.com"
```

### Using Stubs

```python
# Create a stub (dictionary-like object) instead of model instance
stub = UserFactory.stub()
print(stub.username)  # "user0"
print(stub.email)     # "user0@example.com"
```

### Resetting Sequences

```python
# Reset sequence counters
UserFactory.reset_sequence()
user1 = UserFactory.create()
print(user1.username)  # "user0"

# Reset to specific value
UserFactory.reset_sequence(value=100)
user2 = UserFactory.create()
print(user2.username)  # "user100"
```

## Faker Providers

The emulator includes built-in fake data generators:

- `name` - Random names
- `email` - Random email addresses
- `text` - Random text (supports `max_nb_chars` parameter)
- `url` - Random URLs
- `address` - Random addresses
- `phone_number` - Random phone numbers
- `company` - Random company names
- `date` - Random dates
- `datetime` - Random datetimes
- `random_int` - Random integers (supports `min` and `max` parameters)

## Implementation Details

### Pure Python Implementation

This emulator is implemented using only Python standard library:
- No external dependencies required
- Uses metaclasses for factory definition
- Implements lazy evaluation for attributes
- Thread-safe sequence counters

### Differences from factory_boy

This is a simplified emulator. Some advanced features are not implemented:
- No database integration (Django ORM, SQLAlchemy)
- No post-generation hooks
- Simplified trait system
- Basic faker implementation (not as comprehensive as Faker library)
- No file field support
- No image field support

For production use cases requiring these features, use the official factory_boy library.

## Testing

Run the included tests:

```bash
python factory_boy_emulator_tool/test_factory_boy_emulator.py
```

## Common Patterns

### Multiple Factories for Same Model

```python
class ActiveUserFactory(UserFactory):
    is_active = True

class InactiveUserFactory(UserFactory):
    is_active = False
```

### Factory Inheritance

```python
class BaseUserFactory(Factory):
    class Meta:
        model = User
    
    username = Sequence(lambda n: f"user{n}")
    email = Sequence(lambda n: f"user{n}@example.com")

class AdminUserFactory(BaseUserFactory):
    is_admin = True
    username = Sequence(lambda n: f"admin{n}")
```

### Complex Object Graphs

```python
class CommentFactory(Factory):
    class Meta:
        model = Comment
    
    text = Faker('text')
    post = SubFactory(PostFactory)
    author = SubFactory(UserFactory)

# This creates: Comment -> Post (with User) + User
comment = CommentFactory.create()
```

## License

See LICENSE file in the repository root.
