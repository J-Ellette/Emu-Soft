"""
asyncpg Emulator - Async PostgreSQL Database Adapter
Emulates the popular asyncpg library for async PostgreSQL database connections
"""

import asyncio
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple, Union, Sequence
from datetime import datetime, date, time
import json


class PostgresError(Exception):
    """Base exception for PostgreSQL errors"""
    pass


class InterfaceError(PostgresError):
    """Exception for interface errors"""
    pass


class ConnectionError(PostgresError):
    """Exception for connection errors"""
    pass


class DataError(PostgresError):
    """Exception for data-related errors"""
    pass


class IntegrityConstraintViolationError(PostgresError):
    """Exception for integrity constraint violations"""
    pass


class SyntaxError(PostgresError):
    """Exception for SQL syntax errors"""
    pass


class Record:
    """A record (row) returned from a query"""
    
    def __init__(self, data: Dict[str, Any], columns: List[str]):
        """Initialize a record
        
        Args:
            data: Dictionary of column name to value
            columns: List of column names in order
        """
        self._data = data
        self._columns = columns
    
    def __getitem__(self, key: Union[str, int]) -> Any:
        """Get value by column name or index
        
        Args:
            key: Column name (str) or index (int)
            
        Returns:
            Value at the specified column
        """
        if isinstance(key, int):
            if key < 0 or key >= len(self._columns):
                raise IndexError(f"Record index out of range: {key}")
            return self._data[self._columns[key]]
        elif isinstance(key, str):
            if key not in self._data:
                raise KeyError(f"Column not found: {key}")
            return self._data[key]
        else:
            raise TypeError(f"Record indices must be integers or strings, not {type(key).__name__}")
    
    def __len__(self) -> int:
        """Return number of columns"""
        return len(self._columns)
    
    def __iter__(self):
        """Iterate over values in column order"""
        for col in self._columns:
            yield self._data[col]
    
    def __repr__(self) -> str:
        """String representation"""
        items = ', '.join(f"{k}={repr(v)}" for k, v in self._data.items())
        return f"<Record {items}>"
    
    def keys(self) -> List[str]:
        """Return list of column names"""
        return self._columns.copy()
    
    def values(self) -> List[Any]:
        """Return list of values in column order"""
        return [self._data[col] for col in self._columns]
    
    def items(self) -> List[Tuple[str, Any]]:
        """Return list of (column, value) tuples"""
        return [(col, self._data[col]) for col in self._columns]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default if not found"""
        return self._data.get(key, default)


class Connection:
    """Async PostgreSQL database connection"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str, **kwargs):
        """Initialize connection (don't call directly, use connect())
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Username
            password: Password
            **kwargs: Additional connection parameters
        """
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password
        self._closed = False
        self._in_transaction = False
        self._simulated_data: Dict[str, List[Dict]] = {}
        
    async def close(self) -> None:
        """Close the database connection"""
        if not self._closed:
            self._closed = True
            await asyncio.sleep(0)  # Simulate async operation
    
    def is_closed(self) -> bool:
        """Check if connection is closed"""
        return self._closed
    
    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> List[Record]:
        """Execute a query and fetch all results
        
        Args:
            query: SQL query string
            *args: Query parameters
            timeout: Optional query timeout
            
        Returns:
            List of Record objects
            
        Raises:
            InterfaceError: If connection is closed
        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        
        # Simulate async database query
        await asyncio.sleep(0)
        
        # Format query with parameters
        formatted_query = self._format_query(query, args)
        
        # Simulate query execution
        results = self._execute_query(formatted_query)
        
        # Convert to Record objects
        if results and len(results) > 0:
            columns = list(results[0].keys())
            return [Record(row, columns) for row in results]
        return []
    
    async def fetchrow(self, query: str, *args, timeout: Optional[float] = None) -> Optional[Record]:
        """Execute a query and fetch one result
        
        Args:
            query: SQL query string
            *args: Query parameters
            timeout: Optional query timeout
            
        Returns:
            Single Record object or None if no results
        """
        results = await self.fetch(query, *args, timeout=timeout)
        return results[0] if results else None
    
    async def fetchval(self, query: str, *args, column: int = 0, timeout: Optional[float] = None) -> Any:
        """Execute a query and fetch a single value
        
        Args:
            query: SQL query string
            *args: Query parameters
            column: Column index to return (default 0)
            timeout: Optional query timeout
            
        Returns:
            Single value from the result
        """
        row = await self.fetchrow(query, *args, timeout=timeout)
        if row is None:
            return None
        return row[column]
    
    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """Execute a command (no results expected)
        
        Args:
            query: SQL command string
            *args: Command parameters
            timeout: Optional command timeout
            
        Returns:
            Status string (e.g., "INSERT 0 1")
        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        
        await asyncio.sleep(0)  # Simulate async operation
        
        # Format query with parameters
        formatted_query = self._format_query(query, args)
        
        # Simulate command execution
        query_upper = formatted_query.upper()
        
        if 'INSERT' in query_upper:
            return "INSERT 0 1"
        elif 'UPDATE' in query_upper:
            return "UPDATE 1"
        elif 'DELETE' in query_upper:
            return "DELETE 1"
        elif 'CREATE' in query_upper:
            return "CREATE TABLE"
        elif 'DROP' in query_upper:
            return "DROP TABLE"
        else:
            return "OK"
    
    async def executemany(self, query: str, args_list: List[Sequence], timeout: Optional[float] = None) -> None:
        """Execute a command multiple times with different parameters
        
        Args:
            query: SQL command string
            args_list: List of parameter tuples
            timeout: Optional command timeout
        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        
        await asyncio.sleep(0)  # Simulate async operation
        
        for args in args_list:
            await self.execute(query, *args, timeout=timeout)
    
    def transaction(self, *, isolation: str = 'read_committed', readonly: bool = False,
                    deferrable: bool = False) -> 'Transaction':
        """Create a transaction context manager
        
        Args:
            isolation: Transaction isolation level
            readonly: Whether transaction is read-only
            deferrable: Whether transaction is deferrable
            
        Returns:
            Transaction context manager
        """
        return Transaction(self, isolation=isolation, readonly=readonly, deferrable=deferrable)
    
    async def copy_from_table(self, table_name: str, *, output, columns: Optional[List[str]] = None,
                             schema_name: Optional[str] = None, timeout: Optional[float] = None,
                             format: Optional[str] = None, oids: Optional[bool] = None,
                             delimiter: Optional[str] = None, null: Optional[str] = None,
                             header: Optional[bool] = None, quote: Optional[str] = None,
                             escape: Optional[str] = None, force_quote: Optional[bool] = None,
                             force_not_null: Optional[List[str]] = None, 
                             force_null: Optional[List[str]] = None,
                             encoding: Optional[str] = None) -> str:
        """Copy table data to output (COPY TO)
        
        Args:
            table_name: Name of the table
            output: Output stream or path
            columns: Optional list of columns
            Various COPY options...
            
        Returns:
            Status string
        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        
        await asyncio.sleep(0)
        return "COPY 0"
    
    async def copy_to_table(self, table_name: str, *, source, columns: Optional[List[str]] = None,
                           schema_name: Optional[str] = None, timeout: Optional[float] = None,
                           format: Optional[str] = None, oids: Optional[bool] = None,
                           freeze: Optional[bool] = None, delimiter: Optional[str] = None,
                           null: Optional[str] = None, header: Optional[bool] = None,
                           quote: Optional[str] = None, escape: Optional[str] = None,
                           force_quote: Optional[bool] = None,
                           force_not_null: Optional[List[str]] = None,
                           force_null: Optional[List[str]] = None,
                           encoding: Optional[str] = None) -> str:
        """Copy data from source to table (COPY FROM)
        
        Args:
            table_name: Name of the table
            source: Source stream or path
            columns: Optional list of columns
            Various COPY options...
            
        Returns:
            Status string
        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        
        await asyncio.sleep(0)
        return "COPY 0"
    
    async def set_type_codec(self, typename: str, *, schema: str = 'public',
                            encoder: Any = None, decoder: Any = None,
                            binary: bool = False, format: str = 'text') -> None:
        """Set a custom codec for a PostgreSQL data type
        
        Args:
            typename: Name of the type
            schema: Schema name
            encoder: Encoder function
            decoder: Decoder function
            binary: Whether to use binary format
            format: Format ('text' or 'binary')
        """
        await asyncio.sleep(0)
    
    async def reset_type_codec(self, typename: str, *, schema: str = 'public') -> None:
        """Reset codec for a type to default
        
        Args:
            typename: Name of the type
            schema: Schema name
        """
        await asyncio.sleep(0)
    
    def _format_query(self, query: str, parameters: Sequence) -> str:
        """Format query with positional parameters
        
        Args:
            query: SQL query with $1, $2, etc. placeholders
            parameters: Tuple of parameter values
            
        Returns:
            Formatted query string
        """
        if not parameters:
            return query
        
        # Replace $1, $2, etc. with actual values
        formatted = query
        for i, param in enumerate(parameters, 1):
            placeholder = f"${i}"
            value = self._escape_value(param)
            formatted = formatted.replace(placeholder, value)
        
        return formatted
    
    def _escape_value(self, value: Any) -> str:
        """Escape a value for SQL
        
        Args:
            value: Value to escape
            
        Returns:
            Escaped SQL string
        """
        if value is None:
            return 'NULL'
        elif isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, (date, datetime)):
            return f"'{value.isoformat()}'"
        elif isinstance(value, time):
            return f"'{value.isoformat()}'"
        elif isinstance(value, (dict, list)):
            # JSON/JSONB
            return f"'{json.dumps(value)}'"
        elif isinstance(value, bytes):
            # Bytea format
            return f"'\\x{value.hex()}'"
        else:
            return f"'{str(value)}'"
    
    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Simulate query execution
        
        Args:
            query: Formatted SQL query
            
        Returns:
            List of result dictionaries
        """
        query_upper = query.upper()
        
        # Simulate SELECT query results
        if 'SELECT' in query_upper:
            # Return simulated data
            if 'COUNT(*)' in query_upper or 'COUNT (*)' in query_upper:
                return [{'count': 42}]
            else:
                # Generic result
                return [
                    {'id': 1, 'name': 'Test User 1', 'email': 'test1@example.com'},
                    {'id': 2, 'name': 'Test User 2', 'email': 'test2@example.com'},
                ]
        
        # INSERT/UPDATE/DELETE don't return results
        return []


class Transaction:
    """Transaction context manager"""
    
    def __init__(self, connection: Connection, isolation: str = 'read_committed',
                 readonly: bool = False, deferrable: bool = False):
        """Initialize transaction
        
        Args:
            connection: Parent connection
            isolation: Isolation level
            readonly: Read-only flag
            deferrable: Deferrable flag
        """
        self._connection = connection
        self._isolation = isolation
        self._readonly = readonly
        self._deferrable = deferrable
        self._started = False
    
    async def __aenter__(self):
        """Start transaction"""
        if self._connection.is_closed():
            raise InterfaceError("Connection is closed")
        
        await asyncio.sleep(0)  # Simulate BEGIN
        self._started = True
        self._connection._in_transaction = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End transaction (commit or rollback)"""
        if not self._started:
            return
        
        if exc_type is None:
            # No exception, commit
            await asyncio.sleep(0)  # Simulate COMMIT
        else:
            # Exception occurred, rollback
            await asyncio.sleep(0)  # Simulate ROLLBACK
        
        self._connection._in_transaction = False
        self._started = False
        return False  # Don't suppress exceptions
    
    async def start(self) -> None:
        """Manually start the transaction"""
        await self.__aenter__()
    
    async def commit(self) -> None:
        """Commit the transaction"""
        if not self._started:
            raise InterfaceError("Transaction not started")
        await asyncio.sleep(0)
    
    async def rollback(self) -> None:
        """Rollback the transaction"""
        if not self._started:
            raise InterfaceError("Transaction not started")
        await asyncio.sleep(0)


class Pool:
    """Connection pool for managing multiple connections"""
    
    def __init__(self, dsn: Optional[str] = None, *, min_size: int = 10, max_size: int = 10,
                 max_queries: int = 50000, max_inactive_connection_lifetime: float = 300.0,
                 setup: Optional[Any] = None, init: Optional[Any] = None,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 connection_class: type = Connection,
                 **connect_kwargs):
        """Initialize connection pool
        
        Args:
            dsn: Connection string
            min_size: Minimum pool size
            max_size: Maximum pool size
            max_queries: Max queries per connection
            max_inactive_connection_lifetime: Max idle time
            setup: Setup callback
            init: Init callback
            loop: Event loop
            connection_class: Connection class to use
            **connect_kwargs: Connection parameters
        """
        self._min_size = min_size
        self._max_size = max_size
        self._max_queries = max_queries
        self._max_inactive_connection_lifetime = max_inactive_connection_lifetime
        self._setup = setup
        self._init = init
        self._loop = loop or asyncio.get_event_loop()
        self._connection_class = connection_class
        self._connect_kwargs = connect_kwargs
        self._closed = False
        self._connections: List[Connection] = []
        
        # Set defaults if not provided
        if 'host' not in self._connect_kwargs:
            self._connect_kwargs['host'] = 'localhost'
        if 'port' not in self._connect_kwargs:
            self._connect_kwargs['port'] = 5432
        if 'user' not in self._connect_kwargs:
            self._connect_kwargs['user'] = ''
        if 'password' not in self._connect_kwargs:
            self._connect_kwargs['password'] = ''
        if 'database' not in self._connect_kwargs:
            self._connect_kwargs['database'] = ''
        
        # Parse DSN if provided
        if dsn:
            self._parse_dsn(dsn)
    
    def _parse_dsn(self, dsn: str) -> None:
        """Parse PostgreSQL connection string
        
        Args:
            dsn: Connection string like postgres://user:pass@host:port/db
        """
        # Simple DSN parsing
        pattern = r'postgres(?:ql)?://(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?/(.+)'
        match = re.match(pattern, dsn)
        if match:
            user, password, host, port, database = match.groups()
            if user:
                self._connect_kwargs['user'] = user
            if password:
                self._connect_kwargs['password'] = password
            self._connect_kwargs['host'] = host or 'localhost'
            self._connect_kwargs['port'] = int(port) if port else 5432
            self._connect_kwargs['database'] = database
    
    async def close(self) -> None:
        """Close all connections in the pool"""
        if not self._closed:
            for conn in self._connections:
                await conn.close()
            self._connections.clear()
            self._closed = True
    
    def is_closed(self) -> bool:
        """Check if pool is closed"""
        return self._closed
    
    async def acquire(self, *, timeout: Optional[float] = None) -> Connection:
        """Acquire a connection from the pool
        
        Args:
            timeout: Optional timeout
            
        Returns:
            Connection object
        """
        if self._closed:
            raise InterfaceError("Pool is closed")
        
        # Get or create connection
        if self._connections:
            return self._connections.pop()
        else:
            conn = self._connection_class(**self._connect_kwargs)
            return conn
    
    async def release(self, connection: Connection) -> None:
        """Release a connection back to the pool
        
        Args:
            connection: Connection to release
        """
        if not self._closed and len(self._connections) < self._max_size:
            self._connections.append(connection)
        else:
            await connection.close()
    
    def acquire_context(self) -> 'PoolAcquireContext':
        """Get a context manager for acquiring a connection
        
        Returns:
            PoolAcquireContext
        """
        return PoolAcquireContext(self)
    
    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> List[Record]:
        """Execute query using a pooled connection"""
        async with self.acquire_context() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args, timeout: Optional[float] = None) -> Optional[Record]:
        """Execute query and fetch one row using a pooled connection"""
        async with self.acquire_context() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def fetchval(self, query: str, *args, column: int = 0, timeout: Optional[float] = None) -> Any:
        """Execute query and fetch single value using a pooled connection"""
        async with self.acquire_context() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)
    
    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """Execute command using a pooled connection"""
        async with self.acquire_context() as conn:
            return await conn.execute(query, *args, timeout=timeout)
    
    async def executemany(self, query: str, args_list: List[Sequence], timeout: Optional[float] = None) -> None:
        """Execute command multiple times using a pooled connection"""
        async with self.acquire_context() as conn:
            return await conn.executemany(query, args_list, timeout=timeout)


class PoolAcquireContext:
    """Context manager for acquiring connections from a pool"""
    
    def __init__(self, pool: Pool):
        """Initialize context
        
        Args:
            pool: Connection pool
        """
        self._pool = pool
        self._connection: Optional[Connection] = None
    
    async def __aenter__(self) -> Connection:
        """Acquire connection"""
        self._connection = await self._pool.acquire()
        return self._connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release connection"""
        if self._connection:
            await self._pool.release(self._connection)
        return False


async def connect(dsn: Optional[str] = None, *, host: str = 'localhost', port: int = 5432,
                  user: str = '', password: str = '', database: str = '',
                  timeout: float = 60.0, command_timeout: Optional[float] = None,
                  ssl: Optional[Any] = None, direct_tls: bool = False,
                  server_settings: Optional[Dict[str, str]] = None,
                  **kwargs) -> Connection:
    """Create a new database connection
    
    Args:
        dsn: Connection string
        host: Database host
        port: Database port
        user: Username
        password: Password
        database: Database name
        timeout: Connection timeout
        command_timeout: Command timeout
        ssl: SSL context
        direct_tls: Use direct TLS
        server_settings: Server settings
        **kwargs: Additional parameters
        
    Returns:
        Connection object
    """
    # Parse DSN if provided
    if dsn:
        pattern = r'postgres(?:ql)?://(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?/(.+)'
        match = re.match(pattern, dsn)
        if match:
            dsn_user, dsn_password, dsn_host, dsn_port, dsn_database = match.groups()
            user = dsn_user or user
            password = dsn_password or password
            host = dsn_host or host
            port = int(dsn_port) if dsn_port else port
            database = dsn_database or database
    
    # Simulate async connection
    await asyncio.sleep(0)
    
    conn = Connection(host=host, port=port, database=database, user=user, password=password, **kwargs)
    return conn


async def create_pool(dsn: Optional[str] = None, *, min_size: int = 10, max_size: int = 10,
                     max_queries: int = 50000, max_inactive_connection_lifetime: float = 300.0,
                     setup: Optional[Any] = None, init: Optional[Any] = None,
                     loop: Optional[asyncio.AbstractEventLoop] = None,
                     connection_class: type = Connection,
                     **connect_kwargs) -> Pool:
    """Create a connection pool
    
    Args:
        dsn: Connection string
        min_size: Minimum pool size
        max_size: Maximum pool size
        max_queries: Max queries per connection
        max_inactive_connection_lifetime: Max idle time
        setup: Setup callback
        init: Init callback
        loop: Event loop
        connection_class: Connection class
        **connect_kwargs: Connection parameters
        
    Returns:
        Pool object
    """
    pool = Pool(dsn=dsn, min_size=min_size, max_size=max_size,
                max_queries=max_queries,
                max_inactive_connection_lifetime=max_inactive_connection_lifetime,
                setup=setup, init=init, loop=loop,
                connection_class=connection_class, **connect_kwargs)
    
    # Simulate pool initialization
    await asyncio.sleep(0)
    
    return pool


# Module-level exports
__all__ = [
    'connect',
    'create_pool',
    'Connection',
    'Pool',
    'Record',
    'Transaction',
    'PostgresError',
    'InterfaceError',
    'ConnectionError',
    'DataError',
    'IntegrityConstraintViolationError',
    'SyntaxError',
]
