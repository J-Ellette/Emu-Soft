# asyncpg Emulator - Async PostgreSQL Database Adapter

A Python implementation that emulates the core functionality of asyncpg, a fast PostgreSQL database client library for Python/asyncio.

## Overview

This emulator provides an async/await interface for PostgreSQL database operations, implementing the essential features of asyncpg without external dependencies (beyond Python's standard library).

## Features

### Core Functionality
- **Async/Await Interface**: Full async/await support for non-blocking database operations
- **Connection Management**: Async connect, execute, fetch, and close operations
- **Connection Pooling**: Built-in connection pool with min/max size configuration
- **Record Objects**: Rich record objects with dict-like and tuple-like access
- **Transactions**: Full transaction support with isolation levels
- **Parameterized Queries**: Support for positional parameters ($1, $2, etc.)
- **Context Managers**: Both connections and pools support async context managers

### Query Support
- `fetch()` - Fetch all results
- `fetchrow()` - Fetch single row
- `fetchval()` - Fetch single value
- `execute()` - Execute command (INSERT, UPDATE, DELETE, DDL)
- `executemany()` - Bulk operations
- COPY operations (basic support)

### Connection Pool Features
- Configurable min/max pool size
- Connection lifecycle management
- Automatic connection reuse
- Pool-level query methods
- Acquire/release with context managers

### Type Handling
- Automatic type conversion for common Python types
- NULL value handling
- Boolean type support
- Numeric types (int, float)
- String escaping and sanitization
- Date, time, and datetime conversion
- JSON/JSONB support for dict and list types
- Binary data (bytea) support

### Exception Hierarchy
Complete exception hierarchy matching asyncpg:
- `PostgresError` - Base exception
- `InterfaceError` - Interface-related errors
- `ConnectionError` - Connection errors
- `DataError` - Data-related errors
- `IntegrityConstraintViolationError` - Constraint violations
- `SyntaxError` - SQL syntax errors

## Usage

### Basic Connection

```python
import asyncio
from asyncpg_emulator import connect

async def main():
    # Create a connection
    conn = await connect(
        host='localhost',
        port=5432,
        database='mydb',
        user='myuser',
        password='mypassword'
    )
    
    # Execute a query
    rows = await conn.fetch('SELECT * FROM users WHERE age > $1', 25)
    
    # Print results
    for row in rows:
        print(f"ID: {row['id']}, Name: {row['name']}, Email: {row['email']}")
    
    # Close connection
    await conn.close()

# Run the async function
asyncio.run(main())
```

### Using DSN (Data Source Name)

```python
from asyncpg_emulator import connect

async def main():
    conn = await connect(dsn='postgresql://user:pass@localhost:5432/mydb')
    
    # Use the connection
    rows = await conn.fetch('SELECT * FROM users')
    
    await conn.close()

asyncio.run(main())
```

### Fetching Data

```python
async def fetch_examples():
    conn = await connect(database='mydb', user='myuser', password='mypass')
    
    # Fetch all rows
    all_users = await conn.fetch('SELECT * FROM users')
    
    # Fetch single row
    user = await conn.fetchrow('SELECT * FROM users WHERE id = $1', 42)
    if user:
        print(f"Name: {user['name']}")
    
    # Fetch single value
    count = await conn.fetchval('SELECT COUNT(*) FROM users')
    print(f"Total users: {count}")
    
    await conn.close()
```

### Executing Commands

```python
async def execute_examples():
    conn = await connect(database='mydb', user='myuser', password='mypass')
    
    # INSERT
    await conn.execute(
        'INSERT INTO users (name, email) VALUES ($1, $2)',
        'John Doe', 'john@example.com'
    )
    
    # UPDATE
    await conn.execute(
        'UPDATE users SET email = $1 WHERE id = $2',
        'newemail@example.com', 42
    )
    
    # DELETE
    await conn.execute('DELETE FROM users WHERE id = $1', 42)
    
    await conn.close()
```

### Bulk Operations

```python
async def bulk_insert():
    conn = await connect(database='mydb', user='myuser', password='mypass')
    
    data = [
        ('Alice', 'alice@example.com'),
        ('Bob', 'bob@example.com'),
        ('Charlie', 'charlie@example.com'),
    ]
    
    await conn.executemany(
        'INSERT INTO users (name, email) VALUES ($1, $2)',
        data
    )
    
    await conn.close()
```

### Transactions

```python
async def transaction_example():
    conn = await connect(database='mydb', user='myuser', password='mypass')
    
    # Transaction with automatic commit/rollback
    async with conn.transaction():
        await conn.execute(
            'INSERT INTO users (name, email) VALUES ($1, $2)',
            'Jane Doe', 'jane@example.com'
        )
        await conn.execute(
            'UPDATE accounts SET balance = balance - $1 WHERE user_id = $2',
            100, 1
        )
        # Commits automatically on success, rolls back on exception
    
    await conn.close()
```

### Transaction with Isolation Level

```python
async def isolated_transaction():
    conn = await connect(database='mydb', user='myuser', password='mypass')
    
    async with conn.transaction(isolation='serializable'):
        rows = await conn.fetch('SELECT * FROM accounts WHERE balance > $1', 1000)
        # Process rows...
    
    await conn.close()
```

### Connection Pool

```python
from asyncpg_emulator import create_pool

async def pool_example():
    # Create a connection pool
    pool = await create_pool(
        host='localhost',
        database='mydb',
        user='myuser',
        password='mypass',
        min_size=10,
        max_size=20
    )
    
    # Use pool-level query methods
    users = await pool.fetch('SELECT * FROM users WHERE age > $1', 21)
    
    # Or acquire a connection manually
    async with pool.acquire_context() as conn:
        await conn.execute('INSERT INTO users (name) VALUES ($1)', 'Test User')
    
    # Close the pool
    await pool.close()

asyncio.run(pool_example())
```

### Pool with DSN

```python
async def pool_with_dsn():
    pool = await create_pool(
        dsn='postgresql://user:pass@localhost:5432/mydb',
        min_size=5,
        max_size=10
    )
    
    count = await pool.fetchval('SELECT COUNT(*) FROM users')
    print(f"Total users: {count}")
    
    await pool.close()
```

### Record Access Patterns

```python
async def record_access():
    conn = await connect(database='mydb', user='myuser', password='mypass')
    
    row = await conn.fetchrow('SELECT id, name, email FROM users WHERE id = $1', 1)
    
    if row:
        # Dictionary-style access
        print(f"Name: {row['name']}")
        
        # Index-style access
        print(f"ID: {row[0]}")
        
        # Iteration
        for value in row:
            print(value)
        
        # Keys, values, items
        print(f"Columns: {row.keys()}")
        print(f"Values: {row.values()}")
        print(f"Items: {row.items()}")
        
        # Get with default
        email = row.get('email', 'no-email@example.com')
    
    await conn.close()
```

### Error Handling

```python
from asyncpg_emulator import connect, InterfaceError, PostgresError

async def error_handling():
    conn = None
    try:
        conn = await connect(database='mydb', user='myuser')
        await conn.execute('SELECT * FROM nonexistent_table')
    except InterfaceError as e:
        print(f"Interface error: {e}")
    except PostgresError as e:
        print(f"Database error: {e}")
    finally:
        if conn and not conn.is_closed():
            await conn.close()
```

## Architecture

### Connection Class
Manages async database connections with the following features:
- Connection establishment and teardown
- Query execution with parameter binding
- Result fetching (multiple strategies)
- Transaction management
- Custom type codec support
- COPY operations

### Pool Class
Manages a pool of connections:
- Connection acquisition and release
- Min/max pool size management
- Connection lifecycle management
- Pool-level query methods
- Context manager support

### Record Class
Represents a database row:
- Dict-like access by column name
- Tuple-like access by index
- Iterator protocol
- Keys, values, items methods
- Get method with default

### Transaction Class
Context manager for transactions:
- Automatic BEGIN/COMMIT/ROLLBACK
- Isolation level support
- Read-only and deferrable options
- Exception-based rollback

## Implementation Notes

### Simulated vs. Real Implementation

This is an **emulator** designed for:
- Learning and understanding asyncpg architecture
- Testing async code that uses asyncpg without a real PostgreSQL server
- Demonstrating async database patterns
- Prototyping async database-dependent applications

**Not suitable for:**
- Production database operations
- Performance-critical applications
- Real PostgreSQL server communication

### Key Differences from asyncpg

1. **No Network Communication**: Doesn't actually connect to PostgreSQL
2. **Simulated Results**: Query execution is simulated, not real
3. **Limited Type System**: Simplified type conversion
4. **No Protocol Implementation**: Missing low-level PostgreSQL protocol
5. **No Advanced Features**: Missing features like:
   - Server-side prepared statements
   - Cursors for streaming large result sets
   - Binary protocol support
   - Notification/LISTEN support
   - Custom type codecs (stub implementation only)

## Testing

Run the test suite:

```bash
cd asyncpg_emulator_tool
python -m pytest test_asyncpg_emulator.py -v
```

Or using unittest:

```bash
python test_asyncpg_emulator.py
```

Test coverage includes:
- Connection lifecycle management
- Query execution and fetching
- Parameter binding and escaping
- Transaction management
- Connection pool operations
- Record object functionality
- Exception handling
- Context manager behavior

## Compatibility

- Python 3.7+ (requires async/await support)
- No external dependencies
- Cross-platform (Windows, macOS, Linux)

## Use Cases

1. **Development**: Test async database code without PostgreSQL server
2. **Education**: Learn asyncpg and async database programming concepts
3. **Prototyping**: Rapid development of async applications with mock database
4. **Testing**: Unit tests for async database-dependent code
5. **Documentation**: Understanding async patterns and connection pooling

## Limitations

As an emulator, this implementation:
- Does not validate SQL syntax
- Does not enforce database constraints
- Does not perform actual data persistence
- Does not support all PostgreSQL-specific features
- May not handle all edge cases of the real asyncpg
- Performance characteristics don't match real asyncpg

## Performance Notes

The real asyncpg is known for being one of the fastest PostgreSQL drivers. This emulator:
- Focuses on API compatibility, not performance
- Uses simulated async operations (`await asyncio.sleep(0)`)
- Does not implement the binary protocol
- Should not be used for benchmarking or performance testing

## Future Enhancements

Potential improvements:
- In-memory SQLite backend for actual query execution
- More comprehensive type system with custom codecs
- Better SQL parsing and validation
- Prepared statement simulation
- Streaming cursor support
- Better COPY operation support

## References

- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

## License

This is an original implementation created for educational and development purposes. It emulates the API of asyncpg but contains no code from the original project.
