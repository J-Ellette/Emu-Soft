"""
Developed by PowerShield, as an application topology mapper

TopoMapper - Application Topology Mapper from Actual Traffic

This module analyzes actual network traffic and service interactions to
automatically build and visualize application topology maps.

Features:
- Service discovery from traffic patterns
- Dependency graph construction
- Communication protocol detection
- Traffic flow analysis
- Service health scoring
- Topology visualization (text and DOT format)
- Change detection and versioning
- Export to various formats (JSON, DOT, text)

Note: This is a pure Python implementation using only standard library.
"""

import json
import time
import threading
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


class Protocol(Enum):
    """Communication protocols"""
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    GRPC = "gRPC"
    WEBSOCKET = "WebSocket"
    TCP = "TCP"
    UDP = "UDP"
    UNKNOWN = "Unknown"


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "Healthy"
    DEGRADED = "Degraded"
    UNHEALTHY = "Unhealthy"
    UNKNOWN = "Unknown"


@dataclass
class Connection:
    """Represents a connection between two services"""
    source: str
    destination: str
    protocol: Protocol
    request_count: int = 0
    error_count: int = 0
    total_bytes: int = 0
    avg_latency_ms: float = 0.0
    latencies: List[float] = field(default_factory=list)
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    
    def add_request(self, bytes_transferred: int, latency_ms: float, is_error: bool = False):
        """Record a request on this connection"""
        self.request_count += 1
        if is_error:
            self.error_count += 1
        self.total_bytes += bytes_transferred
        self.latencies.append(latency_ms)
        
        # Update average latency
        self.avg_latency_ms = sum(self.latencies) / len(self.latencies)
        self.last_seen = time.time()
    
    def get_error_rate(self) -> float:
        """Calculate error rate"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'source': self.source,
            'destination': self.destination,
            'protocol': self.protocol.value,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.get_error_rate(),
            'total_bytes': self.total_bytes,
            'avg_latency_ms': self.avg_latency_ms,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen
        }


@dataclass
class Service:
    """Represents a service in the topology"""
    name: str
    ip_addresses: Set[str] = field(default_factory=set)
    ports: Set[int] = field(default_factory=set)
    protocols: Set[Protocol] = field(default_factory=set)
    incoming_connections: int = 0
    outgoing_connections: int = 0
    total_requests_received: int = 0
    total_requests_sent: int = 0
    total_errors: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_status(self) -> ServiceStatus:
        """Determine service health status"""
        if self.total_requests_received == 0:
            return ServiceStatus.UNKNOWN
        
        error_rate = self.total_errors / self.total_requests_received
        
        if error_rate == 0:
            return ServiceStatus.HEALTHY
        elif error_rate < 0.05:  # Less than 5% errors
            return ServiceStatus.HEALTHY
        elif error_rate < 0.20:  # 5-20% errors
            return ServiceStatus.DEGRADED
        else:
            return ServiceStatus.UNHEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'ip_addresses': list(self.ip_addresses),
            'ports': list(self.ports),
            'protocols': [p.value for p in self.protocols],
            'incoming_connections': self.incoming_connections,
            'outgoing_connections': self.outgoing_connections,
            'total_requests_received': self.total_requests_received,
            'total_requests_sent': self.total_requests_sent,
            'total_errors': self.total_errors,
            'status': self.get_status().value,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'metadata': self.metadata
        }


class TopologyMapper:
    """Maps application topology from network traffic"""
    
    def __init__(self):
        """Initialize the topology mapper"""
        self.services: Dict[str, Service] = {}
        self.connections: Dict[Tuple[str, str], Connection] = {}
        self.lock = threading.Lock()
        self.snapshot_history: List[Dict[str, Any]] = []
    
    def observe_traffic(
        self,
        source: str,
        destination: str,
        protocol: Protocol = Protocol.UNKNOWN,
        bytes_transferred: int = 0,
        latency_ms: float = 0.0,
        is_error: bool = False,
        source_ip: Optional[str] = None,
        source_port: Optional[int] = None,
        dest_ip: Optional[str] = None,
        dest_port: Optional[int] = None
    ):
        """Observe a traffic flow between services"""
        with self.lock:
            # Ensure services exist
            if source not in self.services:
                self.services[source] = Service(name=source)
            if destination not in self.services:
                self.services[destination] = Service(name=destination)
            
            source_service = self.services[source]
            dest_service = self.services[destination]
            
            # Update service information
            source_service.total_requests_sent += 1
            dest_service.total_requests_received += 1
            
            if is_error:
                dest_service.total_errors += 1
            
            if source_ip:
                source_service.ip_addresses.add(source_ip)
            if source_port:
                source_service.ports.add(source_port)
            if dest_ip:
                dest_service.ip_addresses.add(dest_ip)
            if dest_port:
                dest_service.ports.add(dest_port)
            
            source_service.protocols.add(protocol)
            dest_service.protocols.add(protocol)
            source_service.last_seen = time.time()
            dest_service.last_seen = time.time()
            
            # Get or create connection
            conn_key = (source, destination)
            if conn_key not in self.connections:
                self.connections[conn_key] = Connection(
                    source=source,
                    destination=destination,
                    protocol=protocol
                )
                source_service.outgoing_connections += 1
                dest_service.incoming_connections += 1
            
            connection = self.connections[conn_key]
            connection.add_request(bytes_transferred, latency_ms, is_error)
    
    def get_service(self, name: str) -> Optional[Service]:
        """Get a service by name"""
        with self.lock:
            return self.services.get(name)
    
    def get_all_services(self) -> List[Service]:
        """Get all discovered services"""
        with self.lock:
            return list(self.services.values())
    
    def get_connection(self, source: str, destination: str) -> Optional[Connection]:
        """Get a connection between two services"""
        with self.lock:
            return self.connections.get((source, destination))
    
    def get_all_connections(self) -> List[Connection]:
        """Get all connections"""
        with self.lock:
            return list(self.connections.values())
    
    def get_service_dependencies(self, service_name: str) -> Dict[str, List[str]]:
        """Get dependencies for a specific service"""
        with self.lock:
            dependencies = {
                'depends_on': [],  # Services this service calls
                'depended_by': []  # Services that call this service
            }
            
            for (source, dest), conn in self.connections.items():
                if source == service_name:
                    dependencies['depends_on'].append(dest)
                elif dest == service_name:
                    dependencies['depended_by'].append(source)
            
            return dependencies
    
    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """Get the full dependency graph"""
        with self.lock:
            graph = defaultdict(set)
            for source, dest in self.connections.keys():
                graph[source].add(dest)
            return dict(graph)
    
    def find_entry_points(self) -> List[str]:
        """Find services that are likely entry points (no incoming from other services)"""
        with self.lock:
            return self._find_entry_points_unlocked()
    
    def _find_entry_points_unlocked(self) -> List[str]:
        """Internal method to find entry points without locking"""
        all_services = set(self.services.keys())
        services_with_incoming = set()
        
        for source, dest in self.connections.keys():
            services_with_incoming.add(dest)
        
        # Entry points have no incoming connections
        entry_points = all_services - services_with_incoming
        return list(entry_points)
    
    def find_leaf_services(self) -> List[str]:
        """Find leaf services (no outgoing connections)"""
        with self.lock:
            return self._find_leaf_services_unlocked()
    
    def _find_leaf_services_unlocked(self) -> List[str]:
        """Internal method to find leaf services without locking"""
        all_services = set(self.services.keys())
        services_with_outgoing = set()
        
        for source, dest in self.connections.keys():
            services_with_outgoing.add(source)
        
        # Leaf services have no outgoing connections
        leaf_services = all_services - services_with_outgoing
        return list(leaf_services)
    
    def find_critical_services(self, min_dependents: int = 2) -> List[Tuple[str, int]]:
        """Find critical services (many other services depend on them)"""
        with self.lock:
            return self._find_critical_services_unlocked(min_dependents)
    
    def _find_critical_services_unlocked(self, min_dependents: int = 2) -> List[Tuple[str, int]]:
        """Internal method to find critical services without locking"""
        dependent_counts = defaultdict(int)
        
        for source, dest in self.connections.keys():
            dependent_counts[dest] += 1
        
        critical = [
            (service, count) 
            for service, count in dependent_counts.items()
            if count >= min_dependents
        ]
        
        critical.sort(key=lambda x: x[1], reverse=True)
        return critical
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the topology"""
        # Get graph outside of recursive calls to avoid issues
        graph = self.get_dependency_graph()
        cycles = []
        visited = set()
        rec_stack = []
        
        def dfs(node: str) -> bool:
            """DFS to detect cycles. Returns True if cycle found."""
            if node in rec_stack:
                # Found a cycle
                cycle_start = rec_stack.index(node)
                cycle = rec_stack[cycle_start:] + [node]
                # Avoid duplicate cycles
                if cycle not in cycles and list(reversed(cycle)) not in cycles:
                    cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.append(node)
            
            if node in graph:
                for neighbor in graph[node]:
                    dfs(neighbor)
            
            rec_stack.pop()
            return False
        
        with self.lock:
            for service in self.services.keys():
                if service not in visited:
                    dfs(service)
        
        return cycles
    
    def generate_dot_graph(self, include_stats: bool = True) -> str:
        """Generate a DOT format graph for Graphviz visualization"""
        with self.lock:
            lines = []
            lines.append("digraph topology {")
            lines.append("  rankdir=LR;")
            lines.append("  node [shape=box, style=rounded];")
            lines.append("")
            
            # Add nodes (services)
            for service_name, service in self.services.items():
                status = service.get_status()
                color = {
                    ServiceStatus.HEALTHY: "green",
                    ServiceStatus.DEGRADED: "yellow",
                    ServiceStatus.UNHEALTHY: "red",
                    ServiceStatus.UNKNOWN: "gray"
                }.get(status, "gray")
                
                label = service_name
                if include_stats:
                    label += f"\\n{service.total_requests_received} reqs"
                    label += f"\\nStatus: {status.value}"
                
                lines.append(f'  "{service_name}" [color={color}, label="{label}"];')
            
            lines.append("")
            
            # Add edges (connections)
            for (source, dest), conn in self.connections.items():
                label = f"{conn.request_count} reqs"
                if include_stats:
                    label += f"\\n{conn.protocol.value}"
                    label += f"\\n{conn.avg_latency_ms:.1f}ms avg"
                    if conn.error_count > 0:
                        label += f"\\n{conn.error_count} errors"
                
                # Color edge based on error rate
                error_rate = conn.get_error_rate()
                edge_color = "green" if error_rate == 0 else ("orange" if error_rate < 0.1 else "red")
                
                lines.append(f'  "{source}" -> "{dest}" [label="{label}", color={edge_color}];')
            
            lines.append("}")
            return "\n".join(lines)
    
    def generate_text_topology(self) -> str:
        """Generate a text-based topology visualization"""
        with self.lock:
            lines = []
            lines.append("=" * 80)
            lines.append("Application Topology Map")
            lines.append("=" * 80)
            lines.append("")
            
            # Services
            lines.append("Services:")
            lines.append("-" * 80)
            for service in sorted(self.services.values(), key=lambda s: s.name):
                status = service.get_status()
                lines.append(f"  {service.name} [{status.value}]")
                lines.append(f"    Requests: {service.total_requests_received} in, {service.total_requests_sent} out")
                lines.append(f"    Connections: {service.incoming_connections} in, {service.outgoing_connections} out")
                if service.protocols:
                    protocols = ", ".join(p.value for p in service.protocols)
                    lines.append(f"    Protocols: {protocols}")
                lines.append("")
            
            # Connections
            lines.append("Connections:")
            lines.append("-" * 80)
            for conn in sorted(self.connections.values(), key=lambda c: c.request_count, reverse=True):
                lines.append(f"  {conn.source} -> {conn.destination}")
                lines.append(f"    Protocol: {conn.protocol.value}")
                lines.append(f"    Requests: {conn.request_count}")
                lines.append(f"    Errors: {conn.error_count} ({conn.get_error_rate():.1%})")
                lines.append(f"    Avg Latency: {conn.avg_latency_ms:.2f}ms")
                lines.append(f"    Total Bytes: {conn.total_bytes}")
                lines.append("")
            
            lines.append("=" * 80)
            return "\n".join(lines)
    
    def get_topology_summary(self) -> Dict[str, Any]:
        """Get a summary of the topology"""
        # Get circular dependencies first (it needs to call get_dependency_graph)
        circular_deps = self.detect_circular_dependencies()
        
        with self.lock:
            entry_points = self._find_entry_points_unlocked()
            leaf_services = self._find_leaf_services_unlocked()
            critical_services = self._find_critical_services_unlocked(min_dependents=2)
            
            total_requests = sum(s.total_requests_received for s in self.services.values())
            total_errors = sum(s.total_errors for s in self.services.values())
            
            healthy_services = sum(1 for s in self.services.values() if s.get_status() == ServiceStatus.HEALTHY)
            
            return {
                'total_services': len(self.services),
                'total_connections': len(self.connections),
                'total_requests': total_requests,
                'total_errors': total_errors,
                'overall_error_rate': total_errors / total_requests if total_requests > 0 else 0.0,
                'healthy_services': healthy_services,
                'entry_points': entry_points,
                'leaf_services': leaf_services,
                'critical_services': [name for name, _ in critical_services[:5]],
                'circular_dependencies_count': len(circular_deps),
                'has_circular_dependencies': len(circular_deps) > 0
            }
    
    def take_snapshot(self) -> Dict[str, Any]:
        """Take a snapshot of the current topology"""
        # Get summary first (needs lock)
        summary = self.get_topology_summary()
        
        with self.lock:
            snapshot = {
                'timestamp': time.time(),
                'services': {name: svc.to_dict() for name, svc in self.services.items()},
                'connections': [conn.to_dict() for conn in self.connections.values()],
                'summary': summary
            }
            
            self.snapshot_history.append(snapshot)
            return snapshot
    
    def detect_changes(self, previous_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Detect changes between current topology and a previous snapshot"""
        current = self.take_snapshot()
        
        changes = {
            'timestamp': current['timestamp'],
            'new_services': [],
            'removed_services': [],
            'new_connections': [],
            'removed_connections': [],
            'status_changes': []
        }
        
        # Detect service changes
        prev_services = set(previous_snapshot['services'].keys())
        curr_services = set(current['services'].keys())
        
        changes['new_services'] = list(curr_services - prev_services)
        changes['removed_services'] = list(prev_services - curr_services)
        
        # Detect status changes
        for service_name in prev_services & curr_services:
            prev_status = previous_snapshot['services'][service_name]['status']
            curr_status = current['services'][service_name]['status']
            if prev_status != curr_status:
                changes['status_changes'].append({
                    'service': service_name,
                    'from': prev_status,
                    'to': curr_status
                })
        
        # Detect connection changes
        prev_conns = set((c['source'], c['destination']) for c in previous_snapshot['connections'])
        curr_conns = set((c['source'], c['destination']) for c in current['connections'])
        
        changes['new_connections'] = [f"{s} -> {d}" for s, d in (curr_conns - prev_conns)]
        changes['removed_connections'] = [f"{s} -> {d}" for s, d in (prev_conns - curr_conns)]
        
        return changes
    
    def export_to_json(self, filename: str):
        """Export topology to JSON file"""
        snapshot = self.take_snapshot()
        
        with open(filename, 'w') as f:
            json.dump(snapshot, f, indent=2)
    
    def import_from_json(self, filename: str):
        """Import topology from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        with self.lock:
            # Clear existing data
            self.services.clear()
            self.connections.clear()
            
            # Import services
            for name, svc_data in data['services'].items():
                service = Service(
                    name=name,
                    ip_addresses=set(svc_data['ip_addresses']),
                    ports=set(svc_data['ports']),
                    protocols=set(Protocol(p) for p in svc_data['protocols']),
                    incoming_connections=svc_data['incoming_connections'],
                    outgoing_connections=svc_data['outgoing_connections'],
                    total_requests_received=svc_data['total_requests_received'],
                    total_requests_sent=svc_data['total_requests_sent'],
                    total_errors=svc_data['total_errors'],
                    first_seen=svc_data['first_seen'],
                    last_seen=svc_data['last_seen'],
                    metadata=svc_data['metadata']
                )
                self.services[name] = service
            
            # Import connections
            for conn_data in data['connections']:
                conn = Connection(
                    source=conn_data['source'],
                    destination=conn_data['destination'],
                    protocol=Protocol(conn_data['protocol']),
                    request_count=conn_data['request_count'],
                    error_count=conn_data['error_count'],
                    total_bytes=conn_data['total_bytes'],
                    avg_latency_ms=conn_data['avg_latency_ms'],
                    first_seen=conn_data['first_seen'],
                    last_seen=conn_data['last_seen']
                )
                self.connections[(conn.source, conn.destination)] = conn
    
    def clear(self):
        """Clear all topology data"""
        with self.lock:
            self.services.clear()
            self.connections.clear()
            self.snapshot_history.clear()


def create_mapper() -> TopologyMapper:
    """Create a new topology mapper instance"""
    return TopologyMapper()
