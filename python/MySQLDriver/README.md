# PyMySQL Emulator - Pure Python MySQL Driver

A Python implementation that emulates the core functionality of PyMySQL, a pure-Python MySQL client library.

## Overview

This emulator provides a DB-API 2.0 compliant interface for MySQL database operations, implementing the essential features of PyMySQL without external dependencies (beyond Python's standard library).

## Features

### Core Functionality
- **DB-API 2.0 Compliance**: Full compliance with Python Database API Specification v2.0
- **Connection Management**: Connect, commit, rollback, and close operations
- **Cursor Operations**: Execute queries, fetch results, manage transactions
- **DictCursor**: Return results as dictionaries instead of tuples
- **Parameterized Queries**: Support for both positional (%s) and named (%(name)s) parameters
- **Context Managers**: Both connections and cursors support `with` statements
- **Iterator Protocol**: Cursors can be iterated over directly

### Query Support
- SELECT queries with result fetching
- INSERT queries with auto-increment ID tracking
- UPDATE and DELETE operations
- DDL statements (CREATE, DROP, ALTER, TRUNCATE)
- Database selection with USE command
- Parameterized query execution
- Bulk operations with `executemany()`

### Type Handling
- Automatic type conversion for common Python types
- NULL value handling
- Boolean type support (converted to 1/0)
- Numeric types (int, float)
- String escaping with MySQL-specific rules
- Date, time, and datetime conversion
- Binary data handling with hex encoding
- JSON support for dict and list types
- Timedelta support for TIME fields

### Exception Hierarchy
Complete exception hierarchy matching PyMySQL:
- `Error` - Base exception
- `Warning` - Warning exception
- `InterfaceError` - Interface-related errors
- `DatabaseError` - Base for database errors
  - `DataError` - Data-related errors
  - `OperationalError` - Database operation errors
  - `IntegrityError` - Constraint violations
  - `InternalError` - Internal database errors
  - `ProgrammingError` - Programming errors
  - `NotSupportedError` - Unsupported operations

## Usage

### Basic Connection

```python
from pymysql_emulator import connect

# Create a connection
conn = connect(
    host='localhost',
    port=3306,
    user='myuser',
    password='mypassword',
    database='mydb',
    charset='utf8mb4'
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
from pymysql_emulator import connect

# Connection automatically commits on success, rolls back on error
with connect(user='myuser', password='mypass', database='mydb') as conn:
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)",
                      ('John Doe', 'john@example.com'))
        print(f"Inserted row with ID: {cursor.lastrowid}")
```

### Using DictCursor

```python
from pymysql_emulator import connect, DictCursor

conn = connect(
    user='myuser',
    password='mypass',
    database='mydb',
    cursorclass=DictCursor
)

cursor = conn.cursor()
cursor.execute("SELECT id, name, email FROM users")

for row in cursor:
    print(f"User {row['id']}: {row['name']} ({row['email']})")

cursor.close()
conn.close()
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
print(f"Inserted {cursor.rowcount} rows")
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

### Autocommit Mode

```python
conn = connect(user='myuser', password='mypass', autocommit=True)

# Or set it after connection
conn.autocommit(True)

# Check current setting
if conn.get_autocommit():
    print("Autocommit is enabled")
```

### Database Selection

```python
conn = connect(user='myuser', password='mypass')

# Select a database
conn.select_db('mydb')

# Or use USE statement
cursor = conn.cursor()
cursor.execute("USE mydb")
```

### Type Conversion Helpers

```python
from pymysql_emulator import Date, Time, Timestamp, Binary

# Date types
cursor.execute(
    "INSERT INTO events (name, event_date) VALUES (%s, %s)",
    ('Conference', Date(2024, 6, 15))
)

# Time types
cursor.execute(
    "INSERT INTO schedules (task, start_time) VALUES (%s, %s)",
    ('Meeting', Time(14, 30, 0))
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

### String Escaping

```python
from pymysql_emulator import escape_string

# Manual string escaping
escaped = escape_string("O'Brien")
print(escaped)  # O\'Brien

# Or use parameterized queries (recommended)
cursor.execute("INSERT INTO users (name) VALUES (%s)", ("O'Brien",))
```

### Error Handling

```python
from pymysql_emulator import connect, OperationalError, ProgrammingError

try:
    conn = connect(user='myuser', password='mypass', database='mydb')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
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
- `threadsafety`: 1 (Threads may share the module, but not connections)
- `paramstyle`: 'pyformat' (Python extended format codes, e.g., %(name)s)

### Type Objects

Type comparison objects for column type checking:
- `STRING` - VARCHAR, VAR_STRING, STRING, ENUM, SET
- `BINARY` - BLOB, LONG_BLOB, MEDIUM_BLOB, TINY_BLOB
- `NUMBER` - DECIMAL, TINY, SHORT, LONG, FLOAT, DOUBLE, etc.
- `DATETIME` - TIMESTAMP, DATE, TIME, DATETIME, YEAR
- `ROWID` - (empty for MySQL)

### Field Type Constants

MySQL field type constants are provided:
- `FIELD_TYPE_DECIMAL`, `FIELD_TYPE_TINY`, `FIELD_TYPE_SHORT`, etc.
- `FIELD_TYPE_VARCHAR`, `FIELD_TYPE_BLOB`, `FIELD_TYPE_JSON`, etc.

## Architecture

### Connection Class
Manages database connections with the following features:
- Connection establishment and teardown
- Transaction management (commit/rollback/begin)
- Cursor factory with configurable cursor class
- Context manager support
- Autocommit mode
- Database selection
- Connection ping/keepalive

### Cursor Class
Handles query execution and result management:
- Query execution with parameter binding
- Result fetching (fetchone, fetchmany, fetchall)
- Result set metadata (description, rowcount, lastrowid)
- Row number tracking
- Iterator protocol
- Context manager support

### DictCursor Class
Extends Cursor to return results as dictionaries:
- Column names as dictionary keys
- Easier access to result data
- Compatible with all Cursor methods

### Query Parameter Handling
- Positional parameters using %s placeholders
- Named parameters using %(name)s placeholders
- Automatic type conversion and SQL escaping
- MySQL-specific escape sequences
- Protection against SQL injection

## Implementation Notes

### Simulated vs. Real Implementation

This is an **emulator** designed for:
- Learning and understanding PyMySQL architecture
- Testing code that uses PyMySQL without a real MySQL server
- Demonstrating DB-API 2.0 compliance
- Prototyping database-dependent applications

**Not suitable for:**
- Production database operations
- Performance-critical applications
- Real MySQL server communication

### Key Differences from PyMySQL

1. **No Network Communication**: Doesn't actually connect to MySQL
2. **Simulated Results**: Query execution is simulated, not real
3. **Limited Type System**: Simplified type conversion
4. **No Advanced Features**: Missing advanced PyMySQL features like:
   - Connection pooling
   - SSL/TLS support
   - Server-side cursors (SSCursor, SSDictCursor)
   - Prepared statements
   - Multiple result sets
   - LOAD DATA INFILE
   - Charset negotiation

## Testing

Run the test suite:

```bash
cd pymysql_emulator_tool
python test_pymysql_emulator.py
```

Test coverage includes:
- Connection lifecycle management
- Cursor operations
- DictCursor functionality
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

1. **Development**: Test database code without MySQL server
2. **Education**: Learn PyMySQL and database programming concepts
3. **Prototyping**: Rapid application development with mock database
4. **Testing**: Unit tests for database-dependent code
5. **Documentation**: Understanding DB-API 2.0 specification

## Limitations

As an emulator, this implementation:
- Does not validate SQL syntax
- Does not enforce database constraints
- Does not perform actual data persistence
- Does not support all MySQL-specific features
- May not handle all edge cases of the real PyMySQL

## Future Enhancements

Potential improvements:
- In-memory SQLite backend for actual query execution
- More comprehensive type system
- Better SQL parsing and validation
- Connection pooling support
- Async/await support (like aiomysql)
- SSL/TLS simulation

## References

- [PyMySQL Documentation](https://pymysql.readthedocs.io/)
- [Python DB-API 2.0 Specification](https://www.python.org/dev/peps/pep-0249/)
- [MySQL Documentation](https://dev.mysql.com/doc/)

## License

This is an original implementation created for educational and development purposes. It emulates the API of PyMySQL but contains no code from the original project.
