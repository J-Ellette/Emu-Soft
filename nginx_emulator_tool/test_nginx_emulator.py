"""
Tests for Nginx Emulator
"""

import unittest
from nginx_emulator import NginxConfig, LoadBalancer, ReverseProxy


class TestNginxConfig(unittest.TestCase):
    """Test Nginx configuration parsing"""
    
    def test_simple_server_config(self):
        """Test parsing simple server configuration"""
        config_text = """
        server {
            listen 80;
            server_name example.com;
            
            location / {
                proxy_pass http://backend:8080;
            }
        }
        """
        
        config = NginxConfig(config_text)
        
        self.assertEqual(len(config.servers), 1)
        server = config.servers[0]
        self.assertIn('80', server['listen'])
        self.assertIn('example.com', server['server_name'])
        self.assertEqual(len(server['locations']), 1)
    
    def test_upstream_config(self):
        """Test parsing upstream configuration"""
        config_text = """
        upstream backend {
            server backend1:8080;
            server backend2:8080;
            server backend3:8080;
        }
        
        server {
            listen 80;
            
            location / {
                proxy_pass http://backend;
            }
        }
        """
        
        config = NginxConfig(config_text)
        
        self.assertIn('backend', config.upstreams)
        self.assertEqual(len(config.upstreams['backend']), 3)
        self.assertIn('backend1:8080', config.upstreams['backend'])
    
    def test_multiple_locations(self):
        """Test parsing multiple locations"""
        config_text = """
        server {
            listen 80;
            
            location / {
                proxy_pass http://frontend:3000;
            }
            
            location /api {
                proxy_pass http://backend:8080;
            }
            
            location /static {
                proxy_pass http://static:9000;
            }
        }
        """
        
        config = NginxConfig(config_text)
        
        self.assertEqual(len(config.servers), 1)
        server = config.servers[0]
        self.assertEqual(len(server['locations']), 3)
        
        # Check location paths
        paths = [loc['path'] for loc in server['locations']]
        self.assertIn('/', paths)
        self.assertIn('/api', paths)
        self.assertIn('/static', paths)
    
    def test_location_directives(self):
        """Test parsing location directives"""
        config_text = """
        server {
            listen 80;
            
            location /api {
                proxy_pass http://backend:8080;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
            }
        }
        """
        
        config = NginxConfig(config_text)
        
        location = config.servers[0]['locations'][0]
        self.assertEqual(location['path'], '/api')
        self.assertEqual(location['directives']['proxy_pass'], 'http://backend:8080')
        self.assertIn('proxy_set_header', location['directives'])
    
    def test_comments_ignored(self):
        """Test that comments are ignored"""
        config_text = """
        # This is a comment
        server {
            listen 80; # inline comment
            # Another comment
            location / {
                proxy_pass http://backend:8080;
            }
        }
        """
        
        config = NginxConfig(config_text)
        
        self.assertEqual(len(config.servers), 1)
    
    def test_multiple_servers(self):
        """Test parsing multiple server blocks"""
        config_text = """
        server {
            listen 80;
            server_name example.com;
        }
        
        server {
            listen 443;
            server_name secure.example.com;
        }
        """
        
        config = NginxConfig(config_text)
        
        self.assertEqual(len(config.servers), 2)


class TestLoadBalancer(unittest.TestCase):
    """Test load balancing strategies"""
    
    def test_round_robin(self):
        """Test round-robin load balancing"""
        lb = LoadBalancer('round_robin')
        backends = ['backend1:8080', 'backend2:8080', 'backend3:8080']
        
        # First request goes to backend1
        result1 = lb.select_backend('test', backends)
        self.assertEqual(result1, 'backend1:8080')
        
        # Second request goes to backend2
        result2 = lb.select_backend('test', backends)
        self.assertEqual(result2, 'backend2:8080')
        
        # Third request goes to backend3
        result3 = lb.select_backend('test', backends)
        self.assertEqual(result3, 'backend3:8080')
        
        # Fourth request wraps around to backend1
        result4 = lb.select_backend('test', backends)
        self.assertEqual(result4, 'backend1:8080')
    
    def test_single_backend(self):
        """Test with single backend"""
        lb = LoadBalancer('round_robin')
        backends = ['backend1:8080']
        
        result1 = lb.select_backend('test', backends)
        self.assertEqual(result1, 'backend1:8080')
        
        result2 = lb.select_backend('test', backends)
        self.assertEqual(result2, 'backend1:8080')
    
    def test_empty_backends(self):
        """Test with empty backends list"""
        lb = LoadBalancer('round_robin')
        backends = []
        
        result = lb.select_backend('test', backends)
        self.assertIsNone(result)


class TestReverseProxy(unittest.TestCase):
    """Test reverse proxy functionality"""
    
    def test_find_matching_server(self):
        """Test finding matching server by port"""
        config_text = """
        server {
            listen 80;
            server_name example.com;
        }
        
        server {
            listen 8080;
            server_name api.example.com;
        }
        """
        
        config = NginxConfig(config_text)
        proxy = ReverseProxy(config)
        
        # Find server on port 80
        server = proxy.find_matching_server('example.com', 80)
        self.assertIsNotNone(server)
        self.assertIn('example.com', server['server_name'])
        
        # Find server on port 8080
        server = proxy.find_matching_server('api.example.com', 8080)
        self.assertIsNotNone(server)
        self.assertIn('api.example.com', server['server_name'])
        
        # No server on port 9000
        server = proxy.find_matching_server('example.com', 9000)
        self.assertIsNone(server)
    
    def test_find_matching_location(self):
        """Test finding matching location by path"""
        config_text = """
        server {
            listen 80;
            
            location / {
                proxy_pass http://default:8080;
            }
            
            location /api {
                proxy_pass http://api:8080;
            }
            
            location /api/v2 {
                proxy_pass http://api_v2:8080;
            }
        }
        """
        
        config = NginxConfig(config_text)
        proxy = ReverseProxy(config)
        server = config.servers[0]
        
        # Test exact path
        location = proxy.find_matching_location(server, '/')
        self.assertEqual(location['path'], '/')
        
        # Test prefix match - should match more specific first
        location = proxy.find_matching_location(server, '/api/v2/users')
        self.assertEqual(location['path'], '/api/v2')
        
        # Test prefix match
        location = proxy.find_matching_location(server, '/api/users')
        self.assertEqual(location['path'], '/api')
        
        # Test fallback to root
        location = proxy.find_matching_location(server, '/other')
        self.assertEqual(location['path'], '/')
    
    def test_resolve_proxy_pass_upstream(self):
        """Test resolving proxy_pass with upstream"""
        config_text = """
        upstream backend {
            server backend1:8080;
            server backend2:8080;
        }
        
        server {
            listen 80;
            
            location / {
                proxy_pass http://backend;
            }
        }
        """
        
        config = NginxConfig(config_text)
        proxy = ReverseProxy(config)
        
        # Resolve upstream
        result = proxy.resolve_proxy_pass('http://backend/')
        self.assertIsNotNone(result)
        
        host, port, path = result
        self.assertIn(host + ':' + str(port), ['backend1:8080', 'backend2:8080'])
        self.assertEqual(path, '/')
    
    def test_resolve_proxy_pass_direct(self):
        """Test resolving proxy_pass with direct host"""
        config = NginxConfig()
        proxy = ReverseProxy(config)
        
        # Direct host with port
        result = proxy.resolve_proxy_pass('http://backend:8080/api')
        self.assertIsNotNone(result)
        
        host, port, path = result
        self.assertEqual(host, 'backend')
        self.assertEqual(port, 8080)
        self.assertEqual(path, '/api')
        
        # Direct host without port
        result = proxy.resolve_proxy_pass('http://backend/api')
        self.assertIsNotNone(result)
        
        host, port, path = result
        self.assertEqual(host, 'backend')
        self.assertEqual(port, 80)
        self.assertEqual(path, '/api')


class TestNginxConfigDict(unittest.TestCase):
    """Test creating config from dictionary"""
    
    def test_from_dict(self):
        """Test creating config from dictionary"""
        config_dict = {
            'servers': [
                {
                    'listen': ['80'],
                    'server_name': ['example.com'],
                    'locations': [
                        {
                            'path': '/',
                            'directives': {
                                'proxy_pass': 'http://backend:8080'
                            }
                        }
                    ],
                    'directives': {}
                }
            ],
            'upstreams': {
                'backend': ['backend1:8080', 'backend2:8080']
            }
        }
        
        config = NginxConfig.from_dict(config_dict)
        
        self.assertEqual(len(config.servers), 1)
        self.assertEqual(len(config.upstreams), 1)
        self.assertIn('backend', config.upstreams)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
