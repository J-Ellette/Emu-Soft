# Docker Emulator - Container Platform

A lightweight emulation of **Docker**, the industry-standard containerization platform that enables developers to package applications and their dependencies into portable containers.

## Features

This emulator implements core Docker functionality:

### Container Management
- **Container Lifecycle**: Create, start, stop, restart, pause, unpause, and remove containers
- **Container States**: Track container states (created, running, paused, exited, etc.)
- **Container Inspection**: Get detailed container information and configuration
- **Container Logs**: View container output and logs
- **Exec Commands**: Execute commands inside running containers
- **Resource Stats**: Monitor CPU, memory, network, and disk usage

### Image Management
- **Build Images**: Build images from Dockerfiles
- **Pull/Push Images**: Pull images from registry and push to registry
- **Image Tagging**: Tag and retag images
- **Image Listing**: List all available images
- **Image Removal**: Remove unused images

### Volume Management
- **Create Volumes**: Create named volumes for persistent data
- **Volume Inspection**: Get detailed volume information
- **Volume Listing**: List all volumes
- **Volume Removal**: Remove unused volumes
- **Mount Configuration**: Configure volume and bind mounts for containers

### Network Management
- **Network Creation**: Create custom networks with different drivers
- **Network Drivers**: Support for bridge, host, overlay, macvlan, and none
- **Container Connectivity**: Connect and disconnect containers to/from networks
- **IP Address Management**: Automatic IP address assignment
- **Network Isolation**: Isolate containers in separate networks

### Docker Compose
- **Multi-Container Applications**: Define and run multi-container applications
- **Service Configuration**: Configure services with images, ports, volumes, and environment
- **Compose Up/Down**: Start and stop entire application stacks

### Port Management
- **Port Binding**: Map container ports to host ports
- **Port Protocols**: Support TCP and UDP port mappings
- **Host IP Binding**: Bind to specific host IP addresses

### Resource Management
- **Restart Policies**: Configure automatic container restart (no, on-failure, always, unless-stopped)
- **Labels**: Add metadata to containers, images, volumes, and networks
- **Environment Variables**: Set environment variables for containers
- **Prune Operations**: Clean up unused resources

## What It Emulates

This tool emulates core functionality of [Docker](https://www.docker.com/), the world's leading containerization platform used by millions of developers and thousands of enterprises.

### Core Components Implemented

1. **Docker Engine**
   - Container runtime and lifecycle management
   - Image building and management
   - Resource orchestration

2. **Docker CLI Operations**
   - `docker run` - Create and start containers
   - `docker ps` - List containers
   - `docker stop/start` - Control container lifecycle
   - `docker build` - Build images
   - `docker pull/push` - Registry operations
   - `docker volume` - Volume management
   - `docker network` - Network management
   - `docker exec` - Execute commands in containers
   - `docker logs` - View container logs
   - `docker stats` - View resource usage
   - `docker prune` - Clean up resources

3. **Docker Compose**
   - Multi-container application definitions
   - Service orchestration
   - Volume and network management

4. **Container Networking**
   - Network drivers (bridge, host, overlay)
   - Container connectivity
   - IP address management

5. **Storage Management**
   - Named volumes
   - Bind mounts
   - tmpfs mounts

## Usage

### Basic Container Operations

```python
from docker_emulator import DockerEmulator, Port, Mount

# Initialize Docker emulator
docker = DockerEmulator()

# Create and start a container
container = docker.create_container(
    image="nginx:latest",
    name="web_server",
    ports=[Port(container_port=80, host_port=8080)],
    env={"ENV": "production", "DEBUG": "false"}
)

docker.start_container(container.id)
print(f"Container {container.name} is {container.state.value}")

# List running containers
running = docker.list_containers()
for c in running:
    print(f"{c.name}: {c.image} ({c.state.value})")

# Get container logs
logs = docker.logs(container.id)
for line in logs:
    print(line)

# Execute command in container
result = docker.exec_run(container.id, ["nginx", "-v"])
print(result["output"])

# Get container stats
stats = docker.stats(container.id)
print(f"CPU: {stats['cpu_percent']}%")
print(f"Memory: {stats['memory_usage'] / (1024*1024):.1f}MB")

# Stop and remove container
docker.stop_container(container.id)
docker.remove_container(container.id)
```

### Image Management

```python
# Build an image
image = docker.build_image(
    path="/app",
    tag="myapp:v1.0",
    labels={"version": "1.0", "maintainer": "dev-team"}
)

# Pull an image from registry
redis_image = docker.pull_image("redis", "6.2")

# Tag an image
docker.tag_image("myapp:v1.0", "myapp:latest")

# List all images
images = docker.list_images()
for img in images:
    print(f"{img.repository}:{img.tag} - {img.size / (1024*1024):.1f}MB")

# Push image to registry
docker.push_image("myapp", "v1.0")

# Remove image
docker.remove_image(image.id)
```

### Volume Management

```python
# Create a volume
volume = docker.create_volume(
    name="postgres_data",
    labels={"project": "myapp", "tier": "database"}
)

# Create container with volume mount
container = docker.create_container(
    image="postgres:13",
    mounts=[Mount(source="postgres_data", target="/var/lib/postgresql/data")]
)

# Inspect volume
info = docker.inspect_volume("postgres_data")
print(f"Volume: {info['Name']}")
print(f"Mountpoint: {info['Mountpoint']}")

# List volumes
volumes = docker.list_volumes()
for vol in volumes:
    print(f"{vol.name} - {vol.driver}")

# Remove volume
docker.remove_volume("postgres_data")
```

### Network Management

```python
from docker_emulator import NetworkDriver

# Create a custom network
network = docker.create_network(
    name="app_network",
    driver=NetworkDriver.BRIDGE,
    subnet="172.20.0.0/16",
    gateway="172.20.0.1"
)

# Create containers on the network
web = docker.create_container(
    image="nginx:latest",
    name="web",
    networks=["app_network"]
)

api = docker.create_container(
    image="python:3.9",
    name="api",
    networks=["app_network"]
)

# Connect container to network
docker.connect_network(network.id, web.id)

# List networks
networks = docker.list_networks()
for net in networks:
    print(f"{net.name} ({net.driver.value}): {len(net.containers)} containers")

# Disconnect and remove
docker.disconnect_network(network.id, web.id)
docker.remove_network(network.id)
```

### Docker Compose

```python
# Define services
compose_config = {
    "web": {
        "image": "nginx:latest",
        "ports": ["8080:80"],
        "environment": {"ENV": "production"},
        "volumes": ["/app/html:/usr/share/nginx/html"],
        "networks": ["frontend"]
    },
    "api": {
        "image": "python:3.9",
        "ports": ["5000:5000"],
        "environment": {"DATABASE_URL": "postgres://db:5432/mydb"},
        "networks": ["frontend", "backend"]
    },
    "db": {
        "image": "postgres:13",
        "environment": {"POSTGRES_PASSWORD": "secret"},
        "volumes": ["db_data:/var/lib/postgresql/data"],
        "networks": ["backend"]
    }
}

# Start all services
containers = docker.compose_up(compose_config)
print(f"Started {len(containers)} services")

# Check service status
for name, container in containers.items():
    print(f"{name}: {container.state.value}")

# Stop all services
docker.compose_down(containers)
```

### Advanced Features

```python
from docker_emulator import RestartPolicy

# Container with restart policy
container = docker.create_container(
    image="nginx:latest",
    name="resilient_web",
    restart_policy=RestartPolicy.ALWAYS,
    labels={"env": "production", "team": "platform"}
)

# Pause and unpause
docker.start_container(container.id)
docker.pause_container(container.id)
print(f"State: {container.state.value}")  # paused

docker.unpause_container(container.id)
print(f"State: {container.state.value}")  # running

# Inspect detailed container info
info = docker.inspect_container(container.id)
print(f"Container ID: {info['Id']}")
print(f"State: {info['State']['Status']}")
print(f"Started: {info['State']['StartedAt']}")
print(f"RestartPolicy: {info['HostConfig']['RestartPolicy']['Name']}")

# Prune unused resources
removed = docker.prune(
    prune_containers=True,
    prune_images=True,
    prune_volumes=True,
    prune_networks=True
)
print(f"Removed: {removed['containers']} containers, {removed['images']} images")
```

## Architecture

The emulator is built around several key components:

### Core Classes

- **DockerEmulator**: Main class managing all Docker operations
- **Container**: Represents a Docker container with state and configuration
- **Image**: Represents a Docker image with metadata
- **Volume**: Represents a named volume for persistent storage
- **Network**: Represents a Docker network for container connectivity
- **Port**: Represents a port binding configuration
- **Mount**: Represents a volume or bind mount

### State Management

Containers track their state through the lifecycle:
- `CREATED` → `RUNNING` → `PAUSED` → `RUNNING` → `EXITED`
- Supports transitions: start, stop, pause, unpause, restart, remove

### Resource Tracking

The emulator tracks:
- All containers with their full configuration
- All images with size and metadata
- All volumes with mount points
- All networks with connected containers
- Container logs and execution history

## Key Differences from Real Docker

This is an educational emulator with some simplifications:

1. **No Actual Containerization**: Doesn't create real isolated namespaces or cgroups
2. **No Real Process Management**: Container processes are simulated, not executed
3. **No Real Networking**: Network operations are tracked but not implemented at OS level
4. **No Real Filesystem**: File operations and volumes are tracked but not actually created
5. **No Registry Protocol**: Push/pull operations are simulated without actual registry communication
6. **Simplified Security**: No AppArmor, SELinux, or seccomp profiles
7. **No Resource Limits**: CPU/memory limits are tracked but not enforced
8. **No Multi-Host**: Doesn't support real Docker Swarm or multi-host networking

## Real-World Docker Features Emulated

- Container lifecycle management (create, start, stop, pause, restart, remove)
- Image operations (build, pull, push, tag, remove)
- Volume management (create, inspect, list, remove, mount)
- Network management (create, connect, disconnect, remove)
- Port bindings and port mapping
- Environment variable configuration
- Restart policies
- Docker Compose multi-container orchestration
- Container logs and exec operations
- Resource statistics and monitoring
- Labels and metadata
- Prune operations for cleanup

## Testing

Run the test suite:

```bash
python test_docker_emulator.py
```

The test suite covers:
- Container lifecycle operations
- Image management
- Volume operations
- Network operations
- Docker Compose
- Port bindings
- Volume mounts
- Resource statistics
- Prune operations

## Use Cases

This emulator is useful for:

1. **Learning Docker**: Understand Docker concepts without installing Docker
2. **Testing Docker-dependent Code**: Test applications that use Docker without requiring Docker
3. **CI/CD Simulation**: Simulate Docker operations in CI/CD pipelines
4. **Educational Tools**: Teaching containerization concepts
5. **Development**: Develop Docker orchestration tools without Docker dependency
6. **Documentation**: Generate documentation for Docker-based workflows

## Emulated vs Real Docker

| Feature | Emulated | Real Docker |
|---------|----------|-------------|
| Container Creation | ✅ | ✅ |
| Container Lifecycle | ✅ | ✅ |
| Image Management | ✅ | ✅ |
| Volume Management | ✅ | ✅ |
| Network Management | ✅ | ✅ |
| Docker Compose | ✅ | ✅ |
| Port Mapping | ✅ (tracked) | ✅ (actual) |
| Process Isolation | ❌ | ✅ |
| Resource Limits | ✅ (tracked) | ✅ (enforced) |
| Registry Operations | ✅ (simulated) | ✅ (actual) |
| Swarm Mode | ❌ | ✅ |
| BuildKit | ❌ | ✅ |

## License

This is an educational emulator created for learning purposes.

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Engine API](https://docs.docker.com/engine/api/)
- [Docker Compose Specification](https://compose-spec.io/)
- [OCI Runtime Specification](https://github.com/opencontainers/runtime-spec)
