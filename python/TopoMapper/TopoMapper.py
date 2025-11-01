"""
Developed by PowerShield
"""

#!/usr/bin/env python3
"""
TopoMapper - Application Topology Mapper from Actual Traffic

This module analyzes actual network traffic to automatically discover and map
application topology, service dependencies, and communication patterns.

Features:
- Automatic service discovery from traffic
- Dependency mapping between services
- Protocol detection (HTTP, gRPC, TCP, etc.)
- Traffic pattern analysis
- Health status tracking
- Topology visualization data generation
- Multi-protocol support
"""

import time
import threading
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
from enum import Enum
import json
import hashlib


class Protocol(Enum):
    """Network protocols"""
    HTTP = "http"
    HTTPS = "https"
    GRPC = "grpc"
    TCP = "tcp"
    UDP = "udp"
    WEBSOCKET = "websocket"
    UNKNOWN = "unknown"


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class NetworkConnection:
    """Represents a network connection"""
    source_host: str
    source_port: int
    destination_host: str
    destination_port: int
    protocol: Protocol
    timestamp: float
    bytes_sent: int = 0
    bytes_received: int = 0
    status_code: Optional[int] = None
    method: Optional[str] = None
    path: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def get_connection_key(self) -> str:
        """Generate unique key for this connection type"""
        return f"{self.source_host}:{self.source_port}->{self.destination_host}:{self.destination_port}:{self.protocol.value}"


@dataclass
class Service:
    """Represents a discovered service"""
    name: str
    host: str
    port: int
    protocol: Protocol
    first_seen: float
    last_seen: float
    total_requests: int = 0
    total_errors: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    endpoints: Set[str] = field(default_factory=set)
    status: ServiceStatus = ServiceStatus.UNKNOWN
    
    def get_error_rate(self) -> float:
        """Calculate error rate"""
        return self.total_errors / self.total_requests if self.total_requests > 0 else 0.0
    
    def update_status(self):
        """Update service health status based on error rate"""
        error_rate = self.get_error_rate()
        if error_rate < 0.01:  # Less than 1% errors
            self.status = ServiceStatus.HEALTHY
        elif error_rate < 0.05:  # Less than 5% errors
            self.status = ServiceStatus.DEGRADED
        else:
            self.status = ServiceStatus.UNHEALTHY


@dataclass
class ServiceDependency:
    """Represents a dependency between services"""
    from_service: str
    to_service: str
    protocol: Protocol
    connection_count: int = 0
    total_requests: int = 0
    total_errors: int = 0
    total_bytes: int = 0
    average_latency_ms: float = 0.0
    endpoints_used: Set[str] = field(default_factory=set)
    
    def get_error_rate(self) -> float:
        """Calculate error rate for this dependency"""
        return self.total_errors / self.total_requests if self.total_requests > 0 else 0.0


@dataclass
class TopologyNode:
    """Node in topology graph"""
    service_name: str
    host: str
    port: int
    protocol: str
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TopologyEdge:
    """Edge in topology graph"""
    from_service: str
    to_service: str
    protocol: str
    request_count: int
    error_rate: float
    average_latency_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class TopoMapper:
    """Application Topology Mapper"""
    
    def __init__(self, service_timeout_seconds: int = 300):
        """
        Initialize the topology mapper
        
        Args:
            service_timeout_seconds: Time before marking service as inactive
        """
        self.service_timeout = service_timeout_seconds
        self.services: Dict[str, Service] = {}
        self.dependencies: Dict[Tuple[str, str], ServiceDependency] = {}
        self.connections: List[NetworkConnection] = []
        self.lock = threading.Lock()
        
        # Service naming rules
        self.service_names: Dict[Tuple[str, int], str] = {}
    
    def register_service_name(self, host: str, port: int, name: str):
        """
        Register a known service name
        
        Args:
            host: Service host
            port: Service port
            name: Service name
        """
        with self.lock:
            self.service_names[(host, port)] = name
    
    def _get_service_name(self, host: str, port: int, protocol: Protocol) -> str:
        """
        Get or generate service name
        
        Args:
            host: Service host
            port: Service port
            protocol: Service protocol
            
        Returns:
            Service name
        """
        # Check if we have a registered name
        if (host, port) in self.service_names:
            return self.service_names[(host, port)]
        
        # Generate name based on common patterns
        if port == 80 or port == 8080:
            return f"{host}-web"
        elif port == 443 or port == 8443:
            return f"{host}-https"
        elif port == 3000:
            return f"{host}-api"
        elif port == 5432:
            return f"{host}-postgres"
        elif port == 3306:
            return f"{host}-mysql"
        elif port == 6379:
            return f"{host}-redis"
        elif port == 9092:
            return f"{host}-kafka"
        else:
            return f"{host}:{port}"
    
    def ingest_connection(self, connection_data: Dict[str, Any]) -> str:
        """
        Ingest a network connection
        
        Args:
            connection_data: Connection data dictionary
            
        Returns:
            Connection key
        """
        with self.lock:
            # Create connection object
            connection = NetworkConnection(
                source_host=connection_data['source_host'],
                source_port=connection_data['source_port'],
                destination_host=connection_data['destination_host'],
                destination_port=connection_data['destination_port'],
                protocol=Protocol(connection_data.get('protocol', 'tcp')),
                timestamp=connection_data.get('timestamp', time.time()),
                bytes_sent=connection_data.get('bytes_sent', 0),
                bytes_received=connection_data.get('bytes_received', 0),
                status_code=connection_data.get('status_code'),
                method=connection_data.get('method'),
                path=connection_data.get('path'),
                duration_ms=connection_data.get('duration_ms')
            )
            
            self.connections.append(connection)
            
            # Update services
            self._update_services(connection)
            
            # Update dependencies
            self._update_dependencies(connection)
            
            return connection.get_connection_key()
    
    def _update_services(self, connection: NetworkConnection):
        """Update service information from connection"""
        # Update source service
        source_name = self._get_service_name(
            connection.source_host,
            connection.source_port,
            connection.protocol
        )
        
        if source_name not in self.services:
            self.services[source_name] = Service(
                name=source_name,
                host=connection.source_host,
                port=connection.source_port,
                protocol=connection.protocol,
                first_seen=connection.timestamp,
                last_seen=connection.timestamp
            )
        
        source_service = self.services[source_name]
        source_service.last_seen = connection.timestamp
        source_service.total_bytes_sent += connection.bytes_sent
        
        # Update destination service
        dest_name = self._get_service_name(
            connection.destination_host,
            connection.destination_port,
            connection.protocol
        )
        
        if dest_name not in self.services:
            self.services[dest_name] = Service(
                name=dest_name,
                host=connection.destination_host,
                port=connection.destination_port,
                protocol=connection.protocol,
                first_seen=connection.timestamp,
                last_seen=connection.timestamp
            )
        
        dest_service = self.services[dest_name]
        dest_service.last_seen = connection.timestamp
        dest_service.total_requests += 1
        dest_service.total_bytes_received += connection.bytes_received
        
        # Track endpoints
        if connection.path:
            dest_service.endpoints.add(connection.path)
        
        # Track errors
        if connection.status_code and connection.status_code >= 400:
            dest_service.total_errors += 1
        
        # Update health status
        dest_service.update_status()
    
    def _update_dependencies(self, connection: NetworkConnection):
        """Update service dependencies from connection"""
        source_name = self._get_service_name(
            connection.source_host,
            connection.source_port,
            connection.protocol
        )
        dest_name = self._get_service_name(
            connection.destination_host,
            connection.destination_port,
            connection.protocol
        )
        
        dep_key = (source_name, dest_name)
        
        if dep_key not in self.dependencies:
            self.dependencies[dep_key] = ServiceDependency(
                from_service=source_name,
                to_service=dest_name,
                protocol=connection.protocol
            )
        
        dep = self.dependencies[dep_key]
        dep.connection_count += 1
        dep.total_requests += 1
        dep.total_bytes += connection.bytes_sent + connection.bytes_received
        
        # Track endpoints
        if connection.path:
            dep.endpoints_used.add(connection.path)
        
        # Track errors
        if connection.status_code and connection.status_code >= 400:
            dep.total_errors += 1
        
        # Update latency
        if connection.duration_ms:
            # Running average
            n = dep.total_requests
            dep.average_latency_ms = (
                (dep.average_latency_ms * (n - 1) + connection.duration_ms) / n
            )
    
    def get_services(self) -> List[Service]:
        """Get all discovered services"""
        with self.lock:
            return list(self.services.values())
    
    def get_service(self, service_name: str) -> Optional[Service]:
        """Get a specific service"""
        with self.lock:
            return self.services.get(service_name)
    
    def get_dependencies(self) -> List[ServiceDependency]:
        """Get all service dependencies"""
        with self.lock:
            return list(self.dependencies.values())
    
    def get_topology_graph(self) -> Dict[str, List[str]]:
        """
        Get topology as a graph
        
        Returns:
            Dictionary mapping service names to their downstream dependencies
        """
        with self.lock:
            graph = defaultdict(list)
            for (from_service, to_service), dep in self.dependencies.items():
                graph[from_service].append(to_service)
            return dict(graph)
    
    def get_topology_visualization(self) -> Dict[str, Any]:
        """
        Get topology data for visualization
        
        Returns:
            Dictionary with nodes and edges for visualization
        """
        with self.lock:
            nodes = []
            edges = []
            
            # Create nodes
            for service in self.services.values():
                nodes.append(TopologyNode(
                    service_name=service.name,
                    host=service.host,
                    port=service.port,
                    protocol=service.protocol.value,
                    status=service.status.value,
                    metadata={
                        'total_requests': service.total_requests,
                        'error_rate': service.get_error_rate(),
                        'endpoints': list(service.endpoints)[:10]  # Limit to 10
                    }
                ))
            
            # Create edges
            for dep in self.dependencies.values():
                edges.append(TopologyEdge(
                    from_service=dep.from_service,
                    to_service=dep.to_service,
                    protocol=dep.protocol.value,
                    request_count=dep.total_requests,
                    error_rate=dep.get_error_rate(),
                    average_latency_ms=dep.average_latency_ms,
                    metadata={
                        'total_bytes': dep.total_bytes,
                        'endpoints': list(dep.endpoints_used)[:5]  # Limit to 5
                    }
                ))
            
            return {
                'nodes': [
                    {
                        'id': node.service_name,
                        'host': node.host,
                        'port': node.port,
                        'protocol': node.protocol,
                        'status': node.status,
                        'metadata': node.metadata
                    }
                    for node in nodes
                ],
                'edges': [
                    {
                        'from': edge.from_service,
                        'to': edge.to_service,
                        'protocol': edge.protocol,
                        'requests': edge.request_count,
                        'error_rate': edge.error_rate,
                        'latency_ms': edge.average_latency_ms,
                        'metadata': edge.metadata
                    }
                    for edge in edges
                ]
            }
    
    def find_entry_points(self) -> List[str]:
        """
        Find entry point services (services that don't receive calls from others)
        
        Returns:
            List of entry point service names
        """
        with self.lock:
            all_services = set(self.services.keys())
            downstream_services = set()
            
            for (from_service, to_service) in self.dependencies.keys():
                downstream_services.add(to_service)
            
            entry_points = all_services - downstream_services
            return list(entry_points)
    
    def find_leaf_services(self) -> List[str]:
        """
        Find leaf services (services that don't call other services)
        
        Returns:
            List of leaf service names
        """
        with self.lock:
            all_services = set(self.services.keys())
            upstream_services = set()
            
            for (from_service, to_service) in self.dependencies.keys():
                upstream_services.add(from_service)
            
            leaf_services = all_services - upstream_services
            return list(leaf_services)
    
    def find_critical_services(self, min_dependents: int = 2) -> List[Dict[str, Any]]:
        """
        Find critical services (services with many dependents)
        
        Args:
            min_dependents: Minimum number of dependents to be considered critical
            
        Returns:
            List of critical services with their metrics
        """
        with self.lock:
            # Count dependents for each service
            dependents = defaultdict(set)
            for (from_service, to_service) in self.dependencies.keys():
                dependents[to_service].add(from_service)
            
            critical = []
            for service_name, dependent_set in dependents.items():
                if len(dependent_set) >= min_dependents:
                    service = self.services.get(service_name)
                    if service:
                        critical.append({
                            'service': service_name,
                            'dependent_count': len(dependent_set),
                            'dependents': list(dependent_set),
                            'total_requests': service.total_requests,
                            'error_rate': service.get_error_rate(),
                            'status': service.status.value
                        })
            
            # Sort by number of dependents
            critical.sort(key=lambda x: x['dependent_count'], reverse=True)
            return critical
    
    def analyze_traffic_patterns(self) -> Dict[str, Any]:
        """
        Analyze traffic patterns
        
        Returns:
            Dictionary with traffic analysis
        """
        with self.lock:
            if not self.connections:
                return {}
            
            # Protocol distribution
            protocol_counts = defaultdict(int)
            for conn in self.connections:
                protocol_counts[conn.protocol.value] += 1
            
            # Traffic over time (bucket by minute)
            if self.connections:
                start_time = self.connections[0].timestamp
                time_buckets = defaultdict(int)
                
                for conn in self.connections:
                    bucket = int((conn.timestamp - start_time) / 60)  # 1-minute buckets
                    time_buckets[bucket] += 1
            else:
                time_buckets = {}
            
            # Top endpoints
            endpoint_counts = defaultdict(int)
            for conn in self.connections:
                if conn.path:
                    endpoint_counts[conn.path] += 1
            
            top_endpoints = sorted(
                endpoint_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                'total_connections': len(self.connections),
                'protocols': dict(protocol_counts),
                'traffic_over_time': dict(time_buckets),
                'top_endpoints': [
                    {'path': path, 'count': count}
                    for path, count in top_endpoints
                ]
            }
    
    def get_service_health_summary(self) -> Dict[str, int]:
        """
        Get summary of service health
        
        Returns:
            Dictionary with counts of services by status
        """
        with self.lock:
            summary = defaultdict(int)
            for service in self.services.values():
                summary[service.status.value] += 1
            return dict(summary)
    
    def cleanup_inactive_services(self) -> int:
        """
        Remove services that haven't been seen recently
        
        Returns:
            Number of services removed
        """
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.service_timeout
            
            inactive_services = [
                name for name, service in self.services.items()
                if service.last_seen < cutoff_time
            ]
            
            for service_name in inactive_services:
                del self.services[service_name]
                
                # Also remove related dependencies
                deps_to_remove = [
                    key for key in self.dependencies.keys()
                    if key[0] == service_name or key[1] == service_name
                ]
                for key in deps_to_remove:
                    del self.dependencies[key]
            
            return len(inactive_services)
    
    def export_topology(self) -> Dict[str, Any]:
        """
        Export complete topology data
        
        Returns:
            Complete topology data as dictionary
        """
        return {
            'services': [
                {
                    'name': s.name,
                    'host': s.host,
                    'port': s.port,
                    'protocol': s.protocol.value,
                    'status': s.status.value,
                    'total_requests': s.total_requests,
                    'error_rate': s.get_error_rate(),
                    'endpoints': list(s.endpoints)
                }
                for s in self.get_services()
            ],
            'dependencies': [
                {
                    'from': d.from_service,
                    'to': d.to_service,
                    'protocol': d.protocol.value,
                    'requests': d.total_requests,
                    'errors': d.total_errors,
                    'error_rate': d.get_error_rate(),
                    'avg_latency_ms': d.average_latency_ms,
                    'endpoints': list(d.endpoints_used)
                }
                for d in self.get_dependencies()
            ],
            'topology_graph': self.get_topology_graph(),
            'entry_points': self.find_entry_points(),
            'leaf_services': self.find_leaf_services(),
            'critical_services': self.find_critical_services(),
            'health_summary': self.get_service_health_summary(),
            'traffic_patterns': self.analyze_traffic_patterns()
        }
    
    def clear(self):
        """Clear all topology data"""
        with self.lock:
            self.services.clear()
            self.dependencies.clear()
            self.connections.clear()
            self.service_names.clear()
