"""
Developed by PowerShield, as an application topology mapper

Tests for TopoMapper - Application Topology Mapper

This test suite validates the core functionality of TopoMapper.
"""

import sys
import os
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from TopoMapper import (
    TopologyMapper, Service, Connection, Protocol, ServiceStatus,
    create_mapper
)


def test_service_creation():
    """Test service creation"""
    print("Testing service creation...")
    
    service = Service(name="test-service")
    assert service.name == "test-service"
    assert service.incoming_connections == 0
    assert service.outgoing_connections == 0
    assert service.get_status() == ServiceStatus.UNKNOWN
    
    print("✓ Service creation works")


def test_service_status():
    """Test service health status"""
    print("Testing service status...")
    
    service = Service(name="test")
    
    # No requests = unknown
    assert service.get_status() == ServiceStatus.UNKNOWN
    
    # All successful = healthy
    service.total_requests_received = 100
    service.total_errors = 0
    assert service.get_status() == ServiceStatus.HEALTHY
    
    # 3% errors = healthy
    service.total_errors = 3
    assert service.get_status() == ServiceStatus.HEALTHY
    
    # 10% errors = degraded
    service.total_errors = 10
    assert service.get_status() == ServiceStatus.DEGRADED
    
    # 25% errors = unhealthy
    service.total_errors = 25
    assert service.get_status() == ServiceStatus.UNHEALTHY
    
    print("✓ Service status works")


def test_connection_creation():
    """Test connection creation"""
    print("Testing connection creation...")
    
    conn = Connection(
        source="service-a",
        destination="service-b",
        protocol=Protocol.HTTP
    )
    
    assert conn.source == "service-a"
    assert conn.destination == "service-b"
    assert conn.protocol == Protocol.HTTP
    assert conn.request_count == 0
    assert conn.error_count == 0
    
    print("✓ Connection creation works")


def test_connection_add_request():
    """Test adding requests to connection"""
    print("Testing connection add_request...")
    
    conn = Connection("a", "b", Protocol.HTTP)
    
    conn.add_request(bytes_transferred=1000, latency_ms=50.0)
    assert conn.request_count == 1
    assert conn.total_bytes == 1000
    assert conn.avg_latency_ms == 50.0
    
    conn.add_request(bytes_transferred=2000, latency_ms=100.0, is_error=True)
    assert conn.request_count == 2
    assert conn.error_count == 1
    assert conn.total_bytes == 3000
    assert conn.avg_latency_ms == 75.0  # (50 + 100) / 2
    
    print("✓ Connection add_request works")


def test_connection_error_rate():
    """Test connection error rate calculation"""
    print("Testing connection error rate...")
    
    conn = Connection("a", "b", Protocol.HTTP)
    
    # Add requests with some errors
    for i in range(10):
        conn.add_request(1000, 50.0, is_error=(i % 5 == 0))
    
    # Should be 20% (2 errors out of 10 requests)
    assert conn.get_error_rate() == 0.2
    
    print("✓ Connection error rate works")


def test_mapper_creation():
    """Test mapper creation"""
    print("Testing mapper creation...")
    
    mapper = create_mapper()
    assert mapper is not None
    assert len(mapper.get_all_services()) == 0
    assert len(mapper.get_all_connections()) == 0
    
    print("✓ Mapper creation works")


def test_observe_traffic():
    """Test observing traffic"""
    print("Testing observe_traffic...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic(
        source="api",
        destination="database",
        protocol=Protocol.HTTP,
        bytes_transferred=1024,
        latency_ms=25.5
    )
    
    # Check services were created
    assert len(mapper.get_all_services()) == 2
    assert mapper.get_service("api") is not None
    assert mapper.get_service("database") is not None
    
    # Check connection was created
    conn = mapper.get_connection("api", "database")
    assert conn is not None
    assert conn.request_count == 1
    
    print("✓ Observe traffic works")


def test_observe_multiple_traffic():
    """Test observing multiple traffic flows"""
    print("Testing multiple traffic observation...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("web", "api", Protocol.HTTPS)
    mapper.observe_traffic("api", "database", Protocol.TCP)
    mapper.observe_traffic("api", "cache", Protocol.TCP)
    
    assert len(mapper.get_all_services()) == 4
    assert len(mapper.get_all_connections()) == 3
    
    print("✓ Multiple traffic observation works")


def test_service_statistics():
    """Test service statistics tracking"""
    print("Testing service statistics...")
    
    mapper = TopologyMapper()
    
    # Service A sends to B and C
    mapper.observe_traffic("a", "b", Protocol.HTTP)
    mapper.observe_traffic("a", "c", Protocol.HTTP)
    
    # Service B sends to C
    mapper.observe_traffic("b", "c", Protocol.HTTP)
    
    service_a = mapper.get_service("a")
    assert service_a.total_requests_sent == 2
    assert service_a.outgoing_connections == 2
    
    service_c = mapper.get_service("c")
    assert service_c.total_requests_received == 2
    assert service_c.incoming_connections == 2
    
    print("✓ Service statistics work")


def test_get_dependency_graph():
    """Test dependency graph generation"""
    print("Testing dependency graph...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("frontend", "api", Protocol.HTTPS)
    mapper.observe_traffic("api", "users", Protocol.HTTP)
    mapper.observe_traffic("api", "orders", Protocol.HTTP)
    mapper.observe_traffic("users", "database", Protocol.TCP)
    
    graph = mapper.get_dependency_graph()
    
    assert "api" in graph["frontend"]
    assert "users" in graph["api"]
    assert "orders" in graph["api"]
    assert "database" in graph["users"]
    
    print("✓ Dependency graph works")


def test_get_service_dependencies():
    """Test getting dependencies for specific service"""
    print("Testing service dependencies...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("frontend", "api", Protocol.HTTP)
    mapper.observe_traffic("api", "database", Protocol.TCP)
    mapper.observe_traffic("mobile", "api", Protocol.HTTP)
    
    deps = mapper.get_service_dependencies("api")
    
    assert "database" in deps['depends_on']
    assert "frontend" in deps['depended_by']
    assert "mobile" in deps['depended_by']
    
    print("✓ Service dependencies work")


def test_find_entry_points():
    """Test finding entry point services"""
    print("Testing find entry points...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("load-balancer", "api", Protocol.HTTPS)
    mapper.observe_traffic("api", "database", Protocol.TCP)
    mapper.observe_traffic("api", "cache", Protocol.TCP)
    
    entry_points = mapper.find_entry_points()
    
    assert "load-balancer" in entry_points
    assert "api" not in entry_points
    assert len(entry_points) == 1
    
    print("✓ Find entry points works")


def test_find_leaf_services():
    """Test finding leaf services"""
    print("Testing find leaf services...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("api", "database", Protocol.TCP)
    mapper.observe_traffic("api", "cache", Protocol.TCP)
    mapper.observe_traffic("worker", "database", Protocol.TCP)
    
    leaves = mapper.find_leaf_services()
    
    assert "database" in leaves
    assert "cache" in leaves
    assert "api" not in leaves
    
    print("✓ Find leaf services works")


def test_find_critical_services():
    """Test finding critical services"""
    print("Testing find critical services...")
    
    mapper = TopologyMapper()
    
    # Multiple services depend on auth
    mapper.observe_traffic("api", "auth", Protocol.HTTP)
    mapper.observe_traffic("web", "auth", Protocol.HTTP)
    mapper.observe_traffic("mobile", "auth", Protocol.HTTP)
    mapper.observe_traffic("admin", "auth", Protocol.HTTP)
    
    # Only one depends on logging
    mapper.observe_traffic("api", "logging", Protocol.HTTP)
    
    critical = mapper.find_critical_services(min_dependents=2)
    
    assert len(critical) > 0
    assert critical[0][0] == "auth"
    assert critical[0][1] == 4
    
    print("✓ Find critical services works")


def test_detect_circular_dependencies():
    """Test circular dependency detection"""
    print("Testing circular dependency detection...")
    
    mapper = TopologyMapper()
    
    # Create a circular dependency
    mapper.observe_traffic("a", "b", Protocol.HTTP)
    mapper.observe_traffic("b", "c", Protocol.HTTP)
    mapper.observe_traffic("c", "a", Protocol.HTTP)
    
    cycles = mapper.detect_circular_dependencies()
    
    assert len(cycles) > 0
    
    print("✓ Circular dependency detection works")


def test_no_circular_dependencies():
    """Test with no circular dependencies"""
    print("Testing no circular dependencies...")
    
    mapper = TopologyMapper()
    
    # Linear dependency chain
    mapper.observe_traffic("a", "b", Protocol.HTTP)
    mapper.observe_traffic("b", "c", Protocol.HTTP)
    mapper.observe_traffic("c", "d", Protocol.HTTP)
    
    cycles = mapper.detect_circular_dependencies()
    
    assert len(cycles) == 0
    
    print("✓ No circular dependencies works")


def test_generate_text_topology():
    """Test text topology generation"""
    print("Testing text topology generation...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("web", "api", Protocol.HTTPS, 1000, 50.0)
    mapper.observe_traffic("api", "database", Protocol.TCP, 2000, 25.0)
    
    text = mapper.generate_text_topology()
    
    assert len(text) > 0
    assert "Application Topology Map" in text
    assert "web" in text
    assert "api" in text
    assert "database" in text
    
    print("✓ Text topology generation works")


def test_generate_dot_graph():
    """Test DOT graph generation"""
    print("Testing DOT graph generation...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("frontend", "api", Protocol.HTTPS)
    mapper.observe_traffic("api", "backend", Protocol.HTTP)
    
    dot = mapper.generate_dot_graph(include_stats=True)
    
    assert "digraph topology" in dot
    assert "frontend" in dot
    assert "api" in dot
    assert "backend" in dot
    assert "->" in dot
    
    print("✓ DOT graph generation works")


def test_get_topology_summary():
    """Test topology summary"""
    print("Testing topology summary...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("web", "api", Protocol.HTTP)
    mapper.observe_traffic("api", "db", Protocol.TCP)
    mapper.observe_traffic("api", "cache", Protocol.TCP)
    
    summary = mapper.get_topology_summary()
    
    assert summary['total_services'] == 4
    assert summary['total_connections'] == 3
    assert 'entry_points' in summary
    assert 'leaf_services' in summary
    
    print("✓ Topology summary works")


def test_take_snapshot():
    """Test taking snapshots"""
    print("Testing take snapshot...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("a", "b", Protocol.HTTP)
    mapper.observe_traffic("b", "c", Protocol.HTTP)
    
    snapshot = mapper.take_snapshot()
    
    assert 'timestamp' in snapshot
    assert 'services' in snapshot
    assert 'connections' in snapshot
    assert 'summary' in snapshot
    assert len(snapshot['services']) == 3
    
    print("✓ Take snapshot works")


def test_detect_changes():
    """Test change detection"""
    print("Testing change detection...")
    
    mapper = TopologyMapper()
    
    # Initial topology
    mapper.observe_traffic("a", "b", Protocol.HTTP)
    snapshot1 = mapper.take_snapshot()
    
    time.sleep(0.1)
    
    # Add new service and connection
    mapper.observe_traffic("a", "c", Protocol.HTTP)
    mapper.observe_traffic("b", "d", Protocol.HTTP)
    
    changes = mapper.detect_changes(snapshot1)
    
    assert len(changes['new_services']) == 2  # c and d
    assert len(changes['new_connections']) == 2
    
    print("✓ Change detection works")


def test_export_import_json():
    """Test JSON export and import"""
    print("Testing JSON export/import...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("web", "api", Protocol.HTTPS, 1000, 50.0)
    mapper.observe_traffic("api", "db", Protocol.TCP, 2000, 25.0)
    
    # Export
    filename = "/tmp/test_topology.json"
    mapper.export_to_json(filename)
    
    assert os.path.exists(filename)
    
    # Import into new mapper
    new_mapper = TopologyMapper()
    new_mapper.import_from_json(filename)
    
    assert len(new_mapper.get_all_services()) == 3
    assert len(new_mapper.get_all_connections()) == 2
    
    # Cleanup
    os.remove(filename)
    
    print("✓ JSON export/import works")


def test_clear():
    """Test clearing mapper data"""
    print("Testing clear...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic("a", "b", Protocol.HTTP)
    mapper.observe_traffic("b", "c", Protocol.HTTP)
    
    assert len(mapper.get_all_services()) > 0
    
    mapper.clear()
    
    assert len(mapper.get_all_services()) == 0
    assert len(mapper.get_all_connections()) == 0
    
    print("✓ Clear works")


def test_protocol_types():
    """Test different protocol types"""
    print("Testing protocol types...")
    
    mapper = TopologyMapper()
    
    protocols = [
        Protocol.HTTP,
        Protocol.HTTPS,
        Protocol.GRPC,
        Protocol.WEBSOCKET,
        Protocol.TCP,
        Protocol.UDP,
        Protocol.UNKNOWN
    ]
    
    for i, protocol in enumerate(protocols):
        mapper.observe_traffic(f"service-{i}", f"service-{i+1}", protocol)
    
    assert len(mapper.get_all_connections()) == len(protocols)
    
    print("✓ Protocol types work")


def test_ip_and_port_tracking():
    """Test IP and port tracking"""
    print("Testing IP and port tracking...")
    
    mapper = TopologyMapper()
    
    mapper.observe_traffic(
        "web-server",
        "api",
        Protocol.HTTPS,
        source_ip="192.168.1.10",
        source_port=54321,
        dest_ip="10.0.0.5",
        dest_port=443
    )
    
    api_service = mapper.get_service("api")
    assert "10.0.0.5" in api_service.ip_addresses
    assert 443 in api_service.ports
    
    web_service = mapper.get_service("web-server")
    assert "192.168.1.10" in web_service.ip_addresses
    assert 54321 in web_service.ports
    
    print("✓ IP and port tracking works")


def test_service_to_dict():
    """Test service serialization"""
    print("Testing service to_dict...")
    
    service = Service(name="test-service")
    service.ip_addresses.add("192.168.1.1")
    service.ports.add(8080)
    service.protocols.add(Protocol.HTTP)
    service.total_requests_received = 100
    
    service_dict = service.to_dict()
    
    assert service_dict['name'] == "test-service"
    assert "192.168.1.1" in service_dict['ip_addresses']
    assert 8080 in service_dict['ports']
    assert service_dict['total_requests_received'] == 100
    
    print("✓ Service serialization works")


def test_connection_to_dict():
    """Test connection serialization"""
    print("Testing connection to_dict...")
    
    conn = Connection("a", "b", Protocol.HTTP)
    conn.add_request(1000, 50.0)
    conn.add_request(2000, 100.0, is_error=True)
    
    conn_dict = conn.to_dict()
    
    assert conn_dict['source'] == "a"
    assert conn_dict['destination'] == "b"
    assert conn_dict['protocol'] == "HTTP"
    assert conn_dict['request_count'] == 2
    assert conn_dict['error_count'] == 1
    assert conn_dict['error_rate'] == 0.5
    
    print("✓ Connection serialization works")


def run_all_tests():
    """Run all test functions"""
    print("=" * 60)
    print("Running TopoMapper Tests")
    print("=" * 60)
    print()
    
    test_functions = [
        test_service_creation,
        test_service_status,
        test_connection_creation,
        test_connection_add_request,
        test_connection_error_rate,
        test_mapper_creation,
        test_observe_traffic,
        test_observe_multiple_traffic,
        test_service_statistics,
        test_get_dependency_graph,
        test_get_service_dependencies,
        test_find_entry_points,
        test_find_leaf_services,
        test_find_critical_services,
        test_detect_circular_dependencies,
        test_no_circular_dependencies,
        test_generate_text_topology,
        test_generate_dot_graph,
        test_get_topology_summary,
        test_take_snapshot,
        test_detect_changes,
        test_export_import_json,
        test_clear,
        test_protocol_types,
        test_ip_and_port_tracking,
        test_service_to_dict,
        test_connection_to_dict,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
