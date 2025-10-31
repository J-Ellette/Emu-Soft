"""
Docker-py Emulator - Docker API Client for Python

This module emulates the docker-py (docker) library, which is the official Python
library for the Docker Engine API. It allows you to interact with Docker containers,
images, networks, volumes, and more from Python applications.

Author: CIV-ARCOS Project
License: Original implementation for educational purposes


Developed by PowerShield
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field


@dataclass
class Container:
    """Represents a Docker container."""
    id: str
    name: str
    image: str
    status: str = "created"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    ports: Dict[str, Any] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    command: Optional[List[str]] = None
    network_mode: str = "default"
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    @staticmethod
    def _generate_id():
        """Generate a container ID."""
        import random
        return ''.join(random.choices('0123456789abcdef', k=64))
    
    def start(self):
        """Start the container."""
        if self.status == "created" or self.status == "exited":
            self.status = "running"
        return self
    
    def stop(self, timeout=10):
        """Stop the container."""
        if self.status == "running":
            self.status = "exited"
        return self
    
    def restart(self, timeout=10):
        """Restart the container."""
        self.stop(timeout)
        self.start()
        return self
    
    def kill(self, signal='SIGKILL'):
        """Kill the container."""
        self.status = "exited"
        return self
    
    def remove(self, **kwargs):
        """Remove the container."""
        self.status = "removed"
        return self
    
    def logs(self, **kwargs):
        """Get container logs."""
        return f"Container {self.name} logs\n"
    
    def stats(self, **kwargs):
        """Get container stats."""
        return {
            'id': self.id[:12],
            'name': self.name,
            'cpu_stats': {'cpu_usage': {'total_usage': 1000000}},
            'memory_stats': {'usage': 1024 * 1024 * 100},  # 100MB
            'networks': {},
        }
    
    def exec_run(self, cmd, **kwargs):
        """Execute a command in the container."""
        return (0, f"Executed: {cmd}\n".encode())
    
    def attrs(self):
        """Get container attributes."""
        return {
            'Id': self.id,
            'Name': self.name,
            'State': {'Status': self.status},
            'Config': {
                'Image': self.image,
                'Labels': self.labels,
                'Env': [f"{k}={v}" for k, v in self.environment.items()],
                'Cmd': self.command,
            },
            'NetworkSettings': {
                'Ports': self.ports,
                'Networks': {self.network_mode: {}},
            },
            'Created': self.created,
        }


@dataclass
class Image:
    """Represents a Docker image."""
    id: str
    tags: List[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    size: int = 1024 * 1024 * 100  # 100MB default
    labels: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    @staticmethod
    def _generate_id():
        """Generate an image ID."""
        import random
        return 'sha256:' + ''.join(random.choices('0123456789abcdef', k=64))
    
    def tag(self, repository, tag=None):
        """Tag the image."""
        full_tag = f"{repository}:{tag}" if tag else repository
        if full_tag not in self.tags:
            self.tags.append(full_tag)
        return True
    
    def attrs(self):
        """Get image attributes."""
        return {
            'Id': self.id,
            'RepoTags': self.tags,
            'Created': self.created,
            'Size': self.size,
            'Labels': self.labels,
        }


@dataclass
class Network:
    """Represents a Docker network."""
    id: str
    name: str
    driver: str = "bridge"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    containers: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    @staticmethod
    def _generate_id():
        """Generate a network ID."""
        import random
        return ''.join(random.choices('0123456789abcdef', k=64))
    
    def connect(self, container, **kwargs):
        """Connect a container to this network."""
        container_id = container.id if hasattr(container, 'id') else str(container)
        self.containers[container_id] = kwargs
    
    def disconnect(self, container, **kwargs):
        """Disconnect a container from this network."""
        container_id = container.id if hasattr(container, 'id') else str(container)
        if container_id in self.containers:
            del self.containers[container_id]
    
    def remove(self):
        """Remove the network."""
        return True
    
    def attrs(self):
        """Get network attributes."""
        return {
            'Id': self.id,
            'Name': self.name,
            'Driver': self.driver,
            'Created': self.created,
            'Containers': self.containers,
            'Options': self.options,
            'Labels': self.labels,
        }


@dataclass
class Volume:
    """Represents a Docker volume."""
    name: str
    driver: str = "local"
    mountpoint: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    labels: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.mountpoint:
            self.mountpoint = f"/var/lib/docker/volumes/{self.name}/_data"
    
    def remove(self, **kwargs):
        """Remove the volume."""
        return True
    
    def attrs(self):
        """Get volume attributes."""
        return {
            'Name': self.name,
            'Driver': self.driver,
            'Mountpoint': self.mountpoint,
            'Created': self.created,
            'Labels': self.labels,
            'Options': self.options,
        }


class ContainerCollection:
    """Manages Docker containers."""
    
    def __init__(self, client):
        self.client = client
        self._containers: Dict[str, Container] = {}
    
    def run(self, image, command=None, **kwargs):
        """Run a container."""
        name = kwargs.get('name', f"container_{len(self._containers)}")
        container = Container(
            id="",
            name=name,
            image=image,
            command=command if isinstance(command, list) else [command] if command else None,
            ports=kwargs.get('ports', {}),
            labels=kwargs.get('labels', {}),
            environment=kwargs.get('environment', {}),
            network_mode=kwargs.get('network_mode', 'default'),
        )
        self._containers[container.id] = container
        
        if kwargs.get('detach', True):
            container.start()
            return container
        else:
            container.start()
            # Simulate running and returning output
            return "Command output\n"
    
    def create(self, image, command=None, **kwargs):
        """Create a container without starting it."""
        name = kwargs.get('name', f"container_{len(self._containers)}")
        container = Container(
            id="",
            name=name,
            image=image,
            command=command if isinstance(command, list) else [command] if command else None,
            ports=kwargs.get('ports', {}),
            labels=kwargs.get('labels', {}),
            environment=kwargs.get('environment', {}),
            network_mode=kwargs.get('network_mode', 'default'),
        )
        self._containers[container.id] = container
        return container
    
    def get(self, container_id):
        """Get a container by ID or name."""
        # Try by ID first
        if container_id in self._containers:
            return self._containers[container_id]
        # Try by name
        for container in self._containers.values():
            if container.name == container_id:
                return container
        raise Exception(f"Container {container_id} not found")
    
    def list(self, all=False, **kwargs):
        """List containers."""
        containers = list(self._containers.values())
        if not all:
            containers = [c for c in containers if c.status == "running"]
        
        # Apply filters
        filters = kwargs.get('filters', {})
        if 'status' in filters:
            status_list = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
            containers = [c for c in containers if c.status in status_list]
        
        return containers
    
    def prune(self, **kwargs):
        """Remove stopped containers."""
        removed = [c for c in self._containers.values() if c.status == "exited"]
        for container in removed:
            del self._containers[container.id]
        return {'ContainersDeleted': [c.id for c in removed]}


class ImageCollection:
    """Manages Docker images."""
    
    def __init__(self, client):
        self.client = client
        self._images: Dict[str, Image] = {}
    
    def pull(self, repository, tag=None, **kwargs):
        """Pull an image from a registry."""
        full_tag = f"{repository}:{tag}" if tag else f"{repository}:latest"
        
        # Check if already exists
        for image in self._images.values():
            if full_tag in image.tags:
                return image
        
        # Create new image
        image = Image(id="", tags=[full_tag])
        self._images[image.id] = image
        return image
    
    def build(self, **kwargs):
        """Build an image from a Dockerfile."""
        tag = kwargs.get('tag', 'latest')
        image = Image(id="", tags=[tag])
        self._images[image.id] = image
        return (image, [{'stream': f"Successfully built {image.id[:12]}\n"}])
    
    def get(self, name):
        """Get an image by name or ID."""
        # Try by ID
        if name in self._images:
            return self._images[name]
        # Try by tag
        for image in self._images.values():
            if name in image.tags:
                return image
        raise Exception(f"Image {name} not found")
    
    def list(self, **kwargs):
        """List images."""
        images = list(self._images.values())
        
        # Apply filters
        filters = kwargs.get('filters', {})
        if 'dangling' in filters:
            is_dangling = filters['dangling']
            if is_dangling:
                images = [img for img in images if not img.tags]
        
        return images
    
    def remove(self, image, **kwargs):
        """Remove an image."""
        if isinstance(image, str):
            image = self.get(image)
        if image.id in self._images:
            del self._images[image.id]
        return [{'Deleted': image.id}]
    
    def prune(self, **kwargs):
        """Remove unused images."""
        removed = [img for img in self._images.values() if not img.tags]
        for image in removed:
            del self._images[image.id]
        return {'ImagesDeleted': [{'Deleted': img.id} for img in removed]}


class NetworkCollection:
    """Manages Docker networks."""
    
    def __init__(self, client):
        self.client = client
        self._networks: Dict[str, Network] = {}
        # Create default networks
        self._create_default_networks()
    
    def _create_default_networks(self):
        """Create default Docker networks."""
        for name, driver in [('bridge', 'bridge'), ('host', 'host'), ('none', 'null')]:
            network = Network(id="", name=name, driver=driver)
            self._networks[network.id] = network
    
    def create(self, name, **kwargs):
        """Create a network."""
        network = Network(
            id="",
            name=name,
            driver=kwargs.get('driver', 'bridge'),
            options=kwargs.get('options', {}),
            labels=kwargs.get('labels', {}),
        )
        self._networks[network.id] = network
        return network
    
    def get(self, network_id):
        """Get a network by ID or name."""
        # Try by ID
        if network_id in self._networks:
            return self._networks[network_id]
        # Try by name
        for network in self._networks.values():
            if network.name == network_id:
                return network
        raise Exception(f"Network {network_id} not found")
    
    def list(self, **kwargs):
        """List networks."""
        networks = list(self._networks.values())
        
        # Apply filters
        filters = kwargs.get('filters', {})
        if 'driver' in filters:
            driver_list = filters['driver'] if isinstance(filters['driver'], list) else [filters['driver']]
            networks = [n for n in networks if n.driver in driver_list]
        
        return networks
    
    def prune(self, **kwargs):
        """Remove unused networks."""
        # Remove networks with no containers (except default ones)
        removed = []
        for network in list(self._networks.values()):
            if network.name not in ['bridge', 'host', 'none'] and not network.containers:
                removed.append(network)
                del self._networks[network.id]
        return {'NetworksDeleted': [n.id for n in removed]}


class VolumeCollection:
    """Manages Docker volumes."""
    
    def __init__(self, client):
        self.client = client
        self._volumes: Dict[str, Volume] = {}
    
    def create(self, name=None, **kwargs):
        """Create a volume."""
        if not name:
            import random
            name = ''.join(random.choices('0123456789abcdef', k=64))
        
        volume = Volume(
            name=name,
            driver=kwargs.get('driver', 'local'),
            labels=kwargs.get('labels', {}),
            options=kwargs.get('driver_opts', {}),
        )
        self._volumes[volume.name] = volume
        return volume
    
    def get(self, volume_id):
        """Get a volume by name."""
        if volume_id in self._volumes:
            return self._volumes[volume_id]
        raise Exception(f"Volume {volume_id} not found")
    
    def list(self, **kwargs):
        """List volumes."""
        volumes = list(self._volumes.values())
        
        # Apply filters
        filters = kwargs.get('filters', {})
        if 'driver' in filters:
            driver_list = filters['driver'] if isinstance(filters['driver'], list) else [filters['driver']]
            volumes = [v for v in volumes if v.driver in driver_list]
        
        return volumes
    
    def prune(self, **kwargs):
        """Remove unused volumes."""
        # For simplicity, remove all volumes
        removed = list(self._volumes.keys())
        self._volumes.clear()
        return {'VolumesDeleted': removed}


class DockerClient:
    """
    Main Docker client for interacting with the Docker API.
    
    This emulates the docker.DockerClient class which provides access to
    all Docker resources (containers, images, networks, volumes, etc.).
    """
    
    def __init__(self, base_url=None, version=None, timeout=None, **kwargs):
        """Initialize the Docker client."""
        self.base_url = base_url or 'unix://var/run/docker.sock'
        self.api_version = version or 'auto'
        self.timeout = timeout or 60
        
        # Initialize resource collections
        self.containers = ContainerCollection(self)
        self.images = ImageCollection(self)
        self.networks = NetworkCollection(self)
        self.volumes = VolumeCollection(self)
    
    def ping(self):
        """Test connectivity to the Docker daemon."""
        return True
    
    def version(self):
        """Get version information from the Docker daemon."""
        return {
            'Version': '20.10.0',
            'ApiVersion': '1.41',
            'GoVersion': 'go1.16',
            'Os': 'linux',
            'Arch': 'amd64',
        }
    
    def info(self):
        """Get system-wide information."""
        return {
            'Containers': len(self.containers._containers),
            'ContainersRunning': len([c for c in self.containers._containers.values() if c.status == 'running']),
            'ContainersPaused': 0,
            'ContainersStopped': len([c for c in self.containers._containers.values() if c.status == 'exited']),
            'Images': len(self.images._images),
            'Driver': 'overlay2',
            'MemTotal': 1024 * 1024 * 1024 * 8,  # 8GB
            'NCPU': 4,
            'OperatingSystem': 'Linux',
        }
    
    def events(self, **kwargs):
        """Get real-time events from the server."""
        # Return a generator that yields events
        def event_generator():
            yield {'status': 'start', 'from': 'alpine', 'Type': 'container', 'time': int(time.time())}
        return event_generator()
    
    def close(self):
        """Close connections to the Docker daemon."""
        pass


# Module-level convenience functions
def from_env(**kwargs):
    """
    Create a client configured from environment variables.
    
    This is the most common way to create a Docker client.
    """
    return DockerClient(**kwargs)


# Create a default client instance
_default_client = None


def get_client():
    """Get or create the default client instance."""
    global _default_client
    if _default_client is None:
        _default_client = from_env()
    return _default_client


# Expose commonly used classes at module level
__all__ = [
    'DockerClient',
    'from_env',
    'Container',
    'Image',
    'Network',
    'Volume',
]
