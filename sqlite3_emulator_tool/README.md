# SQLite3 Emulator - Enhanced SQLite Integration

An enhanced version of Python's built-in sqlite3 module with additional functionality and convenience features for better SQLite database integration.

## Overview

This emulator extends Python's standard sqlite3 module with enhanced features including custom SQL functions, aggregate functions, query history tracking, database utilities, and more - all while maintaining full compatibility with the standard sqlite3 API.

## Features

### Enhanced Connection (EnhancedConnection)
- **Custom SQL Functions**: Built-in and custom user-defined functions
- **Custom Aggregates**: Statistical and custom aggregate functions
- **Database Utilities**: Backup, restore, optimize, and integrity checks
- **Metadata Access**: Easy access to tables, indexes, and schema information
- **Foreign Key Management**: Enable/disable foreign key constraints
- **Database Size Tracking**: Get database file size information

### Enhanced Cursor (EnhancedCursor)
- **Query History**: Automatic tracking of executed queries
- **Query Explanation**: Built-in EXPLAIN QUERY PLAN support
- **Full Compatibility**: Works as drop-in replacement for standard cursor

### Built-in Custom Functions
- `regexp(pattern, value)` - Regular expression matching
- `json_extract(json, path)` - Extract values from JSON strings
- `json_array_length(json)` - Get length of JSON arrays
- `md5(value)` - Calculate MD5 hash
- `sha256(value)` - Calculate SHA256 hash
- `reverse(value)` - Reverse a string
- `title_case(value)` - Convert to title case

### Built-in Aggregate Functions
- `stdev(value)` - Calculate standard deviation
- `median(value)` - Calculate median value
- `mode(value)` - Find most common value

### Enhanced Type Support
- Automatic date/datetime conversion
- JSON serialization support
- Binary data handling

## Installation

This module extends the built-in sqlite3, so no external dependencies are required:

```python
from sqlite3_emulator import connect
```

## Usage

### Basic Usage

```python
from sqlite3_emulator import connect

# Create enhanced connection
conn = connect('mydb.db')

# Use like standard sqlite3
cursor = conn.cursor()
cursor.execute("CREATE TABLE users (id INTEGER, name TEXT, email TEXT)")
cursor.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
conn.commit()

# Enhanced features work automatically
cursor.execute("SELECT * FROM users WHERE regexp('^A', name)")
for row in cursor:
    print(row)

conn.close()
```

### Using Built-in Custom Functions

```python
conn = connect(':memory:')
cursor = conn.cursor()

# Regular expression matching
cursor.execute("SELECT * FROM users WHERE regexp('^[A-Z]', name)")

# JSON extraction
cursor.execute("""
    CREATE TABLE data (id INTEGER, info TEXT)
""")
cursor.execute("""
    INSERT INTO data VALUES (1, '{"name": "John", "age": 30}')
""")
cursor.execute("SELECT json_extract(info, '$.name') FROM data")
print(cursor.fetchone()[0])  # John

# Hashing functions
cursor.execute("SELECT md5('password')")
cursor.execute("SELECT sha256('secret')")

# String manipulation
cursor.execute("SELECT reverse('hello')")  # olleh
cursor.execute("SELECT title_case('hello world')")  # Hello World

conn.close()
```

### Creating Custom Functions

```python
conn = connect(':memory:')

# Define a custom function
def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

# Register it
conn.create_custom_function("c_to_f", 1, celsius_to_fahrenheit)

# Use it in queries
cursor = conn.cursor()
cursor.execute("SELECT c_to_f(20)")
print(cursor.fetchone()[0])  # 68.0

conn.close()
```

### Using Enhanced Aggregates

```python
from sqlite3_emulator import connect, register_enhanced_aggregates

conn = connect(':memory:')
register_enhanced_aggregates(conn)

cursor = conn.cursor()
cursor.execute("CREATE TABLE scores (value REAL)")
cursor.execute("INSERT INTO scores VALUES (85), (90), (78), (92), (88)")

# Standard deviation
cursor.execute("SELECT stdev(value) FROM scores")
print(f"Std Dev: {cursor.fetchone()[0]:.2f}")

# Median
cursor.execute("SELECT median(value) FROM scores")
print(f"Median: {cursor.fetchone()[0]}")

# Mode
cursor.execute("CREATE TABLE votes (choice TEXT)")
cursor.execute("INSERT INTO votes VALUES ('A'), ('B'), ('A'), ('C'), ('A')")
cursor.execute("SELECT mode(choice) FROM votes")
print(f"Most common: {cursor.fetchone()[0]}")  # A

conn.close()
```

### Custom Aggregate Example

```python
from sqlite3_emulator import connect

class ConcatAggregate:
    """Concatenate strings with a separator"""
    def __init__(self):
        self.values = []
    
    def step(self, value):
        if value is not None:
            self.values.append(str(value))
    
    def finalize(self):
        return ', '.join(self.values)

conn = connect(':memory:')
conn.create_custom_aggregate("concat", 1, ConcatAggregate)

cursor = conn.cursor()
cursor.execute("CREATE TABLE names (name TEXT)")
cursor.execute("INSERT INTO names VALUES ('Alice'), ('Bob'), ('Charlie')")
cursor.execute("SELECT concat(name) FROM names")
print(cursor.fetchone()[0])  # Alice, Bob, Charlie

conn.close()
```

### Query History Tracking

```python
conn = connect(':memory:')
cursor = conn.cursor()

# Execute some queries
cursor.execute("CREATE TABLE test (id INTEGER)")
cursor.execute("INSERT INTO test VALUES (1)")
cursor.execute("SELECT * FROM test")

# View query history
history = cursor.get_query_history()
for query, params in history:
    print(f"Query: {query}")
    print(f"Params: {params}")
    print()

# Clear history
cursor.clear_history()

conn.close()
```

### Query Explanation

```python
conn = connect(':memory:')
cursor = conn.cursor()

cursor.execute("CREATE TABLE users (id INTEGER, name TEXT)")
cursor.execute("CREATE INDEX idx_name ON users(name)")

# Explain query plan
plan = cursor.explain("SELECT * FROM users WHERE name = 'Alice'")
for row in plan:
    print(row)

conn.close()
```

### Database Utilities

```python
conn = connect('mydb.db')

# Get all tables
tables = conn.get_tables()
print(f"Tables: {tables}")

# Get table schema
info = conn.get_table_info('users')
for column in info:
    print(f"Column: {column[1]}, Type: {column[2]}")

# Get indexes
indexes = conn.get_indexes('users')
for idx in indexes:
    print(f"Index: {idx[1]}")

# Get database size
size = conn.get_database_size()
print(f"Database size: {size} bytes")

# Check integrity
results = conn.check_integrity()
print(f"Integrity: {results}")

conn.close()
```

### Database Backup and Restore

```python
# Open source database
source_conn = connect('mydb.db')

# Backup to file
source_conn.backup('backup.db')

# Or backup to another connection
target_conn = connect('copy.db')
source_conn.backup(target_conn)

# With progress callback
def progress_callback(status, remaining, total):
    print(f"Progress: {status}/{total}")

source_conn.backup('backup2.db', progress=progress_callback)

source_conn.close()
target_conn.close()
```

### Database Optimization

```python
conn = connect('mydb.db')

# Optimize database (VACUUM + ANALYZE)
conn.optimize()

conn.close()
```

### Foreign Key Management

```python
conn = connect('mydb.db')

# Enable foreign keys
conn.enable_foreign_keys()

# Disable foreign keys
conn.disable_foreign_keys()

conn.close()
```

### Date/Time Support

```python
from sqlite3_emulator import connect, PARSE_DECLTYPES
from datetime import datetime, date

conn = connect(':memory:', detect_types=PARSE_DECLTYPES)
cursor = conn.cursor()

# Create table with date/datetime columns
cursor.execute("""
    CREATE TABLE events (
        event_date DATE,
        created_at DATETIME
    )
""")

# Insert Python date/datetime objects
today = date.today()
now = datetime.now()
cursor.execute("INSERT INTO events VALUES (?, ?)", (today, now))

# Retrieve as Python objects
cursor.execute("SELECT * FROM events")
event_date, created_at = cursor.fetchone()
print(f"Date: {event_date} (type: {type(event_date)})")
print(f"DateTime: {created_at} (type: {type(created_at)})")

conn.close()
```

### Context Manager Support

```python
from sqlite3_emulator import connect

# Automatic commit and close
with connect('mydb.db') as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT)")
    cursor.execute("INSERT INTO users VALUES (1, 'Alice')")
    # Automatically commits on success, rolls back on exception
# Connection automatically closed
```

## API Reference

### Connection Methods

#### Standard sqlite3 Methods
All standard sqlite3.Connection methods are supported.

#### Enhanced Methods

- `create_custom_function(name, num_params, func)` - Register custom SQL function
- `create_custom_aggregate(name, num_params, aggregate_class)` - Register custom aggregate
- `get_custom_functions()` - Get dictionary of registered functions
- `get_custom_aggregates()` - Get dictionary of registered aggregates
- `backup(target, pages=-1, progress=None)` - Backup database
- `optimize()` - Optimize database with VACUUM and ANALYZE
- `get_table_info(table_name)` - Get table schema information
- `get_tables()` - Get list of table names
- `get_indexes(table_name=None)` - Get index information
- `get_database_size()` - Get database size in bytes
- `enable_foreign_keys()` - Enable foreign key constraints
- `disable_foreign_keys()` - Disable foreign key constraints
- `check_integrity()` - Run integrity check

### Cursor Methods

#### Standard sqlite3 Methods
All standard sqlite3.Cursor methods are supported.

#### Enhanced Methods

- `get_query_history()` - Get list of executed queries
- `clear_history()` - Clear query history
- `explain(sql, parameters=())` - Get query execution plan

## Built-in Functions Reference

### String Functions
- `regexp(pattern, value)` - Match regular expression
- `reverse(value)` - Reverse string
- `title_case(value)` - Convert to title case

### JSON Functions
- `json_extract(json_str, path)` - Extract value from JSON (path format: $.key.subkey)
- `json_array_length(json_str)` - Get JSON array length

### Hash Functions
- `md5(value)` - MD5 hash (hex string)
- `sha256(value)` - SHA256 hash (hex string)

## Built-in Aggregates Reference

### Statistical Aggregates
- `stdev(value)` - Standard deviation
- `median(value)` - Median value
- `mode(value)` - Most frequent value

## Compatibility

- **Python Version**: 3.7+
- **SQLite Version**: Depends on Python's sqlite3 module
- **Dependencies**: None (uses only standard library)
- **Platform**: Cross-platform (Windows, macOS, Linux)

## Differences from Standard sqlite3

### Enhancements
1. Additional custom functions built-in
2. Statistical aggregate functions
3. Query history tracking
4. Enhanced utility methods
5. Improved backup functionality

### Compatibility
- 100% compatible with standard sqlite3 API
- Can be used as drop-in replacement
- All standard features work identically

## Testing

Run the test suite:

```bash
cd sqlite3_emulator_tool
python test_sqlite3_emulator.py
```

Test coverage includes:
- Enhanced connection features
- Custom functions (built-in and user-defined)
- Custom aggregates
- Query history tracking
- Database utilities
- Backup and restore
- Date/time type support
- Context manager behavior

## Use Cases

1. **Enhanced Analytics**: Use statistical aggregates for data analysis
2. **JSON Processing**: Work with JSON data stored in SQLite
3. **Security**: Hash passwords and data with built-in functions
4. **Debugging**: Track query history for troubleshooting
5. **Database Management**: Backup, optimize, and inspect databases
6. **Text Processing**: Use regex and string functions in queries
7. **Development**: Prototype with enhanced features before production

## Performance Considerations

- Custom Python functions are slower than native SQLite functions
- Query history tracking adds minimal overhead
- Backup operations can be I/O intensive for large databases
- Aggregates implemented in Python are slower than C aggregates

## Best Practices

1. **Custom Functions**: Keep functions simple and fast
2. **History Tracking**: Clear history periodically for long-running connections
3. **Backup**: Use for important data, test restore procedure
4. **Optimization**: Run optimize() periodically, not after every transaction
5. **Foreign Keys**: Enable them explicitly when needed

## Limitations

- Custom functions and aggregates are Python-based (slower than native C)
- Query history is stored in memory (can grow large)
- Not all advanced SQLite features are wrapped with convenience methods

## Future Enhancements

Potential improvements:
- More built-in functions (trigonometry, advanced string ops)
- Query performance analysis tools
- Schema migration utilities
- Full-text search helpers
- Incremental backup support

## References

- [Python sqlite3 Documentation](https://docs.python.org/3/library/sqlite3.html)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [DB-API 2.0 Specification](https://www.python.org/dev/peps/pep-0249/)

## License

This is an enhancement of Python's built-in sqlite3 module, created for educational and development purposes. All new code is original.
