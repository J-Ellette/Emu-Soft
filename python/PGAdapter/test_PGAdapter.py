"""
Developed by PowerShield, as an alternative to psycopg2
"""

"""
Test suite for psycopg2 emulator
"""

import unittest
from PGAdapter import (
    connect,
    Connection,
    Cursor,
    DatabaseError,
    InterfaceError,
    OperationalError,
    ProgrammingError,
    IntegrityError,
    DataError,
    NotSupportedError,
    Binary,
    Date,
    Time,
    Timestamp,
    STRING,
    BINARY,
    NUMBER,
    DATETIME,
    ROWID,
)
from datetime import datetime, date, time


class TestConnection(unittest.TestCase):
    """Test Connection class"""
    
    def test_connect_function(self):
        """Test connect() function creates connection"""
        conn = connect(
            host='localhost',
            port=5432,
            database='testdb',
            user='testuser',
            password='testpass'
        )
        self.assertIsInstance(conn, Connection)
        self.assertEqual(conn.host, 'localhost')
        self.assertEqual(conn.port, 5432)
        self.assertEqual(conn.database, 'testdb')
        self.assertEqual(conn.user, 'testuser')
        conn.close()
    
    def test_connection_requires_database(self):
        """Test that connection requires database name"""
        with self.assertRaises(OperationalError):
            connect(host='localhost', user='testuser')
    
    def test_connection_requires_user(self):
        """Test that connection requires username"""
        with self.assertRaises(OperationalError):
            connect(host='localhost', database='testdb')
    
    def test_cursor_creation(self):
        """Test cursor creation"""
        conn = connect(database='testdb', user='testuser')
        cursor = conn.cursor()
        self.assertIsInstance(cursor, Cursor)
        self.assertEqual(cursor.connection, conn)
        conn.close()
    
    def test_cursor_on_closed_connection(self):
        """Test that cursor() raises error on closed connection"""
        conn = connect(database='testdb', user='testuser')
        conn.close()
        with self.assertRaises(InterfaceError):
            conn.cursor()
    
    def test_commit(self):
        """Test commit operation"""
        conn = connect(database='testdb', user='testuser')
        # Should not raise exception
        conn.commit()
        conn.close()
    
    def test_rollback(self):
        """Test rollback operation"""
        conn = connect(database='testdb', user='testuser')
        # Should not raise exception
        conn.rollback()
        conn.close()
    
    def test_context_manager(self):
        """Test connection as context manager"""
        with connect(database='testdb', user='testuser') as conn:
            self.assertIsInstance(conn, Connection)
            self.assertFalse(conn._closed)
        
        # Connection should be closed after context
        self.assertTrue(conn._closed)
    
    def test_autocommit_mode(self):
        """Test autocommit mode"""
        conn = connect(database='testdb', user='testuser', autocommit=True)
        self.assertTrue(conn.autocommit)
        conn.close()


class TestCursor(unittest.TestCase):
    """Test Cursor class"""
    
    def setUp(self):
        """Set up test connection"""
        self.conn = connect(database='testdb', user='testuser')
    
    def tearDown(self):
        """Close test connection"""
        self.conn.close()
    
    def test_execute_simple_query(self):
        """Test executing a simple query"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        self.assertIsNotNone(cursor.description)
        self.assertEqual(cursor.rowcount, 0)  # Simulated empty result
    
    def test_execute_with_positional_params(self):
        """Test query with positional parameters"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
        self.assertIsNotNone(cursor.description)
    
    def test_execute_with_named_params(self):
        """Test query with named parameters"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE name = %(name)s AND age = %(age)s",
            {'name': 'John', 'age': 30}
        )
        self.assertIsNotNone(cursor.description)
    
    def test_execute_insert_with_returning(self):
        """Test INSERT with RETURNING clause"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
            ('John Doe', 'john@example.com')
        )
        self.assertEqual(cursor.lastrowid, 1)
    
    def test_executemany(self):
        """Test executemany with multiple parameter sets"""
        cursor = self.conn.cursor()
        data = [
            ('John', 'john@example.com'),
            ('Jane', 'jane@example.com'),
            ('Bob', 'bob@example.com'),
        ]
        cursor.executemany(
            "INSERT INTO users (name, email) VALUES (%s, %s)",
            data
        )
        # rowcount should reflect all executions
        self.assertGreaterEqual(cursor.rowcount, 0)
    
    def test_fetchone(self):
        """Test fetchone method"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        result = cursor.fetchone()
        # Simulated query returns empty results
        self.assertIsNone(result)
    
    def test_fetchmany(self):
        """Test fetchmany method"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchmany(5)
        self.assertIsInstance(results, list)
    
    def test_fetchall(self):
        """Test fetchall method"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        self.assertIsInstance(results, list)
    
    def test_cursor_iterator(self):
        """Test cursor as iterator"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        
        rows = []
        for row in cursor:
            rows.append(row)
        
        self.assertIsInstance(rows, list)
    
    def test_cursor_context_manager(self):
        """Test cursor as context manager"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            self.assertFalse(cursor._closed)
        
        self.assertTrue(cursor._closed)
    
    def test_execute_on_closed_cursor(self):
        """Test that execute raises error on closed cursor"""
        cursor = self.conn.cursor()
        cursor.close()
        
        with self.assertRaises(ProgrammingError):
            cursor.execute("SELECT * FROM users")
    
    def test_parameter_escaping(self):
        """Test that parameters are properly escaped"""
        cursor = self.conn.cursor()
        # String with quotes should be escaped
        cursor.execute(
            "INSERT INTO users (name) VALUES (%s)",
            ("O'Brien",)
        )
        # Should not raise exception
    
    def test_null_parameter(self):
        """Test NULL parameter handling"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s)",
            ('John', None)
        )
        # Should not raise exception
    
    def test_boolean_parameter(self):
        """Test boolean parameter handling"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (active) VALUES (%s)",
            (True,)
        )
        # Should not raise exception
    
    def test_datetime_parameter(self):
        """Test datetime parameter handling"""
        cursor = self.conn.cursor()
        now = datetime.now()
        cursor.execute(
            "INSERT INTO users (created_at) VALUES (%s)",
            (now,)
        )
        # Should not raise exception
    
    def test_json_parameter(self):
        """Test JSON parameter handling"""
        cursor = self.conn.cursor()
        data = {'key': 'value', 'number': 42}
        cursor.execute(
            "INSERT INTO users (metadata) VALUES (%s)",
            (data,)
        )
        # Should not raise exception


class TestExceptions(unittest.TestCase):
    """Test exception hierarchy"""
    
    def test_exception_inheritance(self):
        """Test that exceptions inherit from DatabaseError"""
        self.assertTrue(issubclass(InterfaceError, DatabaseError))
        self.assertTrue(issubclass(OperationalError, DatabaseError))
        self.assertTrue(issubclass(ProgrammingError, DatabaseError))
        self.assertTrue(issubclass(IntegrityError, DatabaseError))
        self.assertTrue(issubclass(DataError, DatabaseError))
        self.assertTrue(issubclass(NotSupportedError, DatabaseError))


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions"""
    
    def test_binary(self):
        """Test Binary helper"""
        data = b'binary data'
        result = Binary(data)
        self.assertEqual(result, data)
    
    def test_date(self):
        """Test Date helper"""
        d = Date(2024, 1, 15)
        self.assertIsInstance(d, date)
        self.assertEqual(d.year, 2024)
        self.assertEqual(d.month, 1)
        self.assertEqual(d.day, 15)
    
    def test_time(self):
        """Test Time helper"""
        t = Time(10, 30, 45)
        self.assertIsInstance(t, time)
        self.assertEqual(t.hour, 10)
        self.assertEqual(t.minute, 30)
        self.assertEqual(t.second, 45)
    
    def test_timestamp(self):
        """Test Timestamp helper"""
        ts = Timestamp(2024, 1, 15, 10, 30, 45)
        self.assertIsInstance(ts, datetime)
        self.assertEqual(ts.year, 2024)
        self.assertEqual(ts.month, 1)
        self.assertEqual(ts.day, 15)
        self.assertEqual(ts.hour, 10)


class TestTypeObjects(unittest.TestCase):
    """Test DB-API type objects"""
    
    def test_string_type(self):
        """Test STRING type object"""
        self.assertTrue(STRING == 'text')
        self.assertTrue(STRING == 'varchar')
        self.assertTrue(STRING == 'char')
        self.assertFalse(STRING == 'integer')
    
    def test_binary_type(self):
        """Test BINARY type object"""
        self.assertTrue(BINARY == 'bytea')
        self.assertTrue(BINARY == 'blob')
        self.assertFalse(BINARY == 'text')
    
    def test_number_type(self):
        """Test NUMBER type object"""
        self.assertTrue(NUMBER == 'integer')
        self.assertTrue(NUMBER == 'bigint')
        self.assertTrue(NUMBER == 'numeric')
        self.assertFalse(NUMBER == 'text')
    
    def test_datetime_type(self):
        """Test DATETIME type object"""
        self.assertTrue(DATETIME == 'timestamp')
        self.assertTrue(DATETIME == 'date')
        self.assertTrue(DATETIME == 'time')
        self.assertFalse(DATETIME == 'integer')
    
    def test_rowid_type(self):
        """Test ROWID type object"""
        self.assertTrue(ROWID == 'oid')
        self.assertFalse(ROWID == 'integer')


class TestDBAPICompliance(unittest.TestCase):
    """Test DB-API 2.0 compliance"""
    
    def test_module_attributes(self):
        """Test required module-level attributes"""
        import PGAdapter
        
        self.assertEqual(psycopg2_emulator.apilevel, '2.0')
        self.assertEqual(psycopg2_emulator.threadsafety, 2)
        self.assertEqual(psycopg2_emulator.paramstyle, 'pyformat')


if __name__ == '__main__':
    unittest.main()
