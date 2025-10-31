"""
Tests for Alembic emulator

Comprehensive test suite for database migration tool functionality.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from alembic_emulator import (
    Config, ScriptDirectory, MigrationContext, EnvironmentContext, Operations,
    init, revision, upgrade, downgrade, current, history, heads, stamp, merge, op,
    AlembicError, RevisionError, CommandError,
    _migrations, _migration_history, _current_revision, _migration_scripts
)


class TestConfig(unittest.TestCase):
    """Test Alembic configuration."""
    
    def test_config_creation(self):
        """Test basic config creation."""
        config = Config('alembic.ini')
        
        self.assertEqual(config.file, 'alembic.ini')
        self.assertEqual(config.ini_section, 'alembic')
    
    def test_config_set_option(self):
        """Test setting configuration options."""
        config = Config()
        config.set_main_option('sqlalchemy.url', 'postgresql://localhost/testdb')
        
        self.assertEqual(config.sqlalchemy_url, 'postgresql://localhost/testdb')
    
    def test_config_get_option(self):
        """Test getting configuration options."""
        config = Config()
        config.set_main_option('custom_option', 'value')
        
        self.assertEqual(config.get_main_option('custom_option'), 'value')
        self.assertIsNone(config.get_main_option('nonexistent'))


class TestScriptDirectory(unittest.TestCase):
    """Test script directory management."""
    
    def setUp(self):
        """Clean state before each test."""
        _migrations.clear()
        _migration_history.clear()
        import alembic_emulator
        alembic_emulator._current_revision = None
    
    def test_script_directory_creation(self):
        """Test creating script directory."""
        script_dir = ScriptDirectory('alembic')
        
        self.assertEqual(script_dir.dir, 'alembic')
        self.assertIsInstance(script_dir.config, Config)
    
    def test_script_directory_from_config(self):
        """Test creating script directory from config."""
        config = Config()
        config.set_main_option('script_location', 'migrations')
        
        script_dir = ScriptDirectory.from_config(config)
        
        self.assertEqual(script_dir.dir, 'migrations')
    
    def test_generate_revision(self):
        """Test generating a new revision."""
        script_dir = ScriptDirectory('alembic')
        
        rev = script_dir.generate_revision('abc123', 'Add users table')
        
        self.assertEqual(rev['revision'], 'abc123')
        self.assertEqual(rev['message'], 'Add users table')
        self.assertIsNone(rev['down_revision'])
    
    def test_generate_chained_revisions(self):
        """Test generating chained revisions."""
        script_dir = ScriptDirectory('alembic')
        
        rev1 = script_dir.generate_revision('rev001', 'First migration')
        rev2 = script_dir.generate_revision('rev002', 'Second migration', head='rev001')
        
        self.assertEqual(rev2['down_revision'], 'rev001')
    
    def test_get_current_head(self):
        """Test getting current head."""
        script_dir = ScriptDirectory('alembic')
        
        script_dir.generate_revision('rev001', 'First')
        script_dir.generate_revision('rev002', 'Second', head='rev001')
        
        head = script_dir.get_current_head()
        self.assertEqual(head, 'rev002')


class TestMigrationCommands(unittest.TestCase):
    """Test migration command functions."""
    
    def setUp(self):
        """Clean state before each test."""
        _migrations.clear()
        _migration_history.clear()
        _migration_scripts.clear()
        import alembic_emulator
        alembic_emulator._current_revision = None
    
    def test_init_command(self):
        """Test init command."""
        result = init('alembic')
        
        self.assertEqual(result['directory'], 'alembic')
        self.assertIn('files', result)
    
    def test_revision_command(self):
        """Test revision command."""
        rev_id = revision('Add users table')
        
        self.assertIn(rev_id, _migrations)
        self.assertIn(rev_id, _migration_scripts)
        self.assertIn('Add users table', _migration_scripts[rev_id])
    
    def test_multiple_revisions(self):
        """Test creating multiple revisions."""
        rev1 = revision('First migration')
        rev2 = revision('Second migration')
        
        self.assertIn(rev1, _migrations)
        self.assertIn(rev2, _migrations)
        self.assertEqual(_migrations[rev2]['down_revision'], rev1)
    
    def test_upgrade_command(self):
        """Test upgrade command."""
        rev1 = revision('First migration')
        rev2 = revision('Second migration')
        
        applied = upgrade('head')
        
        self.assertEqual(len(applied), 2)
        self.assertIn(rev1, applied)
        self.assertIn(rev2, applied)
    
    def test_downgrade_one_step(self):
        """Test downgrading one step."""
        rev1 = revision('First migration')
        rev2 = revision('Second migration')
        upgrade('head')
        
        downgraded = downgrade('-1')
        
        self.assertEqual(len(downgraded), 1)
        self.assertIn(rev2, downgraded)
        self.assertEqual(current(), rev1)
    
    def test_downgrade_to_base(self):
        """Test downgrading to base."""
        rev1 = revision('First migration')
        rev2 = revision('Second migration')
        upgrade('head')
        
        downgraded = downgrade('base')
        
        self.assertEqual(len(downgraded), 2)
        self.assertIsNone(current())
    
    def test_current_command(self):
        """Test current command."""
        rev1 = revision('First migration')
        upgrade('head')
        
        curr = current()
        self.assertEqual(curr, rev1)
    
    def test_history_command(self):
        """Test history command."""
        rev1 = revision('First migration')
        rev2 = revision('Second migration')
        upgrade('head')
        
        hist = history()
        
        self.assertEqual(len(hist), 2)
        self.assertTrue(any(h['revision'] == rev1 for h in hist))
        self.assertTrue(any(h['revision'] == rev2 for h in hist))
    
    def test_heads_command(self):
        """Test heads command."""
        rev1 = revision('First migration')
        
        head_list = heads()
        
        self.assertEqual(len(head_list), 1)
        self.assertEqual(head_list[0], rev1)
    
    def test_stamp_command(self):
        """Test stamp command."""
        rev1 = revision('First migration')
        
        stamp(rev1)
        
        self.assertEqual(current(), rev1)
    
    def test_merge_command(self):
        """Test merge command."""
        rev1 = revision('Branch A')
        rev2 = revision('Branch B')
        
        merge_rev = merge([rev1, rev2], 'Merge branches')
        
        self.assertIn(merge_rev, _migrations)
        self.assertEqual(_migrations[merge_rev]['down_revision'], (rev1, rev2))


class TestOperations(unittest.TestCase):
    """Test migration operations."""
    
    def test_create_table_operation(self):
        """Test create table operation."""
        result = op.create_table('users', 'id', 'name', 'email')
        
        self.assertEqual(result['type'], 'create_table')
        self.assertEqual(result['name'], 'users')
    
    def test_drop_table_operation(self):
        """Test drop table operation."""
        result = op.drop_table('users')
        
        self.assertEqual(result['type'], 'drop_table')
        self.assertEqual(result['name'], 'users')
    
    def test_add_column_operation(self):
        """Test add column operation."""
        result = op.add_column('users', 'age')
        
        self.assertEqual(result['type'], 'add_column')
        self.assertEqual(result['table_name'], 'users')
    
    def test_drop_column_operation(self):
        """Test drop column operation."""
        result = op.drop_column('users', 'age')
        
        self.assertEqual(result['type'], 'drop_column')
        self.assertEqual(result['table_name'], 'users')
    
    def test_execute_operation(self):
        """Test execute SQL operation."""
        result = op.execute('ALTER TABLE users ADD COLUMN status VARCHAR(20)')
        
        self.assertEqual(result['type'], 'execute')
        self.assertIn('ALTER TABLE', result['sql'])


class TestMigrationContext(unittest.TestCase):
    """Test migration context."""
    
    def setUp(self):
        """Clean state before each test."""
        _migrations.clear()
        _migration_history.clear()
        import alembic_emulator
        alembic_emulator._current_revision = None
    
    def test_context_creation(self):
        """Test creating migration context."""
        config = Config()
        script = ScriptDirectory('alembic', config)
        context = MigrationContext(config, script)
        
        self.assertEqual(context.config, config)
        self.assertEqual(context.script, script)
    
    def test_context_get_current_revision(self):
        """Test getting current revision from context."""
        config = Config()
        script = ScriptDirectory('alembic', config)
        context = MigrationContext(config, script)
        
        self.assertIsNone(context.get_current_revision())
    
    def test_context_stamp(self):
        """Test stamping via context."""
        config = Config()
        script = ScriptDirectory('alembic', config)
        context = MigrationContext(config, script)
        
        rev1 = script.generate_revision('rev001', 'Test migration')
        context.stamp('rev001')
        
        self.assertEqual(context.get_current_revision(), 'rev001')


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete migration scenarios."""
    
    def setUp(self):
        """Clean state before each test."""
        _migrations.clear()
        _migration_history.clear()
        _migration_scripts.clear()
        import alembic_emulator
        alembic_emulator._current_revision = None
    
    def test_complete_migration_workflow(self):
        """Test complete migration workflow."""
        # Initialize
        init_result = init('alembic')
        self.assertIn('directory', init_result)
        
        # Create migrations
        rev1 = revision('Create users table')
        rev2 = revision('Add email to users')
        rev3 = revision('Create posts table')
        
        # Verify revisions created
        self.assertEqual(len(_migrations), 3)
        
        # Upgrade to head
        applied = upgrade('head')
        self.assertEqual(len(applied), 3)
        
        # Check current
        curr = current()
        self.assertEqual(curr, rev3)
        
        # Downgrade one step
        downgraded = downgrade('-1')
        self.assertEqual(len(downgraded), 1)
        self.assertEqual(current(), rev2)
        
        # Upgrade back to head
        applied = upgrade('head')
        self.assertEqual(len(applied), 1)
        self.assertEqual(current(), rev3)
        
        # Check history
        hist = history()
        self.assertEqual(len(hist), 3)
    
    def test_branching_and_merging(self):
        """Test branch creation and merging."""
        # Create base
        base_rev = revision('Base migration')
        upgrade('head')
        
        # Create two branches from base
        config = Config()
        script = ScriptDirectory.from_config(config)
        
        branch_a = script.generate_revision('branch_a', 'Branch A', head=base_rev)
        branch_b = script.generate_revision('branch_b', 'Branch B', head=base_rev)
        
        # Merge branches
        merge_rev = merge(['branch_a', 'branch_b'], 'Merge A and B')
        
        self.assertIn(merge_rev, _migrations)
        self.assertEqual(_migrations[merge_rev]['down_revision'], ('branch_a', 'branch_b'))
    
    def test_migration_script_generation(self):
        """Test that migration scripts are generated correctly."""
        rev1 = revision('Add users table')
        
        script_content = _migration_scripts[rev1]
        
        self.assertIn('Add users table', script_content)
        self.assertIn(f'revision = \'{rev1}\'', script_content)
        self.assertIn('def upgrade():', script_content)
        self.assertIn('def downgrade():', script_content)


if __name__ == '__main__':
    unittest.main()
