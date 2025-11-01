# TopoMapper - Application Topology Mapper

A pure Python application topology mapper that builds service dependency graphs from actual network traffic.

## What This Tool Does

**Purpose:** TopoMapper observes network traffic between services to automatically discover and map your application's topology, identify dependencies, and detect architectural patterns.

## Features

- **Automatic Service Discovery** - Discover services from traffic patterns
- **Dependency Mapping** - Build complete service dependency graphs
- **Protocol Detection** - Identify communication protocols (HTTP, gRPC, WebSocket, etc.)
- **Health Monitoring** - Track service health based on error rates
- **Critical Service Detection** - Identify services many others depend on
- **Entry Point Discovery** - Find external-facing services
- **Circular Dependency Detection** - Detect dependency cycles
- **Topology Visualization** - Generate DOT graphs and text visualizations
- **Change Detection** - Track topology changes over time
- **Export/Import** - Save and load topology data
- **Thread-safe** - Concurrent traffic observation

## Core Components

- **TopologyMapper**: Main class for topology mapping
- **Service**: Represents a service in the topology
- **Connection**: Represents communication between services
- **Protocol**: Enumeration of supported protocols
- **ServiceStatus**: Health status (Healthy, Degraded, Unhealthy)

## Usage

### Basic Traffic Observation

```python
from TopoMapper import create_mapper, Protocol

# Create mapper
mapper = create_mapper()

# Observe traffic
mapper.observe_traffic(
    source="api-gateway",
    destination="user-service",
    protocol=Protocol.HTTP,
    bytes_transferred=1024,
    latency_ms=25.5
)

mapper.observe_traffic(
    source="user-service",
    destination="database",
    protocol=Protocol.TCP,
    bytes_transferred=2048,
    latency_ms=10.2
)

# View discovered services
services = mapper.get_all_services()
for service in services:
    print(f"Service: {service.name}, Status: {service.get_status().value}")
```

### Building Service Dependencies

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Simulate microservice traffic
mapper.observe_traffic("frontend", "api-gateway", Protocol.HTTPS)
mapper.observe_traffic("api-gateway", "auth-service", Protocol.GRPC)
mapper.observe_traffic("api-gateway", "user-service", Protocol.HTTP)
mapper.observe_traffic("user-service", "database", Protocol.TCP)
mapper.observe_traffic("api-gateway", "order-service", Protocol.HTTP)
mapper.observe_traffic("order-service", "payment-service", Protocol.HTTPS)
mapper.observe_traffic("order-service", "inventory-service", Protocol.HTTP)

# Get dependency graph
dependencies = mapper.get_dependency_graph()
print("Service Dependencies:")
for service, depends_on in dependencies.items():
    print(f"  {service} -> {', '.join(depends_on)}")
```

### Finding Entry Points

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Observe traffic
mapper.observe_traffic("load-balancer", "api-gateway", Protocol.HTTPS)
mapper.observe_traffic("api-gateway", "service-a", Protocol.HTTP)
mapper.observe_traffic("service-a", "service-b", Protocol.GRPC)

# Find entry points (services with no incoming connections)
entry_points = mapper.find_entry_points()
print(f"Entry points: {', '.join(entry_points)}")  # load-balancer
```

### Finding Leaf Services

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Build topology
mapper.observe_traffic("api", "service-a", Protocol.HTTP)
mapper.observe_traffic("service-a", "database", Protocol.TCP)
mapper.observe_traffic("service-a", "cache", Protocol.TCP)

# Find leaf services (services with no outgoing connections)
leaves = mapper.find_leaf_services()
print(f"Leaf services: {', '.join(leaves)}")  # database, cache
```

### Detecting Critical Services

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Multiple services depend on auth-service
mapper.observe_traffic("api", "auth-service", Protocol.HTTP)
mapper.observe_traffic("frontend", "auth-service", Protocol.HTTP)
mapper.observe_traffic("admin", "auth-service", Protocol.HTTP)
mapper.observe_traffic("mobile-app", "auth-service", Protocol.HTTP)

# Find critical services (many dependents)
critical = mapper.find_critical_services(min_dependents=2)
print("Critical Services:")
for service, dependent_count in critical:
    print(f"  {service}: {dependent_count} services depend on it")
```

### Tracking Service Health

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Simulate successful requests
for _ in range(95):
    mapper.observe_traffic(
        "api", "service-a", Protocol.HTTP,
        bytes_transferred=1000,
        latency_ms=50.0,
        is_error=False
    )

# Simulate errors
for _ in range(5):
    mapper.observe_traffic(
        "api", "service-a", Protocol.HTTP,
        bytes_transferred=500,
        latency_ms=100.0,
        is_error=True
    )

# Check service health
service = mapper.get_service("service-a")
print(f"Service: {service.name}")
print(f"Status: {service.get_status().value}")
print(f"Requests: {service.total_requests_received}")
print(f"Errors: {service.total_errors}")
```

### Analyzing Connection Statistics

```python
from TopoMapper import create_mapper, Protocol
import random

mapper = create_mapper()

# Simulate varied traffic
for i in range(100):
    mapper.observe_traffic(
        "api", "backend", Protocol.HTTP,
        bytes_transferred=random.randint(500, 2000),
        latency_ms=random.uniform(10.0, 100.0),
        is_error=(i % 20 == 0)  # 5% error rate
    )

# Get connection details
conn = mapper.get_connection("api", "backend")
print(f"Connection: {conn.source} -> {conn.destination}")
print(f"  Protocol: {conn.protocol.value}")
print(f"  Requests: {conn.request_count}")
print(f"  Errors: {conn.error_count} ({conn.get_error_rate():.1%})")
print(f"  Avg Latency: {conn.avg_latency_ms:.2f}ms")
print(f"  Total Bytes: {conn.total_bytes}")
```

### Detecting Circular Dependencies

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Create a circular dependency
mapper.observe_traffic("service-a", "service-b", Protocol.HTTP)
mapper.observe_traffic("service-b", "service-c", Protocol.HTTP)
mapper.observe_traffic("service-c", "service-a", Protocol.HTTP)  # Circular!

# Detect cycles
cycles = mapper.detect_circular_dependencies()
if cycles:
    print("Circular Dependencies Detected:")
    for cycle in cycles:
        print(f"  {' -> '.join(cycle)}")
else:
    print("No circular dependencies found")
```

### Generating Text Topology

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Build sample topology
mapper.observe_traffic("web", "api", Protocol.HTTPS, 1024, 50.0)
mapper.observe_traffic("api", "database", Protocol.TCP, 2048, 25.0)
mapper.observe_traffic("api", "cache", Protocol.TCP, 512, 5.0)

# Generate text visualization
topology_text = mapper.generate_text_topology()
print(topology_text)
```

### Generating DOT Graph for Graphviz

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Build topology
mapper.observe_traffic("frontend", "api", Protocol.HTTPS, 1000, 40.0)
mapper.observe_traffic("api", "users", Protocol.HTTP, 800, 30.0)
mapper.observe_traffic("api", "orders", Protocol.HTTP, 1200, 45.0)
mapper.observe_traffic("users", "db", Protocol.TCP, 2000, 15.0)
mapper.observe_traffic("orders", "db", Protocol.TCP, 2500, 20.0)

# Generate DOT graph
dot_graph = mapper.generate_dot_graph(include_stats=True)
print(dot_graph)

# Save to file for Graphviz
with open("topology.dot", "w") as f:
    f.write(dot_graph)

# Then use: dot -Tpng topology.dot -o topology.png
```

### Taking Snapshots

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Build initial topology
mapper.observe_traffic("web", "api", Protocol.HTTP)
mapper.observe_traffic("api", "db", Protocol.TCP)

# Take snapshot
snapshot1 = mapper.take_snapshot()
print(f"Snapshot 1: {snapshot1['summary']['total_services']} services")

# Add more traffic
mapper.observe_traffic("web", "cache", Protocol.TCP)
mapper.observe_traffic("api", "search", Protocol.GRPC)

# Take another snapshot
snapshot2 = mapper.take_snapshot()
print(f"Snapshot 2: {snapshot2['summary']['total_services']} services")
```

### Detecting Topology Changes

```python
from TopoMapper import create_mapper, Protocol
import time

mapper = create_mapper()

# Build initial topology
mapper.observe_traffic("api", "service-a", Protocol.HTTP)
mapper.observe_traffic("api", "service-b", Protocol.HTTP)

# Take first snapshot
snapshot1 = mapper.take_snapshot()
time.sleep(1)

# Make changes
mapper.observe_traffic("api", "service-c", Protocol.HTTP)  # New service
mapper.observe_traffic("service-a", "database", Protocol.TCP)  # New connection

# Detect changes
changes = mapper.detect_changes(snapshot1)
print("Changes detected:")
print(f"  New services: {changes['new_services']}")
print(f"  New connections: {changes['new_connections']}")
print(f"  Status changes: {changes['status_changes']}")
```

### Getting Topology Summary

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Build complex topology
services = ["api", "auth", "users", "orders", "payments", "inventory", "db", "cache"]
for i in range(100):
    source = services[i % len(services)]
    dest = services[(i + 1) % len(services)]
    mapper.observe_traffic(source, dest, Protocol.HTTP, 1000, 50.0)

# Get summary
summary = mapper.get_topology_summary()
print("Topology Summary:")
print(f"  Total Services: {summary['total_services']}")
print(f"  Total Connections: {summary['total_connections']}")
print(f"  Total Requests: {summary['total_requests']}")
print(f"  Overall Error Rate: {summary['overall_error_rate']:.2%}")
print(f"  Healthy Services: {summary['healthy_services']}")
print(f"  Entry Points: {', '.join(summary['entry_points'])}")
print(f"  Leaf Services: {', '.join(summary['leaf_services'])}")
print(f"  Critical Services: {', '.join(summary['critical_services'])}")
```

### Export and Import

```python
from TopoMapper import create_mapper, Protocol

# Create and populate mapper
mapper = create_mapper()
mapper.observe_traffic("web", "api", Protocol.HTTPS, 1024, 50.0)
mapper.observe_traffic("api", "db", Protocol.TCP, 2048, 25.0)

# Export to JSON
mapper.export_to_json("topology.json")
print("Topology exported to topology.json")

# Import in another session
new_mapper = create_mapper()
new_mapper.import_from_json("topology.json")
print(f"Loaded {len(new_mapper.get_all_services())} services")
```

### Including IP and Port Information

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Observe traffic with network details
mapper.observe_traffic(
    source="web-server",
    destination="api-gateway",
    protocol=Protocol.HTTPS,
    bytes_transferred=1500,
    latency_ms=45.0,
    source_ip="192.168.1.10",
    source_port=54321,
    dest_ip="10.0.0.5",
    dest_port=443
)

# Check service details
service = mapper.get_service("api-gateway")
print(f"Service: {service.name}")
print(f"  IPs: {', '.join(service.ip_addresses)}")
print(f"  Ports: {', '.join(str(p) for p in service.ports)}")
```

### Monitoring Service Dependencies

```python
from TopoMapper import create_mapper, Protocol

mapper = create_mapper()

# Build topology
mapper.observe_traffic("frontend", "api", Protocol.HTTPS)
mapper.observe_traffic("api", "auth", Protocol.GRPC)
mapper.observe_traffic("api", "users", Protocol.HTTP)
mapper.observe_traffic("users", "database", Protocol.TCP)

# Get dependencies for a specific service
deps = mapper.get_service_dependencies("api")
print("API Service Dependencies:")
print(f"  Depends on: {', '.join(deps['depends_on'])}")
print(f"  Depended by: {', '.join(deps['depended_by'])}")
```

## Testing

Run the test suite:

```bash
python test_TopoMapper.py
```

## Implementation Notes

- **Thread-safe**: All operations use locks for concurrent access
- **Real-time mapping**: Services and connections discovered as traffic is observed
- **Automatic health scoring**: Based on error rates
- **Snapshot history**: Maintains history of topology snapshots
- **No external dependencies**: Pure Python standard library

## API Reference

### TopologyMapper

**Methods:**
- `observe_traffic(source, destination, ...)` - Record traffic between services
- `get_service(name)` - Get service by name
- `get_all_services()` - Get all services
- `get_connection(source, destination)` - Get connection
- `get_all_connections()` - Get all connections
- `get_service_dependencies(service_name)` - Get service dependencies
- `get_dependency_graph()` - Get full dependency graph
- `find_entry_points()` - Find entry point services
- `find_leaf_services()` - Find leaf services
- `find_critical_services(min_dependents)` - Find critical services
- `detect_circular_dependencies()` - Detect circular dependencies
- `generate_dot_graph(include_stats)` - Generate DOT graph
- `generate_text_topology()` - Generate text visualization
- `get_topology_summary()` - Get topology summary
- `take_snapshot()` - Take topology snapshot
- `detect_changes(previous_snapshot)` - Detect changes
- `export_to_json(filename)` - Export to JSON
- `import_from_json(filename)` - Import from JSON
- `clear()` - Clear all data

### Service

**Attributes:**
- `name` - Service name
- `ip_addresses` - Set of IP addresses
- `ports` - Set of ports
- `protocols` - Set of protocols used
- `incoming_connections` - Count of incoming connections
- `outgoing_connections` - Count of outgoing connections
- `total_requests_received` - Total requests received
- `total_requests_sent` - Total requests sent
- `total_errors` - Total errors

**Methods:**
- `get_status()` - Get health status

### Connection

**Attributes:**
- `source` - Source service
- `destination` - Destination service
- `protocol` - Communication protocol
- `request_count` - Total requests
- `error_count` - Total errors
- `total_bytes` - Total bytes transferred
- `avg_latency_ms` - Average latency

**Methods:**
- `add_request(bytes, latency, is_error)` - Record request
- `get_error_rate()` - Get error rate

## Use Cases

### Microservice Discovery

Automatically discover all microservices in your environment by observing traffic:

```python
# Continuously observe traffic
for traffic_event in traffic_stream:
    mapper.observe_traffic(
        traffic_event.source,
        traffic_event.destination,
        traffic_event.protocol
    )

# Periodically check discovered services
services = mapper.get_all_services()
```

### Architecture Validation

Validate that your actual architecture matches the intended design:

```python
# Build expected topology
expected_deps = {
    "api-gateway": ["auth", "users", "orders"],
    "users": ["database"],
    "orders": ["database", "payments"]
}

# Compare with actual
actual_deps = mapper.get_dependency_graph()
for service, expected in expected_deps.items():
    actual = actual_deps.get(service, set())
    if set(expected) != actual:
        print(f"Mismatch in {service}: expected {expected}, got {actual}")
```

### Dependency Impact Analysis

Understand the impact of service failures:

```python
critical_services = mapper.find_critical_services(min_dependents=3)
print("Services with high impact if they fail:")
for service, count in critical_services:
    print(f"  {service}: affects {count} services")
```

### Performance Monitoring

Track service communication performance:

```python
connections = mapper.get_all_connections()
slow_connections = [
    c for c in connections 
    if c.avg_latency_ms > 100
]
print("Slow connections:")
for conn in slow_connections:
    print(f"  {conn.source} -> {conn.destination}: {conn.avg_latency_ms:.1f}ms")
```

## Differences from Full APM Solutions

- **No agent required**: Observes external traffic only
- **Manual instrumentation**: Traffic must be explicitly observed
- **No distributed tracing**: Connection-level only, not request-level
- **Simplified protocol detection**: Limited protocol identification
- **No real-time streaming**: Batch observation model

## Tips

1. **Regular snapshots**: Take periodic snapshots to track changes
2. **Monitor critical services**: Keep eye on services with many dependents
3. **Check for cycles**: Circular dependencies can cause issues
4. **Export regularly**: Save topology data for historical analysis
5. **Use DOT graphs**: Visualize with Graphviz for better understanding
