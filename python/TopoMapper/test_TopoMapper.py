"""
Developed by PowerShield
"""

#!/usr/bin/env python3
"""
Test suite for TopoMapper - Application Topology Mapper

Tests core functionality including:
- Connection ingestion
- Service discovery
- Dependency mapping
- Topology analysis
- Health monitoring
"""

import unittest
import time
from TopoMapper import TopoMapper, Protocol, ServiceStatus


class TestBasicFunctionality(unittest.TestCase):
    """Test basic topology mapping"""
    
    def setUp(self):
        """Set up test mapper"""
        self.mapper = TopoMapper()
    
    def test_initialization(self):
        """Test mapper initialization"""
        self.assertEqual(len(self.mapper.get_services()), 0)
        self.assertEqual(len(self.mapper.get_dependencies()), 0)
    
    def test_single_connection_ingestion(self):
        """Test ingesting a single connection"""
        connection = {
            'source_host': '10.0.0.1',
            'source_port': 5000,
            'destination_host': '10.0.0.2',
            'destination_port': 8080,
            'protocol': 'http',
            'bytes_sent': 1024,
            'bytes_received': 2048
        }
        
        key = self.mapper.ingest_connection(connection)
        self.assertIsNotNone(key)
        
        services = self.mapper.get_services()
        self.assertGreaterEqual(len(services), 2)
    
    def test_service_discovery(self):
        """Test automatic service discovery"""
        connection = {
            'source_host': 'api-gateway',
            'source_port': 8080,
            'destination_host': 'user-service',
            'destination_port': 3000,
            'protocol': 'http'
        }
        
        self.mapper.ingest_connection(connection)
        
        services = self.mapper.get_services()
        service_hosts = [s.host for s in services]
        
        self.assertIn('api-gateway', service_hosts)
        self.assertIn('user-service', service_hosts)
    
    def test_service_naming(self):
        """Test service name generation"""
        self.mapper.register_service_name('10.0.0.1', 8080, 'my-api')
        
        connection = {
            'source_host': '10.0.0.1',
            'source_port': 8080,
            'destination_host': '10.0.0.2',
            'destination_port': 5432,
            'protocol': 'tcp'
        }
        
        self.mapper.ingest_connection(connection)
        
        service = self.mapper.get_service('my-api')
        self.assertIsNotNone(service)
        self.assertEqual(service.host, '10.0.0.1')


class TestDependencyMapping(unittest.TestCase):
    """Test service dependency mapping"""
    
    def setUp(self):
        """Set up test mapper"""
        self.mapper = TopoMapper()
    
    def test_dependency_creation(self):
        """Test creating service dependencies"""
        connection = {
            'source_host': 'service-a',
            'source_port': 8000,
            'destination_host': 'service-b',
            'destination_port': 8001,
            'protocol': 'http'
        }
        
        self.mapper.ingest_connection(connection)
        
        dependencies = self.mapper.get_dependencies()
        self.assertEqual(len(dependencies), 1)
        
        dep = dependencies[0]
        self.assertIn('service-a', dep.from_service)
        self.assertIn('service-b', dep.to_service)
    
    def test_dependency_metrics(self):
        """Test dependency metrics tracking"""
        # Multiple connections
        for i in range(10):
            connection = {
                'source_host': 'api',
                'source_port': 8080,
                'destination_host': 'backend',
                'destination_port': 9000,
                'protocol': 'http',
                'status_code': 200,
                'duration_ms': 50.0 + i
            }
            self.mapper.ingest_connection(connection)
        
        dependencies = self.mapper.get_dependencies()
        self.assertEqual(len(dependencies), 1)
        
        dep = dependencies[0]
        self.assertEqual(dep.total_requests, 10)
        self.assertGreater(dep.average_latency_ms, 0)
    
    def test_error_tracking(self):
        """Test error tracking in dependencies"""
        # 8 successful, 2 errors
        for i in range(10):
            connection = {
                'source_host': 'api',
                'source_port': 8080,
                'destination_host': 'backend',
                'destination_port': 9000,
                'protocol': 'http',
                'status_code': 500 if i < 2 else 200
            }
            self.mapper.ingest_connection(connection)
        
        dependencies = self.mapper.get_dependencies()
        dep = dependencies[0]
        
        self.assertEqual(dep.total_errors, 2)
        self.assertAlmostEqual(dep.get_error_rate(), 0.2, places=2)


class TestTopologyAnalysis(unittest.TestCase):
    """Test topology analysis features"""
    
    def setUp(self):
        """Set up test mapper with sample topology"""
        self.mapper = TopoMapper()
        
        # Create a simple topology:
        # client -> api-gateway -> user-service -> database
        #                       -> order-service -> database
        
        connections = [
            # Client to API Gateway
            {
                'source_host': 'client',
                'source_port': 50000,
                'destination_host': 'api-gateway',
                'destination_port': 8080,
                'protocol': 'http'
            },
            # API Gateway to User Service
            {
                'source_host': 'api-gateway',
                'source_port': 8080,
                'destination_host': 'user-service',
                'destination_port': 3000,
                'protocol': 'http'
            },
            # API Gateway to Order Service
            {
                'source_host': 'api-gateway',
                'source_port': 8080,
                'destination_host': 'order-service',
                'destination_port': 3001,
                'protocol': 'http'
            },
            # User Service to Database
            {
                'source_host': 'user-service',
                'source_port': 3000,
                'destination_host': 'database',
                'destination_port': 5432,
                'protocol': 'tcp'
            },
            # Order Service to Database
            {
                'source_host': 'order-service',
                'source_port': 3001,
                'destination_host': 'database',
                'destination_port': 5432,
                'protocol': 'tcp'
            }
        ]
        
        for conn in connections:
            self.mapper.ingest_connection(conn)
    
    def test_topology_graph(self):
        """Test topology graph generation"""
        graph = self.mapper.get_topology_graph()
        
        self.assertIsInstance(graph, dict)
        self.assertGreater(len(graph), 0)
        
        # Check that api-gateway has downstream services
        api_gateway_key = [k for k in graph.keys() if 'api-gateway' in k]
        if api_gateway_key:
            self.assertGreater(len(graph[api_gateway_key[0]]), 0)
    
    def test_entry_points(self):
        """Test finding entry point services"""
        entry_points = self.mapper.find_entry_points()
        
        self.assertGreater(len(entry_points), 0)
        
        # Client should be an entry point (no one calls it)
        client_services = [ep for ep in entry_points if 'client' in ep]
        self.assertGreater(len(client_services), 0)
    
    def test_leaf_services(self):
        """Test finding leaf services"""
        leaf_services = self.mapper.find_leaf_services()
        
        self.assertGreater(len(leaf_services), 0)
        
        # Database should be a leaf (doesn't call others)
        database_services = [ls for ls in leaf_services if 'database' in ls]
        self.assertGreater(len(database_services), 0)
    
    def test_critical_services(self):
        """Test finding critical services"""
        critical = self.mapper.find_critical_services(min_dependents=2)
        
        # Database should be critical (called by multiple services)
        if critical:
            critical_names = [c['service'] for c in critical]
            database_critical = [name for name in critical_names if 'database' in name]
            self.assertGreater(len(database_critical), 0)


class TestVisualization(unittest.TestCase):
    """Test topology visualization data"""
    
    def setUp(self):
        """Set up test mapper"""
        self.mapper = TopoMapper()
    
    def test_visualization_structure(self):
        """Test visualization data structure"""
        connection = {
            'source_host': 'service-a',
            'source_port': 8000,
            'destination_host': 'service-b',
            'destination_port': 8001,
            'protocol': 'http'
        }
        
        self.mapper.ingest_connection(connection)
        
        viz = self.mapper.get_topology_visualization()
        
        self.assertIn('nodes', viz)
        self.assertIn('edges', viz)
        self.assertIsInstance(viz['nodes'], list)
        self.assertIsInstance(viz['edges'], list)
    
    def test_visualization_nodes(self):
        """Test visualization node data"""
        connection = {
            'source_host': 'service-a',
            'source_port': 8000,
            'destination_host': 'service-b',
            'destination_port': 8001,
            'protocol': 'http',
            'status_code': 200
        }
        
        self.mapper.ingest_connection(connection)
        
        viz = self.mapper.get_topology_visualization()
        nodes = viz['nodes']
        
        self.assertGreater(len(nodes), 0)
        
        for node in nodes:
            self.assertIn('id', node)
            self.assertIn('host', node)
            self.assertIn('port', node)
            self.assertIn('protocol', node)
            self.assertIn('status', node)
    
    def test_visualization_edges(self):
        """Test visualization edge data"""
        connection = {
            'source_host': 'service-a',
            'source_port': 8000,
            'destination_host': 'service-b',
            'destination_port': 8001,
            'protocol': 'http',
            'status_code': 200
        }
        
        self.mapper.ingest_connection(connection)
        
        viz = self.mapper.get_topology_visualization()
        edges = viz['edges']
        
        self.assertGreater(len(edges), 0)
        
        for edge in edges:
            self.assertIn('from', edge)
            self.assertIn('to', edge)
            self.assertIn('protocol', edge)
            self.assertIn('requests', edge)


class TestHealthMonitoring(unittest.TestCase):
    """Test service health monitoring"""
    
    def setUp(self):
        """Set up test mapper"""
        self.mapper = TopoMapper()
    
    def test_healthy_service(self):
        """Test healthy service detection"""
        # All successful requests
        for i in range(100):
            connection = {
                'source_host': 'client',
                'source_port': 5000,
                'destination_host': 'service',
                'destination_port': 8000,
                'protocol': 'http',
                'status_code': 200
            }
            self.mapper.ingest_connection(connection)
        
        service_key = [k for k in self.mapper.services.keys() if 'service' in k][0]
        service = self.mapper.get_service(service_key)
        
        self.assertEqual(service.status, ServiceStatus.HEALTHY)
    
    def test_degraded_service(self):
        """Test degraded service detection"""
        # 3% error rate (degraded)
        for i in range(100):
            connection = {
                'source_host': 'client',
                'source_port': 5000,
                'destination_host': 'service',
                'destination_port': 8000,
                'protocol': 'http',
                'status_code': 500 if i < 3 else 200
            }
            self.mapper.ingest_connection(connection)
        
        service_key = [k for k in self.mapper.services.keys() if 'service' in k][0]
        service = self.mapper.get_service(service_key)
        
        self.assertEqual(service.status, ServiceStatus.DEGRADED)
    
    def test_unhealthy_service(self):
        """Test unhealthy service detection"""
        # 10% error rate (unhealthy)
        for i in range(100):
            connection = {
                'source_host': 'client',
                'source_port': 5000,
                'destination_host': 'service',
                'destination_port': 8000,
                'protocol': 'http',
                'status_code': 500 if i < 10 else 200
            }
            self.mapper.ingest_connection(connection)
        
        service_key = [k for k in self.mapper.services.keys() if 'service' in k][0]
        service = self.mapper.get_service(service_key)
        
        self.assertEqual(service.status, ServiceStatus.UNHEALTHY)
    
    def test_health_summary(self):
        """Test health summary generation"""
        # Create services with different health states
        for i in range(100):
            connection = {
                'source_host': 'client',
                'source_port': 5000,
                'destination_host': 'healthy-service',
                'destination_port': 8000,
                'protocol': 'http',
                'status_code': 200
            }
            self.mapper.ingest_connection(connection)
        
        summary = self.mapper.get_service_health_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('healthy', summary)


class TestTrafficAnalysis(unittest.TestCase):
    """Test traffic pattern analysis"""
    
    def setUp(self):
        """Set up test mapper"""
        self.mapper = TopoMapper()
    
    def test_traffic_patterns(self):
        """Test traffic pattern analysis"""
        # Add various connections
        for i in range(50):
            connection = {
                'source_host': 'client',
                'source_port': 5000,
                'destination_host': 'service',
                'destination_port': 8080,
                'protocol': 'http',
                'path': f'/api/endpoint{i % 5}'
            }
            self.mapper.ingest_connection(connection)
        
        patterns = self.mapper.analyze_traffic_patterns()
        
        self.assertIn('total_connections', patterns)
        self.assertIn('protocols', patterns)
        self.assertIn('top_endpoints', patterns)
        
        self.assertEqual(patterns['total_connections'], 50)
    
    def test_protocol_distribution(self):
        """Test protocol distribution tracking"""
        # Add HTTP connections
        for i in range(30):
            self.mapper.ingest_connection({
                'source_host': 'client',
                'source_port': 5000,
                'destination_host': 'service',
                'destination_port': 8080,
                'protocol': 'http'
            })
        
        # Add TCP connections
        for i in range(20):
            self.mapper.ingest_connection({
                'source_host': 'client',
                'source_port': 5000,
                'destination_host': 'database',
                'destination_port': 5432,
                'protocol': 'tcp'
            })
        
        patterns = self.mapper.analyze_traffic_patterns()
        protocols = patterns['protocols']
        
        self.assertIn('http', protocols)
        self.assertIn('tcp', protocols)
        self.assertEqual(protocols['http'], 30)
        self.assertEqual(protocols['tcp'], 20)


class TestEndpointTracking(unittest.TestCase):
    """Test endpoint tracking"""
    
    def setUp(self):
        """Set up test mapper"""
        self.mapper = TopoMapper()
    
    def test_endpoint_discovery(self):
        """Test endpoint discovery from paths"""
        endpoints = ['/api/users', '/api/orders', '/api/products']
        
        for endpoint in endpoints:
            connection = {
                'source_host': 'client',
                'source_port': 5000,
                'destination_host': 'api',
                'destination_port': 8080,
                'protocol': 'http',
                'path': endpoint
            }
            self.mapper.ingest_connection(connection)
        
        service_key = [k for k in self.mapper.services.keys() if 'api' in k][0]
        service = self.mapper.get_service(service_key)
        
        self.assertGreaterEqual(len(service.endpoints), 3)
        for endpoint in endpoints:
            self.assertIn(endpoint, service.endpoints)


class TestExportAndCleanup(unittest.TestCase):
    """Test export and cleanup functionality"""
    
    def setUp(self):
        """Set up test mapper"""
        self.mapper = TopoMapper()
    
    def test_export_topology(self):
        """Test topology export"""
        connection = {
            'source_host': 'service-a',
            'source_port': 8000,
            'destination_host': 'service-b',
            'destination_port': 8001,
            'protocol': 'http'
        }
        
        self.mapper.ingest_connection(connection)
        
        exported = self.mapper.export_topology()
        
        self.assertIn('services', exported)
        self.assertIn('dependencies', exported)
        self.assertIn('topology_graph', exported)
        self.assertIn('entry_points', exported)
        self.assertIn('leaf_services', exported)
        self.assertIn('critical_services', exported)
    
    def test_cleanup_inactive_services(self):
        """Test cleaning up inactive services"""
        mapper = TopoMapper(service_timeout_seconds=1)
        
        connection = {
            'source_host': 'service-a',
            'source_port': 8000,
            'destination_host': 'service-b',
            'destination_port': 8001,
            'protocol': 'http'
        }
        
        mapper.ingest_connection(connection)
        
        self.assertGreater(len(mapper.get_services()), 0)
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Cleanup
        removed = mapper.cleanup_inactive_services()
        
        self.assertGreater(removed, 0)
        self.assertEqual(len(mapper.get_services()), 0)
    
    def test_clear(self):
        """Test clearing all data"""
        connection = {
            'source_host': 'service-a',
            'source_port': 8000,
            'destination_host': 'service-b',
            'destination_port': 8001,
            'protocol': 'http'
        }
        
        self.mapper.ingest_connection(connection)
        
        self.assertGreater(len(self.mapper.get_services()), 0)
        
        self.mapper.clear()
        
        self.assertEqual(len(self.mapper.get_services()), 0)
        self.assertEqual(len(self.mapper.get_dependencies()), 0)


if __name__ == '__main__':
    unittest.main()
