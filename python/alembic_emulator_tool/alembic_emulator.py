"""
Alembic Emulator - Database Migration Tool

This module emulates the alembic library, which is a lightweight database migration
tool for usage with SQLAlchemy. It provides a complete migration framework including
migration generation, upgrade/downgrade operations, and revision history management.

Key Features:
- Migration environment initialization
- Migration script generation
- Upgrade and downgrade operations
- Revision history tracking
- Branch management
- Auto-generation of migrations
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import json
import uuid
import re


class AlembicError(Exception):
    """Base exception for Alembic errors."""
    pass


class RevisionError(AlembicError):
    """Raised when there's an issue with revisions."""
    pass


class CommandError(AlembicError):
    """Raised when a command fails."""
    pass


# In-memory storage for migrations
_migrations: Dict[str, Dict[str, Any]] = {}  # revision_id -> migration data
_migration_history: List[str] = []  # Ordered list of applied migrations
_current_revision: Optional[str] = None
_migration_scripts: Dict[str, str] = {}  # revision_id -> script content


class Config:
    """Alembic configuration object."""
    
    def __init__(self, file_: Optional[str] = None, ini_section: str = 'alembic'):
        """
        Initialize Alembic configuration.
        
        Args:
            file_: Path to alembic.ini file
            ini_section: Section name in the ini file
        """
        self.file = file_ or 'alembic.ini'
        self.ini_section = ini_section
        self.config_file_name = self.file
        self.attributes = {}
        
        # Default configuration
        self.script_location = 'alembic'
        self.sqlalchemy_url = 'sqlite:///database.db'
        self.file_template = '%%(rev)s_%%(slug)s'
        self.truncate_slug_length = 40
        
    def set_main_option(self, name: str, value: str):
        """Set a configuration option."""
        self.attributes[name] = value
        if name == 'script_location':
            self.script_location = value
        elif name == 'sqlalchemy.url':
            self.sqlalchemy_url = value
    
    def get_main_option(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration option."""
        if name == 'script_location':
            return self.script_location
        elif name == 'sqlalchemy.url':
            return self.sqlalchemy_url
        return self.attributes.get(name, default)


class ScriptDirectory:
    """Manages the directory of migration scripts."""
    
    def __init__(self, dir_: str, config: Optional[Config] = None):
        """
        Initialize script directory.
        
        Args:
            dir_: Path to the scripts directory
            config: Alembic configuration
        """
        self.dir = dir_
        self.config = config or Config()
        self.version_locations = [dir_]
    
    @classmethod
    def from_config(cls, config: Config) -> ScriptDirectory:
        """Create ScriptDirectory from configuration."""
        script_location = config.get_main_option('script_location', 'alembic')
        return cls(script_location, config)
    
    def get_current_head(self) -> Optional[str]:
        """Get the current head revision."""
        if not _migrations:
            return None
        
        # Find revision with no down_revision pointing to it
        all_revisions = set(_migrations.keys())
        down_revisions = {m.get('down_revision') for m in _migrations.values() if m.get('down_revision')}
        heads = all_revisions - down_revisions
        
        if not heads:
            return None
        
        return list(heads)[0] if heads else None
    
    def get_revisions(self, id_: str) -> List[Dict[str, Any]]:
        """Get revisions up to the specified ID."""
        if id_ == 'head':
            id_ = self.get_current_head()
        
        if not id_ or id_ not in _migrations:
            return []
        
        revisions = []
        current = id_
        
        while current:
            if current in _migrations:
                revisions.append(_migrations[current])
                current = _migrations[current].get('down_revision')
            else:
                break
        
        return list(reversed(revisions))
    
    def walk_revisions(self, base: str = 'base', head: str = 'head') -> List[Dict[str, Any]]:
        """Walk through revisions from base to head."""
        if head == 'head':
            head = self.get_current_head()
        
        if not head:
            return []
        
        return self.get_revisions(head)
    
    def generate_revision(
        self,
        revid: str,
        message: Optional[str],
        head: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a new migration revision."""
        if head is None or head == 'head':
            head = self.get_current_head()
        
        revision = {
            'revision': revid,
            'down_revision': head,
            'message': message or 'empty migration',
            'created_at': datetime.utcnow().isoformat(),
            'branch_labels': kwargs.get('branch_labels'),
            'depends_on': kwargs.get('depends_on')
        }
        
        _migrations[revid] = revision
        return revision


class MigrationContext:
    """Context for migration operations."""
    
    def __init__(self, config: Config, script: ScriptDirectory):
        """
        Initialize migration context.
        
        Args:
            config: Alembic configuration
            script: Script directory
        """
        self.config = config
        self.script = script
        self.connection = None
    
    def get_current_revision(self) -> Optional[str]:
        """Get the currently applied revision."""
        return _current_revision
    
    def stamp(self, revision: str):
        """Stamp the database with a specific revision without running migrations."""
        global _current_revision
        
        if revision == 'head':
            revision = self.script.get_current_head()
        
        _current_revision = revision
        if revision and revision not in _migration_history:
            _migration_history.append(revision)


class EnvironmentContext:
    """Environment context for migrations."""
    
    def __init__(self, config: Config, script: ScriptDirectory):
        """
        Initialize environment context.
        
        Args:
            config: Alembic configuration
            script: Script directory
        """
        self.config = config
        self.script = script
        self.context = None
    
    def configure(
        self,
        connection: Any = None,
        target_metadata: Any = None,
        **kwargs
    ):
        """Configure the migration environment."""
        self.connection = connection
        self.target_metadata = target_metadata
        self.context = MigrationContext(self.config, self.script)
    
    def run_migrations(self):
        """Run pending migrations."""
        return self.context
    
    def get_context(self) -> MigrationContext:
        """Get the migration context."""
        return self.context


class Operations:
    """Migration operations class."""
    
    def __init__(self, migration_context: MigrationContext):
        """
        Initialize operations.
        
        Args:
            migration_context: Migration context
        """
        self.migration_context = migration_context
        self.operations = []
    
    def create_table(self, name: str, *columns, **kwargs):
        """Record a create table operation."""
        op = {
            'type': 'create_table',
            'name': name,
            'columns': columns,
            'kwargs': kwargs
        }
        self.operations.append(op)
        return op
    
    def drop_table(self, name: str, **kwargs):
        """Record a drop table operation."""
        op = {
            'type': 'drop_table',
            'name': name,
            'kwargs': kwargs
        }
        self.operations.append(op)
        return op
    
    def add_column(self, table_name: str, column, **kwargs):
        """Record an add column operation."""
        op = {
            'type': 'add_column',
            'table_name': table_name,
            'column': column,
            'kwargs': kwargs
        }
        self.operations.append(op)
        return op
    
    def drop_column(self, table_name: str, column_name: str, **kwargs):
        """Record a drop column operation."""
        op = {
            'type': 'drop_column',
            'table_name': table_name,
            'column_name': column_name,
            'kwargs': kwargs
        }
        self.operations.append(op)
        return op
    
    def alter_column(self, table_name: str, column_name: str, **kwargs):
        """Record an alter column operation."""
        op = {
            'type': 'alter_column',
            'table_name': table_name,
            'column_name': column_name,
            'kwargs': kwargs
        }
        self.operations.append(op)
        return op
    
    def create_index(self, index_name: str, table_name: str, columns: List[str], **kwargs):
        """Record a create index operation."""
        op = {
            'type': 'create_index',
            'index_name': index_name,
            'table_name': table_name,
            'columns': columns,
            'kwargs': kwargs
        }
        self.operations.append(op)
        return op
    
    def drop_index(self, index_name: str, table_name: Optional[str] = None, **kwargs):
        """Record a drop index operation."""
        op = {
            'type': 'drop_index',
            'index_name': index_name,
            'table_name': table_name,
            'kwargs': kwargs
        }
        self.operations.append(op)
        return op
    
    def execute(self, sql: str):
        """Record a raw SQL execution."""
        op = {
            'type': 'execute',
            'sql': sql
        }
        self.operations.append(op)
        return op


def init(directory: str = 'alembic', template: str = 'generic') -> Dict[str, Any]:
    """
    Initialize a new Alembic migration environment.
    
    Args:
        directory: Directory to create for migrations
        template: Template to use for initialization
    
    Returns:
        Dictionary with initialization information
    """
    return {
        'directory': directory,
        'template': template,
        'created': datetime.utcnow().isoformat(),
        'files': [
            f'{directory}/alembic.ini',
            f'{directory}/env.py',
            f'{directory}/script.py.mako',
            f'{directory}/versions/'
        ]
    }


def revision(
    message: Optional[str] = None,
    autogenerate: bool = False,
    head: str = 'head',
    config: Optional[Config] = None,
    **kwargs
) -> str:
    """
    Create a new migration revision.
    
    Args:
        message: Revision message
        autogenerate: Whether to auto-generate migration
        head: Head revision to use as base
        config: Alembic configuration
        **kwargs: Additional options
    
    Returns:
        Revision ID
    """
    config = config or Config()
    script = ScriptDirectory.from_config(config)
    
    # Generate revision ID
    revid = uuid.uuid4().hex[:12]
    
    # Generate revision
    rev = script.generate_revision(revid, message, head=head, **kwargs)
    
    # Generate script content
    template = f'''"""
{message or 'empty migration'}

Revision ID: {revid}
Revises: {rev['down_revision'] or 'None'}
Create Date: {rev['created_at']}

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '{revid}'
down_revision = {repr(rev['down_revision'])}
branch_labels = {repr(rev['branch_labels'])}
depends_on = {repr(rev['depends_on'])}


def upgrade():
    """Upgrade database schema."""
    pass


def downgrade():
    """Downgrade database schema."""
    pass
'''
    
    _migration_scripts[revid] = template
    
    return revid


def upgrade(revision: str = 'head', config: Optional[Config] = None) -> List[str]:
    """
    Upgrade to a later version.
    
    Args:
        revision: Target revision (default: 'head')
        config: Alembic configuration
    
    Returns:
        List of applied revision IDs
    """
    global _current_revision
    
    config = config or Config()
    script = ScriptDirectory.from_config(config)
    
    if revision == 'head':
        revision = script.get_current_head()
    
    if not revision:
        return []
    
    # Get all revisions to apply
    revisions_to_apply = script.get_revisions(revision)
    
    # Filter out already applied
    if _current_revision:
        current_revisions = script.get_revisions(_current_revision)
        current_ids = {r['revision'] for r in current_revisions}
        revisions_to_apply = [r for r in revisions_to_apply if r['revision'] not in current_ids]
    
    applied = []
    for rev in revisions_to_apply:
        rev_id = rev['revision']
        if rev_id not in _migration_history:
            _migration_history.append(rev_id)
        _current_revision = rev_id
        applied.append(rev_id)
    
    return applied


def downgrade(revision: str = '-1', config: Optional[Config] = None) -> List[str]:
    """
    Revert to a previous version.
    
    Args:
        revision: Target revision (default: '-1' for one step back)
        config: Alembic configuration
    
    Returns:
        List of downgraded revision IDs
    """
    global _current_revision
    
    config = config or Config()
    script = ScriptDirectory.from_config(config)
    
    if not _current_revision:
        return []
    
    downgraded = []
    
    if revision == '-1':
        # Downgrade one step
        current_migration = _migrations.get(_current_revision)
        if current_migration:
            downgraded.append(_current_revision)
            if _current_revision in _migration_history:
                _migration_history.remove(_current_revision)
            _current_revision = current_migration.get('down_revision')
    elif revision == 'base':
        # Downgrade all
        while _current_revision:
            downgraded.append(_current_revision)
            current_migration = _migrations.get(_current_revision)
            if _current_revision in _migration_history:
                _migration_history.remove(_current_revision)
            _current_revision = current_migration.get('down_revision') if current_migration else None
    else:
        # Downgrade to specific revision
        while _current_revision and _current_revision != revision:
            downgraded.append(_current_revision)
            current_migration = _migrations.get(_current_revision)
            if _current_revision in _migration_history:
                _migration_history.remove(_current_revision)
            _current_revision = current_migration.get('down_revision') if current_migration else None
    
    return downgraded


def current(config: Optional[Config] = None) -> Optional[str]:
    """
    Get the current revision.
    
    Args:
        config: Alembic configuration
    
    Returns:
        Current revision ID or None
    """
    return _current_revision


def history(config: Optional[Config] = None, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Get migration history.
    
    Args:
        config: Alembic configuration
        verbose: Whether to include verbose information
    
    Returns:
        List of migration information
    """
    config = config or Config()
    script = ScriptDirectory.from_config(config)
    
    head = script.get_current_head()
    if not head:
        return []
    
    revisions = script.get_revisions(head)
    
    if verbose:
        return revisions
    else:
        return [
            {
                'revision': r['revision'],
                'message': r['message'],
                'current': r['revision'] == _current_revision
            }
            for r in revisions
        ]


def heads(config: Optional[Config] = None) -> List[str]:
    """
    Get all head revisions.
    
    Args:
        config: Alembic configuration
    
    Returns:
        List of head revision IDs
    """
    config = config or Config()
    script = ScriptDirectory.from_config(config)
    
    head = script.get_current_head()
    return [head] if head else []


def stamp(revision: str, config: Optional[Config] = None):
    """
    Stamp the version table with a specific revision.
    
    Args:
        revision: Revision ID to stamp
        config: Alembic configuration
    """
    global _current_revision
    
    config = config or Config()
    script = ScriptDirectory.from_config(config)
    context = MigrationContext(config, script)
    
    context.stamp(revision)
    _current_revision = context.get_current_revision()


def merge(revisions: List[str], message: Optional[str] = None, config: Optional[Config] = None) -> str:
    """
    Merge multiple heads into a single revision.
    
    Args:
        revisions: List of revision IDs to merge
        message: Merge message
        config: Alembic configuration
    
    Returns:
        Merge revision ID
    """
    config = config or Config()
    
    merge_revid = uuid.uuid4().hex[:12]
    
    merge_rev = {
        'revision': merge_revid,
        'down_revision': tuple(revisions),
        'message': message or f'merge {", ".join(revisions)}',
        'created_at': datetime.utcnow().isoformat(),
        'branch_labels': None,
        'depends_on': None
    }
    
    _migrations[merge_revid] = merge_rev
    
    return merge_revid


# Context manager for operations
class op:
    """Operations context manager."""
    
    @staticmethod
    def create_table(name: str, *columns, **kwargs):
        """Create a table."""
        return {'type': 'create_table', 'name': name, 'columns': columns}
    
    @staticmethod
    def drop_table(name: str):
        """Drop a table."""
        return {'type': 'drop_table', 'name': name}
    
    @staticmethod
    def add_column(table_name: str, column):
        """Add a column."""
        return {'type': 'add_column', 'table_name': table_name, 'column': column}
    
    @staticmethod
    def drop_column(table_name: str, column_name: str):
        """Drop a column."""
        return {'type': 'drop_column', 'table_name': table_name, 'column_name': column_name}
    
    @staticmethod
    def execute(sql: str):
        """Execute raw SQL."""
        return {'type': 'execute', 'sql': sql}
