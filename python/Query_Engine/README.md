# SQLAlchemy Core Emulator - SQL Toolkit and Database Abstraction

This module emulates **SQLAlchemy Core**, which is the foundational SQL toolkit and database abstraction layer for SQLAlchemy. It provides a generalized interface for creating and executing database-agnostic SQL expressions.

## What is SQLAlchemy Core?

SQLAlchemy Core is the foundational architecture for SQLAlchemy as a "database toolkit". It provides:
- **Engine**: Connection and pool management
- **SQL Expression Language**: Pythonic SQL generation
- **Schema Definition**: Table and column metadata
- **Connection Pooling**: Efficient connection reuse
- **Transaction Management**: ACID compliance
- **Result Sets**: Flexible result handling

Unlike SQLAlchemy ORM (which provides object-relational mapping), Core focuses on schema-centric usage patterns.

## Features

This emulator implements core SQLAlchemy functionality:

### Engine & Connection
- Engine creation with connection URLs
- Connection management and pooling
- Transaction support (begin, commit, rollback)
- Context manager support

### Schema Definition
- MetaData containers
- Table definitions
- Column types and constraints
- Schema creation and dropping

### SQL Expression Language
- SELECT statements with WHERE, ORDER BY, LIMIT, OFFSET
- INSERT statements
- UPDATE statements with WHERE clauses
- DELETE statements with WHERE clauses
- Column comparison operators (==, !=, <, <=, >, >=)
- Boolean operators (AND, OR)
- IN and LIKE operators

### Result Handling
- fetchone(), fetchall(), fetchmany()
- first(), scalar()
- Iterator protocol

### Data Types
- Integer, String, Text
- Boolean, DateTime, Float
- Numeric with precision/scale

## Usage Examples

### Engine and Connection

```python
from sqlalchemy_core_emulator import create_engine

# Create engine
engine = create_engine('sqlite:///database.db')

# Create connection
conn = engine.connect()

# Use connection
result = conn.execute("SELECT * FROM users")

# Close connection
conn.close()

# Using context manager
with engine.connect() as conn:
    result = conn.execute("SELECT * FROM users")
    # Connection automatically closed
```

### Schema Definition

```python
from sqlalchemy_core_emulator import (
    create_engine, MetaData, Table, Column,
    Integer, String, Boolean, DateTime
)

# Create engine and metadata
engine = create_engine('sqlite:///myapp.db')
metadata = MetaData(bind=engine)

# Define tables
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String(50), nullable=False, unique=True),
    Column('email', String(100), nullable=False),
    Column('active', Boolean, default=True),
    Column('created_at', DateTime)
)

posts = Table('posts', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(200), nullable=False),
    Column('content', String),
    Column('author_id', Integer),
    Column('published_at', DateTime)
)

# Create all tables
metadata.create_all()

# Drop all tables
metadata.drop_all()
```

### INSERT Operations

```python
from sqlalchemy_core_emulator import create_engine, MetaData, Table, Column, Integer, String

engine = create_engine('sqlite:///app.db')
metadata = MetaData(bind=engine)

users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50)),
    Column('email', String(100))
)

metadata.create_all()

# Insert single record
with engine.connect() as conn:
    stmt = users.insert().values(
        id=1,
        name='John Doe',
        email='john@example.com'
    )
    result = conn.execute(stmt)

# Insert with dictionary
with engine.connect() as conn:
    stmt = users.insert().values({
        'id': 2,
        'name': 'Jane Smith',
        'email': 'jane@example.com'
    })
    conn.execute(stmt)

# Multiple inserts
with engine.connect() as conn:
    conn.execute(users.insert().values(id=3, name='Alice', email='alice@example.com'))
    conn.execute(users.insert().values(id=4, name='Bob', email='bob@example.com'))
```

### SELECT Operations

```python
from sqlalchemy_core_emulator import create_engine, MetaData, Table, Column, Integer, String

engine = create_engine('sqlite:///app.db')
metadata = MetaData(bind=engine)

users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50)),
    Column('age', Integer)
)

# Select all
with engine.connect() as conn:
    stmt = users.select()
    result = conn.execute(stmt)
    
    for row in result:
        print(f"{row['name']}: {row['age']}")

# Select with WHERE
with engine.connect() as conn:
    stmt = users.select().where(users.c.age > 25)
    result = conn.execute(stmt)
    rows = result.fetchall()

# Multiple conditions
with engine.connect() as conn:
    stmt = users.select().where(
        (users.c.age > 18) & (users.c.name == 'John')
    )
    result = conn.execute(stmt)

# Comparison operators
with engine.connect() as conn:
    # Greater than
    stmt = users.select().where(users.c.age > 30)
    
    # Less than or equal
    stmt = users.select().where(users.c.age <= 25)
    
    # Not equal
    stmt = users.select().where(users.c.name != 'Admin')
    
    # IN operator
    stmt = users.select().where(users.c.id.in_([1, 2, 3]))

# LIMIT and OFFSET
with engine.connect() as conn:
    # First 10 records
    stmt = users.select().limit(10)
    result = conn.execute(stmt)
    
    # Skip first 5, get next 10
    stmt = users.select().offset(5).limit(10)
    result = conn.execute(stmt)

# ORDER BY
with engine.connect() as conn:
    stmt = users.select().order_by(users.c.age)
    result = conn.execute(stmt)
```

### Result Handling

```python
from sqlalchemy_core_emulator import create_engine, MetaData, Table, Column, Integer, String

engine = create_engine('sqlite:///app.db')
metadata = MetaData(bind=engine)

users = Table('users', metadata, Column('id', Integer), Column('name', String(50)))

with engine.connect() as conn:
    stmt = users.select()
    result = conn.execute(stmt)
    
    # Fetch one row at a time
    row = result.fetchone()
    print(row['name'])
    
    # Fetch all remaining rows
    all_rows = result.fetchall()
    
    # Fetch multiple rows
    some_rows = result.fetchmany(5)
    
    # Get first row only
    first_row = result.first()
    
    # Get scalar value (first column of first row)
    count = result.scalar()
    
    # Iterate over results
    for row in result:
        print(row['name'])
```

### UPDATE Operations

```python
from sqlalchemy_core_emulator import create_engine, MetaData, Table, Column, Integer, String

engine = create_engine('sqlite:///app.db')
metadata = MetaData(bind=engine)

users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50)),
    Column('email', String(100)),
    Column('status', String(20))
)

# Update specific record
with engine.connect() as conn:
    stmt = users.update().where(users.c.id == 1).values(
        email='newemail@example.com'
    )
    conn.execute(stmt)

# Update multiple columns
with engine.connect() as conn:
    stmt = users.update().where(users.c.id == 2).values(
        name='John Updated',
        email='john_new@example.com',
        status='active'
    )
    conn.execute(stmt)

# Update all records
with engine.connect() as conn:
    stmt = users.update().values(status='pending')
    conn.execute(stmt)

# Conditional update
with engine.connect() as conn:
    stmt = users.update().where(
        users.c.status == 'inactive'
    ).values(
        status='archived'
    )
    conn.execute(stmt)
```

### DELETE Operations

```python
from sqlalchemy_core_emulator import create_engine, MetaData, Table, Column, Integer, String

engine = create_engine('sqlite:///app.db')
metadata = MetaData(bind=engine)

users = Table('users', metadata, Column('id', Integer), Column('status', String(20)))

# Delete specific record
with engine.connect() as conn:
    stmt = users.delete().where(users.c.id == 5)
    conn.execute(stmt)

# Delete with condition
with engine.connect() as conn:
    stmt = users.delete().where(users.c.status == 'deleted')
    conn.execute(stmt)

# Delete multiple records
with engine.connect() as conn:
    stmt = users.delete().where(users.c.id.in_([10, 20, 30]))
    conn.execute(stmt)
```

### Transactions

```python
from sqlalchemy_core_emulator import create_engine, MetaData, Table, Column, Integer, String

engine = create_engine('sqlite:///app.db')
metadata = MetaData(bind=engine)

users = Table('users', metadata, Column('id', Integer), Column('name', String(50)))

# Automatic transaction with context manager
with engine.connect() as conn:
    conn.execute(users.insert().values(id=1, name='Alice'))
    conn.execute(users.insert().values(id=2, name='Bob'))
    # Automatically committed on successful exit

# Explicit transaction
conn = engine.connect()
trans = conn.begin()
try:
    conn.execute(users.insert().values(id=3, name='Charlie'))
    conn.execute(users.insert().values(id=4, name='Dave'))
    trans.commit()
except:
    trans.rollback()
    raise
finally:
    conn.close()

# Transaction with context manager
with engine.connect() as conn:
    with conn.begin():
        conn.execute(users.insert().values(id=5, name='Eve'))
        # Automatically committed or rolled back
```

## Complete Application Examples

### User Management System

```python
from sqlalchemy_core_emulator import (
    create_engine, MetaData, Table, Column,
    Integer, String, Boolean, DateTime
)
from datetime import datetime

# Setup
engine = create_engine('sqlite:///users.db')
metadata = MetaData(bind=engine)

users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String(50), unique=True),
    Column('email', String(100)),
    Column('active', Boolean, default=True),
    Column('created_at', DateTime)
)

metadata.create_all()

# Create user
def create_user(username, email):
    with engine.connect() as conn:
        stmt = users.insert().values(
            username=username,
            email=email,
            active=True,
            created_at=datetime.utcnow()
        )
        conn.execute(stmt)

# Get user
def get_user(username):
    with engine.connect() as conn:
        stmt = users.select().where(users.c.username == username)
        result = conn.execute(stmt)
        return result.first()

# Update user email
def update_email(username, new_email):
    with engine.connect() as conn:
        stmt = users.update().where(
            users.c.username == username
        ).values(email=new_email)
        conn.execute(stmt)

# Deactivate user
def deactivate_user(username):
    with engine.connect() as conn:
        stmt = users.update().where(
            users.c.username == username
        ).values(active=False)
        conn.execute(stmt)

# List active users
def list_active_users():
    with engine.connect() as conn:
        stmt = users.select().where(users.c.active == True)
        result = conn.execute(stmt)
        return result.fetchall()

# Usage
create_user('john_doe', 'john@example.com')
user = get_user('john_doe')
print(f"User: {user['username']}, Email: {user['email']}")

update_email('john_doe', 'john.doe@example.com')
active = list_active_users()
print(f"Active users: {len(active)}")
```

### Blog System

```python
from sqlalchemy_core_emulator import (
    create_engine, MetaData, Table, Column,
    Integer, String, Text, DateTime
)
from datetime import datetime

engine = create_engine('sqlite:///blog.db')
metadata = MetaData(bind=engine)

posts = Table('posts', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(200)),
    Column('content', Text),
    Column('author', String(50)),
    Column('published_at', DateTime)
)

comments = Table('comments', metadata,
    Column('id', Integer, primary_key=True),
    Column('post_id', Integer),
    Column('author', String(50)),
    Column('content', Text),
    Column('created_at', DateTime)
)

metadata.create_all()

# Create post
def create_post(title, content, author):
    with engine.connect() as conn:
        stmt = posts.insert().values(
            title=title,
            content=content,
            author=author,
            published_at=datetime.utcnow()
        )
        conn.execute(stmt)

# Get posts by author
def get_author_posts(author):
    with engine.connect() as conn:
        stmt = posts.select().where(posts.c.author == author)
        result = conn.execute(stmt)
        return result.fetchall()

# Add comment
def add_comment(post_id, author, content):
    with engine.connect() as conn:
        stmt = comments.insert().values(
            post_id=post_id,
            author=author,
            content=content,
            created_at=datetime.utcnow()
        )
        conn.execute(stmt)

# Get post comments
def get_post_comments(post_id):
    with engine.connect() as conn:
        stmt = comments.select().where(comments.c.post_id == post_id)
        result = conn.execute(stmt)
        return result.fetchall()

# Usage
create_post('First Post', 'This is my first blog post', 'john')
create_post('Second Post', 'Another great post', 'john')

author_posts = get_author_posts('john')
print(f"John has {len(author_posts)} posts")

add_comment(1, 'jane', 'Great post!')
post_comments = get_post_comments(1)
print(f"Post has {len(post_comments)} comments")
```

### Product Inventory

```python
from sqlalchemy_core_emulator import (
    create_engine, MetaData, Table, Column,
    Integer, String, Float, Numeric
)

engine = create_engine('sqlite:///inventory.db')
metadata = MetaData(bind=engine)

products = Table('products', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100)),
    Column('sku', String(50), unique=True),
    Column('price', Numeric(10, 2)),
    Column('stock', Integer),
    Column('category', String(50))
)

metadata.create_all()

# Add product
def add_product(name, sku, price, stock, category):
    with engine.connect() as conn:
        stmt = products.insert().values(
            name=name,
            sku=sku,
            price=price,
            stock=stock,
            category=category
        )
        conn.execute(stmt)

# Update stock
def update_stock(sku, quantity):
    with engine.connect() as conn:
        stmt = products.update().where(
            products.c.sku == sku
        ).values(stock=quantity)
        conn.execute(stmt)

# Get low stock products
def get_low_stock(threshold=10):
    with engine.connect() as conn:
        stmt = products.select().where(products.c.stock <= threshold)
        result = conn.execute(stmt)
        return result.fetchall()

# Get products by category
def get_by_category(category):
    with engine.connect() as conn:
        stmt = products.select().where(products.c.category == category)
        result = conn.execute(stmt)
        return result.fetchall()

# Usage
add_product('Laptop', 'LAP-001', 999.99, 50, 'Electronics')
add_product('Mouse', 'MSE-001', 29.99, 5, 'Electronics')

low_stock = get_low_stock(10)
print(f"Low stock items: {len(low_stock)}")

electronics = get_by_category('Electronics')
print(f"Electronics products: {len(electronics)}")

update_stock('MSE-001', 20)
```

## Testing

Run the comprehensive test suite:

```bash
python test_sqlalchemy_core_emulator.py
```

Tests cover:
- Engine creation and configuration
- Metadata and table definitions
- INSERT, SELECT, UPDATE, DELETE operations
- WHERE clauses and comparison operators
- LIMIT, OFFSET, ORDER BY
- Transaction management
- Result set handling
- Integration scenarios

## Integration with Existing Code

This emulator is designed to be compatible with SQLAlchemy Core usage patterns:

```python
# Instead of:
# from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

# Use:
from sqlalchemy_core_emulator import create_engine, MetaData, Table, Column, Integer, String

# The rest of your code remains largely unchanged
engine = create_engine('sqlite:///database.db')
metadata = MetaData(bind=engine)

users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50))
)

metadata.create_all()
```

## Use Cases

Perfect for:
- **Local Development**: Develop database applications without database server
- **Testing**: Test database logic without external dependencies
- **CI/CD**: Run tests in CI pipelines without database setup
- **Learning**: Learn SQLAlchemy Core patterns and SQL concepts
- **Prototyping**: Quickly prototype database schemas and queries
- **Offline Development**: Work on database applications without network

## Common Patterns

### Check if Table Exists

```python
if 'users' in metadata.tables:
    users_table = metadata.tables['users']
```

### Dynamic Table Access

```python
# Access columns dynamically
table = metadata.tables['users']
stmt = table.select().where(table.c.id == 1)
```

### Pagination

```python
def paginate(table, page=1, per_page=10):
    offset = (page - 1) * per_page
    with engine.connect() as conn:
        stmt = table.select().limit(per_page).offset(offset)
        result = conn.execute(stmt)
        return result.fetchall()
```

### Bulk Insert

```python
with engine.connect() as conn:
    for i in range(100):
        conn.execute(users.insert().values(
            id=i,
            name=f'User {i}'
        ))
```

## Limitations

This is an emulator for development and testing purposes:
- In-memory storage only (data is lost when process ends)
- Simplified SQL expression evaluation
- No JOIN operations
- No aggregation functions (COUNT, SUM, AVG, etc.)
- No subqueries
- No database-specific features
- Simplified transaction isolation
- No connection pooling implementation
- Limited data type validation

## Supported Operations

### Schema Operations
- ✅ MetaData, Table, Column definitions
- ✅ create_all, drop_all
- ✅ Multiple column types

### SQL Operations
- ✅ INSERT with values
- ✅ SELECT with WHERE, LIMIT, OFFSET
- ✅ UPDATE with WHERE and values
- ✅ DELETE with WHERE
- ✅ Comparison operators (==, !=, <, <=, >, >=)
- ✅ IN operator
- ✅ Boolean operators (AND, OR)

### Connection Management
- ✅ Engine creation
- ✅ Connection pooling (basic)
- ✅ Transaction support
- ✅ Context managers

### Result Handling
- ✅ fetchone, fetchall, fetchmany
- ✅ first, scalar
- ✅ Iterator protocol

## Compatibility

Emulates core features of:
- SQLAlchemy 1.4+ Core API
- Common SQL patterns
- Standard CRUD operations

## License

Part of the Emu-Soft project. See main repository LICENSE.
