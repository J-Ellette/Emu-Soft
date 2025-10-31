#!/usr/bin/env python3
"""
Test suite for Nginx Emulator

Tests core functionality including:
- Server block configuration
- Location matching
- Upstream load balancing
- Reverse proxy
- Request/response handling
"""

import unittest
import threading
import time
import socket
from ReverseProxy import (
    ReverseProxy, ServerBlock, Location, Upstream, UpstreamServer,
    Request, Response, LoadBalanceMethod,
    create_server, create_location, create_upstream, add_upstream_server
)


class TestRequest(unittest.TestCase):
    """Test Request parsing"""
    
    def test_parse_simple_request(self):
        """Test parsing a simple GET request"""
        raw = "GET /path HTTP/1.1\r\nHost: localhost\r\n\r\n"
        req = Request.parse(raw, ("127.0.0.1", 12345))
        
        self.assertEqual(req.method, "GET")
        self.assertEqual(req.path, "/path")
        self.assertEqual(req.headers["host"], "localhost")
    
    def test_parse_with_query_string(self):
        """Test parsing request with query string"""
        raw = "GET /search?q=test&page=1 HTTP/1.1\r\nHost: localhost\r\n\r\n"
        req = Request.parse(raw, ("127.0.0.1", 12345))
        
        self.assertEqual(req.path, "/search")
        self.assertEqual(req.query_string, "q=test&page=1")
    
    def test_parse_with_body(self):
        """Test parsing POST request with body"""
        raw = "POST /api HTTP/1.1\r\nHost: localhost\r\nContent-Length: 13\r\n\r\n{\"key\":\"value\"}"
        req = Request.parse(raw, ("127.0.0.1", 12345))
        
        self.assertEqual(req.method, "POST")
        self.assertEqual(req.body, "{\"key\":\"value\"}")


class TestResponse(unittest.TestCase):
    """Test Response building"""
    
    def test_create_response(self):
        """Test creating basic response"""
        resp = Response(200, "OK")
        resp.set_body("<h1>Hello</h1>")
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.body, "<h1>Hello</h1>")
    
    def test_set_headers(self):
        """Test setting response headers"""
        resp = Response()
        resp.set_header("X-Custom", "value")
        
        self.assertEqual(resp.headers["X-Custom"], "value")
    
    def test_json_response(self):
        """Test JSON response"""
        resp = Response()
        resp.json({"status": "ok", "data": [1, 2, 3]})
        
        self.assertEqual(resp.headers["Content-Type"], "application/json")
        self.assertIn("status", resp.body)
    
    def test_to_bytes(self):
        """Test converting response to bytes"""
        resp = Response(200, "OK")
        resp.set_body("Hello")
        
        data = resp.to_bytes()
        self.assertIsInstance(data, bytes)
        self.assertIn(b"HTTP/1.1 200 OK", data)
        self.assertIn(b"Hello", data)


class TestServerBlock(unittest.TestCase):
    """Test ServerBlock configuration"""
    
    def test_create_server(self):
        """Test creating server block"""
        server = create_server(listen=8080, server_name=["example.com"])
        
        self.assertEqual(server.listen, 8080)
        self.assertIn("example.com", server.server_name)
    
    def test_add_location(self):
        """Test adding location to server"""
        server = create_server()
        loc = create_location("/api", proxy_pass="http://backend")
        server.locations.append(loc)
        
        self.assertEqual(len(server.locations), 1)
        self.assertEqual(server.locations[0].path, "/api")


class TestUpstream(unittest.TestCase):
    """Test Upstream load balancing"""
    
    def test_create_upstream(self):
        """Test creating upstream group"""
        upstream = create_upstream("backend", LoadBalanceMethod.ROUND_ROBIN)
        
        self.assertEqual(upstream.name, "backend")
        self.assertEqual(upstream.method, LoadBalanceMethod.ROUND_ROBIN)
    
    def test_add_servers(self):
        """Test adding servers to upstream"""
        upstream = create_upstream("backend")
        add_upstream_server(upstream, "10.0.0.1", 8001)
        add_upstream_server(upstream, "10.0.0.2", 8002, weight=2)
        
        self.assertEqual(len(upstream.servers), 2)
        self.assertEqual(upstream.servers[0].host, "10.0.0.1")
        self.assertEqual(upstream.servers[1].weight, 2)


class TestReverseProxy(unittest.TestCase):
    """Test ReverseProxy functionality"""
    
    def test_add_server(self):
        """Test adding server block"""
        nginx = ReverseProxy()
        server = create_server(listen=8080)
        nginx.add_server(server)
        
        self.assertEqual(len(nginx.server_blocks), 1)
    
    def test_add_upstream(self):
        """Test adding upstream group"""
        nginx = ReverseProxy()
        upstream = create_upstream("backend")
        nginx.add_upstream(upstream)
        
        self.assertIn("backend", nginx.upstreams)
    
    def test_match_location_exact(self):
        """Test exact location matching"""
        nginx = ReverseProxy()
        server = create_server()
        server.locations.append(create_location("/api"))
        server.locations.append(create_location("/api/users"))
        
        loc = nginx._match_location(server, "/api")
        self.assertEqual(loc.path, "/api")
    
    def test_match_location_prefix(self):
        """Test prefix location matching"""
        nginx = ReverseProxy()
        server = create_server()
        server.locations.append(create_location("/api"))
        server.locations.append(create_location("/"))
        
        loc = nginx._match_location(server, "/api/users")
        self.assertEqual(loc.path, "/api")
    
    def test_get_next_upstream_round_robin(self):
        """Test round-robin load balancing"""
        nginx = ReverseProxy()
        upstream = create_upstream("backend", LoadBalanceMethod.ROUND_ROBIN)
        add_upstream_server(upstream, "10.0.0.1", 8001)
        add_upstream_server(upstream, "10.0.0.2", 8002)
        
        server1 = nginx._get_next_upstream_server(upstream)
        server2 = nginx._get_next_upstream_server(upstream)
        server3 = nginx._get_next_upstream_server(upstream)
        
        self.assertEqual(server1.host, "10.0.0.1")
        self.assertEqual(server2.host, "10.0.0.2")
        self.assertEqual(server3.host, "10.0.0.1")  # Round robin back to first
    
    def test_handle_simple_request(self):
        """Test handling a simple request"""
        nginx = ReverseProxy()
        server = create_server()
        server.locations.append(create_location("/"))
        nginx.add_server(server)
        
        req = Request("GET", "/", {"host": "localhost"})
        resp = nginx._handle_request(req)
        
        self.assertEqual(resp.status_code, 200)
    
    def test_handle_proxy_request(self):
        """Test handling reverse proxy request"""
        nginx = ReverseProxy()
        
        upstream = create_upstream("backend")
        add_upstream_server(upstream, "10.0.0.1", 8001)
        nginx.add_upstream(upstream)
        
        server = create_server()
        server.locations.append(create_location("/api", proxy_pass="http://backend"))
        nginx.add_server(server)
        
        req = Request("GET", "/api", {"host": "localhost"})
        resp = nginx._handle_request(req)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("X-Upstream-Server", resp.headers)
    
    def test_handle_not_found(self):
        """Test 404 response"""
        nginx = ReverseProxy()
        server = create_server()
        server.locations.append(create_location("/"))
        nginx.add_server(server)
        
        req = Request("GET", "/nonexistent", {"host": "localhost"})
        resp = nginx._handle_request(req)
        
        self.assertEqual(resp.status_code, 404)
    
    def test_handle_return_directive(self):
        """Test return directive"""
        nginx = ReverseProxy()
        server = create_server()
        loc = create_location("/redirect", return_code=301, return_url="http://example.com")
        server.locations.append(loc)
        nginx.add_server(server)
        
        req = Request("GET", "/redirect", {"host": "localhost"})
        resp = nginx._handle_request(req)
        
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.headers["Location"], "http://example.com")


class TestIntegration(unittest.TestCase):
    """Integration tests with actual HTTP server"""
    
    def test_start_stop(self):
        """Test starting and stopping server"""
        nginx = ReverseProxy()
        server = create_server(listen=18080)
        server.locations.append(create_location("/"))
        nginx.add_server(server)
        
        nginx.start()
        time.sleep(0.5)  # Give server time to start
        
        self.assertTrue(nginx.running)
        
        nginx.stop()
        time.sleep(0.5)  # Give server time to stop
        
        self.assertFalse(nginx.running)
    
    def test_http_request(self):
        """Test actual HTTP request to running server"""
        nginx = ReverseProxy()
        server = create_server(listen=18081)
        server.locations.append(create_location("/test"))
        nginx.add_server(server)
        
        nginx.start()
        time.sleep(0.5)
        
        try:
            # Make HTTP request
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("127.0.0.1", 18081))
            client.sendall(b"GET /test HTTP/1.1\r\nHost: localhost\r\n\r\n")
            
            response = client.recv(4096)
            client.close()
            
            self.assertIn(b"HTTP/1.1 200 OK", response)
            self.assertIn(b"Nginx-Emulator", response)
        
        finally:
            nginx.stop()


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
