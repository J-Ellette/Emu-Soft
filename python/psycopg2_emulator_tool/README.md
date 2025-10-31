# psycopg2 Emulator - PostgreSQL Database Adapter

A Python implementation that emulates the core functionality of psycopg2, the most popular PostgreSQL adapter for Python.

## Overview

This emulator provides a DB-API 2.0 compliant interface for PostgreSQL database operations, implementing the essential features of psycopg2 without external dependencies (beyond Python's standard library).

## Features

### Core Functionality
- **DB-API 2.0 Compliance**: Full compliance with Python Database API Specification v2.0
- **Connection Management**: Connect, commit, rollback, and close operations
- **Cursor Operations**: Execute queries, fetch results, manage transactions
- **Parameterized Queries**: Support for both positional (%s) and named (%(name)s) parameters
- **Context Managers**: Both connections and cursors support `with` statements
- **Iterator Protocol**: Cursors can be iterated over directly

### Query Support
- SELECT queries with result fetching
- INSERT queries with RETURNING clause support
- UPDATE and DELETE operations
- DDL statements (CREATE, DROP, ALTER)
- Parameterized query execution
- Bulk operations with `executemany()`

### Type Handling
- Automatic type conversion for common Python types
- NULL value handling
- Boolean type support
- Numeric types (int, float)
- String escaping and sanitization
- Date, time, and datetime conversion
- JSON/JSONB support for dict and list types

### Exception Hierarchy
Complete exception hierarchy matching psycopg2:
- `DatabaseError` - Base exception
- `InterfaceError` - Interface-related errors
- `OperationalError` - Database operation errors
- `ProgrammingError` - Programming errors
- `IntegrityError` - Constraint violations
- `DataError` - Data-related errors
- `NotSupportedError` - Unsupported operations

## Usage

### Basic Connection

```python
from psycopg2_emulator import connect

# Create a connection
conn = connect(
    host='localhost',
    port=5432,
    database='mydb',
    user='myuser',
    password='mypassword'
)

# Create a cursor
cursor = conn.cursor()

# Execute a query
cursor.execute("SELECT * FROM users WHERE age > %s", (25,))

# Fetch results
for row in cursor:
    print(row)

# Commit and close
conn.commit()
cursor.close()
conn.close()
```

### Using Context Managers

```python
from psycopg2_emulator import connect

# Connection automatically commits on success, rolls back on error
with connect(database='mydb', user='myuser', password='mypass') as conn:
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)",
                      ('John Doe', 'john@example.com'))
        # Automatically closed when context exits
```

### Named Parameters

```python
cursor.execute(
    "SELECT * FROM users WHERE name = %(name)s AND age = %(age)s",
    {'name': 'John', 'age': 30}
)
```

### Bulk Operations

```python
data = [
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com'),
    ('Charlie', 'charlie@example.com'),
]

cursor.executemany(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    data
)
```

### Fetching Results

```python
cursor.execute("SELECT * FROM users")

# Fetch one row at a time
row = cursor.fetchone()

# Fetch multiple rows
rows = cursor.fetchmany(10)

# Fetch all remaining rows
all_rows = cursor.fetchall()

# Or iterate directly
for row in cursor:
    print(row)
```

### Working with RETURNING Clause

```python
cursor.execute(
    "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
    ('John Doe', 'john@example.com')
)

# Get the inserted ID
new_id = cursor.lastrowid
print(f"Inserted user with ID: {new_id}")
```

### Type Conversion Helpers

```python
from psycopg2_emulator import Date, Time, Timestamp, Binary

# Date types
cursor.execute(
    "INSERT INTO events (name, event_date) VALUES (%s, %s)",
    ('Conference', Date(2024, 6, 15))
)

# Timestamps
cursor.execute(
    "INSERT INTO logs (message, created_at) VALUES (%s, %s)",
    ('Error occurred', Timestamp(2024, 1, 15, 10, 30, 0))
)

# Binary data
cursor.execute(
    "INSERT INTO files (name, data) VALUES (%s, %s)",
    ('image.png', Binary(b'\x89PNG\r\n\x1a\n...'))
)
```

### Error Handling

```python
from psycopg2_emulator import connect, OperationalError, ProgrammingError

try:
    conn = connect(database='mydb', user='myuser')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nonexistent_table")
except OperationalError as e:
    print(f"Database operation failed: {e}")
except ProgrammingError as e:
    print(f"Query error: {e}")
finally:
    if conn:
        conn.close()
```

## DB-API 2.0 Compliance

This emulator adheres to the Python Database API Specification v2.0:

- `apilevel`: '2.0'
- `threadsafety`: 2 (Threads may share the module and connections)
- `paramstyle`: 'pyformat' (Python extended format codes, e.g., %(name)s)

### Type Objects

Type comparison objects for column type checking:
- `STRING` - Text, varchar, char types
- `BINARY` - Bytea, blob types
- `NUMBER` - Integer, numeric, decimal types
- `DATETIME` - Timestamp, date, time types
- `ROWID` - OID type

## Architecture

### Connection Class
Manages database connections with the following features:
- Connection establishment and teardown
- Transaction management (commit/rollback)
- Cursor factory
- Context manager support
- Autocommit mode

### Cursor Class
Handles query execution and result management:
- Query execution with parameter binding
- Result fetching (fetchone, fetchmany, fetchall)
- Result set metadata (description, rowcount)
- Iterator protocol
- Context manager support

### Query Parameter Handling
- Positional parameters using %s placeholders
- Named parameters using %(name)s placeholders
- Automatic type conversion and SQL escaping
- Protection against SQL injection through proper escaping

## Implementation Notes

### Simulated vs. Real Implementation

This is an **emulator** designed for:
- Learning and understanding psycopg2 architecture
- Testing code that uses psycopg2 without a real PostgreSQL server
- Demonstrating DB-API 2.0 compliance
- Prototyping database-dependent applications

**Not suitable for:**
- Production database operations
- Performance-critical applications
- Real PostgreSQL server communication

### Key Differences from psycopg2

1. **No Network Communication**: Doesn't actually connect to PostgreSQL
2. **Simulated Results**: Query execution is simulated, not real
3. **Limited Type System**: Simplified type conversion
4. **No Advanced Features**: Missing advanced psycopg2 features like:
   - Connection pooling
   - Server-side cursors
   - COPY operations
   - Notification/LISTEN support
   - Custom type adapters

## Testing

Run the test suite:

```bash
cd psycopg2_emulator_tool
python -m pytest test_psycopg2_emulator.py -v
```

Or using unittest:

```bash
python test_psycopg2_emulator.py
```

Test coverage includes:
- Connection lifecycle management
- Cursor operations
- Parameter binding and escaping
- Transaction management
- Exception handling
- Context manager behavior
- DB-API 2.0 compliance
- Type conversion helpers

## Compatibility

- Python 3.7+
- No external dependencies
- Cross-platform (Windows, macOS, Linux)

## Use Cases

1. **Development**: Test database code without PostgreSQL server
2. **Education**: Learn psycopg2 and database programming concepts
3. **Prototyping**: Rapid application development with mock database
4. **Testing**: Unit tests for database-dependent code
5. **Documentation**: Understanding DB-API 2.0 specification

## Limitations

As an emulator, this implementation:
- Does not validate SQL syntax
- Does not enforce database constraints
- Does not perform actual data persistence
- Does not support all PostgreSQL-specific features
- May not handle all edge cases of the real psycopg2

## Future Enhancements

Potential improvements:
- In-memory SQLite backend for actual query execution
- More comprehensive type system
- Better SQL parsing and validation
- Connection pooling support
- Async/await support (like psycopg3)

## References

- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [Python DB-API 2.0 Specification](https://www.python.org/dev/peps/pep-0249/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## License

This is an original implementation created for educational and development purposes. It emulates the API of psycopg2 but contains no code from the original project.
