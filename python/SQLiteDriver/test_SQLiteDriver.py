"""
Developed by PowerShield, as an alternative to sqlite3
"""

"""
Test suite for SQLite3 emulator enhancements
"""

import unittest
import os
import tempfile
from datetime import datetime, date
from SQLiteDriver import (
    connect,
    EnhancedConnection,
    EnhancedCursor,
    StdDevAggregate,
    MedianAggregate,
    ModeAggregate,
    register_enhanced_aggregates,
    Error,
    IntegrityError,
    OperationalError,
    PARSE_DECLTYPES,
)


class TestEnhancedConnection(unittest.TestCase):
    """Test EnhancedConnection class"""
    
    def setUp(self):
        """Set up test database"""
        self.conn = connect(':memory:')
    
    def tearDown(self):
        """Close test connection"""
        self.conn.close()
    
    def test_connect_creates_enhanced_connection(self):
        """Test that connect returns EnhancedConnection"""
        self.assertIsInstance(self.conn, EnhancedConnection)
    
    def test_cursor_creates_enhanced_cursor(self):
        """Test that cursor() returns EnhancedCursor"""
        cursor = self.conn.cursor()
        self.assertIsInstance(cursor, EnhancedCursor)
    
    def test_create_custom_function(self):
        """Test custom function registration"""
        def double(x):
            return x * 2
        
        self.conn.create_custom_function("double", 1, double)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT double(5)")
        result = cursor.fetchone()[0]
        self.assertEqual(result, 10)
    
    def test_builtin_regexp_function(self):
        """Test built-in REGEXP function"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE test (value TEXT)")
        cursor.execute("INSERT INTO test VALUES ('hello'), ('world'), ('test')")
        
        cursor.execute("SELECT value FROM test WHERE regexp('^h', value)")
        results = cursor.fetchall()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 'hello')
    
    def test_builtin_json_extract_function(self):
        """Test built-in json_extract function"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE test (data TEXT)")
        cursor.execute('INSERT INTO test VALUES (\'{"name": "John", "age": 30}\')')
        
        cursor.execute("SELECT json_extract(data, '$.name') FROM test")
        result = cursor.fetchone()[0]
        self.assertEqual(result, 'John')
    
    def test_builtin_json_array_length_function(self):
        """Test built-in json_array_length function"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE test (data TEXT)")
        cursor.execute("INSERT INTO test VALUES ('[1, 2, 3, 4, 5]')")
        
        cursor.execute("SELECT json_array_length(data) FROM test")
        result = cursor.fetchone()[0]
        self.assertEqual(result, 5)
    
    def test_builtin_md5_function(self):
        """Test built-in md5 function"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT md5('hello')")
        result = cursor.fetchone()[0]
        self.assertEqual(result, '5d41402abc4b2a76b9719d911017c592')
    
    def test_builtin_sha256_function(self):
        """Test built-in sha256 function"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT sha256('hello')")
        result = cursor.fetchone()[0]
        self.assertEqual(len(result), 64)  # SHA256 produces 64 hex characters
    
    def test_builtin_reverse_function(self):
        """Test built-in reverse function"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT reverse('hello')")
        result = cursor.fetchone()[0]
        self.assertEqual(result, 'olleh')
    
    def test_builtin_title_case_function(self):
        """Test built-in title_case function"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT title_case('hello world')")
        result = cursor.fetchone()[0]
        self.assertEqual(result, 'Hello World')
    
    def test_get_tables(self):
        """Test get_tables method"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        cursor.execute("CREATE TABLE posts (id INTEGER, title TEXT)")
        
        tables = self.conn.get_tables()
        self.assertIn('users', tables)
        self.assertIn('posts', tables)
    
    def test_get_table_info(self):
        """Test get_table_info method"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        
        info = self.conn.get_table_info('users')
        self.assertEqual(len(info), 2)  # Two columns
        self.assertEqual(info[0][1], 'id')  # First column name
        self.assertEqual(info[1][1], 'name')  # Second column name
    
    def test_get_indexes(self):
        """Test get_indexes method"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        cursor.execute("CREATE INDEX idx_name ON users(name)")
        
        indexes = self.conn.get_indexes('users')
        self.assertGreater(len(indexes), 0)
    
    def test_get_database_size(self):
        """Test get_database_size method"""
        # Create some data first
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER)")
        cursor.execute("INSERT INTO test VALUES (1)")
        self.conn.commit()
        
        size = self.conn.get_database_size()
        self.assertIsInstance(size, int)
        self.assertGreaterEqual(size, 0)
    
    def test_optimize(self):
        """Test optimize method"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER)")
        cursor.execute("INSERT INTO test VALUES (1), (2), (3)")
        self.conn.commit()  # Commit before optimize
        
        # Should not raise exception
        self.conn.optimize()
    
    def test_enable_disable_foreign_keys(self):
        """Test foreign key enable/disable"""
        self.conn.enable_foreign_keys()
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()[0]
        self.assertEqual(result, 1)
        
        self.conn.disable_foreign_keys()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()[0]
        self.assertEqual(result, 0)
    
    def test_check_integrity(self):
        """Test check_integrity method"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER)")
        
        results = self.conn.check_integrity()
        self.assertIn('ok', results)
    
    def test_backup_to_file(self):
        """Test backup to file"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        cursor.execute("INSERT INTO test VALUES (1, 'Alice'), (2, 'Bob')")
        self.conn.commit()
        
        # Create temp file for backup
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            backup_path = f.name
        
        try:
            # Backup database
            self.conn.backup(backup_path)
            
            # Verify backup
            backup_conn = connect(backup_path)
            backup_cursor = backup_conn.cursor()
            backup_cursor.execute("SELECT COUNT(*) FROM test")
            count = backup_cursor.fetchone()[0]
            self.assertEqual(count, 2)
            backup_conn.close()
        finally:
            # Clean up
            if os.path.exists(backup_path):
                os.unlink(backup_path)
    
    def test_backup_to_connection(self):
        """Test backup to another connection"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER)")
        cursor.execute("INSERT INTO test VALUES (1), (2), (3)")
        self.conn.commit()
        
        # Create target connection
        target_conn = connect(':memory:')
        
        # Backup
        self.conn.backup(target_conn)
        
        # Verify
        target_cursor = target_conn.cursor()
        target_cursor.execute("SELECT COUNT(*) FROM test")
        count = target_cursor.fetchone()[0]
        self.assertEqual(count, 3)
        
        target_conn.close()


class TestEnhancedCursor(unittest.TestCase):
    """Test EnhancedCursor class"""
    
    def setUp(self):
        """Set up test database"""
        self.conn = connect(':memory:')
        self.cursor = self.conn.cursor()
    
    def tearDown(self):
        """Close test connection"""
        self.conn.close()
    
    def test_query_history(self):
        """Test query history tracking"""
        self.cursor.execute("CREATE TABLE test (id INTEGER)")
        self.cursor.execute("INSERT INTO test VALUES (1)")
        self.cursor.execute("SELECT * FROM test")
        
        history = self.cursor.get_query_history()
        self.assertEqual(len(history), 3)
        self.assertIn("CREATE TABLE", history[0][0])
        self.assertIn("INSERT", history[1][0])
        self.assertIn("SELECT", history[2][0])
    
    def test_clear_history(self):
        """Test clearing query history"""
        self.cursor.execute("SELECT 1")
        self.cursor.execute("SELECT 2")
        
        self.assertEqual(len(self.cursor.get_query_history()), 2)
        
        self.cursor.clear_history()
        self.assertEqual(len(self.cursor.get_query_history()), 0)
    
    def test_explain(self):
        """Test EXPLAIN QUERY PLAN"""
        self.cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        self.cursor.execute("CREATE INDEX idx_name ON test(name)")
        
        plan = self.cursor.explain("SELECT * FROM test WHERE name = 'Alice'")
        self.assertIsInstance(plan, list)
        # Should have some plan rows
        self.assertGreater(len(plan), 0)


class TestCustomAggregates(unittest.TestCase):
    """Test custom aggregate functions"""
    
    def setUp(self):
        """Set up test database"""
        self.conn = connect(':memory:')
        register_enhanced_aggregates(self.conn)
        
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE numbers (value REAL)")
        cursor.execute("INSERT INTO numbers VALUES (1), (2), (3), (4), (5)")
        self.conn.commit()
    
    def tearDown(self):
        """Close test connection"""
        self.conn.close()
    
    def test_stdev_aggregate(self):
        """Test standard deviation aggregate"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT stdev(value) FROM numbers")
        result = cursor.fetchone()[0]
        
        # Stdev of 1,2,3,4,5 is approximately 1.414
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result, 1.414, places=2)
    
    def test_median_aggregate(self):
        """Test median aggregate"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT median(value) FROM numbers")
        result = cursor.fetchone()[0]
        
        # Median of 1,2,3,4,5 is 3
        self.assertEqual(result, 3.0)
    
    def test_mode_aggregate(self):
        """Test mode aggregate"""
        cursor = self.conn.cursor()
        # 'values' is a reserved word, use different name
        cursor.execute("CREATE TABLE test_values (val INTEGER)")
        cursor.execute("INSERT INTO test_values VALUES (1), (2), (2), (3), (2), (4)")
        
        cursor.execute("SELECT mode(val) FROM test_values")
        result = cursor.fetchone()[0]
        
        # Mode of 1,2,2,3,2,4 is 2
        self.assertEqual(result, 2)


class TestDateTimeSupport(unittest.TestCase):
    """Test date/datetime type support"""
    
    def setUp(self):
        """Set up test database with type detection"""
        self.conn = connect(':memory:', detect_types=PARSE_DECLTYPES)
    
    def tearDown(self):
        """Close test connection"""
        self.conn.close()
    
    def test_date_type(self):
        """Test date type handling"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE events (event_date DATE)")
        
        test_date = date(2024, 1, 15)
        cursor.execute("INSERT INTO events VALUES (?)", (test_date,))
        
        cursor.execute("SELECT event_date FROM events")
        result = cursor.fetchone()[0]
        
        # Should be a date object
        self.assertIsInstance(result, date)
        self.assertEqual(result, test_date)
    
    def test_datetime_type(self):
        """Test datetime type handling"""
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE logs (timestamp DATETIME)")
        
        test_datetime = datetime(2024, 1, 15, 10, 30, 45)
        cursor.execute("INSERT INTO logs VALUES (?)", (test_datetime,))
        
        cursor.execute("SELECT timestamp FROM logs")
        result = cursor.fetchone()[0]
        
        # Should be a datetime object
        self.assertIsInstance(result, datetime)
        self.assertEqual(result, test_datetime)


class TestContextManager(unittest.TestCase):
    """Test context manager support"""
    
    def test_connection_context_manager(self):
        """Test connection as context manager"""
        with connect(':memory:') as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER)")
            cursor.execute("INSERT INTO test VALUES (1)")
        
        # Connection should auto-commit and close


if __name__ == '__main__':
    unittest.main()
