# Database Layer

Custom Object-Relational Mapping (ORM) system without external dependencies.

## What This Emulates

**Emulates:** Django ORM, SQLAlchemy, Peewee
**Purpose:** Database abstraction with Pythonic API

## Features

- Object-Relational Mapping (ORM)
- Model definitions with field types
- Fluent query builder interface
- Database migrations
- Connection pooling
- Relationship management (one-to-many, many-to-many)
- Transaction support
- Query optimization

## Components

### ORM Core
- **orm.py** - Object-Relational Mapping
  - Model base class
  - Field definitions (CharField, IntegerField, etc.)
  - CRUD operations (Create, Read, Update, Delete)
  - Model relationships (ForeignKey, ManyToMany)
  - Model meta options
  - Instance methods

### Query Builder
- **query.py** - Fluent query interface
  - SQL query generation
  - Query chaining (.filter(), .exclude(), .order_by())
  - Aggregations (count, sum, avg, etc.)
  - Joins and relationships
  - Raw SQL support
  - Query optimization

### Database Connection
- **connection.py** - Connection management
  - Connection pooling
  - Connection lifecycle
  - Transaction management
  - Multiple database support
  - Connection string parsing

### Migrations
- **migrations.py** - Schema migration system
  - Migration generation
  - Schema versioning
  - Forward migrations (up)
  - Rollback migrations (down)
  - Migration history tracking

### Query Optimization
- **optimization.py** - Performance optimization
  - Query plan analysis
  - Index recommendations
  - N+1 query detection
  - Query performance metrics

## Usage Examples

### Defining Models
```python
from database.orm import Model, CharField, IntegerField, ForeignKey

class User(Model):
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100)
    age = IntegerField(null=True)
    
    class Meta:
        table_name = "users"
        indexes = ["username", "email"]

class Post(Model):
    title = CharField(max_length=200)
    content = TextField()
    author = ForeignKey(User, related_name="posts")
    
    class Meta:
        table_name = "posts"
```

### CRUD Operations
```python
# Create
user = User(username="john", email="john@example.com", age=30)
await user.save()

# Read
user = await User.get(id=1)
user = await User.get(username="john")

# Update
user.age = 31
await user.save()

# Delete
await user.delete()
```

### Querying
```python
from database.query import QueryBuilder

# Filter
users = await User.objects.filter(age__gte=18).all()

# Exclude
active_users = await User.objects.exclude(deleted=True).all()

# Order by
sorted_users = await User.objects.order_by("-created_at").all()

# Limit and offset
page = await User.objects.limit(10).offset(20).all()

# Aggregations
count = await User.objects.count()
avg_age = await User.objects.aggregate("age", "AVG")

# Join relationships
posts = await Post.objects.select_related("author").all()
for post in posts:
    print(post.author.username)  # No additional query
```

### Transactions
```python
from database.connection import db

async with db.transaction():
    user = User(username="jane")
    await user.save()
    
    post = Post(title="Hello", author=user)
    await post.save()
    # Both saved together or both rolled back
```

### Migrations
```python
from database.migrations import Migration

# Create migration
migration = Migration.create("add_user_table")
migration.add_table("users", [
    {"name": "id", "type": "INTEGER", "primary_key": True},
    {"name": "username", "type": "VARCHAR(50)"},
])
migration.save()

# Run migrations
Migration.run_all()

# Rollback
Migration.rollback()
```

## Field Types

- `CharField` - String field with max length
- `TextField` - Large text field
- `IntegerField` - Integer numbers
- `FloatField` - Floating point numbers
- `BooleanField` - True/False values
- `DateTimeField` - Date and time
- `DateField` - Date only
- `JSONField` - JSON data
- `ForeignKey` - One-to-many relationship
- `ManyToManyField` - Many-to-many relationship

## Query Operations

- `.filter(**kwargs)` - Filter by conditions
- `.exclude(**kwargs)` - Exclude by conditions
- `.get(**kwargs)` - Get single object
- `.all()` - Get all objects
- `.first()` - Get first object
- `.last()` - Get last object
- `.count()` - Count objects
- `.exists()` - Check existence
- `.order_by(*fields)` - Order results
- `.limit(n)` - Limit results
- `.offset(n)` - Offset results

## Query Lookups

- `field__exact` - Exact match
- `field__iexact` - Case-insensitive exact match
- `field__contains` - Contains substring
- `field__icontains` - Case-insensitive contains
- `field__in` - In list
- `field__gt` - Greater than
- `field__gte` - Greater than or equal
- `field__lt` - Less than
- `field__lte` - Less than or equal
- `field__startswith` - Starts with
- `field__endswith` - Ends with

## Database Support

Currently supports PostgreSQL with extensible architecture for:
- MySQL/MariaDB
- SQLite
- SQL Server

## Performance Features

- Connection pooling
- Query caching
- Lazy loading
- Eager loading (select_related, prefetch_related)
- Index optimization
- Query plan analysis

## Integration

Works with:
- Web framework (framework/ module)
- API framework (api/ module)
- Admin interface (admin/ module)
- All application modules

## Why This Was Created

Part of the CIV-ARCOS project to provide database capabilities without external ORM dependencies, enabling data persistence with a Pythonic API while maintaining self-containment.
