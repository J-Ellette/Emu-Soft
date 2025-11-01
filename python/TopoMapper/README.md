# TopoMapper - Application Topology Mapper from Actual Traffic

A pure Python implementation of an application topology mapper that discovers and visualizes service architecture by analyzing actual network traffic, without external dependencies.

## What This Provides

**Purpose:** Automatically discover and map application topology from real network traffic
**Use Case:** Understanding microservice architectures, dependency mapping, and traffic analysis

## Features

- **Automatic Service Discovery** from network traffic
- **Dependency Mapping** between services with metrics
- **Protocol Detection** (HTTP, HTTPS, gRPC, TCP, UDP, WebSocket)
- **Health Monitoring** with automatic status detection
- **Traffic Pattern Analysis** with endpoint tracking
- **Topology Visualization** data generation
- **Critical Service Detection** identifying key dependencies
- **Entry Point & Leaf Service** identification
- **Real-time Updates** as traffic flows
- **Thread-safe** concurrent ingestion

## Core Components

- **TopoMapper.py**: Main implementation
  - `TopoMapper`: Main topology mapper class
  - `NetworkConnection`: Represents network connection
  - `Service`: Discovered service with metrics
  - `ServiceDependency`: Dependency between services
  - `Protocol`: Network protocol enumeration
  - `ServiceStatus`: Health status enumeration
  - `TopologyNode` / `TopologyEdge`: Visualization data structures

## Usage

### Basic Connection Ingestion

```python
from TopoMapper import TopoMapper

# Initialize mapper
mapper = TopoMapper(service_timeout_seconds=300)

# Ingest a network connection
connection_data = {
    'source_host': 'api-gateway',
    'source_port': 8080,
    'destination_host': 'user-service',
    'destination_port': 3000,
    'protocol': 'http',
    'bytes_sent': 1024,
    'bytes_received': 2048,
    'status_code': 200,
    'method': 'GET',
    'path': '/api/users',
    'duration_ms': 45.5
}

key = mapper.ingest_connection(connection_data)
print(f"Ingested connection: {key}")
```

### Service Discovery

```python
from TopoMapper import TopoMapper

mapper = TopoMapper()

# Ingest multiple connections
connections = [
    {
        'source_host': 'client-app',
        'source_port': 50000,
        'destination_host': 'api-gateway',
        'destination_port': 8080,
        'protocol': 'http'
    },
    {
        'source_host': 'api-gateway',
        'source_port': 8080,
        'destination_host': 'user-service',
        'destination_port': 3000,
        'protocol': 'http'
    },
    {
        'source_host': 'user-service',
        'source_port': 3000,
        'destination_host': 'postgres-db',
        'destination_port': 5432,
        'protocol': 'tcp'
    }
]

for conn in connections:
    mapper.ingest_connection(conn)

# Get discovered services
services = mapper.get_services()
print(f"Discovered {len(services)} services:")
for service in services:
    print(f"  - {service.name} ({service.host}:{service.port}) [{service.protocol.value}]")
    print(f"    Status: {service.status.value}")
    print(f"    Requests: {service.total_requests}")
    print(f"    Error Rate: {service.get_error_rate():.2%}")
```

### Service Naming

```python
from TopoMapper import TopoMapper

mapper = TopoMapper()

# Register known service names
mapper.register_service_name('10.0.0.1', 8080, 'api-gateway')
mapper.register_service_name('10.0.0.2', 3000, 'user-service')
mapper.register_service_name('10.0.0.3', 5432, 'main-database')

# Now connections will use these names
connection = {
    'source_host': '10.0.0.1',
    'source_port': 8080,
    'destination_host': '10.0.0.2',
    'destination_port': 3000,
    'protocol': 'http'
}

mapper.ingest_connection(connection)

# Retrieve by registered name
service = mapper.get_service('api-gateway')
print(f"Service: {service.name}")
```

### Dependency Mapping

```python
from TopoMapper import TopoMapper

mapper = TopoMapper()

# Simulate traffic flow
for i in range(100):
    mapper.ingest_connection({
        'source_host': 'api',
        'source_port': 8080,
        'destination_host': 'backend',
        'destination_port': 9000,
        'protocol': 'http',
        'status_code': 500 if i < 5 else 200,
        'duration_ms': 50.0 + i % 10,
        'path': f'/api/endpoint{i % 3}'
    })

# Get dependencies
dependencies = mapper.get_dependencies()
for dep in dependencies:
    print(f"\n{dep.from_service} -> {dep.to_service}")
    print(f"  Protocol: {dep.protocol.value}")
    print(f"  Requests: {dep.total_requests}")
    print(f"  Errors: {dep.total_errors}")
    print(f"  Error Rate: {dep.get_error_rate():.2%}")
    print(f"  Avg Latency: {dep.average_latency_ms:.2f}ms")
    print(f"  Endpoints: {', '.join(list(dep.endpoints_used)[:5])}")
```

### Topology Graph

```python
from TopoMapper import TopoMapper

mapper = TopoMapper()

# Build topology through traffic
# ... ingest connections ...

# Get topology graph
graph = mapper.get_topology_graph()

print("Topology Graph:")
for service, downstream_services in graph.items():
    print(f"{service} calls:")
    for downstream in downstream_services:
        print(f"  -> {downstream}")
```

### Finding Key Services

```python
from TopoMapper import TopoMapper

mapper = TopoMapper()

# ... ingest connections ...

# Find entry points (services receiving external traffic)
entry_points = mapper.find_entry_points()
print("Entry Point Services:")
for service in entry_points:
    print(f"  - {service}")

# Find leaf services (databases, external APIs, etc.)
leaf_services = mapper.find_leaf_services()
print("\nLeaf Services:")
for service in leaf_services:
    print(f"  - {service}")

# Find critical services (many dependents)
critical = mapper.find_critical_services(min_dependents=2)
print("\nCritical Services:")
for crit in critical:
    print(f"  - {crit['service']}")
    print(f"    Dependents: {crit['dependent_count']}")
    print(f"    Status: {crit['status']}")
    print(f"    Error Rate: {crit['error_rate']:.2%}")
```

### Health Monitoring

```python
from TopoMapper import TopoMapper

mapper = TopoMapper()

# Simulate healthy and unhealthy services
for i in range(100):
    # Healthy service
    mapper.ingest_connection({
        'source_host': 'client',
        'source_port': 5000,
        'destination_host': 'healthy-api',
        'destination_port': 8000,
        'protocol': 'http',
        'status_code': 200
    })
    
    # Unhealthy service (10% errors)
    mapper.ingest_connection({
        'source_host': 'client',
        'source_port': 5000,
        'destination_host': 'unhealthy-api',
        'destination_port': 8001,
        'protocol': 'http',
        'status_code': 500 if i < 10 else 200
    })

# Get health summary
health = mapper.get_service_health_summary()
print("Service Health Summary:")
for status, count in health.items():
    print(f"  {status}: {count} services")

# Check individual service
service = mapper.get_service('unhealthy-api:8001')
if service:
    print(f"\n{service.name}:")
    print(f"  Status: {service.status.value}")
    print(f"  Error Rate: {service.get_error_rate():.2%}")
```

### Traffic Analysis

```python
from TopoMapper import TopoMapper

mapper = TopoMapper()

# Ingest diverse traffic
protocols = ['http', 'tcp', 'grpc']
endpoints = ['/api/users', '/api/orders', '/api/products']

for i in range(150):
    mapper.ingest_connection({
        'source_host': 'client',
        'source_port': 5000,
        'destination_host': 'api',
        'destination_port': 8080,
        'protocol': protocols[i % 3],
        'path': endpoints[i % 3] if i % 3 == 0 else None
    })

# Analyze patterns
patterns = mapper.analyze_traffic_patterns()

print(f"Total Connections: {patterns['total_connections']}")

print("\nProtocol Distribution:")
for protocol, count in patterns['protocols'].items():
    print(f"  {protocol}: {count}")

print("\nTop Endpoints:")
for endpoint_info in patterns['top_endpoints']:
    print(f"  {endpoint_info['path']}: {endpoint_info['count']} requests")

print("\nTraffic Over Time:")
for bucket, count in patterns['traffic_over_time'].items():
    print(f"  Minute {bucket}: {count} connections")
```

### Visualization Data

```python
from TopoMapper import TopoMapper
import json

mapper = TopoMapper()

# ... ingest connections ...

# Get visualization data
viz = mapper.get_topology_visualization()

print(f"Nodes: {len(viz['nodes'])}")
print(f"Edges: {len(viz['edges'])}")

# Export to JSON for visualization tools
with open('topology.json', 'w') as f:
    json.dump(viz, f, indent=2)

# Access nodes
for node in viz['nodes']:
    print(f"\nNode: {node['id']}")
    print(f"  Host: {node['host']}:{node['port']}")
    print(f"  Status: {node['status']}")
    print(f"  Requests: {node['metadata']['total_requests']}")

# Access edges
for edge in viz['edges']:
    print(f"\nEdge: {edge['from']} -> {edge['to']}")
    print(f"  Requests: {edge['requests']}")
    print(f"  Latency: {edge['latency_ms']:.2f}ms")
    print(f"  Error Rate: {edge['error_rate']:.2%}")
```

### Complete Export

```python
from TopoMapper import TopoMapper
import json

mapper = TopoMapper()

# ... build topology from traffic ...

# Export everything
topology = mapper.export_topology()

# Save to file
with open('complete_topology.json', 'w') as f:
    json.dump(topology, f, indent=2)

# Access exported data
print(f"Services: {len(topology['services'])}")
print(f"Dependencies: {len(topology['dependencies'])}")
print(f"Entry Points: {topology['entry_points']}")
print(f"Leaf Services: {topology['leaf_services']}")
print(f"Critical Services: {len(topology['critical_services'])}")

# Traffic patterns
patterns = topology['traffic_patterns']
print(f"\nTotal Connections: {patterns['total_connections']}")
print(f"Protocols: {patterns['protocols']}")
```

### Cleanup and Maintenance

```python
from TopoMapper import TopoMapper

# Set short timeout for demo
mapper = TopoMapper(service_timeout_seconds=60)

# ... ingest connections ...

# Remove inactive services
removed = mapper.cleanup_inactive_services()
print(f"Removed {removed} inactive services")

# Clear all data
mapper.clear()
print("All topology data cleared")
```

## Testing

Run the test suite:

```bash
cd python/TopoMapper
python test_TopoMapper.py
```

Or run specific test classes:

```bash
python test_TopoMapper.py TestBasicFunctionality
python test_TopoMapper.py TestDependencyMapping
python test_TopoMapper.py TestTopologyAnalysis
```

## Implementation Notes

- **Thread-safe**: All operations use locks for concurrent access
- **Real-time Discovery**: Services discovered as traffic flows
- **Automatic Naming**: Smart service naming based on ports and patterns
- **Health Tracking**: Automatic health status based on error rates
- **Flexible Protocols**: Supports multiple network protocols
- **Memory Efficient**: Configurable timeout for inactive services

## API Reference

### TopoMapper Class

**Constructor:**
```python
TopoMapper(service_timeout_seconds: int = 300)
```

**Methods:**
- `register_service_name(host, port, name)`: Register known service name
- `ingest_connection(connection_data)`: Ingest network connection
- `get_services() -> List[Service]`: Get all discovered services
- `get_service(service_name) -> Optional[Service]`: Get specific service
- `get_dependencies() -> List[ServiceDependency]`: Get all dependencies
- `get_topology_graph() -> Dict`: Get topology as graph
- `get_topology_visualization() -> Dict`: Get visualization data
- `find_entry_points() -> List[str]`: Find entry point services
- `find_leaf_services() -> List[str]`: Find leaf services
- `find_critical_services(min_dependents) -> List[Dict]`: Find critical services
- `analyze_traffic_patterns() -> Dict`: Analyze traffic patterns
- `get_service_health_summary() -> Dict`: Get health summary
- `cleanup_inactive_services() -> int`: Remove inactive services
- `export_topology() -> Dict`: Export complete topology
- `clear()`: Clear all data

### Connection Data Format

```python
{
    'source_host': str,          # Required
    'source_port': int,          # Required
    'destination_host': str,     # Required
    'destination_port': int,     # Required
    'protocol': str,             # Required (http, https, grpc, tcp, udp, websocket)
    'timestamp': float,          # Optional (default: current time)
    'bytes_sent': int,           # Optional
    'bytes_received': int,       # Optional
    'status_code': int,          # Optional (for HTTP-like protocols)
    'method': str,               # Optional (GET, POST, etc.)
    'path': str,                 # Optional (endpoint path)
    'duration_ms': float         # Optional (request duration)
}
```

## Example Use Cases

### Microservice Architecture Discovery

```python
from TopoMapper import TopoMapper

mapper = TopoMapper()

def capture_request(request, response):
    """Capture HTTP request/response"""
    mapper.ingest_connection({
        'source_host': request.client_host,
        'source_port': request.client_port,
        'destination_host': request.server_host,
        'destination_port': request.server_port,
        'protocol': 'http',
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
        'duration_ms': response.duration_ms,
        'bytes_sent': len(request.body),
        'bytes_received': len(response.body)
    })

# After capturing traffic, analyze
print("\n=== Discovered Architecture ===")

# Show all services
services = mapper.get_services()
print(f"\nServices ({len(services)}):")
for service in services:
    print(f"  {service.name}: {service.total_requests} requests")

# Show dependencies
graph = mapper.get_topology_graph()
print(f"\nDependencies:")
for service, deps in graph.items():
    if deps:
        print(f"  {service} -> {', '.join(deps)}")

# Identify critical services
critical = mapper.find_critical_services()
if critical:
    print(f"\nCritical Services:")
    for c in critical:
        print(f"  {c['service']} ({c['dependent_count']} dependents)")
```

### Real-Time Monitoring Dashboard

```python
from TopoMapper import TopoMapper
import time

mapper = TopoMapper()

def monitoring_dashboard():
    """Display real-time topology monitoring"""
    while True:
        # ... connections are ingested continuously ...
        
        print("\033[2J\033[H")  # Clear screen
        print("=== Application Topology Monitor ===\n")
        
        # Service health
        health = mapper.get_service_health_summary()
        print("Service Health:")
        for status, count in health.items():
            print(f"  {status.upper()}: {count}")
        
        # Critical services
        critical = mapper.find_critical_services(min_dependents=2)
        print(f"\nCritical Services: {len(critical)}")
        for c in critical[:5]:
            print(f"  {c['service']}: {c['dependent_count']} deps, "
                  f"{c['error_rate']:.1%} errors")
        
        # Traffic
        patterns = mapper.analyze_traffic_patterns()
        print(f"\nTotal Traffic: {patterns['total_connections']} connections")
        
        time.sleep(5)

# Run dashboard
monitoring_dashboard()
```

### Service Dependency Audit

```python
from TopoMapper import TopoMapper

mapper = TopoMapper()

# ... collect traffic data ...

def audit_dependencies():
    """Audit service dependencies"""
    print("=== Dependency Audit Report ===\n")
    
    dependencies = mapper.get_dependencies()
    
    # Group by source service
    by_service = {}
    for dep in dependencies:
        if dep.from_service not in by_service:
            by_service[dep.from_service] = []
        by_service[dep.from_service].append(dep)
    
    # Report
    for service, deps in sorted(by_service.items()):
        print(f"\n{service} Dependencies:")
        for dep in sorted(deps, key=lambda d: d.total_requests, reverse=True):
            print(f"  -> {dep.to_service}")
            print(f"     Requests: {dep.total_requests:,}")
            print(f"     Latency: {dep.average_latency_ms:.1f}ms")
            print(f"     Errors: {dep.get_error_rate():.2%}")
            if dep.endpoints_used:
                endpoints = list(dep.endpoints_used)[:3]
                print(f"     Endpoints: {', '.join(endpoints)}")

audit_dependencies()
```

### Architecture Visualization Export

```python
from TopoMapper import TopoMapper
import json

mapper = TopoMapper()

# ... collect traffic ...

def export_for_visualization():
    """Export topology for visualization tools"""
    viz = mapper.get_topology_visualization()
    
    # Export for D3.js force-directed graph
    d3_data = {
        'nodes': [
            {
                'id': node['id'],
                'label': f"{node['host']}:{node['port']}",
                'status': node['status'],
                'size': node['metadata']['total_requests']
            }
            for node in viz['nodes']
        ],
        'links': [
            {
                'source': edge['from'],
                'target': edge['to'],
                'value': edge['requests'],
                'color': 'red' if edge['error_rate'] > 0.05 else 'green'
            }
            for edge in viz['edges']
        ]
    }
    
    with open('topology_d3.json', 'w') as f:
        json.dump(d3_data, f, indent=2)
    
    print("Exported topology for D3.js visualization")

export_for_visualization()
```

## Performance Considerations

- **Memory**: Stores all connections; configure timeout appropriately
- **Thread Safety**: Concurrent ingestion supported
- **Service Timeout**: Balance between persistence and memory usage
- **Connection Volume**: Efficient for moderate to high traffic volumes
- **Cleanup**: Regular cleanup recommended for long-running applications

## Best Practices

1. **Register service names**: Use `register_service_name()` for known services
2. **Include timing data**: Provide `duration_ms` for latency analysis
3. **Include status codes**: Enable health monitoring with status codes
4. **Track endpoints**: Provide `path` for endpoint discovery
5. **Regular cleanup**: Call `cleanup_inactive_services()` periodically
6. **Export topology**: Export and archive topology snapshots
7. **Monitor critical services**: Pay attention to services with many dependents
8. **Analyze patterns**: Use traffic pattern analysis for optimization

## License

This implementation is part of the Emu-Soft project and is original code written from scratch.
