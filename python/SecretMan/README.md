# Vault Emulator - Secrets Management

A lightweight emulation of **HashiCorp Vault**, the industry-standard secrets management and data protection tool.

## Features

This emulator implements core Vault functionality:

### Secrets Storage (KV Engine)
- **Key-Value Storage**: Store and retrieve secrets
- **Versioning**: Track secret versions (KV v2)
- **Soft Delete**: Mark secrets as deleted without destroying
- **Secret Metadata**: Track creation time and versions

### Encryption as a Service (Transit Engine)
- **Encryption Keys**: Create and manage encryption keys
- **Encrypt/Decrypt**: Encrypt and decrypt data without exposing keys
- **Key Rotation**: Support for key versioning

### Authentication & Authorization
- **Token-Based Auth**: Issue and manage tokens
- **Token Lifecycle**: Create, renew, revoke tokens
- **Token Expiry**: Automatic token expiration
- **Policy-Based Access**: Fine-grained access control

### Security Features
- **Seal/Unseal**: Vault sealing for security
- **Shamir Secret Sharing**: Initialize with split keys
- **Audit Logging**: Track all operations
- **Policy Enforcement**: Path-based permissions

## What It Emulates

This tool emulates core functionality of [HashiCorp Vault](https://www.vaultproject.io/), a tool for secrets management, encryption, and privileged access.

### Core Components Implemented

1. **Initialization and Unsealing**
   - Shamir secret sharing (simplified)
   - Unseal threshold mechanism
   - Root token generation

2. **KV Secrets Engine (v2)**
   - Write/read/delete secrets
   - Secret versioning
   - Metadata tracking

3. **Transit Secrets Engine**
   - Encryption key management
   - Encrypt/decrypt operations
   - Versioned ciphertext

4. **Token Management**
   - Token creation with policies
   - Token renewal and revocation
   - TTL-based expiration

5. **Policy Management**
   - Policy CRUD operations
   - Path-based capabilities
   - Permission checking

6. **Audit System**
   - Operation logging
   - Success/failure tracking

## Usage

### Initialize and Unseal Vault

```python
from vault_emulator import VaultEmulator

# Create Vault instance
vault = VaultEmulator()

# Initialize (generates unseal keys and root token)
init_result = vault.initialize(secret_shares=5, secret_threshold=3)

print(f"Root token: {init_result['root_token']}")
print(f"Unseal keys: {init_result['keys']}")

# Unseal Vault (need threshold number of keys)
for key in init_result['keys'][:3]:
    vault.unseal(key)

# Check status
status = vault.status()
print(f"Sealed: {status['sealed']}")
```

### Store and Retrieve Secrets

```python
# Use root token from initialization
root_token = init_result['root_token']

# Write a secret
vault.write_secret(
    root_token,
    "secret/myapp/database",
    {
        "host": "db.example.com",
        "username": "dbuser",
        "password": "secretpass123"
    }
)

# Read the secret
result = vault.read_secret(root_token, "secret/myapp/database")
db_config = result['data']['data']

print(f"Database host: {db_config['host']}")
print(f"Username: {db_config['username']}")
```

### Secret Versioning

```python
# Write version 1
vault.write_secret(root_token, "secret/config", {"api_key": "key_v1"})

# Write version 2
vault.write_secret(root_token, "secret/config", {"api_key": "key_v2"})

# Read latest version (v2)
result = vault.read_secret(root_token, "secret/config")
print(f"Latest: {result['data']['data']['api_key']}")

# Read specific version (v1)
result = vault.read_secret(root_token, "secret/config", version=1)
print(f"Version 1: {result['data']['data']['api_key']}")
```

### Encryption as a Service

```python
import base64

# Create encryption key
vault.create_encryption_key(root_token, "myapp-key")

# Encrypt sensitive data
plaintext = "Credit card: 4111-1111-1111-1111"
encrypted = vault.encrypt(root_token, "myapp-key", plaintext)
ciphertext = encrypted['data']['ciphertext']

print(f"Encrypted: {ciphertext}")

# Decrypt when needed
decrypted = vault.decrypt(root_token, "myapp-key", ciphertext)
original = base64.b64decode(decrypted['data']['plaintext']).decode('utf-8')

print(f"Decrypted: {original}")
```

### Token Management

```python
# Create a token with limited permissions
token_result = vault.create_token(
    root_token,
    policies=["read-only"],
    ttl=3600,  # 1 hour
    renewable=True
)

app_token = token_result['auth']['client_token']

# Use the token
vault.read_secret(app_token, "secret/myapp/config")

# Renew the token before it expires
vault.renew_token(app_token, increment=7200)  # Extend by 2 hours

# Revoke when done
vault.revoke_token(root_token, app_token)
```

### Policy-Based Access Control

```python
# Define a policy
policy_rules = [
    {
        "path": "secret/myapp/*",
        "capabilities": ["read", "list"]
    },
    {
        "path": "secret/shared/*",
        "capabilities": ["read", "create", "update"]
    }
]

# Write the policy
vault.write_policy(root_token, "myapp-policy", policy_rules)

# Create token with this policy
result = vault.create_token(root_token, policies=["myapp-policy"])
limited_token = result['auth']['client_token']

# This token can now only access paths allowed by the policy
vault.read_secret(limited_token, "secret/myapp/config")  # OK
# vault.write_secret(limited_token, "secret/other/data", {})  # Permission denied
```

### List Secrets

```python
# Write some secrets
vault.write_secret(root_token, "secret/app/db", {"host": "localhost"})
vault.write_secret(root_token, "secret/app/api", {"key": "123"})
vault.write_secret(root_token, "secret/app/cache", {"url": "redis:6379"})

# List all secrets under secret/app/
result = vault.list_secrets(root_token, "secret/app/")
print(f"Secrets: {result['data']['keys']}")
```

### Seal Vault

```python
# Seal the Vault (for maintenance or security)
vault.seal()

# Now all operations are blocked
try:
    vault.read_secret(root_token, "secret/myapp/config")
except Exception as e:
    print(f"Error: {e}")  # "Vault is sealed"

# Unseal again
for key in init_result['keys'][:3]:
    vault.unseal(key)
```

### Audit Logging

```python
# Perform various operations
vault.write_secret(root_token, "secret/audit-test", {"key": "value"})
vault.read_secret(root_token, "secret/audit-test")

# Get audit log (root only)
audit_entries = vault.get_audit_log(root_token, limit=50)

for entry in audit_entries:
    print(f"{entry.timestamp} - {entry.operation} {entry.path} - Success: {entry.success}")
```

## API Reference

### Main Class

#### `VaultEmulator()`
Main Vault emulator class.

**Methods:**

**Initialization & Sealing:**
- `initialize(secret_shares=5, secret_threshold=3)` - Initialize Vault
- `unseal(key)` - Unseal with key
- `seal()` - Seal Vault
- `status()` - Get Vault status

**KV Secrets Engine:**
- `write_secret(token, path, data)` - Write secret
- `read_secret(token, path, version=None)` - Read secret
- `delete_secret(token, path)` - Delete secret
- `list_secrets(token, path)` - List secrets

**Transit Engine:**
- `create_encryption_key(token, name)` - Create encryption key
- `encrypt(token, key_name, plaintext)` - Encrypt data
- `decrypt(token, key_name, ciphertext)` - Decrypt data

**Token Management:**
- `create_token(token, policies, ttl, renewable)` - Create token
- `renew_token(token, increment)` - Renew token
- `revoke_token(token, revoke_token_id)` - Revoke token

**Policy Management:**
- `write_policy(token, name, rules)` - Write policy
- `read_policy(token, name)` - Read policy
- `list_policies(token)` - List all policies

**Audit:**
- `get_audit_log(token, limit)` - Get audit log

### Data Classes

#### `Token`
**Attributes:**
- `id` (str) - Token ID
- `policies` (list) - Assigned policies
- `ttl` (int) - Time to live in seconds
- `created_at` (float) - Creation timestamp
- `renewable` (bool) - Can be renewed
- `metadata` (dict) - Additional metadata

#### `Policy`
**Attributes:**
- `name` (str) - Policy name
- `rules` (list) - Policy rules

#### `Secret`
**Attributes:**
- `path` (str) - Secret path
- `versions` (dict) - Version history
- `current_version` (int) - Latest version
- `metadata` (dict) - Secret metadata

## Use Cases

### Database Credentials
```python
# Store database credentials securely
vault.write_secret(root_token, "secret/prod/db", {
    "host": "prod-db.example.com",
    "port": 5432,
    "username": "prod_user",
    "password": "secure_password_here"
})

# Application retrieves credentials at runtime
db_creds = vault.read_secret(app_token, "secret/prod/db")
```

### API Key Management
```python
# Store API keys
vault.write_secret(root_token, "secret/api-keys/stripe", {
    "public_key": "pk_live_...",
    "secret_key": "sk_live_..."
})

# Rotate API key (creates new version)
vault.write_secret(root_token, "secret/api-keys/stripe", {
    "public_key": "pk_live_new...",
    "secret_key": "sk_live_new..."
})
```

### Data Encryption
```python
# Encrypt PII before storing in database
vault.create_encryption_key(root_token, "customer-data")

# Encrypt customer SSN
encrypted_ssn = vault.encrypt(root_token, "customer-data", "123-45-6789")
# Store encrypted_ssn in database

# Decrypt when needed for compliance
decrypted = vault.decrypt(root_token, "customer-data", encrypted_ssn['data']['ciphertext'])
```

### Multi-Tenant Secrets
```python
# Create policies for each tenant
vault.write_policy(root_token, "tenant-a", [
    {"path": "secret/tenant-a/*", "capabilities": ["read", "create", "update"]}
])

vault.write_policy(root_token, "tenant-b", [
    {"path": "secret/tenant-b/*", "capabilities": ["read", "create", "update"]}
])

# Each tenant gets their own token
token_a = vault.create_token(root_token, policies=["tenant-a"])
token_b = vault.create_token(root_token, policies=["tenant-b"])
```

## Testing

Run the test suite:

```bash
python test_vault_emulator.py
```

Tests cover:
- Initialization and unsealing
- Secret CRUD operations
- Secret versioning
- Encryption/decryption
- Token lifecycle
- Policy enforcement
- Access control
- Audit logging

## Limitations

This is an educational emulation with some limitations:

1. **Simplified Encryption**: Uses basic XOR (not production-grade)
2. **No Persistence**: Data is in-memory only
3. **Basic Shamir**: Simplified secret sharing implementation
4. **No Network**: No HTTP API (direct function calls only)
5. **Limited Auth Methods**: Token-based only (no LDAP, AWS IAM, etc.)
6. **No High Availability**: Single instance only
7. **No Secret Backends**: Limited to KV and Transit
8. **Simplified Policies**: Basic path matching only
9. **No Auto-Unseal**: Manual unsealing only
10. **No Replication**: No enterprise features

## Real-World Vault

To use real HashiCorp Vault, see the [official documentation](https://www.vaultproject.io/docs).

### Real Vault CLI Examples

```bash
# Initialize
vault operator init

# Unseal
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>

# Login
vault login <token>

# Write secret
vault kv put secret/myapp password=secret123

# Read secret
vault kv get secret/myapp

# Encrypt data
vault write transit/encrypt/mykey plaintext=$(echo -n "data" | base64)

# Decrypt data
vault write transit/decrypt/mykey ciphertext="vault:v1:..."
```

## Security Best Practices

1. **Never commit tokens or keys** to version control
2. **Use short TTLs** for tokens
3. **Rotate secrets** regularly
4. **Implement least privilege** with policies
5. **Monitor audit logs** for suspicious activity
6. **Seal Vault** when not in use
7. **Protect unseal keys** (never store all together)
8. **Use encrypted storage** for backups

## Complexity

**Implementation Complexity**: Medium-High

This emulator involves:
- Secret storage and versioning
- Encryption/decryption algorithms
- Token lifecycle management
- Policy-based access control
- Audit logging
- Thread-safe operations
- Seal/unseal mechanism

## Comparison with Real Vault

### Similarities
- Token-based authentication
- Policy-based authorization
- KV secrets engine with versioning
- Transit engine for encryption
- Seal/unseal mechanism
- Audit logging

### Differences
- Real Vault has production-grade encryption
- Real Vault persists to storage backends
- Real Vault has HTTP API
- Real Vault supports many auth methods
- Real Vault has dozens of secret engines
- Real Vault has enterprise HA features
- Real Vault has automatic unsealing options

## Dependencies

- Python 3.6+
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
