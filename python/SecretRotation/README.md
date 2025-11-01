# SecretRotation - Secret Rotation Automation

A comprehensive tool for automating secret rotation in local development environments, including API keys, passwords, tokens, and other sensitive credentials.

## Features

- **Multiple Secret Types**: API keys, passwords, tokens, database passwords, encryption keys, signing keys
- **Automated Generation**: Generate secure secrets based on type
- **Rotation Strategies**: Random, derived, or custom rotation strategies
- **Rotation Scheduling**: Schedule automatic rotation based on time intervals
- **Rotation History**: Track all secret rotations with detailed history
- **Callbacks**: Register callbacks to execute when secrets are rotated
- **Import/Export**: Save and load secrets with metadata
- **Validation**: Validate secret strength and security
- **Environment Files**: Generate .env files from managed secrets
- **Statistics**: Track secret management statistics

## What It Does

SecretRotation helps developers manage secrets in local development by:

1. **Generating Secrets**: Create strong, cryptographically secure secrets
2. **Rotating Secrets**: Automatically or manually rotate secrets
3. **Tracking Usage**: Monitor secret rotations and usage patterns
4. **Enforcing Policies**: Validate secret strength and rotation intervals
5. **Automating Updates**: Execute callbacks to update dependent systems

## Usage

### Basic Setup

```python
from SecretRotation import SecretRotation, SecretType

# Initialize manager
manager = SecretRotation(storage_path='.secrets')

# Add secrets with auto-generation
api_key = manager.add_secret(
    'my_api_key',
    secret_type=SecretType.API_KEY,
    rotation_interval_days=30,
    tags=['production', 'api']
)
print(f"Generated API key: {api_key}")

# Add secret with specific value
manager.add_secret(
    'database_password',
    value='MyS3cur3P@ssw0rd',
    secret_type=SecretType.DATABASE_PASSWORD,
    rotation_interval_days=90
)
```

### Secret Generation

```python
# Generate API key
api_key = manager.generate_api_key(length=32)
print(f"API Key: {api_key}")

# Generate secure password
password = manager.generate_password(length=16, use_special=True)
print(f"Password: {password}")

# Generate token
token = manager.generate_token(length=32)
print(f"Token: {token}")

# Generate encryption key
encryption_key = manager.generate_encryption_key(key_size=32)  # AES-256
print(f"Encryption Key: {encryption_key}")

# Generate signing key
signing_key = manager.generate_signing_key(length=64)
print(f"Signing Key: {signing_key}")
```

### Secret Rotation

```python
from SecretRotation import RotationStrategy

# Rotate with random value (default)
new_value = manager.rotate_secret('my_api_key')
print(f"New API key: {new_value}")

# Rotate with specific value
manager.rotate_secret('my_api_key', new_value='custom-key-123')

# Rotate with derived strategy (based on old value)
manager.rotate_secret('my_api_key', strategy=RotationStrategy.DERIVED)

# Rotate all secrets that are due
results = manager.rotate_all_due()
for secret_name, success in results.items():
    print(f"{secret_name}: {'✓' if success else '✗'}")
```

### Rotation Callbacks

```python
# Register callback to update external systems
def update_api_service(name, old_value, new_value):
    print(f"Updating API service with new key: {new_value}")
    # Call API to update key
    # api_client.update_key(new_value)

manager.register_rotation_callback('my_api_key', update_api_service)

# When rotated, callback will be executed automatically
manager.rotate_secret('my_api_key')
```

### Secret Management

```python
# Get secret value
api_key = manager.get_secret('my_api_key')

# Get secret metadata
metadata = manager.get_metadata('my_api_key')
print(f"Created: {metadata.created_at}")
print(f"Rotations: {metadata.rotation_count}")
print(f"Next rotation: {metadata.next_rotation}")

# List all secrets
all_secrets = manager.list_secrets()
print(f"Total secrets: {len(all_secrets)}")

# List by type
api_keys = manager.list_secrets(secret_type=SecretType.API_KEY)
passwords = manager.list_secrets(secret_type=SecretType.PASSWORD)

# Check which secrets need rotation
needs_rotation = manager.check_rotation_needed()
print(f"Secrets needing rotation: {needs_rotation}")

# Delete secret
manager.delete_secret('old_api_key')
```

### Import/Export

```python
# Export secrets with metadata
manager.export_secrets('secrets-backup.json', include_metadata=True)

# Export secrets only (no metadata)
manager.export_secrets('secrets-only.json', include_metadata=False)

# Import secrets
manager.import_secrets('secrets-backup.json')
```

### Environment File Generation

```python
# Generate .env file with all secrets
manager.generate_env_file('.env.local')

# Generate .env file with selected secrets
manager.generate_env_file(
    '.env.production',
    secrets=['DATABASE_URL', 'API_KEY', 'JWT_SECRET']
)
```

### Statistics and History

```python
# Get statistics
stats = manager.get_statistics()
print(f"Total secrets: {stats['total_secrets']}")
print(f"Total rotations: {stats['total_rotations']}")
print(f"Needs rotation: {stats['needs_rotation']}")
print(f"By type: {stats['secrets_by_type']}")

# Get rotation history
all_history = manager.get_rotation_history()
for record in all_history:
    print(f"{record.rotated_at}: {record.secret_name} (rotation #{record.rotation_count})")

# Get history for specific secret
api_key_history = manager.get_rotation_history('my_api_key')
```

### Secret Validation

```python
# Validate secret strength
result = manager.validate_secret_strength('MyP@ssw0rd123', SecretType.PASSWORD)

print(f"Valid: {result['valid']}")
print(f"Score: {result['score']}/100")
if result['issues']:
    print("Issues:")
    for issue in result['issues']:
        print(f"  - {issue}")
```

## Examples

### Complete Secret Management System

```python
from SecretRotation import SecretRotation, SecretType, RotationStrategy

# Initialize
manager = SecretRotation()

# Add various types of secrets
secrets_to_add = [
    ('database_url', 'postgres://localhost/mydb', SecretType.DATABASE_PASSWORD, 90),
    ('api_key', None, SecretType.API_KEY, 30),  # Auto-generate
    ('jwt_secret', None, SecretType.SIGNING_KEY, 60),
    ('encryption_key', None, SecretType.ENCRYPTION_KEY, 180),
]

for name, value, secret_type, rotation_days in secrets_to_add:
    manager.add_secret(
        name,
        value=value,
        secret_type=secret_type,
        rotation_interval_days=rotation_days,
        auto_generate=True
    )
    print(f"Added: {name}")

# Generate .env file
manager.generate_env_file('.env.local')
print("\nGenerated .env.local file")

# Check secret strength
for secret_name in manager.list_secrets():
    value = manager.get_secret(secret_name)
    meta = manager.get_metadata(secret_name)
    validation = manager.validate_secret_strength(value, meta.secret_type)
    
    print(f"\n{secret_name}:")
    print(f"  Score: {validation['score']}/100")
    if validation['issues']:
        print(f"  Issues: {', '.join(validation['issues'])}")

# Export for backup
manager.export_secrets('secrets-backup.json')
print("\nBackup created: secrets-backup.json")
```

### Automated Rotation Service

```python
from SecretRotation import SecretRotation
import time

def rotation_service():
    """Service to automatically rotate secrets"""
    manager = SecretRotation()
    
    # Load existing secrets
    try:
        manager.import_secrets('secrets-backup.json')
    except FileNotFoundError:
        # Initialize with default secrets
        manager.add_secret('api_key', secret_type=SecretType.API_KEY, rotation_interval_days=1)
    
    while True:
        print("\nChecking for secrets needing rotation...")
        
        # Check which secrets need rotation
        needs_rotation = manager.check_rotation_needed()
        
        if needs_rotation:
            print(f"Found {len(needs_rotation)} secret(s) needing rotation")
            
            # Rotate all due secrets
            results = manager.rotate_all_due()
            
            for secret_name, success in results.items():
                if success:
                    print(f"✓ Rotated: {secret_name}")
                else:
                    print(f"✗ Failed to rotate: {secret_name}")
            
            # Save updated secrets
            manager.export_secrets('secrets-backup.json')
            
            # Regenerate .env file
            manager.generate_env_file('.env.local')
        else:
            print("No secrets need rotation")
        
        # Show statistics
        stats = manager.get_statistics()
        print(f"\nStatistics:")
        print(f"  Total secrets: {stats['total_secrets']}")
        print(f"  Total rotations: {stats['total_rotations']}")
        
        # Wait before next check (in production, use cron or scheduler)
        time.sleep(3600)  # Check every hour

# Run service
# rotation_service()
```

### Integration with CI/CD

```python
from SecretRotation import SecretRotation, SecretType

def setup_ci_secrets():
    """Setup secrets for CI/CD environment"""
    manager = SecretRotation()
    
    # Add CI/CD specific secrets
    ci_secrets = {
        'DOCKER_HUB_TOKEN': SecretType.TOKEN,
        'GITHUB_TOKEN': SecretType.TOKEN,
        'NPM_TOKEN': SecretType.TOKEN,
        'DEPLOYMENT_KEY': SecretType.SIGNING_KEY,
    }
    
    for name, secret_type in ci_secrets.items():
        manager.add_secret(
            name,
            secret_type=secret_type,
            rotation_interval_days=30,
            tags=['ci', 'automation']
        )
    
    # Generate secrets file for CI
    manager.generate_env_file('.env.ci')
    
    # Export with metadata
    manager.export_secrets('ci-secrets.json')
    
    print("CI/CD secrets initialized")
    print(f"Created {len(ci_secrets)} secrets")

setup_ci_secrets()
```

### Database Password Rotation

```python
from SecretRotation import SecretRotation, SecretType
import psycopg2  # Example for PostgreSQL

def rotate_database_password():
    """Rotate database password and update database"""
    manager = SecretRotation()
    
    # Add database password if not exists
    if manager.get_secret('db_password') is None:
        manager.add_secret(
            'db_password',
            secret_type=SecretType.DATABASE_PASSWORD,
            rotation_interval_days=90
        )
    
    def update_database_password(name, old_password, new_password):
        """Callback to update database with new password"""
        try:
            # Connect with old password
            conn = psycopg2.connect(
                host="localhost",
                database="mydb",
                user="myuser",
                password=old_password
            )
            
            cursor = conn.cursor()
            
            # Update password in database
            cursor.execute(f"ALTER USER myuser WITH PASSWORD '{new_password}'")
            conn.commit()
            
            cursor.close()
            conn.close()
            
            print("Database password updated successfully")
        except Exception as e:
            print(f"Failed to update database password: {e}")
            raise
    
    # Register callback
    manager.register_rotation_callback('db_password', update_database_password)
    
    # Rotate password
    new_password = manager.rotate_secret('db_password')
    
    # Update .env file
    manager.generate_env_file('.env.local')
    
    return new_password

# Rotate database password
# new_password = rotate_database_password()
```

### Secret Rotation Dashboard

```python
from SecretRotation import SecretRotation
from datetime import datetime

def display_dashboard():
    """Display secret management dashboard"""
    manager = SecretRotation()
    
    # Load secrets
    try:
        manager.import_secrets('secrets-backup.json')
    except FileNotFoundError:
        print("No secrets file found")
        return
    
    print("=" * 70)
    print("SECRET ROTATION DASHBOARD")
    print("=" * 70)
    
    # Statistics
    stats = manager.get_statistics()
    print(f"\nTotal Secrets: {stats['total_secrets']}")
    print(f"Total Rotations: {stats['total_rotations']}")
    print(f"Needs Rotation: {stats['needs_rotation']}")
    
    print("\nSecrets by Type:")
    for secret_type, count in stats['secrets_by_type'].items():
        print(f"  {secret_type}: {count}")
    
    # List all secrets with details
    print("\nSecret Details:")
    print("-" * 70)
    
    for secret_name in manager.list_secrets():
        meta = manager.get_metadata(secret_name)
        value = manager.get_secret(secret_name)
        
        print(f"\n{secret_name}")
        print(f"  Type: {meta.secret_type.value}")
        print(f"  Created: {meta.created_at}")
        print(f"  Rotations: {meta.rotation_count}")
        
        if meta.next_rotation:
            next_date = datetime.fromisoformat(meta.next_rotation)
            days_until = (next_date - datetime.utcnow()).days
            print(f"  Next Rotation: in {days_until} days")
        
        if meta.tags:
            print(f"  Tags: {', '.join(meta.tags)}")
        
        # Validate strength
        validation = manager.validate_secret_strength(value, meta.secret_type)
        print(f"  Strength Score: {validation['score']}/100")
    
    # Recent history
    print("\n" + "=" * 70)
    print("RECENT ROTATION HISTORY (Last 10)")
    print("=" * 70)
    
    recent_history = manager.get_rotation_history()[-10:]
    for record in reversed(recent_history):
        status = "✓" if record.success else "✗"
        print(f"{status} {record.rotated_at}: {record.secret_name} (#{record.rotation_count})")
    
    print("\n" + "=" * 70)

# Display dashboard
# display_dashboard()
```

## API Reference

### SecretRotation Class

**Methods:**

- `generate_api_key(length=32)` - Generate random API key
- `generate_password(length=16, use_special=True)` - Generate secure password
- `generate_token(length=32)` - Generate random token
- `generate_encryption_key(key_size=32)` - Generate encryption key
- `generate_signing_key(length=64)` - Generate signing key
- `add_secret(name, value, secret_type, rotation_interval_days, tags, auto_generate)` - Add secret
- `rotate_secret(name, new_value, strategy)` - Rotate secret
- `register_rotation_callback(secret_name, callback)` - Register rotation callback
- `get_secret(name)` - Get secret value
- `get_metadata(name)` - Get secret metadata
- `list_secrets(secret_type)` - List secrets
- `check_rotation_needed()` - Check which secrets need rotation
- `rotate_all_due()` - Rotate all due secrets
- `delete_secret(name)` - Delete secret
- `export_secrets(filepath, include_metadata)` - Export secrets
- `import_secrets(filepath)` - Import secrets
- `get_rotation_history(secret_name)` - Get rotation history
- `generate_env_file(filepath, secrets)` - Generate .env file
- `get_statistics()` - Get statistics
- `validate_secret_strength(value, secret_type)` - Validate secret

### SecretType Enum

- `API_KEY` - API keys
- `PASSWORD` - Passwords
- `TOKEN` - Generic tokens
- `DATABASE_PASSWORD` - Database passwords
- `ENCRYPTION_KEY` - Encryption keys
- `SIGNING_KEY` - Signing keys for HMAC/JWT
- `CERTIFICATE` - Certificates
- `GENERIC` - Generic secrets

### RotationStrategy Enum

- `RANDOM` - Generate new random value
- `DERIVED` - Derive from old value using HMAC
- `CUSTOM` - Use provided custom value

## Security Considerations

- **Storage**: Secrets are stored in plaintext in the configured directory. Use appropriate file permissions.
- **Production Use**: This tool is designed for local development. For production, use proper secret management services (AWS Secrets Manager, HashiCorp Vault, etc.)
- **Callbacks**: Ensure rotation callbacks properly handle errors and don't expose secrets
- **Backups**: Encrypted backups recommended for exported secret files
- **Access Control**: Restrict access to the storage directory

## Use Cases

- **Local Development**: Manage secrets for local development environments
- **Testing**: Generate test secrets for automated testing
- **Secret Rotation**: Automate regular secret rotation
- **Multi-Environment**: Maintain separate secrets for different environments
- **Compliance**: Enforce secret rotation policies
- **Migration**: Migrate from hardcoded secrets to managed secrets

## Testing

Run the test suite:

```bash
python test_SecretRotation.py
```

Tests cover:
- Secret generation
- Secret addition and management
- Rotation strategies
- Callbacks
- Import/export
- Validation
- History tracking

## Dependencies

- Python 3.7+
- No external dependencies (uses only standard library)

## License

Part of the Emu-Soft project - see main repository LICENSE.
