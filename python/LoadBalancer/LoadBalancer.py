"""
Developed by PowerShield, as an alternative to Nginx


Nginx Emulator - Configuration and Reverse Proxy
Emulates Nginx functionality for configuration parsing, reverse proxy, and load balancing
"""

import socket
import asyncio
import threading
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from urllib.parse import urlparse
import traceback


class NginxConfig:
    """Parse and represent Nginx configuration"""
    
    def __init__(self, config_text: str = ""):
        self.config_text = config_text
        self.servers: List[Dict[str, Any]] = []
        self.upstreams: Dict[str, List[str]] = {}
        self.http_directives: Dict[str, Any] = {}
        
        if config_text:
            self.parse()
    
    def parse(self):
        """Parse Nginx configuration"""
        # Remove comments
        lines = []
        for line in self.config_text.split('\n'):
            if '#' in line:
                line = line[:line.index('#')]
            lines.append(line.strip())
        
        text = ' '.join(lines)
        
        # Parse upstream blocks
        self._parse_upstreams(text)
        
        # Parse server blocks
        self._parse_servers(text)
    
    def _parse_upstreams(self, text: str):
        """Parse upstream blocks"""
        i = 0
        while i < len(text):
            # Find "upstream"
            upstream_pos = text.find('upstream', i)
            if upstream_pos == -1:
                break
            
            # Find upstream name
            name_start = upstream_pos + 8
            while name_start < len(text) and text[name_start].isspace():
                name_start += 1
            
            name_end = name_start
            while name_end < len(text) and (text[name_end].isalnum() or text[name_end] in '_-'):
                name_end += 1
            
            name = text[name_start:name_end].strip()
            
            # Find opening brace
            brace_pos = text.find('{', name_end)
            if brace_pos == -1:
                break
            
            # Find matching closing brace
            block_start = brace_pos + 1
            block_end = self._find_matching_brace(text, brace_pos)
            if block_end == -1:
                break
            
            block = text[block_start:block_end]
            
            # Extract servers
            servers = []
            server_pattern = r'server\s+([^;]+);'
            for match in re.finditer(server_pattern, block):
                servers.append(match.group(1).strip())
            
            self.upstreams[name] = servers
            i = block_end + 1
    
    def _parse_servers(self, text: str):
        """Parse server blocks"""
        i = 0
        while i < len(text):
            # Find "server"
            server_pos = text.find('server', i)
            if server_pos == -1:
                break
            
            # Make sure it's "server {" not "server something;"
            next_char_pos = server_pos + 6
            while next_char_pos < len(text) and text[next_char_pos].isspace():
                next_char_pos += 1
            
            if next_char_pos >= len(text) or text[next_char_pos] != '{':
                i = next_char_pos
                continue
            
            # Find matching closing brace
            block_start = next_char_pos + 1
            block_end = self._find_matching_brace(text, next_char_pos)
            if block_end == -1:
                break
            
            block = text[block_start:block_end]
            server = self._parse_server_block(block)
            if server:
                self.servers.append(server)
            
            i = block_end + 1
    
    def _find_matching_brace(self, text: str, start: int) -> int:
        """Find matching closing brace"""
        if start >= len(text) or text[start] != '{':
            return -1
        
        count = 1
        i = start + 1
        
        while i < len(text) and count > 0:
            if text[i] == '{':
                count += 1
            elif text[i] == '}':
                count -= 1
            i += 1
        
        if count == 0:
            return i - 1
        return -1
    
    def _parse_server_block(self, block: str) -> Dict[str, Any]:
        """Parse a server block"""
        server = {
            'listen': [],
            'server_name': [],
            'locations': [],
            'directives': {}
        }
        
        # Parse listen directives
        listen_pattern = r'listen\s+([^;]+);'
        for match in re.finditer(listen_pattern, block):
            server['listen'].append(match.group(1).strip())
        
        # Parse server_name
        name_pattern = r'server_name\s+([^;]+);'
        match = re.search(name_pattern, block)
        if match:
            server['server_name'] = match.group(1).strip().split()
        
        # Parse location blocks
        self._parse_locations(block, server)
        
        # Parse other directives
        directive_pattern = r'(\w+)\s+([^;]+);'
        for match in re.finditer(directive_pattern, block):
            directive = match.group(1)
            value = match.group(2).strip()
            
            # Skip already parsed directives
            if directive not in ('listen', 'server_name', 'location', 'server'):
                server['directives'][directive] = value
        
        return server
    
    def _parse_locations(self, block: str, server: Dict[str, Any]):
        """Parse location blocks within a server block"""
        i = 0
        while i < len(block):
            # Find "location"
            location_pos = block.find('location', i)
            if location_pos == -1:
                break
            
            # Find path
            path_start = location_pos + 8
            while path_start < len(block) and block[path_start].isspace():
                path_start += 1
            
            # Find opening brace
            brace_pos = block.find('{', path_start)
            if brace_pos == -1:
                break
            
            path = block[path_start:brace_pos].strip()
            
            # Find matching closing brace
            loc_block_start = brace_pos + 1
            loc_block_end = self._find_matching_brace(block, brace_pos)
            if loc_block_end == -1:
                break
            
            location_block = block[loc_block_start:loc_block_end]
            location = self._parse_location_block(path, location_block)
            server['locations'].append(location)
            
            i = loc_block_end + 1
    
    def _parse_location_block(self, path: str, block: str) -> Dict[str, Any]:
        """Parse a location block"""
        location = {
            'path': path,
            'directives': {}
        }
        
        # Parse proxy_pass
        proxy_pattern = r'proxy_pass\s+([^;]+);'
        match = re.search(proxy_pattern, block)
        if match:
            location['directives']['proxy_pass'] = match.group(1).strip()
        
        # Parse other directives
        directive_pattern = r'(\w+)\s+([^;]+);'
        for match in re.finditer(directive_pattern, block):
            directive = match.group(1)
            value = match.group(2).strip()
            location['directives'][directive] = value
        
        return location
    
    @classmethod
    def from_file(cls, filepath: str) -> 'NginxConfig':
        """Load configuration from file"""
        with open(filepath, 'r') as f:
            config_text = f.read()
        return cls(config_text)
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'NginxConfig':
        """Create configuration from dictionary"""
        obj = cls()
        obj.servers = config.get('servers', [])
        obj.upstreams = config.get('upstreams', {})
        obj.http_directives = config.get('http', {})
        return obj


class LoadBalancer:
    """Load balancing strategies"""
    
    def __init__(self, strategy: str = 'round_robin'):
        self.strategy = strategy
        self.counters: Dict[str, int] = {}
    
    def select_backend(self, upstream_name: str, backends: List[str]) -> Optional[str]:
        """Select a backend server"""
        if not backends:
            return None
        
        if self.strategy == 'round_robin':
            return self._round_robin(upstream_name, backends)
        elif self.strategy == 'least_conn':
            return self._least_connections(upstream_name, backends)
        elif self.strategy == 'ip_hash':
            return self._ip_hash(upstream_name, backends)
        else:
            return backends[0]
    
    def _round_robin(self, upstream_name: str, backends: List[str]) -> str:
        """Round-robin selection"""
        if upstream_name not in self.counters:
            self.counters[upstream_name] = 0
        
        index = self.counters[upstream_name] % len(backends)
        self.counters[upstream_name] += 1
        return backends[index]
    
    def _least_connections(self, upstream_name: str, backends: List[str]) -> str:
        """Least connections selection (simplified: just round-robin for now)"""
        return self._round_robin(upstream_name, backends)
    
    def _ip_hash(self, upstream_name: str, backends: List[str]) -> str:
        """IP hash selection (simplified)"""
        # In a real implementation, this would hash the client IP
        return backends[0]


class ReverseProxy:
    """Reverse proxy implementation"""
    
    def __init__(self, config: NginxConfig, load_balancer: LoadBalancer = None):
        self.config = config
        self.load_balancer = load_balancer or LoadBalancer()
    
    def find_matching_server(self, host: str, port: int) -> Optional[Dict[str, Any]]:
        """Find matching server configuration"""
        for server in self.config.servers:
            for listen in server['listen']:
                # Parse listen directive
                listen_parts = listen.split()
                listen_addr = listen_parts[0]
                
                # Check if port matches
                if ':' in listen_addr:
                    listen_host, listen_port = listen_addr.rsplit(':', 1)
                    if int(listen_port) == port:
                        return server
                else:
                    # Just a port number
                    if int(listen_addr) == port:
                        return server
        
        return None
    
    def find_matching_location(self, server: Dict[str, Any], path: str) -> Optional[Dict[str, Any]]:
        """Find matching location for path"""
        # Sort by specificity (longer paths first)
        locations = sorted(
            server['locations'],
            key=lambda loc: len(loc['path']),
            reverse=True
        )
        
        for location in locations:
            loc_path = location['path']
            
            # Exact match
            if loc_path.startswith('='):
                if path == loc_path[1:].strip():
                    return location
            # Prefix match
            elif loc_path.startswith('^~'):
                if path.startswith(loc_path[2:].strip()):
                    return location
            # Regex match
            elif loc_path.startswith('~'):
                pattern = loc_path[1:].strip()
                if re.match(pattern, path):
                    return location
            # Regular prefix match
            else:
                if path.startswith(loc_path):
                    return location
        
        return None
    
    def resolve_proxy_pass(self, proxy_pass: str) -> Optional[Tuple[str, int, str]]:
        """Resolve proxy_pass URL to (host, port, path)"""
        # Handle upstream references
        if proxy_pass.startswith('http://'):
            url = proxy_pass[7:]  # Remove http://
            
            # Check if it's an upstream name
            if '/' in url:
                upstream_name, path = url.split('/', 1)
                path = '/' + path
            else:
                upstream_name = url
                path = '/'
            
            # Check if it's an upstream
            if upstream_name in self.config.upstreams:
                backends = self.config.upstreams[upstream_name]
                backend = self.load_balancer.select_backend(upstream_name, backends)
                
                if backend:
                    # Parse backend address
                    if ':' in backend:
                        host, port = backend.rsplit(':', 1)
                        return (host, int(port), path)
                    else:
                        return (backend, 80, path)
            else:
                # Direct host:port
                if ':' in upstream_name:
                    host, port = upstream_name.rsplit(':', 1)
                    return (host, int(port), path)
                else:
                    return (upstream_name, 80, path)
        
        return None
    
    def proxy_request(self, method: str, path: str, headers: Dict[str, str],
                     body: bytes, target_host: str, target_port: int,
                     target_path: str) -> Tuple[int, Dict[str, str], bytes]:
        """Proxy request to backend"""
        try:
            # Create socket to backend
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((target_host, target_port))
            
            # Build request
            request_line = f"{method} {target_path} HTTP/1.1\r\n"
            
            # Update Host header
            headers = headers.copy()
            headers['Host'] = f"{target_host}:{target_port}"
            
            # Build header lines
            header_lines = [f"{k}: {v}" for k, v in headers.items()]
            
            # Build full request
            request = request_line + '\r\n'.join(header_lines) + '\r\n\r\n'
            sock.sendall(request.encode('utf-8') + body)
            
            # Receive response
            response_data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                
                # Check if we have complete response
                if b'\r\n\r\n' in response_data:
                    # Simple check: if we have headers, we might have body too
                    headers_end = response_data.index(b'\r\n\r\n')
                    headers_part = response_data[:headers_end]
                    
                    # Check for Content-Length
                    if b'Content-Length:' in headers_part:
                        # Extract content length
                        for line in headers_part.split(b'\r\n'):
                            if line.lower().startswith(b'content-length:'):
                                length = int(line.split(b':', 1)[1].strip())
                                body_part = response_data[headers_end + 4:]
                                if len(body_part) >= length:
                                    break
                    else:
                        # No content-length, assume we have everything after a short wait
                        sock.settimeout(0.5)
                        try:
                            chunk = sock.recv(4096)
                            if chunk:
                                response_data += chunk
                        except socket.timeout:
                            break
                        break
            
            sock.close()
            
            # Parse response
            if b'\r\n\r\n' not in response_data:
                return (502, {'Content-Type': 'text/plain'}, b'Bad Gateway')
            
            headers_part, body_part = response_data.split(b'\r\n\r\n', 1)
            lines = headers_part.decode('utf-8', errors='ignore').split('\r\n')
            
            # Parse status line
            status_line = lines[0]
            status_code = int(status_line.split(' ')[1])
            
            # Parse headers
            response_headers = {}
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    response_headers[key.strip()] = value.strip()
            
            return (status_code, response_headers, body_part)
        
        except Exception as e:
            print(f"Proxy error: {e}")
            traceback.print_exc()
            return (502, {'Content-Type': 'text/plain'}, b'Bad Gateway')


class NginxEmulator:
    """Main Nginx emulator class"""
    
    def __init__(self, config: NginxConfig, load_balancer: LoadBalancer = None):
        self.config = config
        self.load_balancer = load_balancer or LoadBalancer()
        self.proxy = ReverseProxy(config, self.load_balancer)
        self.servers: List[threading.Thread] = []
        self.running = False
    
    def start(self):
        """Start all configured servers"""
        self.running = True
        
        # Start a server for each listen directive
        unique_ports = set()
        for server in self.config.servers:
            for listen in server['listen']:
                # Parse listen directive
                listen_parts = listen.split()
                listen_addr = listen_parts[0]
                
                if ':' in listen_addr:
                    host, port = listen_addr.rsplit(':', 1)
                    port = int(port)
                else:
                    host = '0.0.0.0'
                    port = int(listen_addr)
                
                if port not in unique_ports:
                    unique_ports.add(port)
                    thread = threading.Thread(
                        target=self._run_server,
                        args=(host, port),
                        daemon=True
                    )
                    thread.start()
                    self.servers.append(thread)
                    print(f"[Nginx] Listening on {host}:{port}")
    
    def _run_server(self, host: str, port: int):
        """Run a server on specified port"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(100)
        sock.settimeout(1.0)
        
        while self.running:
            try:
                conn, addr = sock.accept()
                threading.Thread(
                    target=self._handle_request,
                    args=(conn, addr, host, port),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
        
        sock.close()
    
    def _handle_request(self, conn: socket.socket, addr: tuple, host: str, port: int):
        """Handle incoming request"""
        try:
            # Receive request
            data = conn.recv(16384)
            if not data:
                return
            
            # Parse request
            lines = data.split(b'\r\n')
            request_line = lines[0].decode('utf-8', errors='ignore')
            parts = request_line.split(' ')
            
            if len(parts) < 3:
                return
            
            method = parts[0]
            path = parts[1]
            
            # Parse headers
            headers = {}
            body_start = None
            for i, line in enumerate(lines[1:], 1):
                if not line:
                    body_start = i + 1
                    break
                
                line_str = line.decode('utf-8', errors='ignore')
                if ':' in line_str:
                    key, value = line_str.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            # Get body
            body = b''
            if body_start and body_start < len(lines):
                if b'\r\n\r\n' in data:
                    body = data.split(b'\r\n\r\n', 1)[1]
            
            # Find matching server
            server = self.proxy.find_matching_server(host, port)
            if not server:
                self._send_error(conn, 404, 'Not Found')
                return
            
            # Find matching location
            location = self.proxy.find_matching_location(server, path)
            if not location:
                self._send_error(conn, 404, 'Not Found')
                return
            
            # Handle proxy_pass
            proxy_pass = location['directives'].get('proxy_pass')
            if proxy_pass:
                target = self.proxy.resolve_proxy_pass(proxy_pass)
                if target:
                    target_host, target_port, target_path = target
                    
                    # Proxy the request
                    status, resp_headers, resp_body = self.proxy.proxy_request(
                        method, path, headers, body,
                        target_host, target_port, target_path
                    )
                    
                    # Send response
                    self._send_response(conn, status, resp_headers, resp_body)
                else:
                    self._send_error(conn, 502, 'Bad Gateway')
            else:
                # No proxy_pass, return 404
                self._send_error(conn, 404, 'Not Found')
        
        except Exception as e:
            print(f"Error handling request: {e}")
            traceback.print_exc()
            try:
                self._send_error(conn, 500, 'Internal Server Error')
            except:
                pass
        finally:
            try:
                conn.close()
            except:
                pass
    
    def _send_response(self, conn: socket.socket, status: int,
                      headers: Dict[str, str], body: bytes):
        """Send HTTP response"""
        # Build status line
        status_text = {
            200: 'OK',
            404: 'Not Found',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable'
        }.get(status, 'Unknown')
        
        response = f"HTTP/1.1 {status} {status_text}\r\n".encode('utf-8')
        
        # Add headers
        for key, value in headers.items():
            response += f"{key}: {value}\r\n".encode('utf-8')
        
        response += b'\r\n'
        response += body
        
        conn.sendall(response)
    
    def _send_error(self, conn: socket.socket, status: int, message: str):
        """Send error response"""
        headers = {'Content-Type': 'text/plain'}
        body = message.encode('utf-8')
        self._send_response(conn, status, headers, body)
    
    def stop(self):
        """Stop all servers"""
        print("[Nginx] Stopping...")
        self.running = False
        
        # Wait for threads
        for thread in self.servers:
            thread.join(timeout=5)
        
        print("[Nginx] Stopped")
    
    @staticmethod
    def run(config: NginxConfig, daemon: bool = False):
        """Run Nginx emulator"""
        emulator = NginxEmulator(config)
        emulator.start()
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            emulator.stop()


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nginx Emulator')
    parser.add_argument('-c', '--config', required=True,
                       help='Configuration file path')
    parser.add_argument('-t', '--test', action='store_true',
                       help='Test configuration and exit')
    
    args = parser.parse_args()
    
    # Load configuration
    config = NginxConfig.from_file(args.config)
    
    if args.test:
        print("Configuration OK")
        print(f"Found {len(config.servers)} server(s)")
        print(f"Found {len(config.upstreams)} upstream(s)")
        return
    
    # Run emulator
    NginxEmulator.run(config)


if __name__ == '__main__':
    main()
