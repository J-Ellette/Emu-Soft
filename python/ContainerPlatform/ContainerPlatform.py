#!/usr/bin/env python3
"""
Docker Emulator - Container Platform

This module emulates core Docker functionality including:
- Container lifecycle management
- Image building and management
- Volume management
- Network management
- Docker Compose orchestration
- Registry operations
"""

import json
import time
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ContainerState(Enum):
    """Container states"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"


class RestartPolicy(Enum):
    """Container restart policies"""
    NO = "no"
    ON_FAILURE = "on-failure"
    ALWAYS = "always"
    UNLESS_STOPPED = "unless-stopped"


class NetworkDriver(Enum):
    """Network driver types"""
    BRIDGE = "bridge"
    HOST = "host"
    OVERLAY = "overlay"
    MACVLAN = "macvlan"
    NONE = "none"


@dataclass
class Port:
    """Port binding configuration"""
    container_port: int
    host_port: Optional[int] = None
    protocol: str = "tcp"
    host_ip: str = "0.0.0.0"


@dataclass
class Volume:
    """Volume mount configuration"""
    name: str
    driver: str = "local"
    mountpoint: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Mount:
    """Mount configuration for containers"""
    source: str
    target: str
    type: str = "volume"  # volume, bind, tmpfs
    read_only: bool = False


@dataclass
class Network:
    """Docker network"""
    id: str
    name: str
    driver: NetworkDriver
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    containers: Dict[str, str] = field(default_factory=dict)  # container_id -> ip
    labels: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Image:
    """Docker image"""
    id: str
    repository: str
    tag: str
    digest: Optional[str] = None
    size: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    labels: Dict[str, str] = field(default_factory=dict)
    env: List[str] = field(default_factory=list)
    cmd: List[str] = field(default_factory=list)
    entrypoint: List[str] = field(default_factory=list)


@dataclass
class Container:
    """Docker container"""
    id: str
    name: str
    image: str
    state: ContainerState
    command: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    env: Dict[str, str] = field(default_factory=dict)
    ports: List[Port] = field(default_factory=list)
    mounts: List[Mount] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    restart_policy: RestartPolicy = RestartPolicy.NO
    restart_count: int = 0
    log_lines: List[str] = field(default_factory=list)


class ContainerPlatform:
    """Main Docker emulator class"""
    
    def __init__(self):
        self.containers: Dict[str, Container] = {}
        self.images: Dict[str, Image] = {}
        self.volumes: Dict[str, Volume] = {}
        self.networks: Dict[str, Network] = {}
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Create default networks and images"""
        # Create default bridge network
        default_network = Network(
            id=self._generate_id(),
            name="bridge",
            driver=NetworkDriver.BRIDGE,
            subnet="172.17.0.0/16",
            gateway="172.17.0.1"
        )
        self.networks[default_network.id] = default_network
        
        # Create some default images
        default_images = [
            ("ubuntu", "latest"),
            ("nginx", "latest"),
            ("python", "3.9"),
            ("alpine", "latest")
        ]
        for repo, tag in default_images:
            image = Image(
                id=self._generate_id(),
                repository=repo,
                tag=tag,
                size=100 * 1024 * 1024  # 100MB
            )
            self.images[image.id] = image
    
    def _generate_id(self, length: int = 12) -> str:
        """Generate a Docker-style ID"""
        return secrets.token_hex(length)
    
    def _find_image(self, image_name: str) -> Optional[Image]:
        """Find image by name:tag"""
        if ":" in image_name:
            repo, tag = image_name.rsplit(":", 1)
        else:
            repo, tag = image_name, "latest"
        
        for image in self.images.values():
            if image.repository == repo and image.tag == tag:
                return image
        return None
    
    # Container Operations
    
    def create_container(self, image: str, name: Optional[str] = None,
                        command: Optional[List[str]] = None,
                        env: Optional[Dict[str, str]] = None,
                        ports: Optional[List[Port]] = None,
                        mounts: Optional[List[Mount]] = None,
                        networks: Optional[List[str]] = None,
                        labels: Optional[Dict[str, str]] = None,
                        restart_policy: RestartPolicy = RestartPolicy.NO) -> Container:
        """Create a new container"""
        img = self._find_image(image)
        if not img:
            raise ValueError(f"Image not found: {image}")
        
        container_id = self._generate_id()
        container_name = name or f"container_{container_id[:8]}"
        
        container = Container(
            id=container_id,
            name=container_name,
            image=image,
            state=ContainerState.CREATED,
            command=command or img.cmd,
            env=env or {},
            ports=ports or [],
            mounts=mounts or [],
            networks=networks or ["bridge"],
            labels=labels or {},
            restart_policy=restart_policy
        )
        
        self.containers[container_id] = container
        return container
    
    def start_container(self, container_id: str) -> bool:
        """Start a container"""
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        container = self.containers[container_id]
        if container.state == ContainerState.RUNNING:
            return False
        
        container.state = ContainerState.RUNNING
        container.started_at = datetime.utcnow().isoformat()
        container.log_lines.append(f"[{datetime.utcnow().isoformat()}] Container started")
        return True
    
    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a running container"""
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        container = self.containers[container_id]
        if container.state != ContainerState.RUNNING:
            return False
        
        container.state = ContainerState.EXITED
        container.finished_at = datetime.utcnow().isoformat()
        container.exit_code = 0
        container.log_lines.append(f"[{datetime.utcnow().isoformat()}] Container stopped")
        return True
    
    def restart_container(self, container_id: str) -> bool:
        """Restart a container"""
        self.stop_container(container_id)
        return self.start_container(container_id)
    
    def pause_container(self, container_id: str) -> bool:
        """Pause a running container"""
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        container = self.containers[container_id]
        if container.state != ContainerState.RUNNING:
            return False
        
        container.state = ContainerState.PAUSED
        return True
    
    def unpause_container(self, container_id: str) -> bool:
        """Unpause a paused container"""
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        container = self.containers[container_id]
        if container.state != ContainerState.PAUSED:
            return False
        
        container.state = ContainerState.RUNNING
        return True
    
    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """Remove a container"""
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        container = self.containers[container_id]
        if container.state == ContainerState.RUNNING and not force:
            raise ValueError("Cannot remove running container without force=True")
        
        del self.containers[container_id]
        return True
    
    def list_containers(self, all: bool = False) -> List[Container]:
        """List containers"""
        if all:
            return list(self.containers.values())
        return [c for c in self.containers.values() if c.state == ContainerState.RUNNING]
    
    def inspect_container(self, container_id: str) -> Dict[str, Any]:
        """Get detailed container information"""
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        container = self.containers[container_id]
        return {
            "Id": container.id,
            "Name": container.name,
            "Image": container.image,
            "State": {
                "Status": container.state.value,
                "Running": container.state == ContainerState.RUNNING,
                "Paused": container.state == ContainerState.PAUSED,
                "StartedAt": container.started_at,
                "FinishedAt": container.finished_at,
                "ExitCode": container.exit_code
            },
            "Config": {
                "Cmd": container.command,
                "Env": [f"{k}={v}" for k, v in container.env.items()],
                "Labels": container.labels
            },
            "HostConfig": {
                "RestartPolicy": {"Name": container.restart_policy.value},
                "PortBindings": [
                    {
                        "ContainerPort": p.container_port,
                        "HostPort": p.host_port,
                        "Protocol": p.protocol
                    } for p in container.ports
                ]
            },
            "Mounts": [
                {
                    "Type": m.type,
                    "Source": m.source,
                    "Destination": m.target,
                    "RW": not m.read_only
                } for m in container.mounts
            ],
            "NetworkSettings": {
                "Networks": container.networks
            }
        }
    
    def logs(self, container_id: str, tail: Optional[int] = None) -> List[str]:
        """Get container logs"""
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        container = self.containers[container_id]
        logs = container.log_lines
        if tail:
            return logs[-tail:]
        return logs
    
    def exec_run(self, container_id: str, cmd: List[str]) -> Dict[str, Any]:
        """Execute command in container"""
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        container = self.containers[container_id]
        if container.state != ContainerState.RUNNING:
            raise ValueError("Container is not running")
        
        # Simulate command execution
        output = f"Executed: {' '.join(cmd)}"
        container.log_lines.append(f"[{datetime.utcnow().isoformat()}] Exec: {' '.join(cmd)}")
        
        return {
            "exit_code": 0,
            "output": output
        }
    
    # Image Operations
    
    def build_image(self, path: str, tag: str, dockerfile: str = "Dockerfile",
                   labels: Optional[Dict[str, str]] = None) -> Image:
        """Build an image from Dockerfile"""
        if ":" in tag:
            repo, tag_name = tag.rsplit(":", 1)
        else:
            repo, tag_name = tag, "latest"
        
        image = Image(
            id=self._generate_id(),
            repository=repo,
            tag=tag_name,
            size=150 * 1024 * 1024,  # 150MB
            labels=labels or {}
        )
        
        self.images[image.id] = image
        return image
    
    def pull_image(self, repository: str, tag: str = "latest") -> Image:
        """Pull an image from registry"""
        image = Image(
            id=self._generate_id(),
            repository=repository,
            tag=tag,
            size=100 * 1024 * 1024
        )
        
        self.images[image.id] = image
        return image
    
    def push_image(self, repository: str, tag: str = "latest") -> bool:
        """Push an image to registry"""
        img = self._find_image(f"{repository}:{tag}")
        if not img:
            raise ValueError(f"Image not found: {repository}:{tag}")
        return True
    
    def list_images(self) -> List[Image]:
        """List all images"""
        return list(self.images.values())
    
    def remove_image(self, image_id: str, force: bool = False) -> bool:
        """Remove an image"""
        if image_id not in self.images:
            raise ValueError(f"Image not found: {image_id}")
        
        # Check if any container is using this image
        if not force:
            for container in self.containers.values():
                if container.image == image_id:
                    raise ValueError("Image is being used by containers")
        
        del self.images[image_id]
        return True
    
    def tag_image(self, source: str, target: str) -> bool:
        """Tag an image"""
        img = self._find_image(source)
        if not img:
            raise ValueError(f"Source image not found: {source}")
        
        if ":" in target:
            repo, tag = target.rsplit(":", 1)
        else:
            repo, tag = target, "latest"
        
        # Create a new reference to the same image
        new_image = Image(
            id=img.id,
            repository=repo,
            tag=tag,
            size=img.size,
            labels=img.labels.copy()
        )
        self.images[self._generate_id()] = new_image
        return True
    
    # Volume Operations
    
    def create_volume(self, name: str, driver: str = "local",
                     labels: Optional[Dict[str, str]] = None,
                     options: Optional[Dict[str, str]] = None) -> Volume:
        """Create a volume"""
        volume = Volume(
            name=name,
            driver=driver,
            mountpoint=f"/var/lib/docker/volumes/{name}/_data",
            labels=labels or {},
            options=options or {}
        )
        
        self.volumes[name] = volume
        return volume
    
    def list_volumes(self) -> List[Volume]:
        """List all volumes"""
        return list(self.volumes.values())
    
    def remove_volume(self, name: str, force: bool = False) -> bool:
        """Remove a volume"""
        if name not in self.volumes:
            raise ValueError(f"Volume not found: {name}")
        
        # Check if any container is using this volume
        if not force:
            for container in self.containers.values():
                for mount in container.mounts:
                    if mount.source == name:
                        raise ValueError("Volume is being used by containers")
        
        del self.volumes[name]
        return True
    
    def inspect_volume(self, name: str) -> Dict[str, Any]:
        """Get detailed volume information"""
        if name not in self.volumes:
            raise ValueError(f"Volume not found: {name}")
        
        volume = self.volumes[name]
        return {
            "Name": volume.name,
            "Driver": volume.driver,
            "Mountpoint": volume.mountpoint,
            "Labels": volume.labels,
            "Options": volume.options,
            "CreatedAt": volume.created_at
        }
    
    # Network Operations
    
    def create_network(self, name: str, driver: NetworkDriver = NetworkDriver.BRIDGE,
                      subnet: Optional[str] = None, gateway: Optional[str] = None,
                      labels: Optional[Dict[str, str]] = None) -> Network:
        """Create a network"""
        network = Network(
            id=self._generate_id(),
            name=name,
            driver=driver,
            subnet=subnet,
            gateway=gateway,
            labels=labels or {}
        )
        
        self.networks[network.id] = network
        return network
    
    def list_networks(self) -> List[Network]:
        """List all networks"""
        return list(self.networks.values())
    
    def remove_network(self, network_id: str) -> bool:
        """Remove a network"""
        if network_id not in self.networks:
            raise ValueError(f"Network not found: {network_id}")
        
        network = self.networks[network_id]
        if network.name == "bridge":
            raise ValueError("Cannot remove default bridge network")
        
        if network.containers:
            raise ValueError("Network has active endpoints")
        
        del self.networks[network_id]
        return True
    
    def connect_network(self, network_id: str, container_id: str, 
                       ip_address: Optional[str] = None) -> bool:
        """Connect container to network"""
        if network_id not in self.networks:
            raise ValueError(f"Network not found: {network_id}")
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        network = self.networks[network_id]
        container = self.containers[container_id]
        
        # Assign IP address
        if not ip_address:
            ip_address = f"172.18.0.{len(network.containers) + 2}"
        
        network.containers[container_id] = ip_address
        if network.name not in container.networks:
            container.networks.append(network.name)
        
        return True
    
    def disconnect_network(self, network_id: str, container_id: str, 
                          force: bool = False) -> bool:
        """Disconnect container from network"""
        if network_id not in self.networks:
            raise ValueError(f"Network not found: {network_id}")
        
        network = self.networks[network_id]
        if container_id in network.containers:
            del network.containers[container_id]
            
            if container_id in self.containers:
                container = self.containers[container_id]
                if network.name in container.networks:
                    container.networks.remove(network.name)
        
        return True
    
    # Docker Compose Operations
    
    def compose_up(self, services: Dict[str, Dict[str, Any]]) -> Dict[str, Container]:
        """Start services defined in compose configuration"""
        created_containers = {}
        
        for service_name, config in services.items():
            image = config.get("image")
            command = config.get("command")
            env = config.get("environment", {})
            
            ports = []
            for port_config in config.get("ports", []):
                if ":" in str(port_config):
                    host, container = port_config.split(":")
                    ports.append(Port(container_port=int(container), host_port=int(host)))
                else:
                    ports.append(Port(container_port=int(port_config)))
            
            mounts = []
            for volume in config.get("volumes", []):
                if ":" in volume:
                    source, target = volume.split(":", 1)
                    mounts.append(Mount(source=source, target=target))
            
            networks = config.get("networks", ["default"])
            
            container = self.create_container(
                image=image,
                name=service_name,
                command=command,
                env=env,
                ports=ports,
                mounts=mounts,
                networks=networks
            )
            
            self.start_container(container.id)
            created_containers[service_name] = container
        
        return created_containers
    
    def compose_down(self, containers: Dict[str, Container]) -> bool:
        """Stop and remove compose services"""
        for container in containers.values():
            try:
                self.stop_container(container.id)
                self.remove_container(container.id)
            except ValueError:
                pass
        return True
    
    # Utility Methods
    
    def stats(self, container_id: str) -> Dict[str, Any]:
        """Get container resource usage statistics"""
        if container_id not in self.containers:
            raise ValueError(f"Container not found: {container_id}")
        
        container = self.containers[container_id]
        if container.state != ContainerState.RUNNING:
            raise ValueError("Container is not running")
        
        return {
            "cpu_percent": 25.5,
            "memory_usage": 256 * 1024 * 1024,  # 256MB
            "memory_limit": 512 * 1024 * 1024,  # 512MB
            "memory_percent": 50.0,
            "network_rx": 1024 * 1024,  # 1MB
            "network_tx": 512 * 1024,   # 512KB
            "block_read": 2048 * 1024,  # 2MB
            "block_write": 1024 * 1024  # 1MB
        }
    
    def prune(self, prune_containers: bool = True, prune_images: bool = True,
             prune_volumes: bool = False, prune_networks: bool = False) -> Dict[str, int]:
        """Remove unused resources"""
        removed = {
            "containers": 0,
            "images": 0,
            "volumes": 0,
            "networks": 0
        }
        
        if prune_containers:
            stopped = [cid for cid, c in self.containers.items() 
                      if c.state == ContainerState.EXITED]
            for cid in stopped:
                del self.containers[cid]
                removed["containers"] += 1
        
        if prune_images:
            # Remove untagged images
            used_images = {c.image for c in self.containers.values()}
            unused = [iid for iid, img in self.images.items() 
                     if img.id not in used_images and not img.tag]
            for iid in unused:
                del self.images[iid]
                removed["images"] += 1
        
        if prune_volumes:
            # Remove unused volumes
            used_volumes = set()
            for container in self.containers.values():
                for mount in container.mounts:
                    used_volumes.add(mount.source)
            
            unused = [name for name in self.volumes.keys() if name not in used_volumes]
            for name in unused:
                del self.volumes[name]
                removed["volumes"] += 1
        
        if prune_networks:
            # Remove networks with no containers
            unused = [nid for nid, net in self.networks.items() 
                     if not net.containers and net.name != "bridge"]
            for nid in unused:
                del self.networks[nid]
                removed["networks"] += 1
        
        return removed


# Example usage
if __name__ == "__main__":
    docker = ContainerPlatform()
    
    # Create and start a container
    container = docker.create_container(
        image="nginx:latest",
        name="web",
        ports=[Port(container_port=80, host_port=8080)],
        env={"ENV": "production"}
    )
    print(f"Created container: {container.name} ({container.id[:12]})")
    
    docker.start_container(container.id)
    print(f"Container state: {container.state.value}")
    
    # List running containers
    running = docker.list_containers()
    print(f"\nRunning containers: {len(running)}")
    for c in running:
        print(f"  - {c.name}: {c.image} ({c.state.value})")
    
    # Create a volume
    volume = docker.create_volume("mydata")
    print(f"\nCreated volume: {volume.name}")
    
    # Create a network
    network = docker.create_network("mynetwork")
    print(f"Created network: {network.name}")
    
    # Get container stats
    stats = docker.stats(container.id)
    print(f"\nContainer stats:")
    print(f"  CPU: {stats['cpu_percent']}%")
    print(f"  Memory: {stats['memory_usage'] / (1024*1024):.1f}MB / {stats['memory_limit'] / (1024*1024):.1f}MB")
