"""
psycopg2 Emulator - PostgreSQL Database Adapter
Emulates the popular psycopg2 library for PostgreSQL database connections
"""

import socket
import struct
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple, Union, Sequence
from datetime import datetime, date, time
import json


class DatabaseError(Exception):
    """Base exception for database errors"""
    pass


class InterfaceError(DatabaseError):
    """Exception for interface errors"""
    pass


class OperationalError(DatabaseError):
    """Exception for operational errors"""
    pass


class ProgrammingError(DatabaseError):
    """Exception for programming errors"""
    pass


class IntegrityError(DatabaseError):
    """Exception for integrity constraint violations"""
    pass


class DataError(DatabaseError):
    """Exception for data-related errors"""
    pass


class NotSupportedError(DatabaseError):
    """Exception for unsupported operations"""
    pass


# Module-level attributes (DB-API 2.0 compliance)
apilevel = '2.0'
threadsafety = 2
paramstyle = 'pyformat'


class Cursor:
    """Database cursor for executing queries"""
    
    def __init__(self, connection: 'Connection'):
        """Initialize cursor
        
        Args:
            connection: Parent connection object
        """
        self.connection = connection
        self.description: Optional[List[Tuple]] = None
        self.rowcount: int = -1
        self.arraysize: int = 1
        self._results: List[Tuple] = []
        self._result_index: int = 0
        self.lastrowid: Optional[int] = None
        self._closed: bool = False
    
    def execute(self, query: str, parameters: Union[Tuple, Dict, None] = None) -> 'Cursor':
        """Execute a database query
        
        Args:
            query: SQL query string
            parameters: Query parameters (tuple or dict)
            
        Returns:
            Self for chaining
            
        Raises:
            ProgrammingError: If cursor is closed or query fails
        """
        if self._closed:
            raise ProgrammingError("Cannot execute on a closed cursor")
        
        # Format the query with parameters
        formatted_query = self._format_query(query, parameters)
        
        # Send query to the connection
        try:
            self._results, self.description = self.connection._execute_query(formatted_query)
            self.rowcount = len(self._results)
            self._result_index = 0
            
            # Extract lastrowid if INSERT with RETURNING
            if 'INSERT' in query.upper() and 'RETURNING' in query.upper():
                if self._results:
                    self.lastrowid = self._results[0][0]
            
            return self
        except Exception as e:
            raise ProgrammingError(f"Query execution failed: {e}")
    
    def executemany(self, query: str, parameters_list: Sequence[Union[Tuple, Dict]]) -> 'Cursor':
        """Execute a query multiple times with different parameters
        
        Args:
            query: SQL query string
            parameters_list: List of parameter sets
            
        Returns:
            Self for chaining
        """
        if self._closed:
            raise ProgrammingError("Cannot execute on a closed cursor")
        
        total_rows = 0
        for parameters in parameters_list:
            self.execute(query, parameters)
            total_rows += self.rowcount
        
        self.rowcount = total_rows
        return self
    
    def fetchone(self) -> Optional[Tuple]:
        """Fetch next row of query result
        
        Returns:
            Next row as tuple, or None if no more rows
        """
        if self._closed:
            raise ProgrammingError("Cannot fetch from a closed cursor")
        
        if self._result_index < len(self._results):
            row = self._results[self._result_index]
            self._result_index += 1
            return row
        return None
    
    def fetchmany(self, size: Optional[int] = None) -> List[Tuple]:
        """Fetch multiple rows of query result
        
        Args:
            size: Number of rows to fetch (default: arraysize)
            
        Returns:
            List of rows
        """
        if self._closed:
            raise ProgrammingError("Cannot fetch from a closed cursor")
        
        if size is None:
            size = self.arraysize
        
        result = []
        for _ in range(size):
            row = self.fetchone()
            if row is None:
                break
            result.append(row)
        return result
    
    def fetchall(self) -> List[Tuple]:
        """Fetch all remaining rows of query result
        
        Returns:
            List of all remaining rows
        """
        if self._closed:
            raise ProgrammingError("Cannot fetch from a closed cursor")
        
        result = self._results[self._result_index:]
        self._result_index = len(self._results)
        return result
    
    def close(self) -> None:
        """Close the cursor"""
        self._closed = True
        self._results = []
        self.description = None
    
    def _format_query(self, query: str, parameters: Union[Tuple, Dict, None]) -> str:
        """Format query with parameters
        
        Args:
            query: SQL query with placeholders
            parameters: Query parameters
            
        Returns:
            Formatted query string
        """
        if parameters is None:
            return query
        
        formatted_query = query
        
        if isinstance(parameters, dict):
            # Named parameters: %(name)s style
            for key, value in parameters.items():
                placeholder = f"%({key})s"
                formatted_value = self._escape_value(value)
                formatted_query = formatted_query.replace(placeholder, formatted_value)
        elif isinstance(parameters, (tuple, list)):
            # Positional parameters: %s style
            parts = formatted_query.split('%s')
            if len(parts) - 1 != len(parameters):
                raise ProgrammingError(
                    f"Query expects {len(parts) - 1} parameters, got {len(parameters)}"
                )
            
            formatted_query = parts[0]
            for i, param in enumerate(parameters):
                formatted_query += self._escape_value(param) + parts[i + 1]
        
        return formatted_query
    
    def _escape_value(self, value: Any) -> str:
        """Escape a value for SQL query
        
        Args:
            value: Value to escape
            
        Returns:
            Escaped string representation
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
        elif isinstance(value, (datetime, date, time)):
            return f"'{value.isoformat()}'"
        elif isinstance(value, (list, dict)):
            # JSON serialization for arrays/objects
            return f"'{json.dumps(value)}'"
        else:
            return f"'{str(value)}'"
    
    def __enter__(self) -> 'Cursor':
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.close()
    
    def __iter__(self):
        """Make cursor iterable"""
        return self
    
    def __next__(self):
        """Iterator protocol"""
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row


class Connection:
    """PostgreSQL database connection"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5432,
        database: str = '',
        user: str = '',
        password: str = '',
        **kwargs
    ):
        """Initialize connection
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Username
            password: Password
            **kwargs: Additional connection parameters
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.autocommit = kwargs.get('autocommit', False)
        self._closed = False
        self._in_transaction = False
        
        # Simulated connection state
        self._socket = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish database connection"""
        try:
            # In a real implementation, this would create a socket connection
            # For emulation, we just validate parameters
            if not self.database:
                raise OperationalError("Database name is required")
            if not self.user:
                raise OperationalError("Username is required")
            
            # Simulate connection (in real psycopg2, this would be a socket)
            self._socket = f"simulated_connection_{self.host}:{self.port}/{self.database}"
        except Exception as e:
            raise OperationalError(f"Could not connect to database: {e}")
    
    def cursor(self) -> Cursor:
        """Create a new cursor
        
        Returns:
            New cursor object
            
        Raises:
            InterfaceError: If connection is closed
        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        return Cursor(self)
    
    def commit(self) -> None:
        """Commit the current transaction
        
        Raises:
            OperationalError: If connection is closed
        """
        if self._closed:
            raise OperationalError("Cannot commit on a closed connection")
        
        if self._in_transaction:
            # In real implementation, send COMMIT to database
            self._in_transaction = False
    
    def rollback(self) -> None:
        """Rollback the current transaction
        
        Raises:
            OperationalError: If connection is closed
        """
        if self._closed:
            raise OperationalError("Cannot rollback on a closed connection")
        
        if self._in_transaction:
            # In real implementation, send ROLLBACK to database
            self._in_transaction = False
    
    def close(self) -> None:
        """Close the connection"""
        if not self._closed:
            if self._in_transaction:
                self.rollback()
            self._socket = None
            self._closed = True
    
    def _execute_query(self, query: str) -> Tuple[List[Tuple], Optional[List[Tuple]]]:
        """Execute a query and return results
        
        This is a simplified simulation. In a real implementation,
        this would communicate with PostgreSQL server.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Tuple of (results, description)
        """
        if self._closed:
            raise OperationalError("Connection is closed")
        
        # Mark as in transaction if not autocommit
        if not self.autocommit:
            self._in_transaction = True
        
        # Simulate query execution
        query_upper = query.upper().strip()
        
        if query_upper.startswith('SELECT'):
            # Simulate SELECT query
            return self._simulate_select(query)
        elif query_upper.startswith('INSERT'):
            # Simulate INSERT query
            return self._simulate_insert(query)
        elif query_upper.startswith('UPDATE'):
            # Simulate UPDATE query
            return self._simulate_update(query)
        elif query_upper.startswith('DELETE'):
            # Simulate DELETE query
            return self._simulate_delete(query)
        elif query_upper.startswith(('CREATE', 'DROP', 'ALTER')):
            # DDL queries
            return ([], None)
        else:
            # Other queries
            return ([], None)
    
    def _simulate_select(self, query: str) -> Tuple[List[Tuple], List[Tuple]]:
        """Simulate SELECT query execution"""
        # Parse column names from query
        columns = self._parse_select_columns(query)
        
        # Create description (column metadata)
        description = [
            (col, 'text', None, None, None, None, None)
            for col in columns
        ]
        
        # Return empty results (in real implementation, would query database)
        return ([], description)
    
    def _simulate_insert(self, query: str) -> Tuple[List[Tuple], Optional[List[Tuple]]]:
        """Simulate INSERT query execution"""
        if 'RETURNING' in query.upper():
            # Return simulated ID
            return ([(1,)], [('id', 'integer', None, None, None, None, None)])
        return ([], None)
    
    def _simulate_update(self, query: str) -> Tuple[List[Tuple], Optional[List[Tuple]]]:
        """Simulate UPDATE query execution"""
        # Simulate affected rows
        return ([], None)
    
    def _simulate_delete(self, query: str) -> Tuple[List[Tuple], Optional[List[Tuple]]]:
        """Simulate DELETE query execution"""
        # Simulate affected rows
        return ([], None)
    
    def _parse_select_columns(self, query: str) -> List[str]:
        """Parse column names from SELECT query"""
        # Simplified parsing - just return generic columns
        if '*' in query:
            return ['col1', 'col2', 'col3']
        
        # Try to extract column names
        match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE)
        if match:
            columns_str = match.group(1)
            columns = [col.strip() for col in columns_str.split(',')]
            return columns
        
        return ['col1']
    
    def __enter__(self) -> 'Connection':
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


def connect(
    host: str = 'localhost',
    port: int = 5432,
    database: str = '',
    user: str = '',
    password: str = '',
    **kwargs
) -> Connection:
    """Create a new database connection
    
    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Username
        password: Password
        **kwargs: Additional connection parameters
        
    Returns:
        New connection object
    """
    return Connection(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        **kwargs
    )


# Convenience function aliases
def Binary(data: bytes) -> bytes:
    """Construct binary data"""
    return data


def Date(year: int, month: int, day: int) -> date:
    """Construct date"""
    return date(year, month, day)


def Time(hour: int, minute: int, second: int) -> time:
    """Construct time"""
    return time(hour, minute, second)


def Timestamp(year: int, month: int, day: int, hour: int, minute: int, second: int) -> datetime:
    """Construct timestamp"""
    return datetime(year, month, day, hour, minute, second)


def DateFromTicks(ticks: float) -> date:
    """Construct date from timestamp"""
    return datetime.fromtimestamp(ticks).date()


def TimeFromTicks(ticks: float) -> time:
    """Construct time from timestamp"""
    return datetime.fromtimestamp(ticks).time()


def TimestampFromTicks(ticks: float) -> datetime:
    """Construct timestamp from ticks"""
    return datetime.fromtimestamp(ticks)


# Type objects for type comparison
class _DBAPITypeObject:
    """Type object for DB-API type comparison"""
    
    def __init__(self, *values):
        self.values = values
    
    def __eq__(self, other):
        return other in self.values


STRING = _DBAPITypeObject('text', 'varchar', 'char')
BINARY = _DBAPITypeObject('bytea', 'blob')
NUMBER = _DBAPITypeObject('integer', 'int', 'bigint', 'smallint', 'numeric', 'decimal', 'real', 'double')
DATETIME = _DBAPITypeObject('timestamp', 'date', 'time', 'timestamptz', 'timetz')
ROWID = _DBAPITypeObject('oid')
