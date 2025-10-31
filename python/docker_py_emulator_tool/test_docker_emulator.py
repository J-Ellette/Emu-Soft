"""
Test suite for Docker-py Emulator

Tests the core functionality of the docker-py emulator including:
- Client creation and connection
- Container operations
- Image management
- Network operations
- Volume management
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from docker_emulator import (
    DockerClient,
    from_env,
    Container,
    Image,
    Network,
    Volume,
)


def test_client_creation():
    """Test creating Docker clients."""
    print("Testing client creation...")
    
    # Create client from environment
    client = from_env()
    assert client is not None
    assert client.ping() == True
    
    # Create client with explicit parameters
    client2 = DockerClient(base_url='unix://var/run/docker.sock')
    assert client2 is not None
    
    print("  ✓ Client creation works")


def test_client_info():
    """Test getting Docker daemon information."""
    print("Testing client info...")
    
    client = from_env()
    
    # Get version
    version = client.version()
    assert 'Version' in version
    assert 'ApiVersion' in version
    
    # Get info
    info = client.info()
    assert 'Containers' in info
    assert 'Images' in info
    assert 'Driver' in info
    
    print("  ✓ Client info works")


def test_container_lifecycle():
    """Test container creation and lifecycle management."""
    print("Testing container lifecycle...")
    
    client = from_env()
    
    # Create a container
    container = client.containers.create('ubuntu:latest', name='test_container')
    assert container is not None
    assert container.name == 'test_container'
    assert container.status == 'created'
    
    # Start container
    container.start()
    assert container.status == 'running'
    
    # Stop container
    container.stop()
    assert container.status == 'exited'
    
    # Restart container
    container.restart()
    assert container.status == 'running'
    
    # Kill container
    container.kill()
    assert container.status == 'exited'
    
    # Remove container
    container.remove()
    assert container.status == 'removed'
    
    print("  ✓ Container lifecycle works")


def test_container_run():
    """Test running containers."""
    print("Testing container run...")
    
    client = from_env()
    
    # Run a container in detached mode
    container = client.containers.run(
        'nginx:latest',
        name='web_server',
        ports={'80/tcp': 8080},
        environment={'ENV_VAR': 'value'},
        detach=True
    )
    assert container is not None
    assert container.name == 'web_server'
    assert container.status == 'running'
    
    # Get container
    retrieved = client.containers.get('web_server')
    assert retrieved.id == container.id
    
    print("  ✓ Container run works")


def test_container_exec():
    """Test executing commands in containers."""
    print("Testing container exec...")
    
    client = from_env()
    
    container = client.containers.run('ubuntu:latest', detach=True)
    
    # Execute command
    exit_code, output = container.exec_run('ls -la')
    assert exit_code == 0
    assert b'Executed' in output
    
    # Get logs
    logs = container.logs()
    assert 'logs' in logs
    
    # Get stats
    stats = container.stats()
    assert 'cpu_stats' in stats
    assert 'memory_stats' in stats
    
    print("  ✓ Container exec works")


def test_container_list():
    """Test listing containers."""
    print("Testing container list...")
    
    client = from_env()
    
    # Create some containers
    c1 = client.containers.run('nginx', detach=True)
    c2 = client.containers.create('alpine')
    
    # List running containers
    running = client.containers.list()
    assert len(running) >= 1
    assert all(c.status == 'running' for c in running)
    
    # List all containers
    all_containers = client.containers.list(all=True)
    assert len(all_containers) >= 2
    
    # Filter by status
    filtered = client.containers.list(all=True, filters={'status': 'created'})
    assert c2 in filtered
    
    print("  ✓ Container list works")


def test_container_prune():
    """Test pruning stopped containers."""
    print("Testing container prune...")
    
    client = from_env()
    
    # Create and stop a container
    container = client.containers.run('alpine', detach=True)
    container.stop()
    
    # Prune stopped containers
    result = client.containers.prune()
    assert 'ContainersDeleted' in result
    assert len(result['ContainersDeleted']) >= 1
    
    print("  ✓ Container prune works")


def test_image_pull():
    """Test pulling images."""
    print("Testing image pull...")
    
    client = from_env()
    
    # Pull an image
    image = client.images.pull('python', tag='3.9')
    assert image is not None
    assert 'python:3.9' in image.tags
    
    # Pull without tag (should default to latest)
    image2 = client.images.pull('alpine')
    assert 'alpine:latest' in image2.tags
    
    print("  ✓ Image pull works")


def test_image_build():
    """Test building images."""
    print("Testing image build...")
    
    client = from_env()
    
    # Build an image
    image, logs = client.images.build(tag='myapp:latest')
    assert image is not None
    assert 'myapp:latest' in image.tags
    assert len(logs) > 0
    
    print("  ✓ Image build works")


def test_image_tag():
    """Test tagging images."""
    print("Testing image tag...")
    
    client = from_env()
    
    # Pull and tag an image
    image = client.images.pull('alpine')
    result = image.tag('myalpine', tag='v1')
    assert result == True
    assert 'myalpine:v1' in image.tags
    
    print("  ✓ Image tag works")


def test_image_list():
    """Test listing images."""
    print("Testing image list...")
    
    client = from_env()
    
    # Pull some images
    client.images.pull('alpine')
    client.images.pull('ubuntu')
    
    # List all images
    images = client.images.list()
    assert len(images) >= 2
    
    print("  ✓ Image list works")


def test_image_remove():
    """Test removing images."""
    print("Testing image remove...")
    
    client = from_env()
    
    # Pull and remove an image
    image = client.images.pull('busybox')
    result = client.images.remove(image)
    assert len(result) > 0
    assert 'Deleted' in result[0]
    
    print("  ✓ Image remove works")


def test_network_create():
    """Test creating networks."""
    print("Testing network create...")
    
    client = from_env()
    
    # Create a network
    network = client.networks.create('my_network', driver='bridge')
    assert network is not None
    assert network.name == 'my_network'
    assert network.driver == 'bridge'
    
    print("  ✓ Network create works")


def test_network_connect():
    """Test connecting containers to networks."""
    print("Testing network connect...")
    
    client = from_env()
    
    # Create network and container
    network = client.networks.create('test_network')
    container = client.containers.run('alpine', detach=True)
    
    # Connect container to network
    network.connect(container)
    assert container.id in network.containers
    
    # Disconnect container from network
    network.disconnect(container)
    assert container.id not in network.containers
    
    print("  ✓ Network connect works")


def test_network_list():
    """Test listing networks."""
    print("Testing network list...")
    
    client = from_env()
    
    # List all networks (should include default ones)
    networks = client.networks.list()
    assert len(networks) >= 3  # bridge, host, none
    
    network_names = [n.name for n in networks]
    assert 'bridge' in network_names
    assert 'host' in network_names
    
    print("  ✓ Network list works")


def test_network_prune():
    """Test pruning unused networks."""
    print("Testing network prune...")
    
    client = from_env()
    
    # Create a network
    network = client.networks.create('unused_network')
    
    # Prune unused networks
    result = client.networks.prune()
    assert 'NetworksDeleted' in result
    
    print("  ✓ Network prune works")


def test_volume_create():
    """Test creating volumes."""
    print("Testing volume create...")
    
    client = from_env()
    
    # Create a named volume
    volume = client.volumes.create('my_volume')
    assert volume is not None
    assert volume.name == 'my_volume'
    assert volume.driver == 'local'
    
    # Create anonymous volume
    volume2 = client.volumes.create()
    assert volume2 is not None
    assert len(volume2.name) > 0
    
    print("  ✓ Volume create works")


def test_volume_list():
    """Test listing volumes."""
    print("Testing volume list...")
    
    client = from_env()
    
    # Create some volumes
    client.volumes.create('vol1')
    client.volumes.create('vol2')
    
    # List volumes
    volumes = client.volumes.list()
    assert len(volumes) >= 2
    
    volume_names = [v.name for v in volumes]
    assert 'vol1' in volume_names
    assert 'vol2' in volume_names
    
    print("  ✓ Volume list works")


def test_volume_remove():
    """Test removing volumes."""
    print("Testing volume remove...")
    
    client = from_env()
    
    # Create and remove a volume
    volume = client.volumes.create('temp_volume')
    result = volume.remove()
    assert result == True
    
    print("  ✓ Volume remove works")


def test_volume_prune():
    """Test pruning volumes."""
    print("Testing volume prune...")
    
    client = from_env()
    
    # Create some volumes
    client.volumes.create('prune_vol1')
    client.volumes.create('prune_vol2')
    
    # Prune volumes
    result = client.volumes.prune()
    assert 'VolumesDeleted' in result
    assert len(result['VolumesDeleted']) >= 2
    
    print("  ✓ Volume prune works")


def test_container_attrs():
    """Test getting container attributes."""
    print("Testing container attrs...")
    
    client = from_env()
    
    container = client.containers.run(
        'nginx',
        name='attrs_test',
        ports={'80/tcp': 8080},
        labels={'app': 'web'},
        environment={'KEY': 'value'},
        detach=True
    )
    
    attrs = container.attrs()
    assert 'Id' in attrs
    assert attrs['Name'] == 'attrs_test'
    assert attrs['State']['Status'] == 'running'
    assert attrs['Config']['Image'] == 'nginx'
    assert attrs['Config']['Labels']['app'] == 'web'
    
    print("  ✓ Container attrs works")


def test_image_attrs():
    """Test getting image attributes."""
    print("Testing image attrs...")
    
    client = from_env()
    
    image = client.images.pull('alpine')
    attrs = image.attrs()
    
    assert 'Id' in attrs
    assert 'RepoTags' in attrs
    assert 'Created' in attrs
    assert 'Size' in attrs
    
    print("  ✓ Image attrs works")


def test_network_attrs():
    """Test getting network attributes."""
    print("Testing network attrs...")
    
    client = from_env()
    
    network = client.networks.create('attrs_network', labels={'env': 'test'})
    attrs = network.attrs()
    
    assert 'Id' in attrs
    assert attrs['Name'] == 'attrs_network'
    assert attrs['Driver'] == 'bridge'
    assert attrs['Labels']['env'] == 'test'
    
    print("  ✓ Network attrs works")


def test_volume_attrs():
    """Test getting volume attributes."""
    print("Testing volume attrs...")
    
    client = from_env()
    
    volume = client.volumes.create('attrs_volume', labels={'type': 'test'})
    attrs = volume.attrs()
    
    assert 'Name' in attrs
    assert attrs['Name'] == 'attrs_volume'
    assert attrs['Driver'] == 'local'
    assert attrs['Labels']['type'] == 'test'
    
    print("  ✓ Volume attrs works")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Docker-py Emulator Test Suite")
    print("=" * 60)
    
    tests = [
        test_client_creation,
        test_client_info,
        test_container_lifecycle,
        test_container_run,
        test_container_exec,
        test_container_list,
        test_container_prune,
        test_image_pull,
        test_image_build,
        test_image_tag,
        test_image_list,
        test_image_remove,
        test_network_create,
        test_network_connect,
        test_network_list,
        test_network_prune,
        test_volume_create,
        test_volume_list,
        test_volume_remove,
        test_volume_prune,
        test_container_attrs,
        test_image_attrs,
        test_network_attrs,
        test_volume_attrs,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
