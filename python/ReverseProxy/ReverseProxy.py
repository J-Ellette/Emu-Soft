"""
Developed by PowerShield, as an alternative to Nginx
"""

#!/usr/bin/env python3
"""
Nginx Emulator - Web Server and Reverse Proxy

This module emulates core Nginx functionality including:
- HTTP server configuration
- Reverse proxy capabilities
- Load balancing
- Virtual hosts (server blocks)
- Location-based routing
- Static file serving
- Request/response headers manipulation
"""

import socket
import threading
from typing import Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class LoadBalanceMethod(Enum):
    """Load balancing algorithms"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONN = "least_conn"
    IP_HASH = "ip_hash"


@dataclass
class UpstreamServer:
    """Backend server in upstream group"""
    host: str
    port: int
    weight: int = 1
    max_fails: int = 3
    fail_timeout: int = 10
    backup: bool = False
    down: bool = False
    connections: int = 0


@dataclass
class Location:
    """Location block configuration"""
    path: str
    root: Optional[str] = None
    proxy_pass: Optional[str] = None
    alias: Optional[str] = None
    index: List[str] = field(default_factory=lambda: ["index.html"])
    try_files: List[str] = field(default_factory=list)
    return_code: Optional[int] = None
    return_url: Optional[str] = None
    add_headers: Dict[str, str] = field(default_factory=dict)
    handler: Optional[Callable] = None


@dataclass
class ServerBlock:
    """Server block (virtual host) configuration"""
    listen: int = 80
    server_name: List[str] = field(default_factory=lambda: ["localhost"])
    root: Optional[str] = None
    index: List[str] = field(default_factory=lambda: ["index.html"])
    locations: List[Location] = field(default_factory=list)
    access_log: Optional[str] = None
    error_log: Optional[str] = None
    client_max_body_size: str = "1m"


@dataclass
class Upstream:
    """Upstream server group for load balancing"""
    name: str
    servers: List[UpstreamServer] = field(default_factory=list)
    method: LoadBalanceMethod = LoadBalanceMethod.ROUND_ROBIN
    keepalive: int = 32
    current_index: int = 0


class Request:
    """HTTP Request representation"""
    def __init__(self, method: str, path: str, headers: Dict[str, str], 
                 body: str = "", query_string: str = ""):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
        self.query_string = query_string
        self.client_ip = ""
    
    @classmethod
    def parse(cls, raw_request: str, client_address: Tuple[str, int]):
        """Parse raw HTTP request"""
        lines = raw_request.split('\r\n')
        if not lines:
            return None
        
        # Parse request line
        request_line = lines[0].split(' ')
        if len(request_line) < 3:
            return None
        
        method, full_path, _ = request_line
        path = full_path.split('?')[0]
        query_string = full_path.split('?')[1] if '?' in full_path else ""
        
        # Parse headers
        headers = {}
        body_start = 0
        for i, line in enumerate(lines[1:], 1):
            if line == '':
                body_start = i + 1
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        
        # Parse body
        body = '\r\n'.join(lines[body_start:]) if body_start < len(lines) else ""
        
        req = cls(method, path, headers, body, query_string)
        req.client_ip = client_address[0]
        return req


class Response:
    """HTTP Response builder"""
    def __init__(self, status_code: int = 200, status_text: str = "OK"):
        self.status_code = status_code
        self.status_text = status_text
        self.headers: Dict[str, str] = {
            "Server": "Nginx-Emulator/1.0",
            "Content-Type": "text/html"
        }
        self.body = ""
    
    def set_header(self, key: str, value: str):
        """Set response header"""
        self.headers[key] = value
        return self
    
    def set_body(self, body: str):
        """Set response body"""
        self.body = body
        return self
    
    def json(self, data: dict):
        """Set JSON response"""
        self.headers["Content-Type"] = "application/json"
        self.body = json.dumps(data)
        return self
    
    def to_bytes(self) -> bytes:
        """Convert response to HTTP wire format"""
        response_lines = [
            f"HTTP/1.1 {self.status_code} {self.status_text}",
        ]
        
        # Add Content-Length if not present
        if "Content-Length" not in self.headers:
            self.headers["Content-Length"] = str(len(self.body.encode('utf-8')))
        
        # Add headers
        for key, value in self.headers.items():
            response_lines.append(f"{key}: {value}")
        
        # Add body
        response_lines.append("")
        response_lines.append(self.body)
        
        return '\r\n'.join(response_lines).encode('utf-8')


class ReverseProxy:
    """Main Nginx emulator class"""
    
    def __init__(self):
        self.server_blocks: List[ServerBlock] = []
        self.upstreams: Dict[str, Upstream] = {}
        self.running = False
        self.threads: List[threading.Thread] = []
    
    def add_server(self, server: ServerBlock):
        """Add server block configuration"""
        self.server_blocks.append(server)
    
    def add_upstream(self, upstream: Upstream):
        """Add upstream server group"""
        self.upstreams[upstream.name] = upstream
    
    def _get_next_upstream_server(self, upstream: Upstream) -> Optional[UpstreamServer]:
        """Get next server from upstream group based on load balancing method"""
        available_servers = [s for s in upstream.servers if not s.down]
        
        if not available_servers:
            return None
        
        if upstream.method == LoadBalanceMethod.ROUND_ROBIN:
            server = available_servers[upstream.current_index % len(available_servers)]
            upstream.current_index += 1
            return server
        
        elif upstream.method == LoadBalanceMethod.LEAST_CONN:
            return min(available_servers, key=lambda s: s.connections)
        
        elif upstream.method == LoadBalanceMethod.IP_HASH:
            # Simplified IP hash - just use round robin for emulation
            server = available_servers[upstream.current_index % len(available_servers)]
            upstream.current_index += 1
            return server
        
        return available_servers[0]
    
    def _match_location(self, server: ServerBlock, path: str) -> Optional[Location]:
        """Match request path to location block"""
        # Exact match first
        for location in server.locations:
            if location.path == path:
                return location
        
        # Prefix match (longest wins)
        matches = []
        for location in server.locations:
            if path.startswith(location.path):
                matches.append(location)
        
        if matches:
            return max(matches, key=lambda loc: len(loc.path))
        
        return None
    
    def _handle_request(self, request: Request) -> Response:
        """Handle incoming HTTP request"""
        # Find matching server block
        server = None
        host_header = request.headers.get('host', 'localhost').split(':')[0]
        
        for srv in self.server_blocks:
            if host_header in srv.server_name or 'localhost' in srv.server_name:
                server = srv
                break
        
        if not server:
            return Response(404, "Not Found").set_body("<h1>404 Not Found</h1>")
        
        # Find matching location
        location = self._match_location(server, request.path)
        
        if not location:
            return Response(404, "Not Found").set_body("<h1>404 Not Found</h1>")
        
        # Apply additional headers from location
        response = Response()
        for key, value in location.add_headers.items():
            response.set_header(key, value)
        
        # Handle return directive
        if location.return_code:
            if location.return_url:
                response.status_code = location.return_code
                response.set_header("Location", location.return_url)
            else:
                response.status_code = location.return_code
            return response
        
        # Handle custom handler
        if location.handler:
            return location.handler(request)
        
        # Handle proxy_pass (reverse proxy)
        if location.proxy_pass:
            upstream_name = location.proxy_pass.replace("http://", "")
            if upstream_name in self.upstreams:
                upstream = self.upstreams[upstream_name]
                server = self._get_next_upstream_server(upstream)
                if server:
                    response.set_body(f"<h1>Proxied to {server.host}:{server.port}</h1>")
                    response.set_header("X-Upstream-Server", f"{server.host}:{server.port}")
                    return response
            
            response.set_body(f"<h1>Proxy to {location.proxy_pass}</h1>")
            return response
        
        # Handle static file serving
        if location.root or server.root:
            response.set_body("<h1>Static Content</h1><p>File serving emulated</p>")
            return response
        
        return Response(200, "OK").set_body("<h1>Welcome to Nginx Emulator</h1>")
    
    def _handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle client connection"""
        try:
            # Receive request
            raw_request = client_socket.recv(4096).decode('utf-8')
            
            if not raw_request:
                return
            
            # Parse request
            request = Request.parse(raw_request, client_address)
            
            if not request:
                response = Response(400, "Bad Request")
            else:
                response = self._handle_request(request)
            
            # Send response
            client_socket.sendall(response.to_bytes())
        
        except Exception as e:
            error_response = Response(500, "Internal Server Error")
            error_response.set_body(f"<h1>500 Internal Server Error</h1><p>{str(e)}</p>")
            client_socket.sendall(error_response.to_bytes())
        
        finally:
            client_socket.close()
    
    def _run_server(self, server: ServerBlock):
        """Run server block listener"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', server.listen))
            server_socket.listen(5)
            server_socket.settimeout(1.0)  # Timeout to allow checking self.running
            
            print(f"[Nginx] Server listening on port {server.listen}")
            
            while self.running:
                try:
                    client_socket, client_address = server_socket.accept()
                    # Handle each client in a thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[Nginx] Error: {e}")
        
        finally:
            server_socket.close()
    
    def start(self):
        """Start all configured server blocks"""
        if self.running:
            return
        
        self.running = True
        
        for server in self.server_blocks:
            thread = threading.Thread(target=self._run_server, args=(server,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
    
    def stop(self):
        """Stop all server blocks"""
        self.running = False
        
        for thread in self.threads:
            thread.join(timeout=2.0)
        
        self.threads.clear()
    
    def reload(self):
        """Reload configuration (graceful restart)"""
        print("[Nginx] Reloading configuration...")
        # In a real implementation, this would reload config without dropping connections
        self.stop()
        self.start()


# Convenience functions
def create_server(listen: int = 80, server_name: List[str] = None) -> ServerBlock:
    """Create a server block"""
    if server_name is None:
        server_name = ["localhost"]
    return ServerBlock(listen=listen, server_name=server_name)


def create_location(path: str, **kwargs) -> Location:
    """Create a location block"""
    return Location(path=path, **kwargs)


def create_upstream(name: str, method: LoadBalanceMethod = LoadBalanceMethod.ROUND_ROBIN) -> Upstream:
    """Create an upstream group"""
    return Upstream(name=name, method=method)


def add_upstream_server(upstream: Upstream, host: str, port: int, weight: int = 1):
    """Add server to upstream group"""
    server = UpstreamServer(host=host, port=port, weight=weight)
    upstream.servers.append(server)


if __name__ == "__main__":
    # Example usage
    nginx = ReverseProxy()
    
    # Create upstream for load balancing
    app_upstream = create_upstream("app_servers", LoadBalanceMethod.ROUND_ROBIN)
    add_upstream_server(app_upstream, "127.0.0.1", 8001)
    add_upstream_server(app_upstream, "127.0.0.1", 8002)
    nginx.add_upstream(app_upstream)
    
    # Create server block
    server = create_server(listen=8080, server_name=["localhost", "example.com"])
    
    # Add locations
    server.locations.append(create_location("/", root="/var/www/html"))
    server.locations.append(create_location("/api", proxy_pass="http://app_servers"))
    server.locations.append(create_location("/static", alias="/var/www/static"))
    
    nginx.add_server(server)
    
    print("Starting Nginx emulator...")
    nginx.start()
    
    try:
        import time
        time.sleep(60)  # Run for 60 seconds
    except KeyboardInterrupt:
        pass
    
    nginx.stop()
    print("Nginx emulator stopped")
