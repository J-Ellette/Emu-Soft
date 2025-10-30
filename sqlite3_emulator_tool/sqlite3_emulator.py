"""
SQLite3 Emulator - Enhanced SQLite Integration
Emulates and enhances Python's built-in sqlite3 module with additional features
"""

import sqlite3 as _sqlite3
import json
import hashlib
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime, date
from functools import wraps
import io


# Re-export standard sqlite3 items
from sqlite3 import (
    Error,
    Warning,
    InterfaceError,
    DatabaseError,
    DataError,
    OperationalError,
    IntegrityError,
    InternalError,
    ProgrammingError,
    NotSupportedError,
    Row,
    PARSE_DECLTYPES,
    PARSE_COLNAMES,
)

# Module attributes
apilevel = '2.0'
threadsafety = 1
paramstyle = 'qmark'

# SQLite version
sqlite_version = _sqlite3.sqlite_version
sqlite_version_info = _sqlite3.sqlite_version_info


class EnhancedCursor(_sqlite3.Cursor):
    """Enhanced cursor with additional functionality"""
    
    def __init__(self, connection):
        """Initialize enhanced cursor
        
        Args:
            connection: Parent connection object
        """
        super().__init__(connection)
        self._query_history: List[Tuple[str, Any]] = []
        self._max_history = 100
    
    def execute(self, sql: str, parameters: Union[Tuple, Dict] = ()) -> 'EnhancedCursor':
        """Execute SQL with query history tracking
        
        Args:
            sql: SQL query
            parameters: Query parameters
            
        Returns:
            Self for chaining
        """
        # Add to history
        self._add_to_history(sql, parameters)
        
        # Execute query
        return super().execute(sql, parameters)
    
    def executemany(self, sql: str, seq_of_parameters) -> 'EnhancedCursor':
        """Execute SQL multiple times
        
        Args:
            sql: SQL query
            seq_of_parameters: Sequence of parameter sets
            
        Returns:
            Self for chaining
        """
        self._add_to_history(sql, f"<executemany with {len(list(seq_of_parameters))} sets>")
        return super().executemany(sql, seq_of_parameters)
    
    def _add_to_history(self, sql: str, parameters: Any) -> None:
        """Add query to history
        
        Args:
            sql: SQL query
            parameters: Query parameters
        """
        self._query_history.append((sql, parameters))
        
        # Keep history size limited
        if len(self._query_history) > self._max_history:
            self._query_history.pop(0)
    
    def get_query_history(self) -> List[Tuple[str, Any]]:
        """Get query execution history
        
        Returns:
            List of (query, parameters) tuples
        """
        return self._query_history.copy()
    
    def clear_history(self) -> None:
        """Clear query history"""
        self._query_history.clear()
    
    def explain(self, sql: str, parameters: Union[Tuple, Dict] = ()) -> List[Tuple]:
        """Get query execution plan
        
        Args:
            sql: SQL query to explain
            parameters: Query parameters
            
        Returns:
            Query plan as list of tuples
        """
        explain_sql = f"EXPLAIN QUERY PLAN {sql}"
        return self.execute(explain_sql, parameters).fetchall()


class EnhancedConnection(_sqlite3.Connection):
    """Enhanced connection with additional functionality"""
    
    def __init__(self, *args, **kwargs):
        """Initialize enhanced connection"""
        super().__init__(*args, **kwargs)
        self._custom_functions: Dict[str, Callable] = {}
        self._custom_aggregates: Dict[str, type] = {}
        self._setup_enhancements()
    
    def cursor(self, factory=EnhancedCursor) -> EnhancedCursor:
        """Create enhanced cursor
        
        Args:
            factory: Cursor factory class
            
        Returns:
            New cursor instance
        """
        return super().cursor(factory)
    
    def _setup_enhancements(self) -> None:
        """Set up default enhancements"""
        # Register default custom functions
        self.create_function("regexp", 2, self._regexp_function)
        self.create_function("json_extract", 2, self._json_extract_function)
        self.create_function("json_array_length", 1, self._json_array_length_function)
        self.create_function("md5", 1, self._md5_function)
        self.create_function("sha256", 1, self._sha256_function)
        self.create_function("reverse", 1, self._reverse_function)
        self.create_function("title_case", 1, self._title_case_function)
    
    @staticmethod
    def _regexp_function(pattern: str, value: str) -> bool:
        """Regular expression matching function
        
        Args:
            pattern: Regex pattern
            value: Value to match
            
        Returns:
            True if match found
        """
        if value is None or pattern is None:
            return False
        return bool(re.search(pattern, value))
    
    @staticmethod
    def _json_extract_function(json_str: str, path: str) -> Any:
        """Extract value from JSON string
        
        Args:
            json_str: JSON string
            path: JSON path (e.g., '$.key.subkey')
            
        Returns:
            Extracted value
        """
        if not json_str:
            return None
        
        try:
            data = json.loads(json_str)
            
            # Simple path extraction (supports $.key.subkey format)
            if path.startswith('$.'):
                path = path[2:]
            
            keys = path.split('.')
            result = data
            for key in keys:
                if isinstance(result, dict):
                    result = result.get(key)
                elif isinstance(result, list) and key.isdigit():
                    result = result[int(key)]
                else:
                    return None
            
            return result
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            return None
    
    @staticmethod
    def _json_array_length_function(json_str: str) -> Optional[int]:
        """Get length of JSON array
        
        Args:
            json_str: JSON array string
            
        Returns:
            Array length or None
        """
        if not json_str:
            return None
        
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return len(data)
            return None
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def _md5_function(value: str) -> str:
        """Calculate MD5 hash
        
        Args:
            value: Input string
            
        Returns:
            MD5 hash hex string
        """
        if value is None:
            return None
        return hashlib.md5(str(value).encode()).hexdigest()
    
    @staticmethod
    def _sha256_function(value: str) -> str:
        """Calculate SHA256 hash
        
        Args:
            value: Input string
            
        Returns:
            SHA256 hash hex string
        """
        if value is None:
            return None
        return hashlib.sha256(str(value).encode()).hexdigest()
    
    @staticmethod
    def _reverse_function(value: str) -> Optional[str]:
        """Reverse a string
        
        Args:
            value: Input string
            
        Returns:
            Reversed string
        """
        if value is None:
            return None
        return str(value)[::-1]
    
    @staticmethod
    def _title_case_function(value: str) -> Optional[str]:
        """Convert to title case
        
        Args:
            value: Input string
            
        Returns:
            Title cased string
        """
        if value is None:
            return None
        return str(value).title()
    
    def create_custom_function(self, name: str, num_params: int, func: Callable) -> None:
        """Register a custom SQL function
        
        Args:
            name: Function name
            num_params: Number of parameters (-1 for any)
            func: Python function to call
        """
        self.create_function(name, num_params, func)
        self._custom_functions[name] = func
    
    def create_custom_aggregate(self, name: str, num_params: int, aggregate_class: type) -> None:
        """Register a custom aggregate function
        
        Args:
            name: Aggregate name
            num_params: Number of parameters
            aggregate_class: Aggregate class with step() and finalize()
        """
        self.create_aggregate(name, num_params, aggregate_class)
        self._custom_aggregates[name] = aggregate_class
    
    def get_custom_functions(self) -> Dict[str, Callable]:
        """Get registered custom functions
        
        Returns:
            Dictionary of function name to callable
        """
        return self._custom_functions.copy()
    
    def get_custom_aggregates(self) -> Dict[str, type]:
        """Get registered custom aggregates
        
        Returns:
            Dictionary of aggregate name to class
        """
        return self._custom_aggregates.copy()
    
    def backup(self, target: Union[str, 'EnhancedConnection'], pages: int = -1,
               progress: Optional[Callable] = None) -> None:
        """Backup database to another database or file
        
        Args:
            target: Target connection or filename
            pages: Pages to copy per iteration (-1 for all)
            progress: Progress callback function
        """
        if isinstance(target, str):
            # Backup to file
            target_conn = connect(target)
            try:
                self._backup_to_connection(target_conn, pages, progress)
            finally:
                target_conn.close()
        else:
            # Backup to connection
            self._backup_to_connection(target, pages, progress)
    
    def _backup_to_connection(self, target: _sqlite3.Connection,
                             pages: int, progress: Optional[Callable]) -> None:
        """Internal backup to connection
        
        Args:
            target: Target connection
            pages: Pages per iteration
            progress: Progress callback
        """
        # Use iterdump for full database backup
        for line in self.iterdump():
            target.execute(line)
        
        target.commit()
        
        if progress:
            progress(100, 100, True)
    
    def optimize(self) -> None:
        """Optimize database (VACUUM and ANALYZE)"""
        self.execute("VACUUM")
        self.execute("ANALYZE")
        self.commit()
    
    def get_table_info(self, table_name: str) -> List[Tuple]:
        """Get table schema information
        
        Args:
            table_name: Name of table
            
        Returns:
            List of column information tuples
        """
        cursor = self.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()
    
    def get_tables(self) -> List[str]:
        """Get list of table names
        
        Returns:
            List of table names
        """
        cursor = self.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def get_indexes(self, table_name: Optional[str] = None) -> List[Tuple]:
        """Get index information
        
        Args:
            table_name: Optional table name to filter by
            
        Returns:
            List of index information tuples
        """
        cursor = self.cursor()
        if table_name:
            cursor.execute(
                "SELECT * FROM sqlite_master WHERE type='index' AND tbl_name=?",
                (table_name,)
            )
        else:
            cursor.execute(
                "SELECT * FROM sqlite_master WHERE type='index' ORDER BY name"
            )
        return cursor.fetchall()
    
    def get_database_size(self) -> int:
        """Get database size in bytes
        
        Returns:
            Database size
        """
        cursor = self.cursor()
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def enable_foreign_keys(self) -> None:
        """Enable foreign key constraints"""
        self.execute("PRAGMA foreign_keys = ON")
    
    def disable_foreign_keys(self) -> None:
        """Disable foreign key constraints"""
        self.execute("PRAGMA foreign_keys = OFF")
    
    def check_integrity(self) -> List[str]:
        """Check database integrity
        
        Returns:
            List of integrity check results
        """
        cursor = self.cursor()
        cursor.execute("PRAGMA integrity_check")
        results = cursor.fetchall()
        return [row[0] for row in results]


def connect(
    database: str,
    timeout: float = 5.0,
    detect_types: int = 0,
    isolation_level: Optional[str] = "DEFERRED",
    check_same_thread: bool = True,
    factory: type = EnhancedConnection,
    cached_statements: int = 128,
    uri: bool = False
) -> EnhancedConnection:
    """Create enhanced database connection
    
    Args:
        database: Database filename or ":memory:" for in-memory
        timeout: Connection timeout
        detect_types: Type detection flags
        isolation_level: Transaction isolation level
        check_same_thread: Check if connection used in same thread
        factory: Connection factory class
        cached_statements: Number of statements to cache
        uri: Treat database as URI
        
    Returns:
        New enhanced connection
    """
    conn = _sqlite3.connect(
        database=database,
        timeout=timeout,
        detect_types=detect_types,
        isolation_level=isolation_level,
        check_same_thread=check_same_thread,
        factory=factory,
        cached_statements=cached_statements,
        uri=uri
    )
    return conn


# Utility classes for custom aggregates
class StdDevAggregate:
    """Standard deviation aggregate function"""
    
    def __init__(self):
        self.values = []
    
    def step(self, value):
        """Add value to aggregate"""
        if value is not None:
            self.values.append(float(value))
    
    def finalize(self):
        """Calculate standard deviation"""
        if not self.values:
            return None
        
        n = len(self.values)
        mean = sum(self.values) / n
        variance = sum((x - mean) ** 2 for x in self.values) / n
        return variance ** 0.5


class MedianAggregate:
    """Median aggregate function"""
    
    def __init__(self):
        self.values = []
    
    def step(self, value):
        """Add value to aggregate"""
        if value is not None:
            self.values.append(float(value))
    
    def finalize(self):
        """Calculate median"""
        if not self.values:
            return None
        
        sorted_values = sorted(self.values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]


class ModeAggregate:
    """Mode aggregate function"""
    
    def __init__(self):
        self.counts = {}
    
    def step(self, value):
        """Add value to aggregate"""
        if value is not None:
            self.counts[value] = self.counts.get(value, 0) + 1
    
    def finalize(self):
        """Calculate mode"""
        if not self.counts:
            return None
        
        return max(self.counts.items(), key=lambda x: x[1])[0]


def register_enhanced_aggregates(connection: EnhancedConnection) -> None:
    """Register enhanced aggregate functions
    
    Args:
        connection: Database connection
    """
    connection.create_custom_aggregate("stdev", 1, StdDevAggregate)
    connection.create_custom_aggregate("median", 1, MedianAggregate)
    connection.create_custom_aggregate("mode", 1, ModeAggregate)


# Converters for date/datetime
def adapt_date(val: date) -> str:
    """Adapt date to ISO format"""
    return val.isoformat()


def adapt_datetime(val: datetime) -> str:
    """Adapt datetime to ISO format"""
    return val.isoformat()


def convert_date(val: bytes) -> date:
    """Convert ISO date string to date object"""
    return date.fromisoformat(val.decode())


def convert_datetime(val: bytes) -> datetime:
    """Convert ISO datetime string to datetime object"""
    return datetime.fromisoformat(val.decode())


def convert_timestamp(val: bytes) -> datetime:
    """Convert timestamp to datetime object"""
    return datetime.fromisoformat(val.decode())


# Register adapters and converters
_sqlite3.register_adapter(date, adapt_date)
_sqlite3.register_adapter(datetime, adapt_datetime)
_sqlite3.register_converter("date", convert_date)
_sqlite3.register_converter("datetime", convert_datetime)
_sqlite3.register_converter("timestamp", convert_timestamp)
