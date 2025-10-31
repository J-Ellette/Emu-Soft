# Alembic Emulator - Database Migration Tool

This module emulates the **Alembic** library, which is a lightweight database migration tool for usage with SQLAlchemy. It provides a complete migration framework including migration generation, upgrade/downgrade operations, and revision history management.

## What is Alembic?

Alembic is a database migrations tool written by Mike Bayer, the author of SQLAlchemy. It provides:
- Database schema version control
- Migration script generation
- Upgrade and downgrade operations
- Branch and merge support
- Auto-generation from SQLAlchemy models
- Revision history tracking

## Features

This emulator implements core Alembic functionality:

### Migration Environment
- Environment initialization (`init`)
- Configuration management
- Script directory structure

### Revision Management
- Create new revisions
- Chain revisions with dependencies
- Auto-generate migration scripts
- Branch and merge support

### Migration Operations
- Upgrade to specific revision or head
- Downgrade to previous revisions
- Stamp database version
- Query current revision and history

### Schema Operations
- Create/drop tables
- Add/drop columns
- Alter columns
- Create/drop indexes
- Execute raw SQL

## Usage Examples

### Initializing a Migration Environment

```python
from alembic_emulator import init, Config

# Initialize new migration environment
result = init(directory='alembic', template='generic')
print(f"Created migration directory: {result['directory']}")
```

### Creating Migration Revisions

```python
from alembic_emulator import revision, Config

# Create a new migration
rev_id = revision(message='Create users table')
print(f"Created revision: {rev_id}")

# Create another migration (will chain to previous)
rev_id2 = revision(message='Add email to users')
print(f"Created revision: {rev_id2}")

# Create with specific configuration
config = Config()
config.set_main_option('script_location', 'migrations')
rev_id3 = revision(message='Create posts table', config=config)
```

### Upgrading and Downgrading

```python
from alembic_emulator import upgrade, downgrade, current

# Upgrade to latest version
applied = upgrade('head')
print(f"Applied {len(applied)} migrations")

# Check current revision
curr = current()
print(f"Current revision: {curr}")

# Downgrade one step
downgraded = downgrade('-1')
print(f"Downgraded {len(downgraded)} migrations")

# Downgrade to base (remove all migrations)
downgraded = downgrade('base')
print(f"Downgraded to base")

# Upgrade to specific revision
upgrade('abc123')
```

### Querying Migration History

```python
from alembic_emulator import history, heads, current

# Get migration history
hist = history(verbose=True)
for migration in hist:
    print(f"{migration['revision']}: {migration['message']}")
    if migration.get('down_revision'):
        print(f"  (depends on {migration['down_revision']})")

# Get head revisions
head_revisions = heads()
print(f"Head revisions: {head_revisions}")

# Get current revision
curr = current()
print(f"Current: {curr}")
```

### Stamping Database Version

```python
from alembic_emulator import stamp, revision

# Create revisions
rev1 = revision('First migration')
rev2 = revision('Second migration')

# Stamp database as if migrations were applied
# (without actually running them)
stamp(rev2)

# Now current() will return rev2
print(f"Current revision: {current()}")
```

### Using Script Directory

```python
from alembic_emulator import Config, ScriptDirectory

# Create configuration
config = Config('alembic.ini')
config.set_main_option('script_location', 'migrations')

# Create script directory
script = ScriptDirectory.from_config(config)

# Generate a revision
rev = script.generate_revision('abc123', 'Add users table')
print(f"Generated revision: {rev['revision']}")

# Get current head
head = script.get_current_head()
print(f"Current head: {head}")

# Walk through revisions
revisions = script.walk_revisions(base='base', head='head')
for rev in revisions:
    print(f"{rev['revision']}: {rev['message']}")
```

### Branch and Merge

```python
from alembic_emulator import revision, merge, Config, ScriptDirectory

# Create base migration
base = revision('Base migration')

# Create two branches
config = Config()
script = ScriptDirectory.from_config(config)

branch_a = script.generate_revision('branch_a', 'Feature A', head=base)
branch_b = script.generate_revision('branch_b', 'Feature B', head=base)

# Merge branches
merge_rev = merge([branch_a['revision'], branch_b['revision']], 'Merge A and B')
print(f"Merge revision: {merge_rev}")
```

### Using Operations in Migration Scripts

```python
from alembic_emulator import op

# In your migration's upgrade() function:
def upgrade():
    # Create table
    op.create_table(
        'users',
        'id', 'username', 'email', 'created_at'
    )
    
    # Add column
    op.add_column('users', 'last_login')
    
    # Create index
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Execute raw SQL
    op.execute('ALTER TABLE users ADD CONSTRAINT ...')

def downgrade():
    # Drop table
    op.drop_table('users')
```

### Complete Migration Workflow

```python
from alembic_emulator import (
    init, revision, upgrade, downgrade, 
    current, history, Config
)

# 1. Initialize migration environment
init_result = init('alembic')
print("Initialized migration environment")

# 2. Create configuration
config = Config('alembic.ini')
config.set_main_option('sqlalchemy.url', 'postgresql://localhost/mydb')

# 3. Create first migration
rev1 = revision('Create users table', config=config)
print(f"Created migration: {rev1}")

# 4. Create second migration
rev2 = revision('Add posts table', config=config)
print(f"Created migration: {rev2}")

# 5. Create third migration
rev3 = revision('Add comments table', config=config)
print(f"Created migration: {rev3}")

# 6. Upgrade to latest
applied = upgrade('head', config=config)
print(f"Applied migrations: {applied}")

# 7. Check current revision
curr = current(config=config)
print(f"Current revision: {curr}")

# 8. View history
hist = history(config=config)
print("\nMigration history:")
for h in hist:
    marker = "(current)" if h.get('current') else ""
    print(f"  {h['revision']}: {h['message']} {marker}")

# 9. Downgrade one step
downgraded = downgrade('-1', config=config)
print(f"\nDowngraded: {downgraded}")
print(f"Current revision: {current(config=config)}")

# 10. Upgrade back to head
applied = upgrade('head', config=config)
print(f"Re-applied: {applied}")
```

### Working with Migration Context

```python
from alembic_emulator import Config, ScriptDirectory, MigrationContext

# Setup
config = Config()
script = ScriptDirectory.from_config(config)

# Create migration context
context = MigrationContext(config, script)

# Check current revision
curr = context.get_current_revision()
print(f"Current: {curr}")

# Stamp database
context.stamp('abc123')
print(f"Stamped to: {context.get_current_revision()}")
```

## Testing

Run the comprehensive test suite:

```bash
python test_alembic_emulator.py
```

Tests cover:
- Configuration management
- Script directory operations
- Revision generation and management
- Upgrade and downgrade operations
- History and status queries
- Branch and merge functionality
- Migration context operations
- Complete workflow scenarios

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for Alembic in development and testing:

```python
# Instead of:
# from alembic import command, config

# Use:
from alembic_emulator import revision, upgrade, downgrade, Config
```

## Use Cases

Perfect for:
- **Testing**: Test database migrations without a real database
- **Development**: Develop migration scripts locally
- **CI/CD**: Run migration tests in pipelines
- **Learning**: Learn Alembic concepts and patterns
- **Prototyping**: Quickly prototype migration strategies
- **Documentation**: Generate migration documentation

## Command Reference

### Initialization Commands
- `init(directory, template)` - Initialize migration environment

### Revision Commands
- `revision(message, autogenerate, head, config)` - Create new revision
- `merge(revisions, message, config)` - Merge multiple heads

### Migration Commands
- `upgrade(revision, config)` - Upgrade to revision
- `downgrade(revision, config)` - Downgrade to revision
- `stamp(revision, config)` - Stamp database version

### Query Commands
- `current(config)` - Show current revision
- `history(config, verbose)` - Show revision history
- `heads(config)` - Show head revisions

### Operation Commands (in migration scripts)
- `op.create_table(name, *columns)` - Create table
- `op.drop_table(name)` - Drop table
- `op.add_column(table, column)` - Add column
- `op.drop_column(table, column)` - Drop column
- `op.alter_column(table, column, **kwargs)` - Alter column
- `op.create_index(name, table, columns)` - Create index
- `op.drop_index(name, table)` - Drop index
- `op.execute(sql)` - Execute raw SQL

## Limitations

This is an emulator for development and testing purposes:
- In-memory storage only (data is lost when process ends)
- Simplified implementations of migration operations
- Does not connect to actual databases
- Auto-generation feature is simplified
- Some advanced features may not be fully implemented

## Compatibility

Emulates core features of:
- Alembic 1.x API
- Common migration patterns
- Standard workflow operations

## License

Part of the Emu-Soft project. See main repository LICENSE.
