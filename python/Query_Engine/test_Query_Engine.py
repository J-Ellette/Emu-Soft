"""
Tests for SQLAlchemy Core emulator

Comprehensive test suite for SQLAlchemy Core emulator functionality.


Developed by PowerShield
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from Query_Engine import (
    create_engine, Engine, Connection, MetaData, Table, Column,
    select, text,
    Integer, String, Text, Boolean, DateTime, Float, Numeric,
    SQLAlchemyError, OperationalError, IntegrityError,
    _database_tables, _database_schemas
)


class TestEngine(unittest.TestCase):
    """Test engine functionality."""
    
    def setUp(self):
        """Clean storage before each test."""
        _database_tables.clear()
        _database_schemas.clear()
    
    def test_create_engine(self):
        """Test creating an engine."""
        engine = create_engine('sqlite:///:memory:')
        self.assertIsInstance(engine, Engine)
        self.assertEqual(engine.url, 'sqlite:///:memory:')
    
    def test_engine_with_options(self):
        """Test creating engine with options."""
        engine = create_engine(
            'postgresql://localhost/test',
            echo=True,
            pool_size=10
        )
        self.assertTrue(engine.echo)
        self.assertEqual(engine.pool_size, 10)
    
    def test_engine_connect(self):
        """Test creating a connection."""
        engine = create_engine('sqlite:///:memory:')
        conn = engine.connect()
        self.assertIsInstance(conn, Connection)


class TestMetadataAndTables(unittest.TestCase):
    """Test metadata and table definitions."""
    
    def setUp(self):
        """Clean storage before each test."""
        _database_tables.clear()
        _database_schemas.clear()
        self.engine = create_engine('sqlite:///:memory:')
        self.metadata = MetaData(bind=self.engine)
    
    def test_table_creation(self):
        """Test defining a table."""
        users = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50)),
            Column('email', String(100))
        )
        
        self.assertEqual(users.name, 'users')
        self.assertEqual(len(users.columns), 3)
        self.assertIn('users', self.metadata.tables)
    
    def test_column_types(self):
        """Test different column types."""
        table = Table('test_types', self.metadata,
            Column('int_col', Integer),
            Column('str_col', String(100)),
            Column('text_col', Text),
            Column('bool_col', Boolean),
            Column('dt_col', DateTime),
            Column('float_col', Float),
            Column('num_col', Numeric(10, 2))
        )
        
        self.assertEqual(len(table.columns), 7)
    
    def test_create_all(self):
        """Test creating all tables."""
        users = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50))
        )
        
        self.metadata.create_all()
        
        self.assertIn('users', _database_schemas)
    
    def test_drop_all(self):
        """Test dropping all tables."""
        users = Table('users', self.metadata,
            Column('id', Integer, primary_key=True)
        )
        
        self.metadata.create_all()
        self.metadata.drop_all()
        
        self.assertNotIn('users', _database_schemas)


class TestInsert(unittest.TestCase):
    """Test INSERT operations."""
    
    def setUp(self):
        """Clean storage and setup tables."""
        _database_tables.clear()
        _database_schemas.clear()
        self.engine = create_engine('sqlite:///:memory:')
        self.metadata = MetaData(bind=self.engine)
        
        self.users = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50)),
            Column('email', String(100))
        )
        self.metadata.create_all()
    
    def test_insert_values(self):
        """Test inserting values."""
        with self.engine.connect() as conn:
            stmt = self.users.insert().values(id=1, name='John', email='john@example.com')
            result = conn.execute(stmt)
        
        self.assertEqual(len(_database_tables['users']), 1)
        self.assertEqual(_database_tables['users'][0]['name'], 'John')
    
    def test_insert_multiple(self):
        """Test inserting multiple rows."""
        with self.engine.connect() as conn:
            conn.execute(self.users.insert().values(id=1, name='John', email='john@example.com'))
            conn.execute(self.users.insert().values(id=2, name='Jane', email='jane@example.com'))
        
        self.assertEqual(len(_database_tables['users']), 2)


class TestSelect(unittest.TestCase):
    """Test SELECT operations."""
    
    def setUp(self):
        """Clean storage and setup tables with data."""
        _database_tables.clear()
        _database_schemas.clear()
        self.engine = create_engine('sqlite:///:memory:')
        self.metadata = MetaData(bind=self.engine)
        
        self.users = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50)),
            Column('age', Integer)
        )
        self.metadata.create_all()
        
        # Insert test data
        with self.engine.connect() as conn:
            conn.execute(self.users.insert().values(id=1, name='Alice', age=30))
            conn.execute(self.users.insert().values(id=2, name='Bob', age=25))
            conn.execute(self.users.insert().values(id=3, name='Charlie', age=35))
    
    def test_select_all(self):
        """Test selecting all rows."""
        with self.engine.connect() as conn:
            stmt = self.users.select()
            result = conn.execute(stmt)
            rows = result.fetchall()
        
        self.assertEqual(len(rows), 3)
    
    def test_select_where(self):
        """Test SELECT with WHERE clause."""
        with self.engine.connect() as conn:
            stmt = self.users.select().where(self.users.c.name == 'Alice')
            result = conn.execute(stmt)
            rows = result.fetchall()
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], 'Alice')
    
    def test_select_where_comparison(self):
        """Test SELECT with comparison operators."""
        with self.engine.connect() as conn:
            # Greater than
            stmt = self.users.select().where(self.users.c.age > 30)
            result = conn.execute(stmt)
            rows = result.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['name'], 'Charlie')
            
            # Less than or equal
            stmt = self.users.select().where(self.users.c.age <= 25)
            result = conn.execute(stmt)
            rows = result.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['name'], 'Bob')
    
    def test_select_limit(self):
        """Test SELECT with LIMIT."""
        with self.engine.connect() as conn:
            stmt = self.users.select().limit(2)
            result = conn.execute(stmt)
            rows = result.fetchall()
        
        self.assertEqual(len(rows), 2)
    
    def test_select_offset(self):
        """Test SELECT with OFFSET."""
        with self.engine.connect() as conn:
            stmt = self.users.select().offset(1).limit(2)
            result = conn.execute(stmt)
            rows = result.fetchall()
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['id'], 2)
    
    def test_fetchone(self):
        """Test fetchone method."""
        with self.engine.connect() as conn:
            stmt = self.users.select()
            result = conn.execute(stmt)
            row = result.fetchone()
        
        self.assertIsNotNone(row)
        self.assertIn('name', row)
    
    def test_fetchmany(self):
        """Test fetchmany method."""
        with self.engine.connect() as conn:
            stmt = self.users.select()
            result = conn.execute(stmt)
            rows = result.fetchmany(2)
        
        self.assertEqual(len(rows), 2)
    
    def test_first(self):
        """Test first method."""
        with self.engine.connect() as conn:
            stmt = self.users.select()
            result = conn.execute(stmt)
            row = result.first()
        
        self.assertIsNotNone(row)
    
    def test_scalar(self):
        """Test scalar method."""
        with self.engine.connect() as conn:
            stmt = self.users.select().where(self.users.c.id == 1)
            result = conn.execute(stmt)
            value = result.scalar()
        
        self.assertEqual(value, 1)


class TestUpdate(unittest.TestCase):
    """Test UPDATE operations."""
    
    def setUp(self):
        """Clean storage and setup tables with data."""
        _database_tables.clear()
        _database_schemas.clear()
        self.engine = create_engine('sqlite:///:memory:')
        self.metadata = MetaData(bind=self.engine)
        
        self.users = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50)),
            Column('email', String(100))
        )
        self.metadata.create_all()
        
        # Insert test data
        with self.engine.connect() as conn:
            conn.execute(self.users.insert().values(id=1, name='John', email='john@example.com'))
            conn.execute(self.users.insert().values(id=2, name='Jane', email='jane@example.com'))
    
    def test_update_values(self):
        """Test updating values."""
        with self.engine.connect() as conn:
            stmt = self.users.update().where(self.users.c.id == 1).values(name='John Doe')
            conn.execute(stmt)
        
        self.assertEqual(_database_tables['users'][0]['name'], 'John Doe')
    
    def test_update_all(self):
        """Test updating all rows."""
        with self.engine.connect() as conn:
            stmt = self.users.update().values(email='updated@example.com')
            conn.execute(stmt)
        
        for row in _database_tables['users']:
            self.assertEqual(row['email'], 'updated@example.com')


class TestDelete(unittest.TestCase):
    """Test DELETE operations."""
    
    def setUp(self):
        """Clean storage and setup tables with data."""
        _database_tables.clear()
        _database_schemas.clear()
        self.engine = create_engine('sqlite:///:memory:')
        self.metadata = MetaData(bind=self.engine)
        
        self.users = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50))
        )
        self.metadata.create_all()
        
        # Insert test data
        with self.engine.connect() as conn:
            conn.execute(self.users.insert().values(id=1, name='Alice'))
            conn.execute(self.users.insert().values(id=2, name='Bob'))
            conn.execute(self.users.insert().values(id=3, name='Charlie'))
    
    def test_delete_where(self):
        """Test deleting specific rows."""
        with self.engine.connect() as conn:
            stmt = self.users.delete().where(self.users.c.id == 2)
            conn.execute(stmt)
        
        self.assertEqual(len(_database_tables['users']), 2)
        names = [row['name'] for row in _database_tables['users']]
        self.assertNotIn('Bob', names)


class TestTransactions(unittest.TestCase):
    """Test transaction management."""
    
    def setUp(self):
        """Clean storage and setup tables."""
        _database_tables.clear()
        _database_schemas.clear()
        self.engine = create_engine('sqlite:///:memory:')
        self.metadata = MetaData(bind=self.engine)
        
        self.users = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50))
        )
        self.metadata.create_all()
    
    def test_commit(self):
        """Test committing a transaction."""
        with self.engine.connect() as conn:
            conn.execute(self.users.insert().values(id=1, name='Alice'))
        
        self.assertEqual(len(_database_tables['users']), 1)
    
    def test_explicit_transaction(self):
        """Test explicit transaction."""
        conn = self.engine.connect()
        trans = conn.begin()
        
        conn.execute(self.users.insert().values(id=1, name='Alice'))
        trans.commit()
        
        conn.close()
        
        self.assertEqual(len(_database_tables['users']), 1)


class TestColumnOperators(unittest.TestCase):
    """Test column operators."""
    
    def setUp(self):
        """Setup tables."""
        _database_tables.clear()
        _database_schemas.clear()
        self.engine = create_engine('sqlite:///:memory:')
        self.metadata = MetaData(bind=self.engine)
        
        self.users = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50)),
            Column('age', Integer)
        )
        self.metadata.create_all()
        
        with self.engine.connect() as conn:
            conn.execute(self.users.insert().values(id=1, name='Alice', age=30))
            conn.execute(self.users.insert().values(id=2, name='Bob', age=25))
            conn.execute(self.users.insert().values(id=3, name='Charlie', age=35))
    
    def test_in_operator(self):
        """Test IN operator."""
        with self.engine.connect() as conn:
            stmt = self.users.select().where(self.users.c.id.in_([1, 3]))
            result = conn.execute(stmt)
            rows = result.fetchall()
        
        self.assertEqual(len(rows), 2)
        names = [row['name'] for row in rows]
        self.assertIn('Alice', names)
        self.assertIn('Charlie', names)


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete usage scenarios."""
    
    def setUp(self):
        """Clean storage."""
        _database_tables.clear()
        _database_schemas.clear()
    
    def test_user_management_system(self):
        """Test user management scenario."""
        # Setup
        engine = create_engine('sqlite:///users.db')
        metadata = MetaData(bind=engine)
        
        users = Table('users', metadata,
            Column('id', Integer, primary_key=True),
            Column('username', String(50)),
            Column('email', String(100)),
            Column('active', Boolean)
        )
        
        metadata.create_all()
        
        # Create users
        with engine.connect() as conn:
            conn.execute(users.insert().values(
                id=1,
                username='john_doe',
                email='john@example.com',
                active=True
            ))
            conn.execute(users.insert().values(
                id=2,
                username='jane_smith',
                email='jane@example.com',
                active=True
            ))
        
        # Query users
        with engine.connect() as conn:
            stmt = users.select().where(users.c.active == True)
            result = conn.execute(stmt)
            active_users = result.fetchall()
        
        self.assertEqual(len(active_users), 2)
        
        # Update user
        with engine.connect() as conn:
            stmt = users.update().where(users.c.id == 1).values(email='newemail@example.com')
            conn.execute(stmt)
        
        # Verify update
        with engine.connect() as conn:
            stmt = users.select().where(users.c.id == 1)
            result = conn.execute(stmt)
            user = result.first()
        
        self.assertEqual(user['email'], 'newemail@example.com')
    
    def test_blog_system(self):
        """Test blog system scenario."""
        engine = create_engine('sqlite:///blog.db')
        metadata = MetaData(bind=engine)
        
        posts = Table('posts', metadata,
            Column('id', Integer, primary_key=True),
            Column('title', String(200)),
            Column('content', Text),
            Column('author', String(50))
        )
        
        metadata.create_all()
        
        # Create posts
        with engine.connect() as conn:
            conn.execute(posts.insert().values(
                id=1,
                title='First Post',
                content='This is my first blog post',
                author='john'
            ))
            conn.execute(posts.insert().values(
                id=2,
                title='Second Post',
                content='Another great post',
                author='john'
            ))
        
        # Query posts by author
        with engine.connect() as conn:
            stmt = posts.select().where(posts.c.author == 'john')
            result = conn.execute(stmt)
            author_posts = result.fetchall()
        
        self.assertEqual(len(author_posts), 2)


if __name__ == '__main__':
    unittest.main()
