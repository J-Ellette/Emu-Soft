"""
Tests for asyncpg emulator
"""

import asyncio
import unittest
from AsyncPG import (
    connect, create_pool, Connection, Pool, Record, Transaction,
    PostgresError, InterfaceError, ConnectionError as AsyncpgConnectionError
)


class TestRecord(unittest.TestCase):
    """Test Record class"""
    
    def test_record_creation(self):
        """Test creating a record"""
        data = {'id': 1, 'name': 'Test', 'email': 'test@example.com'}
        columns = ['id', 'name', 'email']
        record = Record(data, columns)
        
        self.assertEqual(record['id'], 1)
        self.assertEqual(record['name'], 'Test')
        self.assertEqual(record['email'], 'test@example.com')
    
    def test_record_index_access(self):
        """Test accessing record by index"""
        data = {'id': 1, 'name': 'Test', 'email': 'test@example.com'}
        columns = ['id', 'name', 'email']
        record = Record(data, columns)
        
        self.assertEqual(record[0], 1)
        self.assertEqual(record[1], 'Test')
        self.assertEqual(record[2], 'test@example.com')
    
    def test_record_iteration(self):
        """Test iterating over record values"""
        data = {'id': 1, 'name': 'Test', 'email': 'test@example.com'}
        columns = ['id', 'name', 'email']
        record = Record(data, columns)
        
        values = list(record)
        self.assertEqual(values, [1, 'Test', 'test@example.com'])
    
    def test_record_keys(self):
        """Test getting record keys"""
        data = {'id': 1, 'name': 'Test'}
        columns = ['id', 'name']
        record = Record(data, columns)
        
        self.assertEqual(record.keys(), ['id', 'name'])
    
    def test_record_values(self):
        """Test getting record values"""
        data = {'id': 1, 'name': 'Test'}
        columns = ['id', 'name']
        record = Record(data, columns)
        
        self.assertEqual(record.values(), [1, 'Test'])
    
    def test_record_items(self):
        """Test getting record items"""
        data = {'id': 1, 'name': 'Test'}
        columns = ['id', 'name']
        record = Record(data, columns)
        
        self.assertEqual(record.items(), [('id', 1), ('name', 'Test')])
    
    def test_record_get(self):
        """Test get method with default"""
        data = {'id': 1, 'name': 'Test'}
        columns = ['id', 'name']
        record = Record(data, columns)
        
        self.assertEqual(record.get('id'), 1)
        self.assertEqual(record.get('missing', 'default'), 'default')


class TestConnection(unittest.IsolatedAsyncioTestCase):
    """Test Connection class"""
    
    async def test_connect(self):
        """Test creating a connection"""
        conn = await connect(
            host='localhost',
            port=5432,
            database='testdb',
            user='testuser',
            password='testpass'
        )
        
        self.assertIsInstance(conn, Connection)
        self.assertFalse(conn.is_closed())
        
        await conn.close()
        self.assertTrue(conn.is_closed())
    
    async def test_connect_with_dsn(self):
        """Test creating connection with DSN"""
        conn = await connect(dsn='postgresql://user:pass@localhost:5432/testdb')
        
        self.assertIsInstance(conn, Connection)
        self.assertFalse(conn.is_closed())
        
        await conn.close()
    
    async def test_fetch(self):
        """Test fetching multiple rows"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        results = await conn.fetch('SELECT * FROM users WHERE age > $1', 25)
        
        self.assertIsInstance(results, list)
        if results:
            self.assertIsInstance(results[0], Record)
        
        await conn.close()
    
    async def test_fetchrow(self):
        """Test fetching single row"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        result = await conn.fetchrow('SELECT * FROM users WHERE id = $1', 1)
        
        if result is not None:
            self.assertIsInstance(result, Record)
        
        await conn.close()
    
    async def test_fetchval(self):
        """Test fetching single value"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        count = await conn.fetchval('SELECT COUNT(*) FROM users')
        
        self.assertIsInstance(count, int)
        
        await conn.close()
    
    async def test_execute(self):
        """Test executing a command"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        status = await conn.execute(
            'INSERT INTO users (name, email) VALUES ($1, $2)',
            'John Doe', 'john@example.com'
        )
        
        self.assertIsInstance(status, str)
        self.assertIn('INSERT', status)
        
        await conn.close()
    
    async def test_executemany(self):
        """Test executing command multiple times"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
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
    
    async def test_closed_connection_error(self):
        """Test that closed connection raises error"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        await conn.close()
        
        with self.assertRaises(InterfaceError):
            await conn.fetch('SELECT * FROM users')


class TestTransaction(unittest.IsolatedAsyncioTestCase):
    """Test Transaction class"""
    
    async def test_transaction_context(self):
        """Test transaction as context manager"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        async with conn.transaction():
            await conn.execute('INSERT INTO users (name) VALUES ($1)', 'Test User')
        
        # Transaction should commit automatically
        self.assertFalse(conn._in_transaction)
        
        await conn.close()
    
    async def test_transaction_rollback_on_error(self):
        """Test transaction rollback on exception"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        try:
            async with conn.transaction():
                await conn.execute('INSERT INTO users (name) VALUES ($1)', 'Test User')
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Transaction should have rolled back
        self.assertFalse(conn._in_transaction)
        
        await conn.close()
    
    async def test_transaction_isolation_levels(self):
        """Test different isolation levels"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        async with conn.transaction(isolation='serializable'):
            await conn.execute('SELECT * FROM users')
        
        async with conn.transaction(isolation='repeatable_read'):
            await conn.execute('SELECT * FROM users')
        
        await conn.close()


class TestPool(unittest.IsolatedAsyncioTestCase):
    """Test Pool class"""
    
    async def test_create_pool(self):
        """Test creating a connection pool"""
        pool = await create_pool(
            host='localhost',
            port=5432,
            database='testdb',
            user='testuser',
            password='testpass',
            min_size=5,
            max_size=10
        )
        
        self.assertIsInstance(pool, Pool)
        self.assertFalse(pool.is_closed())
        
        await pool.close()
        self.assertTrue(pool.is_closed())
    
    async def test_create_pool_with_dsn(self):
        """Test creating pool with DSN"""
        pool = await create_pool(
            dsn='postgresql://user:pass@localhost:5432/testdb',
            min_size=5,
            max_size=10
        )
        
        self.assertIsInstance(pool, Pool)
        
        await pool.close()
    
    async def test_pool_acquire_release(self):
        """Test acquiring and releasing connections"""
        pool = await create_pool(
            database='testdb',
            user='testuser',
            password='testpass',
            min_size=2,
            max_size=5
        )
        
        conn = await pool.acquire()
        self.assertIsInstance(conn, Connection)
        
        await pool.release(conn)
        
        await pool.close()
    
    async def test_pool_acquire_context(self):
        """Test pool acquire context manager"""
        pool = await create_pool(
            database='testdb',
            user='testuser',
            password='testpass',
            min_size=2,
            max_size=5
        )
        
        async with pool.acquire_context() as conn:
            self.assertIsInstance(conn, Connection)
            self.assertFalse(conn.is_closed())
        
        # Connection should be released
        
        await pool.close()
    
    async def test_pool_fetch(self):
        """Test pool fetch method"""
        pool = await create_pool(
            database='testdb',
            user='testuser',
            password='testpass'
        )
        
        results = await pool.fetch('SELECT * FROM users WHERE age > $1', 25)
        
        self.assertIsInstance(results, list)
        
        await pool.close()
    
    async def test_pool_fetchrow(self):
        """Test pool fetchrow method"""
        pool = await create_pool(
            database='testdb',
            user='testuser',
            password='testpass'
        )
        
        result = await pool.fetchrow('SELECT * FROM users WHERE id = $1', 1)
        
        if result is not None:
            self.assertIsInstance(result, Record)
        
        await pool.close()
    
    async def test_pool_fetchval(self):
        """Test pool fetchval method"""
        pool = await create_pool(
            database='testdb',
            user='testuser',
            password='testpass'
        )
        
        count = await pool.fetchval('SELECT COUNT(*) FROM users')
        
        self.assertIsInstance(count, int)
        
        await pool.close()
    
    async def test_pool_execute(self):
        """Test pool execute method"""
        pool = await create_pool(
            database='testdb',
            user='testuser',
            password='testpass'
        )
        
        status = await pool.execute(
            'INSERT INTO users (name, email) VALUES ($1, $2)',
            'John Doe', 'john@example.com'
        )
        
        self.assertIsInstance(status, str)
        
        await pool.close()
    
    async def test_pool_executemany(self):
        """Test pool executemany method"""
        pool = await create_pool(
            database='testdb',
            user='testuser',
            password='testpass'
        )
        
        data = [
            ('Alice', 'alice@example.com'),
            ('Bob', 'bob@example.com'),
        ]
        
        await pool.executemany(
            'INSERT INTO users (name, email) VALUES ($1, $2)',
            data
        )
        
        await pool.close()


class TestParameterEscaping(unittest.IsolatedAsyncioTestCase):
    """Test parameter escaping and formatting"""
    
    async def test_positional_parameters(self):
        """Test positional parameter binding"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        # Test with various parameter types
        await conn.execute(
            'INSERT INTO users (name, age, active) VALUES ($1, $2, $3)',
            'John Doe', 30, True
        )
        
        await conn.close()
    
    async def test_null_parameter(self):
        """Test NULL parameter handling"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        await conn.execute(
            'INSERT INTO users (name, email) VALUES ($1, $2)',
            'John Doe', None
        )
        
        await conn.close()
    
    async def test_string_escaping(self):
        """Test string escaping"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        # String with quotes
        await conn.execute(
            'INSERT INTO users (name) VALUES ($1)',
            "O'Brien"
        )
        
        await conn.close()
    
    async def test_json_parameter(self):
        """Test JSON parameter handling"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        
        data = {'key': 'value', 'nested': {'foo': 'bar'}}
        await conn.execute(
            'INSERT INTO users (data) VALUES ($1)',
            data
        )
        
        await conn.close()


class TestExceptions(unittest.IsolatedAsyncioTestCase):
    """Test exception handling"""
    
    async def test_interface_error(self):
        """Test InterfaceError"""
        conn = await connect(database='testdb', user='testuser', password='testpass')
        await conn.close()
        
        with self.assertRaises(InterfaceError):
            await conn.execute('SELECT * FROM users')
    
    async def test_closed_pool_error(self):
        """Test error when using closed pool"""
        pool = await create_pool(database='testdb', user='testuser', password='testpass')
        await pool.close()
        
        with self.assertRaises(InterfaceError):
            await pool.acquire()


if __name__ == '__main__':
    unittest.main()
