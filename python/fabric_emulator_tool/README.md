# Fabric Emulator - SSH Deployment Automation Tool

This module emulates the **Fabric** library, which is a high-level Python library designed to execute shell commands remotely over SSH, simplifying deployment and system administration tasks.

## What is Fabric?

Fabric is a Python library and command-line tool for streamlining the use of SSH for application deployment or systems administration tasks. It provides:
- High-level Pythonic API for SSH operations
- Simple command execution on remote hosts
- File upload/download capabilities
- Task definition and execution
- Group operations on multiple hosts
- Configuration management

## Features

This emulator implements core Fabric functionality:

### Connection Management
- SSH connection to remote hosts
- Context manager support
- Multiple connection handling
- Connection pooling

### Remote Command Execution
- Run commands on remote hosts
- Sudo command execution
- Local command execution
- Command result handling

### File Transfer
- Upload files (put)
- Download files (get)
- Preserve file permissions
- Transfer tracking

### Group Operations
- Execute on multiple hosts
- Serial execution
- Threading support
- Result aggregation

### Task Management
- Task decorator
- Task organization
- Reusable deployment scripts

## Usage Examples

### Basic Connection and Command Execution

```python
from fabric_emulator import Connection

# Create connection
conn = Connection('web1.example.com', user='deployer')

# Run a command
result = conn.run('hostname')
print(result.stdout)

# Run with sudo
result = conn.sudo('systemctl restart nginx')

# Run local command
result = conn.local('ls -la')
```

### Using Context Manager

```python
from fabric_emulator import Connection

# Automatic connection management
with Connection('web1.example.com', user='admin') as conn:
    result = conn.run('uptime')
    print(f"Uptime: {result.stdout}")
    
    conn.sudo('apt-get update')
    conn.sudo('apt-get upgrade -y')

# Connection automatically closed
```

### File Transfer

```python
from fabric_emulator import Connection

conn = Connection('deploy.example.com')

# Upload a file
transfer = conn.put('local_app.tar.gz', '/tmp/app.tar.gz')
print(f"Uploaded {transfer.bytes_transferred} bytes")

# Download a file
transfer = conn.get('/var/log/app.log', 'local_app.log')
print(f"Downloaded {transfer.bytes_transferred} bytes")

# Upload with default remote path
conn.put('config.yml')  # Uploads to config.yml on remote
```

### Command Results

```python
from fabric_emulator import Connection

conn = Connection('server.com')

# Execute command
result = conn.run('ls /var/www')

# Check result
if result.ok:
    print(f"Success: {result.stdout}")
else:
    print(f"Failed: {result.stderr}")
    print(f"Exit code: {result.exited}")

# Result is truthy if successful
if result:
    print("Command succeeded!")

# Convert to string gets stdout
output = str(result)
```

### Group Operations

```python
from fabric_emulator import Group

# Create group of servers
servers = Group(
    'web1.example.com',
    'web2.example.com',
    'web3.example.com',
    user='deployer'
)

# Run command on all servers
results = servers.run('uptime')

for host, result in results.items():
    print(f"{host}: {result.stdout}")

# Sudo on all servers
results = servers.sudo('systemctl restart nginx')

# Upload to all servers
transfers = servers.put('config.json', '/etc/app/config.json')

# Close all connections
servers.close()
```

### Sudo with Specific User

```python
from fabric_emulator import Connection

conn = Connection('server.com')

# Run as root (default)
conn.sudo('systemctl restart nginx')

# Run as specific user
conn.sudo('touch /home/appuser/file.txt', user='appuser')

# Run with environment variables
conn.sudo('npm install', user='nodejs', env={'NODE_ENV': 'production'})
```

### Task Definition

```python
from fabric_emulator import Connection, task

@task
def deploy(conn):
    """Deploy application to server."""
    # Upload application
    conn.put('dist/app.tar.gz', '/tmp/app.tar.gz')
    
    # Extract
    conn.run('tar -xzf /tmp/app.tar.gz -C /opt/app')
    
    # Install dependencies
    conn.sudo('pip install -r /opt/app/requirements.txt')
    
    # Restart service
    conn.sudo('systemctl restart myapp')
    
    print("Deployment complete!")

# Use the task
with Connection('deploy.example.com') as conn:
    deploy(conn)
```

### Module-Level Functions

```python
from fabric_emulator import run, sudo, put, get

# Quick command execution
result = run('hostname', 'server.com', user='admin')

# Quick sudo
result = sudo('apt-get update', 'server.com', user='admin')

# Quick file transfer
put('local.txt', '/remote/file.txt', 'server.com')
get('/remote/log.txt', 'local_log.txt', 'server.com')
```

### Complete Deployment Example

```python
from fabric_emulator import Connection, Group

def deploy_application():
    """Complete deployment workflow."""
    
    # Build application locally
    with Connection('localhost') as local:
        local.local('npm run build')
        local.local('tar -czf dist.tar.gz dist/')
    
    # Deploy to servers
    servers = Group(
        'web1.example.com',
        'web2.example.com',
        user='deployer'
    )
    
    # Upload application
    print("Uploading application...")
    servers.put('dist.tar.gz', '/tmp/dist.tar.gz')
    
    # Stop services
    print("Stopping services...")
    servers.sudo('systemctl stop myapp')
    
    # Extract new version
    print("Extracting application...")
    servers.run('rm -rf /opt/myapp')
    servers.run('tar -xzf /tmp/dist.tar.gz -C /opt/')
    servers.run('mv /opt/dist /opt/myapp')
    
    # Install dependencies
    print("Installing dependencies...")
    servers.run('cd /opt/myapp && npm install --production')
    
    # Start services
    print("Starting services...")
    servers.sudo('systemctl start myapp')
    
    # Verify
    print("Verifying deployment...")
    results = servers.run('curl -f http://localhost:3000/health')
    
    for host, result in results.items():
        if result.ok:
            print(f"✓ {host} is healthy")
        else:
            print(f"✗ {host} failed health check")
    
    print("Deployment complete!")

# Execute deployment
deploy_application()
```

### Configuration Management

```python
from fabric_emulator import Connection, Config

# Create configuration
config = Config(overrides={
    'run': {'warn': True},
    'sudo': {'user': 'root'},
    'timeouts': {'connect': 10}
})

# Use configuration
conn = Connection('server.com', config=config)

# Configuration is inherited
result = conn.run('might-fail-command')
# Won't raise exception because warn=True
```

### Database Backup Example

```python
from fabric_emulator import Connection
from datetime import datetime

def backup_database(db_host, db_name):
    """Backup database from remote server."""
    conn = Connection(db_host, user='backup')
    
    # Generate backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    remote_file = f'/backups/{db_name}_{timestamp}.sql'
    local_file = f'backups/{db_name}_{timestamp}.sql'
    
    # Create backup
    print(f"Creating backup of {db_name}...")
    conn.run(f'pg_dump {db_name} > {remote_file}')
    
    # Compress backup
    print("Compressing backup...")
    conn.run(f'gzip {remote_file}')
    
    # Download backup
    print("Downloading backup...")
    conn.get(f'{remote_file}.gz', f'{local_file}.gz')
    
    # Clean up old backups (keep last 7 days)
    print("Cleaning old backups...")
    conn.run('find /backups -name "*.sql.gz" -mtime +7 -delete')
    
    print(f"Backup complete: {local_file}.gz")

# Execute backup
backup_database('db.example.com', 'production_db')
```

### Multi-Environment Deployment

```python
from fabric_emulator import Group

def deploy_to_environment(env):
    """Deploy to specific environment."""
    
    if env == 'staging':
        servers = Group(
            'staging1.example.com',
            'staging2.example.com',
            user='deployer'
        )
    elif env == 'production':
        servers = Group(
            'prod1.example.com',
            'prod2.example.com',
            'prod3.example.com',
            user='deployer'
        )
    else:
        raise ValueError(f"Unknown environment: {env}")
    
    # Deploy application
    print(f"Deploying to {env}...")
    
    servers.put(f'config.{env}.yml', '/etc/app/config.yml')
    servers.put('app.tar.gz', '/tmp/app.tar.gz')
    
    servers.run('tar -xzf /tmp/app.tar.gz -C /opt/app')
    servers.sudo('systemctl restart myapp')
    
    print(f"Deployed to {env}!")

# Deploy to staging
deploy_to_environment('staging')

# Deploy to production
deploy_to_environment('production')
```

## Testing

Run the comprehensive test suite:

```bash
python test_fabric_emulator.py
```

Tests cover:
- Connection management
- Command execution
- File transfers
- Group operations
- Task decoration
- Module-level functions
- Integration scenarios

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for Fabric in development and testing:

```python
# Instead of:
# from fabric import Connection, Config, Group

# Use:
from fabric_emulator import Connection, Config, Group
```

## Use Cases

Perfect for:
- **Testing**: Test deployment scripts without SSH access
- **Development**: Develop automation scripts locally
- **CI/CD**: Run deployment tests in pipelines
- **Learning**: Learn Fabric patterns and best practices
- **Prototyping**: Quickly prototype deployment workflows
- **Offline Development**: Work on deployment scripts without servers

## API Reference

### Connection
- `Connection(host, user, port, config)` - Create SSH connection
- `conn.run(command, **kwargs)` - Execute command
- `conn.sudo(command, user, **kwargs)` - Execute with sudo
- `conn.local(command, **kwargs)` - Execute locally
- `conn.put(local, remote)` - Upload file
- `conn.get(remote, local)` - Download file
- `conn.open()` - Open connection
- `conn.close()` - Close connection

### Group
- `Group(*hosts, user, port, config)` - Create host group
- `group.run(command, **kwargs)` - Run on all hosts
- `group.sudo(command, **kwargs)` - Sudo on all hosts
- `group.put(local, remote, **kwargs)` - Upload to all
- `group.close()` - Close all connections

### Result
- `result.ok` - Command succeeded
- `result.failed` - Command failed
- `result.stdout` - Standard output
- `result.stderr` - Standard error
- `result.exited` - Exit code
- `result.command` - Executed command

### Transfer
- `transfer.success` - Transfer succeeded
- `transfer.local` - Local file path
- `transfer.remote` - Remote file path
- `transfer.operation` - 'put' or 'get'
- `transfer.bytes_transferred` - Bytes transferred

## Limitations

This is an emulator for development and testing purposes:
- No actual SSH connections are made
- Commands are emulated (not actually executed)
- File transfers are simulated
- Some advanced features may not be fully implemented

## Compatibility

Emulates core features of:
- Fabric 2.x API
- Common deployment patterns
- Standard SSH operations

## License

Part of the Emu-Soft project. See main repository LICENSE.
