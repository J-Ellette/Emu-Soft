"""
Developed by PowerShield, as an alternative to Docker
"""

#!/usr/bin/env python3
"""
Test suite for Docker Emulator
"""

import unittest
from ContainerPlatform import (
    ContainerPlatform, Container, Image, Volume, Network,
    ContainerState, RestartPolicy, NetworkDriver, Port, Mount
)


class TestContainerPlatform(unittest.TestCase):
    """Test cases for Docker emulator"""
    
    def setUp(self):
        """Set up test instance"""
        self.docker = ContainerPlatform()
    
    def test_initialization(self):
        """Test emulator initializes with defaults"""
        self.assertIsNotNone(self.docker.containers)
        self.assertIsNotNone(self.docker.images)
        self.assertIsNotNone(self.docker.volumes)
        self.assertIsNotNone(self.docker.networks)
        
        # Check default network exists
        bridge_exists = any(net.name == "bridge" for net in self.docker.networks.values())
        self.assertTrue(bridge_exists)
        
        # Check default images exist
        self.assertGreater(len(self.docker.images), 0)
    
    def test_create_container(self):
        """Test container creation"""
        container = self.docker.create_container(
            image="nginx:latest",
            name="test_nginx",
            env={"ENV": "test"}
        )
        
        self.assertEqual(container.name, "test_nginx")
        self.assertEqual(container.image, "nginx:latest")
        self.assertEqual(container.state, ContainerState.CREATED)
        self.assertIn(container.id, self.docker.containers)
    
    def test_start_stop_container(self):
        """Test starting and stopping containers"""
        container = self.docker.create_container(image="nginx:latest")
        
        # Start container
        result = self.docker.start_container(container.id)
        self.assertTrue(result)
        self.assertEqual(container.state, ContainerState.RUNNING)
        self.assertIsNotNone(container.started_at)
        
        # Stop container
        result = self.docker.stop_container(container.id)
        self.assertTrue(result)
        self.assertEqual(container.state, ContainerState.EXITED)
        self.assertIsNotNone(container.finished_at)
        self.assertEqual(container.exit_code, 0)
    
    def test_restart_container(self):
        """Test restarting a container"""
        container = self.docker.create_container(image="nginx:latest")
        self.docker.start_container(container.id)
        
        result = self.docker.restart_container(container.id)
        self.assertTrue(result)
        self.assertEqual(container.state, ContainerState.RUNNING)
    
    def test_pause_unpause_container(self):
        """Test pausing and unpausing containers"""
        container = self.docker.create_container(image="nginx:latest")
        self.docker.start_container(container.id)
        
        # Pause
        result = self.docker.pause_container(container.id)
        self.assertTrue(result)
        self.assertEqual(container.state, ContainerState.PAUSED)
        
        # Unpause
        result = self.docker.unpause_container(container.id)
        self.assertTrue(result)
        self.assertEqual(container.state, ContainerState.RUNNING)
    
    def test_remove_container(self):
        """Test removing containers"""
        container = self.docker.create_container(image="nginx:latest")
        container_id = container.id
        
        # Stop and remove
        self.docker.start_container(container_id)
        self.docker.stop_container(container_id)
        
        result = self.docker.remove_container(container_id)
        self.assertTrue(result)
        self.assertNotIn(container_id, self.docker.containers)
    
    def test_list_containers(self):
        """Test listing containers"""
        # Create some containers
        c1 = self.docker.create_container(image="nginx:latest")
        c2 = self.docker.create_container(image="python:3.9")
        
        # Start only one
        self.docker.start_container(c1.id)
        
        # List running only
        running = self.docker.list_containers(all=False)
        self.assertEqual(len(running), 1)
        self.assertEqual(running[0].id, c1.id)
        
        # List all
        all_containers = self.docker.list_containers(all=True)
        self.assertEqual(len(all_containers), 2)
    
    def test_inspect_container(self):
        """Test inspecting container details"""
        container = self.docker.create_container(
            image="nginx:latest",
            name="test",
            env={"KEY": "value"}
        )
        
        info = self.docker.inspect_container(container.id)
        
        self.assertEqual(info["Id"], container.id)
        self.assertEqual(info["Name"], "test")
        self.assertEqual(info["Image"], "nginx:latest")
        self.assertIn("State", info)
        self.assertIn("Config", info)
    
    def test_container_logs(self):
        """Test getting container logs"""
        container = self.docker.create_container(image="nginx:latest")
        self.docker.start_container(container.id)
        
        logs = self.docker.logs(container.id)
        self.assertIsInstance(logs, list)
        self.assertGreater(len(logs), 0)
    
    def test_exec_run(self):
        """Test executing commands in container"""
        container = self.docker.create_container(image="nginx:latest")
        self.docker.start_container(container.id)
        
        result = self.docker.exec_run(container.id, ["echo", "test"])
        
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("output", result)
    
    def test_build_image(self):
        """Test building an image"""
        image = self.docker.build_image(
            path="/app",
            tag="myapp:latest",
            labels={"version": "1.0"}
        )
        
        self.assertEqual(image.repository, "myapp")
        self.assertEqual(image.tag, "latest")
        self.assertIn(image.id, self.docker.images)
    
    def test_pull_image(self):
        """Test pulling an image"""
        image = self.docker.pull_image("redis", "6.0")
        
        self.assertEqual(image.repository, "redis")
        self.assertEqual(image.tag, "6.0")
        self.assertIn(image.id, self.docker.images)
    
    def test_list_images(self):
        """Test listing images"""
        initial_count = len(self.docker.list_images())
        
        self.docker.pull_image("redis")
        images = self.docker.list_images()
        
        self.assertEqual(len(images), initial_count + 1)
    
    def test_remove_image(self):
        """Test removing an image"""
        image = self.docker.pull_image("test_image")
        image_id = image.id
        
        result = self.docker.remove_image(image_id)
        self.assertTrue(result)
        self.assertNotIn(image_id, self.docker.images)
    
    def test_tag_image(self):
        """Test tagging an image"""
        result = self.docker.tag_image("nginx:latest", "mynginx:v1")
        self.assertTrue(result)
        
        # Verify new tag exists
        found = False
        for image in self.docker.images.values():
            if image.repository == "mynginx" and image.tag == "v1":
                found = True
                break
        self.assertTrue(found)
    
    def test_create_volume(self):
        """Test creating a volume"""
        volume = self.docker.create_volume(
            name="myvolume",
            labels={"project": "test"}
        )
        
        self.assertEqual(volume.name, "myvolume")
        self.assertIn("myvolume", self.docker.volumes)
    
    def test_list_volumes(self):
        """Test listing volumes"""
        self.docker.create_volume("vol1")
        self.docker.create_volume("vol2")
        
        volumes = self.docker.list_volumes()
        self.assertGreaterEqual(len(volumes), 2)
    
    def test_remove_volume(self):
        """Test removing a volume"""
        volume = self.docker.create_volume("test_volume")
        
        result = self.docker.remove_volume("test_volume")
        self.assertTrue(result)
        self.assertNotIn("test_volume", self.docker.volumes)
    
    def test_inspect_volume(self):
        """Test inspecting volume details"""
        volume = self.docker.create_volume(
            name="myvol",
            labels={"env": "prod"}
        )
        
        info = self.docker.inspect_volume("myvol")
        
        self.assertEqual(info["Name"], "myvol")
        self.assertEqual(info["Driver"], "local")
        self.assertIn("Mountpoint", info)
    
    def test_create_network(self):
        """Test creating a network"""
        network = self.docker.create_network(
            name="mynet",
            driver=NetworkDriver.BRIDGE,
            subnet="172.20.0.0/16"
        )
        
        self.assertEqual(network.name, "mynet")
        self.assertEqual(network.driver, NetworkDriver.BRIDGE)
        self.assertIn(network.id, self.docker.networks)
    
    def test_list_networks(self):
        """Test listing networks"""
        initial_count = len(self.docker.list_networks())
        
        self.docker.create_network("testnet")
        networks = self.docker.list_networks()
        
        self.assertEqual(len(networks), initial_count + 1)
    
    def test_remove_network(self):
        """Test removing a network"""
        network = self.docker.create_network("removeme")
        network_id = network.id
        
        result = self.docker.remove_network(network_id)
        self.assertTrue(result)
        self.assertNotIn(network_id, self.docker.networks)
    
    def test_connect_disconnect_network(self):
        """Test connecting and disconnecting containers to networks"""
        network = self.docker.create_network("testnet")
        container = self.docker.create_container(image="nginx:latest")
        
        # Connect
        result = self.docker.connect_network(network.id, container.id)
        self.assertTrue(result)
        self.assertIn(container.id, network.containers)
        
        # Disconnect
        result = self.docker.disconnect_network(network.id, container.id)
        self.assertTrue(result)
        self.assertNotIn(container.id, network.containers)
    
    def test_compose_up_down(self):
        """Test Docker Compose operations"""
        services = {
            "web": {
                "image": "nginx:latest",
                "ports": ["8080:80"],
                "environment": {"ENV": "prod"}
            },
            "db": {
                "image": "python:3.9",
                "volumes": ["/data:/var/lib/data"]
            }
        }
        
        # Up
        containers = self.docker.compose_up(services)
        self.assertEqual(len(containers), 2)
        self.assertIn("web", containers)
        self.assertIn("db", containers)
        self.assertEqual(containers["web"].state, ContainerState.RUNNING)
        
        # Down
        result = self.docker.compose_down(containers)
        self.assertTrue(result)
    
    def test_stats(self):
        """Test getting container statistics"""
        container = self.docker.create_container(image="nginx:latest")
        self.docker.start_container(container.id)
        
        stats = self.docker.stats(container.id)
        
        self.assertIn("cpu_percent", stats)
        self.assertIn("memory_usage", stats)
        self.assertIn("network_rx", stats)
        self.assertGreater(stats["cpu_percent"], 0)
    
    def test_prune(self):
        """Test pruning unused resources"""
        # Create some stopped containers
        c1 = self.docker.create_container(image="nginx:latest")
        c2 = self.docker.create_container(image="python:3.9")
        self.docker.start_container(c1.id)
        self.docker.start_container(c2.id)
        self.docker.stop_container(c1.id)
        self.docker.stop_container(c2.id)
        
        # Create unused volume
        self.docker.create_volume("unused_vol")
        
        # Prune
        removed = self.docker.prune(
            prune_containers=True,
            prune_volumes=True
        )
        
        self.assertGreater(removed["containers"], 0)
        self.assertGreaterEqual(removed["volumes"], 0)
    
    def test_port_binding(self):
        """Test port binding configuration"""
        ports = [
            Port(container_port=80, host_port=8080),
            Port(container_port=443, host_port=8443, protocol="tcp")
        ]
        
        container = self.docker.create_container(
            image="nginx:latest",
            ports=ports
        )
        
        self.assertEqual(len(container.ports), 2)
        self.assertEqual(container.ports[0].host_port, 8080)
        self.assertEqual(container.ports[1].host_port, 8443)
    
    def test_volume_mount(self):
        """Test volume mounting"""
        mounts = [
            Mount(source="mydata", target="/data", type="volume"),
            Mount(source="/host/path", target="/app", type="bind")
        ]
        
        container = self.docker.create_container(
            image="nginx:latest",
            mounts=mounts
        )
        
        self.assertEqual(len(container.mounts), 2)
        self.assertEqual(container.mounts[0].source, "mydata")
        self.assertEqual(container.mounts[1].type, "bind")


if __name__ == "__main__":
    unittest.main()
