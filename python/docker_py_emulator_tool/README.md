# docker-py Emulator - Docker API Client for Python

This module emulates the **docker-py** (also known as `docker`) library, which is the official Docker SDK for Python. It allows Python developers to interact with Docker containers, images, networks, volumes, and other Docker resources programmatically.

## What is docker-py?

docker-py is the official Python library for the Docker Engine API. It provides:
- High-level API for Docker containers, images, networks, and volumes
- Low-level API client for advanced use cases
- Pythonic interface to all Docker operations
- Support for Docker Swarm and Docker Compose
- Stream-based operations for logs and events

## Features

This emulator implements core functionality for Docker resource management:

### Client Management
- Docker client creation and configuration
- Connection to Docker daemon
- Version and system information retrieval
- Event streaming
- Health checks

### Container Operations
- Create, start, stop, restart, and remove containers
- Run containers in detached or attached mode
- Execute commands in running containers
- Get container logs and statistics
- List and filter containers
- Container lifecycle management
- Port mapping and environment variables
- Labels and metadata

### Image Management
- Pull images from registries
- Build images from Dockerfiles
- Tag and untag images
- List and filter images
- Remove images
- Image metadata and attributes
- Prune unused images

### Network Operations
- Create and remove networks
- Connect and disconnect containers from networks
- List and filter networks
- Network drivers (bridge, host, overlay)
- Network metadata and configuration
- Prune unused networks

### Volume Management
- Create named and anonymous volumes
- List and filter volumes
- Remove volumes
- Volume drivers and options
- Volume metadata
- Prune unused volumes

## Usage Examples

### Creating a Docker Client

```python
from docker_emulator import DockerClient, from_env

# Create client from environment variables
client = from_env()

# Or create with explicit parameters
client = DockerClient(base_url='unix://var/run/docker.sock')

# Test connection
if client.ping():
    print("Connected to Docker daemon")
```

### Working with Containers

#### Running Containers

```python
from docker_emulator import from_env

client = from_env()

# Run a container in detached mode
container = client.containers.run(
    'nginx:latest',
    name='my_web_server',
    ports={'80/tcp': 8080},
    environment={'ENV_VAR': 'value'},
    labels={'app': 'web', 'env': 'production'},
    detach=True
)

print(f"Container {container.name} is {container.status}")
```

#### Container Lifecycle Management

```python
# Create a container without starting it
container = client.containers.create(
    'ubuntu:latest',
    name='my_container',
    command=['sleep', '3600']
)

# Start the container
container.start()

# Execute a command
exit_code, output = container.exec_run('ls -la /app')
print(output.decode())

# Get logs
logs = container.logs()
print(logs)

# Get statistics
stats = container.stats()
print(f"CPU usage: {stats['cpu_stats']}")
print(f"Memory usage: {stats['memory_stats']}")

# Stop the container
container.stop(timeout=10)

# Restart the container
container.restart()

# Remove the container
container.remove(force=True)
```

#### Listing Containers

```python
# List running containers
running = client.containers.list()
for container in running:
    print(f"{container.name}: {container.status}")

# List all containers (including stopped)
all_containers = client.containers.list(all=True)

# Filter containers by status
stopped = client.containers.list(all=True, filters={'status': 'exited'})
```

#### Pruning Stopped Containers

```python
# Remove all stopped containers
result = client.containers.prune()
print(f"Removed {len(result['ContainersDeleted'])} containers")
```

### Working with Images

#### Pulling Images

```python
# Pull an image
image = client.images.pull('python', tag='3.9')
print(f"Pulled: {image.tags}")

# Pull latest version
image = client.images.pull('alpine')
```

#### Building Images

```python
# Build an image from a Dockerfile
image, logs = client.images.build(
    path='.',
    tag='myapp:latest',
    dockerfile='Dockerfile'
)

# Print build logs
for log in logs:
    if 'stream' in log:
        print(log['stream'], end='')
```

#### Tagging Images

```python
# Pull and tag an image
image = client.images.pull('alpine:latest')
image.tag('myregistry/alpine', tag='v1.0')

# Now the image has multiple tags
print(image.tags)  # ['alpine:latest', 'myregistry/alpine:v1.0']
```

#### Listing and Removing Images

```python
# List all images
images = client.images.list()
for image in images:
    print(f"Tags: {image.tags}, Size: {image.size}")

# Remove an image
client.images.remove('myapp:latest')

# Prune unused images (without tags)
result = client.images.prune()
print(f"Removed {len(result['ImagesDeleted'])} images")
```

### Working with Networks

#### Creating Networks

```python
# Create a custom bridge network
network = client.networks.create(
    'my_network',
    driver='bridge',
    options={'com.docker.network.bridge.name': 'my_bridge'},
    labels={'env': 'development'}
)
```

#### Connecting Containers to Networks

```python
# Create network and container
network = client.networks.create('app_network')
container = client.containers.run('nginx', detach=True)

# Connect container to network
network.connect(container)

# Disconnect container from network
network.disconnect(container)
```

#### Listing Networks

```python
# List all networks
networks = client.networks.list()
for network in networks:
    print(f"Name: {network.name}, Driver: {network.driver}")

# Filter networks by driver
bridge_networks = client.networks.list(filters={'driver': 'bridge'})
```

#### Removing Networks

```python
# Get and remove a network
network = client.networks.get('my_network')
network.remove()

# Prune unused networks
result = client.networks.prune()
print(f"Removed {len(result['NetworksDeleted'])} networks")
```

### Working with Volumes

#### Creating Volumes

```python
# Create a named volume
volume = client.volumes.create(
    'my_data',
    driver='local',
    labels={'backup': 'daily'}
)

# Create an anonymous volume
volume = client.volumes.create()
print(f"Created volume: {volume.name}")
```

#### Listing and Managing Volumes

```python
# List all volumes
volumes = client.volumes.list()
for volume in volumes:
    print(f"Name: {volume.name}, Driver: {volume.driver}")

# Get a specific volume
volume = client.volumes.get('my_data')

# Remove a volume
volume.remove()

# Prune all unused volumes
result = client.volumes.prune()
print(f"Removed {len(result['VolumesDeleted'])} volumes")
```

### Getting System Information

```python
# Get Docker version
version = client.version()
print(f"Docker version: {version['Version']}")
print(f"API version: {version['ApiVersion']}")

# Get system information
info = client.info()
print(f"Containers: {info['Containers']}")
print(f"Images: {info['Images']}")
print(f"CPUs: {info['NCPU']}")
print(f"Total Memory: {info['MemTotal']}")
```

### Container Attributes

```python
# Get detailed container information
container = client.containers.get('my_container')
attrs = container.attrs()

print(f"ID: {attrs['Id']}")
print(f"Name: {attrs['Name']}")
print(f"Status: {attrs['State']['Status']}")
print(f"Image: {attrs['Config']['Image']}")
print(f"Ports: {attrs['NetworkSettings']['Ports']}")
```

## Real-World Use Cases

### Container Orchestration Script

```python
from docker_emulator import from_env

client = from_env()

# Deploy a web application stack
def deploy_stack():
    # Create network
    network = client.networks.create('app_network')
    
    # Create volume for data persistence
    db_volume = client.volumes.create('postgres_data')
    
    # Run database container
    db = client.containers.run(
        'postgres:13',
        name='db',
        environment={
            'POSTGRES_DB': 'myapp',
            'POSTGRES_USER': 'admin',
            'POSTGRES_PASSWORD': 'secret'
        },
        volumes={db_volume.name: '/var/lib/postgresql/data'},
        network='app_network',
        detach=True
    )
    
    # Run web application container
    web = client.containers.run(
        'myapp:latest',
        name='web',
        ports={'8000/tcp': 8000},
        environment={'DATABASE_URL': 'postgresql://admin:secret@db:5432/myapp'},
        network='app_network',
        detach=True
    )
    
    print("Stack deployed successfully!")
    return {'database': db, 'web': web}

# Clean up resources
def cleanup_stack():
    # Stop and remove containers
    for name in ['web', 'db']:
        try:
            container = client.containers.get(name)
            container.stop()
            container.remove()
        except:
            pass
    
    # Remove network
    try:
        network = client.networks.get('app_network')
        network.remove()
    except:
        pass
    
    print("Stack cleaned up!")
```

### Automated Testing with Docker

```python
from docker_emulator import from_env
import time

client = from_env()

def run_integration_tests():
    # Start test database
    db = client.containers.run(
        'postgres:13',
        environment={'POSTGRES_PASSWORD': 'test'},
        ports={'5432/tcp': 5432},
        detach=True
    )
    
    # Wait for database to be ready
    time.sleep(5)
    
    # Run tests in a container
    test_container = client.containers.run(
        'myapp-tests:latest',
        environment={'DB_HOST': 'localhost', 'DB_PORT': '5432'},
        network_mode='host',
        detach=False
    )
    
    # Clean up
    db.stop()
    db.remove()
    
    return test_container
```

## API Compatibility

This emulator provides compatibility with docker-py's high-level API:

- ✅ `DockerClient` - Main client class
- ✅ `from_env()` - Create client from environment
- ✅ Container operations (create, start, stop, remove, exec)
- ✅ Image operations (pull, build, tag, remove)
- ✅ Network operations (create, connect, disconnect, remove)
- ✅ Volume operations (create, list, remove)
- ✅ System operations (version, info, ping)
- ✅ Resource attributes and metadata
- ✅ Filtering and listing operations
- ✅ Prune operations for cleanup

## Emulated Concepts

### Container Lifecycle
Simulates the full lifecycle of Docker containers from creation through running to removal, including state transitions and metadata management.

### Image Registry Operations
Emulates pulling from and pushing to Docker registries, including tag management and image building.

### Network Isolation
Simulates Docker's network isolation and container connectivity features.

### Volume Persistence
Emulates Docker's volume system for data persistence across container lifecycles.

## Implementation Notes

- **In-Memory Storage**: All resources (containers, images, networks, volumes) are stored in memory
- **ID Generation**: Uses random hexadecimal strings to simulate Docker IDs
- **Timestamps**: Uses UTC timestamps for created dates
- **Default Networks**: Automatically creates default networks (bridge, host, none)
- **State Management**: Tracks container states (created, running, exited, removed)
- **Metadata**: Supports labels, environment variables, and custom configuration

## Testing

Run the test suite:

```bash
python test_docker_emulator.py
```

The test suite covers:
- Client creation and system information
- Container lifecycle operations
- Image management
- Network operations
- Volume management
- Resource attributes and metadata
- Filtering and pruning operations

## Emulates

This module emulates the **docker-py** library (PyPI package: `docker`):
- Repository: https://github.com/docker/docker-py
- Documentation: https://docker-py.readthedocs.io/
- License: Apache 2.0

## Educational Purpose

This is an educational reimplementation created for the CIV-ARCOS project. It demonstrates:
- Client-server API design patterns
- Resource lifecycle management
- RESTful API abstractions
- Container orchestration concepts
- Docker API architecture

For production use, please use the official docker-py library.
