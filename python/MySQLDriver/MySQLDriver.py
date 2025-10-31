"""
Developed by PowerShield, as an alternative to PyMySQL


PyMySQL Emulator - Pure Python MySQL Driver
Emulates the popular PyMySQL library for MySQL database connections
"""

import socket
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple, Union, Sequence
from datetime import datetime, date, time, timedelta
import json


class Error(Exception):
    """Base exception for MySQL errors"""
    pass


class Warning(Exception):
    """Exception for warnings"""
    pass


class InterfaceError(Error):
    """Exception for interface errors"""
    pass


class DatabaseError(Error):
    """Exception for database errors"""
    pass


class DataError(DatabaseError):
    """Exception for data-related errors"""
    pass


class OperationalError(DatabaseError):
    """Exception for operational errors"""
    pass


class IntegrityError(DatabaseError):
    """Exception for integrity constraint violations"""
    pass


class InternalError(DatabaseError):
    """Exception for internal database errors"""
    pass


class ProgrammingError(DatabaseError):
    """Exception for programming errors"""
    pass


class NotSupportedError(DatabaseError):
    """Exception for unsupported operations"""
    pass


# Module-level attributes (DB-API 2.0 compliance)
apilevel = '2.0'
threadsafety = 1
paramstyle = 'pyformat'

# MySQL client/server constants
FIELD_TYPE_DECIMAL = 0
FIELD_TYPE_TINY = 1
FIELD_TYPE_SHORT = 2
FIELD_TYPE_LONG = 3
FIELD_TYPE_FLOAT = 4
FIELD_TYPE_DOUBLE = 5
FIELD_TYPE_NULL = 6
FIELD_TYPE_TIMESTAMP = 7
FIELD_TYPE_LONGLONG = 8
FIELD_TYPE_INT24 = 9
FIELD_TYPE_DATE = 10
FIELD_TYPE_TIME = 11
FIELD_TYPE_DATETIME = 12
FIELD_TYPE_YEAR = 13
FIELD_TYPE_NEWDATE = 14
FIELD_TYPE_VARCHAR = 15
FIELD_TYPE_BIT = 16
FIELD_TYPE_JSON = 245
FIELD_TYPE_NEWDECIMAL = 246
FIELD_TYPE_ENUM = 247
FIELD_TYPE_SET = 248
FIELD_TYPE_TINY_BLOB = 249
FIELD_TYPE_MEDIUM_BLOB = 250
FIELD_TYPE_LONG_BLOB = 251
FIELD_TYPE_BLOB = 252
FIELD_TYPE_VAR_STRING = 253
FIELD_TYPE_STRING = 254
FIELD_TYPE_GEOMETRY = 255


class Cursor:
    """MySQL database cursor for executing queries"""
    
    def __init__(self, connection: 'Connection'):
        """Initialize cursor
        
        Args:
            connection: Parent connection object
        """
        self.connection = connection
        self.description: Optional[List[Tuple]] = None
        self.rowcount: int = -1
        self.arraysize: int = 1
        self.lastrowid: Optional[int] = None
        self._results: List[Tuple] = []
        self._result_index: int = 0
        self._closed: bool = False
        self.rownumber: Optional[int] = None
    
    def execute(self, query: str, args: Union[Tuple, Dict, None] = None) -> int:
        """Execute a database query
        
        Args:
            query: SQL query string
            args: Query parameters (tuple or dict)
            
        Returns:
            Number of affected rows
            
        Raises:
            ProgrammingError: If cursor is closed or query fails
        """
        if self._closed:
            raise ProgrammingError("Cursor is closed")
        
        # Format the query with parameters
        formatted_query = self._format_query(query, args)
        
        # Execute query through connection
        try:
            self._results, self.description, self.lastrowid = \
                self.connection._execute_query(formatted_query)
            self.rowcount = len(self._results)
            self._result_index = 0
            self.rownumber = 0 if self._results else None
            
            return self.rowcount
        except Exception as e:
            raise ProgrammingError(f"Query execution failed: {e}")
    
    def executemany(self, query: str, args: Sequence[Union[Tuple, Dict]]) -> int:
        """Execute a query multiple times with different parameters
        
        Args:
            query: SQL query string
            args: Sequence of parameter sets
            
        Returns:
            Number of affected rows
        """
        if self._closed:
            raise ProgrammingError("Cursor is closed")
        
        total_rows = 0
        for params in args:
            affected = self.execute(query, params)
            total_rows += affected
        
        self.rowcount = total_rows
        return total_rows
    
    def fetchone(self) -> Optional[Tuple]:
        """Fetch next row of query result
        
        Returns:
            Next row as tuple, or None if no more rows
        """
        if self._closed:
            raise ProgrammingError("Cursor is closed")
        
        if self._result_index < len(self._results):
            row = self._results[self._result_index]
            self._result_index += 1
            self.rownumber = self._result_index
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
            raise ProgrammingError("Cursor is closed")
        
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
            raise ProgrammingError("Cursor is closed")
        
        result = self._results[self._result_index:]
        self.rownumber = len(self._results) if result else None
        self._result_index = len(self._results)
        return result
    
    def close(self) -> None:
        """Close the cursor"""
        self._closed = True
        self._results = []
        self.description = None
    
    def _format_query(self, query: str, args: Union[Tuple, Dict, None]) -> str:
        """Format query with parameters
        
        Args:
            query: SQL query with placeholders
            args: Query parameters
            
        Returns:
            Formatted query string
        """
        if args is None:
            return query
        
        formatted_query = query
        
        if isinstance(args, dict):
            # Named parameters: %(name)s style
            for key, value in args.items():
                placeholder = f"%({key})s"
                formatted_value = self._escape_value(value)
                formatted_query = formatted_query.replace(placeholder, formatted_value)
        elif isinstance(args, (tuple, list)):
            # Positional parameters: %s style
            parts = formatted_query.split('%s')
            if len(parts) - 1 != len(args):
                raise ProgrammingError(
                    f"Query expects {len(parts) - 1} parameters, got {len(args)}"
                )
            
            formatted_query = parts[0]
            for i, param in enumerate(args):
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
            return '1' if value else '0'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Escape special characters for MySQL
            escaped = value.replace('\\', '\\\\')
            escaped = escaped.replace("'", "\\'")
            escaped = escaped.replace('"', '\\"')
            escaped = escaped.replace('\n', '\\n')
            escaped = escaped.replace('\r', '\\r')
            escaped = escaped.replace('\t', '\\t')
            return f"'{escaped}'"
        elif isinstance(value, (datetime, date, time)):
            return f"'{value.isoformat()}'"
        elif isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"'{hours:02d}:{minutes:02d}:{seconds:02d}'"
        elif isinstance(value, bytes):
            # Binary data - hex encoding
            return f"X'{value.hex()}'"
        elif isinstance(value, (list, dict)):
            # JSON serialization
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


class DictCursor(Cursor):
    """Cursor that returns results as dictionaries"""
    
    def fetchone(self) -> Optional[Dict[str, Any]]:
        """Fetch next row as dictionary"""
        row = super().fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)
    
    def fetchmany(self, size: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch multiple rows as dictionaries"""
        rows = super().fetchmany(size)
        return [self._row_to_dict(row) for row in rows]
    
    def fetchall(self) -> List[Dict[str, Any]]:
        """Fetch all rows as dictionaries"""
        rows = super().fetchall()
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row: Tuple) -> Dict[str, Any]:
        """Convert row tuple to dictionary"""
        if self.description is None:
            return {}
        
        column_names = [desc[0] for desc in self.description]
        return dict(zip(column_names, row))


class Connection:
    """MySQL database connection"""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 3306,
        user: str = '',
        password: str = '',
        database: str = '',
        charset: str = 'utf8mb4',
        cursorclass: type = Cursor,
        autocommit: bool = False,
        **kwargs
    ):
        """Initialize connection
        
        Args:
            host: Database host
            port: Database port
            user: Username
            password: Password
            database: Database name
            charset: Character set
            cursorclass: Cursor class to use
            autocommit: Enable autocommit mode
            **kwargs: Additional connection parameters
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = database
        self.charset = charset
        self.cursorclass = cursorclass
        self._autocommit = autocommit
        self._closed = False
        self._in_transaction = False
        
        # Connection attributes
        self.server_version = (8, 0, 28)
        self.server_info = "8.0.28"
        self.protocol_version = 10
        self.character_set_name_value = charset
        
        # Simulated connection
        self._socket = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish database connection"""
        try:
            if not self.user:
                raise OperationalError("Username is required")
            
            # Simulate connection (in real PyMySQL, this creates a socket)
            self._socket = f"simulated_mysql_{self.host}:{self.port}"
            
            if self.db:
                # Select database
                pass
        except Exception as e:
            raise OperationalError(f"Could not connect to MySQL: {e}")
    
    def cursor(self, cursor: Optional[type] = None) -> Cursor:
        """Create a new cursor
        
        Args:
            cursor: Cursor class to use (overrides default)
            
        Returns:
            New cursor object
            
        Raises:
            InterfaceError: If connection is closed
        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        
        cursor_class = cursor or self.cursorclass
        return cursor_class(self)
    
    def commit(self) -> None:
        """Commit the current transaction
        
        Raises:
            OperationalError: If connection is closed
        """
        if self._closed:
            raise OperationalError("Cannot commit on a closed connection")
        
        if self._in_transaction:
            # Send COMMIT to database
            self._in_transaction = False
    
    def rollback(self) -> None:
        """Rollback the current transaction
        
        Raises:
            OperationalError: If connection is closed
        """
        if self._closed:
            raise OperationalError("Cannot rollback on a closed connection")
        
        if self._in_transaction:
            # Send ROLLBACK to database
            self._in_transaction = False
    
    def close(self) -> None:
        """Close the connection"""
        if not self._closed:
            if self._in_transaction:
                self.rollback()
            self._socket = None
            self._closed = True
    
    def select_db(self, db: str) -> None:
        """Select a database
        
        Args:
            db: Database name
        """
        if self._closed:
            raise OperationalError("Connection is closed")
        self.db = db
    
    def ping(self, reconnect: bool = True) -> None:
        """Check if connection is alive
        
        Args:
            reconnect: Whether to reconnect if connection is lost
            
        Raises:
            OperationalError: If connection is closed and reconnect is False
        """
        if self._closed:
            if reconnect:
                self._connect()
            else:
                raise OperationalError("Connection is closed")
    
    def autocommit(self, value: bool) -> None:
        """Set autocommit mode
        
        Args:
            value: True to enable autocommit, False to disable
        """
        self._autocommit = value
    
    def get_autocommit(self) -> bool:
        """Get autocommit mode
        
        Returns:
            Current autocommit setting
        """
        return self._autocommit
    
    def begin(self) -> None:
        """Explicitly start a transaction"""
        if self._closed:
            raise OperationalError("Connection is closed")
        self._in_transaction = True
    
    def _execute_query(self, query: str) -> Tuple[List[Tuple], Optional[List[Tuple]], Optional[int]]:
        """Execute a query and return results
        
        This is a simplified simulation. In a real implementation,
        this would communicate with MySQL server.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Tuple of (results, description, lastrowid)
        """
        if self._closed:
            raise OperationalError("Connection is closed")
        
        # Mark as in transaction if not autocommit
        if not self._autocommit:
            self._in_transaction = True
        
        # Simulate query execution
        query_upper = query.upper().strip()
        
        if query_upper.startswith('SELECT'):
            return self._simulate_select(query)
        elif query_upper.startswith('INSERT'):
            return self._simulate_insert(query)
        elif query_upper.startswith('UPDATE'):
            return self._simulate_update(query)
        elif query_upper.startswith('DELETE'):
            return self._simulate_delete(query)
        elif query_upper.startswith(('CREATE', 'DROP', 'ALTER', 'TRUNCATE')):
            # DDL queries
            return ([], None, None)
        elif query_upper.startswith('USE'):
            # Database selection
            return ([], None, None)
        else:
            # Other queries
            return ([], None, None)
    
    def _simulate_select(self, query: str) -> Tuple[List[Tuple], List[Tuple], None]:
        """Simulate SELECT query execution"""
        columns = self._parse_select_columns(query)
        
        # Create description (column metadata)
        description = [
            (col, FIELD_TYPE_VAR_STRING, None, None, None, None, None)
            for col in columns
        ]
        
        # Return empty results
        return ([], description, None)
    
    def _simulate_insert(self, query: str) -> Tuple[List[Tuple], None, int]:
        """Simulate INSERT query execution"""
        # Return simulated auto-increment ID
        return ([], None, 1)
    
    def _simulate_update(self, query: str) -> Tuple[List[Tuple], None, None]:
        """Simulate UPDATE query execution"""
        return ([], None, None)
    
    def _simulate_delete(self, query: str) -> Tuple[List[Tuple], None, None]:
        """Simulate DELETE query execution"""
        return ([], None, None)
    
    def _parse_select_columns(self, query: str) -> List[str]:
        """Parse column names from SELECT query"""
        if '*' in query:
            return ['col1', 'col2', 'col3']
        
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
    port: int = 3306,
    user: str = '',
    password: str = '',
    database: str = '',
    charset: str = 'utf8mb4',
    cursorclass: type = Cursor,
    autocommit: bool = False,
    **kwargs
) -> Connection:
    """Create a new database connection
    
    Args:
        host: Database host
        port: Database port
        user: Username
        password: Password
        database: Database name
        charset: Character set
        cursorclass: Cursor class to use
        autocommit: Enable autocommit mode
        **kwargs: Additional connection parameters
        
    Returns:
        New connection object
    """
    return Connection(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset=charset,
        cursorclass=cursorclass,
        autocommit=autocommit,
        **kwargs
    )


# Alias for compatibility
Connect = connect


def escape_string(value: str) -> str:
    """Escape a string for MySQL query
    
    Args:
        value: String to escape
        
    Returns:
        Escaped string
    """
    escaped = value.replace('\\', '\\\\')
    escaped = escaped.replace("'", "\\'")
    escaped = escaped.replace('"', '\\"')
    escaped = escaped.replace('\n', '\\n')
    escaped = escaped.replace('\r', '\\r')
    escaped = escaped.replace('\t', '\\t')
    return escaped


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


STRING = _DBAPITypeObject(
    FIELD_TYPE_VARCHAR, FIELD_TYPE_VAR_STRING, FIELD_TYPE_STRING,
    FIELD_TYPE_ENUM, FIELD_TYPE_SET
)
BINARY = _DBAPITypeObject(
    FIELD_TYPE_BLOB, FIELD_TYPE_LONG_BLOB, FIELD_TYPE_MEDIUM_BLOB,
    FIELD_TYPE_TINY_BLOB
)
NUMBER = _DBAPITypeObject(
    FIELD_TYPE_DECIMAL, FIELD_TYPE_NEWDECIMAL, FIELD_TYPE_TINY,
    FIELD_TYPE_SHORT, FIELD_TYPE_LONG, FIELD_TYPE_FLOAT,
    FIELD_TYPE_DOUBLE, FIELD_TYPE_LONGLONG, FIELD_TYPE_INT24
)
DATETIME = _DBAPITypeObject(
    FIELD_TYPE_TIMESTAMP, FIELD_TYPE_DATE, FIELD_TYPE_TIME,
    FIELD_TYPE_DATETIME, FIELD_TYPE_YEAR, FIELD_TYPE_NEWDATE
)
ROWID = _DBAPITypeObject()
