"""
Developed by PowerShield, as an alternative to Uvicorn


Uvicorn Emulator - ASGI Server
Emulates Uvicorn functionality for serving ASGI applications
"""

import asyncio
import socket
import sys
import time
import importlib
import importlib.util
from typing import Dict, Any, Callable, Optional, List
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json
import traceback


class ASGIRequest:
    """Represents an ASGI HTTP request"""
    
    def __init__(self, raw_request: bytes, client_addr: tuple):
        self.raw_request = raw_request
        self.client_addr = client_addr
        self.method = ""
        self.path = "/"
        self.query_string = b""
        self.headers = {}
        self.body = b""
        self._parse_request()
    
    def _parse_request(self):
        """Parse HTTP request"""
        try:
            lines = self.raw_request.split(b'\r\n')
            if not lines:
                return
            
            # Parse request line
            request_line = lines[0].decode('utf-8', errors='ignore')
            parts = request_line.split(' ')
            if len(parts) >= 2:
                self.method = parts[0]
                url = parts[1]
                
                # Parse URL
                if '?' in url:
                    self.path, query = url.split('?', 1)
                    self.query_string = query.encode('utf-8')
                else:
                    self.path = url
            
            # Parse headers
            body_start = None
            for i, line in enumerate(lines[1:], 1):
                if not line:
                    body_start = i + 1
                    break
                
                line_str = line.decode('utf-8', errors='ignore')
                if ':' in line_str:
                    key, value = line_str.split(':', 1)
                    self.headers[key.strip().lower()] = value.strip()
            
            # Parse body
            if body_start and body_start < len(lines):
                self.body = b'\r\n'.join(lines[body_start:])
        
        except Exception as e:
            print(f"Error parsing request: {e}")
    
    def to_asgi_scope(self) -> Dict[str, Any]:
        """Convert to ASGI scope dictionary"""
        return {
            'type': 'http',
            'asgi': {'version': '3.0'},
            'http_version': '1.1',
            'method': self.method,
            'scheme': 'http',
            'path': self.path,
            'query_string': self.query_string,
            'root_path': '',
            'headers': [
                (k.encode('latin-1'), v.encode('latin-1'))
                for k, v in self.headers.items()
            ],
            'server': ('127.0.0.1', 8000),
            'client': self.client_addr,
        }


class ASGIResponse:
    """Builds HTTP response from ASGI messages"""
    
    def __init__(self):
        self.status_code = 200
        self.headers = []
        self.body = b""
    
    def add_start_event(self, event: Dict[str, Any]):
        """Handle http.response.start event"""
        self.status_code = event.get('status', 200)
        self.headers = event.get('headers', [])
    
    def add_body_event(self, event: Dict[str, Any]):
        """Handle http.response.body event"""
        body = event.get('body', b'')
        if body:
            self.body += body
    
    def to_http_response(self) -> bytes:
        """Convert to HTTP response bytes"""
        # Status line
        response = f"HTTP/1.1 {self.status_code} OK\r\n".encode('utf-8')
        
        # Headers
        for name, value in self.headers:
            if isinstance(name, bytes):
                name = name.decode('latin-1')
            if isinstance(value, bytes):
                value = value.decode('latin-1')
            response += f"{name}: {value}\r\n".encode('utf-8')
        
        # Content-Length if not present
        has_content_length = any(
            h[0].lower() == b'content-length' if isinstance(h[0], bytes) else h[0].lower() == 'content-length'
            for h in self.headers
        )
        if not has_content_length and self.body:
            response += f"Content-Length: {len(self.body)}\r\n".encode('utf-8')
        
        response += b"\r\n"
        response += self.body
        
        return response


class FileWatcher:
    """Watches files for changes to trigger auto-reload"""
    
    def __init__(self, paths: List[str]):
        self.paths = [Path(p) for p in paths]
        self.file_mtimes: Dict[Path, float] = {}
        self._scan_files()
    
    def _scan_files(self):
        """Scan all Python files and record modification times"""
        for path in self.paths:
            if path.is_file():
                self.file_mtimes[path] = path.stat().st_mtime
            elif path.is_dir():
                for py_file in path.rglob('*.py'):
                    self.file_mtimes[py_file] = py_file.stat().st_mtime
    
    def check_changes(self) -> bool:
        """Check if any files have changed"""
        for path, old_mtime in list(self.file_mtimes.items()):
            try:
                if not path.exists():
                    return True
                
                new_mtime = path.stat().st_mtime
                if new_mtime != old_mtime:
                    return True
            except Exception:
                pass
        
        # Check for new files
        current_files = set()
        for path in self.paths:
            if path.is_file():
                current_files.add(path)
            elif path.is_dir():
                for py_file in path.rglob('*.py'):
                    current_files.add(py_file)
        
        if current_files != set(self.file_mtimes.keys()):
            return True
        
        return False


class ASGIServer:
    """ASGI HTTP server implementation"""
    
    def __init__(self, app: Callable, host: str = '127.0.0.1', 
                 port: int = 8000, reload: bool = False, 
                 reload_dirs: Optional[List[str]] = None):
        self.app = app
        self.host = host
        self.port = port
        self.reload = reload
        self.reload_dirs = reload_dirs or ['.']
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.file_watcher = None
        
        if self.reload:
            self.file_watcher = FileWatcher(self.reload_dirs)
    
    async def handle_client(self, client_socket: socket.socket, 
                           client_addr: tuple):
        """Handle a client connection"""
        try:
            # Receive request
            request_data = b""
            client_socket.settimeout(5.0)
            
            while True:
                try:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    request_data += chunk
                    
                    # Check if we have complete request
                    if b'\r\n\r\n' in request_data:
                        # Check if there's a body
                        headers_end = request_data.index(b'\r\n\r\n')
                        headers_part = request_data[:headers_end].decode('utf-8', errors='ignore')
                        
                        # Check Content-Length
                        content_length = 0
                        for line in headers_part.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                content_length = int(line.split(':', 1)[1].strip())
                                break
                        
                        body_received = len(request_data) - (headers_end + 4)
                        if body_received >= content_length:
                            break
                
                except socket.timeout:
                    break
            
            if not request_data:
                return
            
            # Parse request
            request = ASGIRequest(request_data, client_addr)
            
            # Create ASGI scope
            scope = request.to_asgi_scope()
            
            # Handle request
            response = await self._call_asgi_app(scope, request.body)
            
            # Send response
            client_socket.sendall(response.to_http_response())
        
        except Exception as e:
            print(f"Error handling client: {e}")
            traceback.print_exc()
            
            # Send 500 error
            error_response = (
                b"HTTP/1.1 500 Internal Server Error\r\n"
                b"Content-Type: text/plain\r\n"
                b"Content-Length: 21\r\n"
                b"\r\n"
                b"Internal Server Error"
            )
            try:
                client_socket.sendall(error_response)
            except:
                pass
        
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    async def _call_asgi_app(self, scope: Dict[str, Any], 
                            body: bytes) -> ASGIResponse:
        """Call ASGI application"""
        response = ASGIResponse()
        body_sent = False
        
        async def receive():
            """ASGI receive callable"""
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {
                    'type': 'http.request',
                    'body': body,
                    'more_body': False
                }
            return {
                'type': 'http.disconnect'
            }
        
        async def send(message: Dict[str, Any]):
            """ASGI send callable"""
            msg_type = message.get('type')
            
            if msg_type == 'http.response.start':
                response.add_start_event(message)
            elif msg_type == 'http.response.body':
                response.add_body_event(message)
        
        # Call the ASGI app
        await self.app(scope, receive, send)
        
        return response
    
    def start(self):
        """Start the server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)
        self.running = True
        
        print(f"✓ ASGI server started at http://{self.host}:{self.port}")
        if self.reload:
            print("  ↻ Auto-reload enabled")
        print("  Press CTRL+C to quit")
        
        asyncio.run(self._serve())
    
    async def _serve(self):
        """Main server loop"""
        last_check = time.time()
        check_interval = 1.0  # Check for file changes every second
        
        while self.running:
            try:
                # Check for file changes if reload is enabled
                if self.reload and (time.time() - last_check) > check_interval:
                    if self.file_watcher.check_changes():
                        print("\n⟳ Detected file changes, reloading...")
                        self.running = False
                        break
                    last_check = time.time()
                
                # Accept connections with timeout
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    # Handle in background
                    asyncio.create_task(
                        self.handle_client(client_socket, client_addr)
                    )
                except socket.timeout:
                    # No connection, continue loop
                    await asyncio.sleep(0.01)
                    continue
            
            except KeyboardInterrupt:
                print("\n⊗ Shutting down server...")
                self.running = False
                break
            except Exception as e:
                print(f"Server error: {e}")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


class UvicornEmulator:
    """Main Uvicorn emulator interface"""
    
    @staticmethod
    def run(app: str, host: str = '127.0.0.1', port: int = 8000,
            reload: bool = False, reload_dirs: Optional[List[str]] = None,
            log_level: str = 'info'):
        """
        Run ASGI application
        
        Args:
            app: Application import string (e.g., "main:app")
            host: Bind host
            port: Bind port
            reload: Enable auto-reload
            reload_dirs: Directories to watch for changes
            log_level: Logging level
        """
        # Import the application
        try:
            if ':' in app:
                module_path, app_name = app.split(':', 1)
            else:
                module_path = app
                app_name = 'app'
            
            # Import module
            if '/' in module_path or module_path.endswith('.py'):
                # Load from file path
                module_path = module_path.replace('.py', '')
                spec = importlib.util.spec_from_file_location("app_module", f"{module_path}.py")
                module = importlib.util.module_from_spec(spec)
                sys.modules["app_module"] = module
                spec.loader.exec_module(module)
            else:
                # Import as module
                module = importlib.import_module(module_path)
            
            # Get app
            app_callable = getattr(module, app_name)
            
        except Exception as e:
            print(f"Error loading application: {e}")
            traceback.print_exc()
            return
        
        # Create and start server
        while True:
            server = ASGIServer(
                app=app_callable,
                host=host,
                port=port,
                reload=reload,
                reload_dirs=reload_dirs
            )
            
            try:
                server.start()
            except KeyboardInterrupt:
                print("\n⊗ Server stopped")
                break
            
            # If reload is enabled and server stopped due to file changes, restart
            if reload and not server.running:
                print("⟳ Restarting server...")
                # Reload the module
                try:
                    if '/' in module_path or module_path.endswith('.py'):
                        module_path_file = module_path.replace('.py', '') + '.py'
                        spec = importlib.util.spec_from_file_location("app_module", module_path_file)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules["app_module"] = module
                        spec.loader.exec_module(module)
                    else:
                        importlib.reload(module)
                    app_callable = getattr(module, app_name)
                except Exception as e:
                    print(f"Error reloading application: {e}")
                    break
                
                time.sleep(0.5)
                continue
            else:
                break


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Uvicorn Emulator - ASGI server'
    )
    parser.add_argument('app', help='Application import string (e.g., "main:app")')
    parser.add_argument('--host', default='127.0.0.1', help='Bind host')
    parser.add_argument('--port', type=int, default=8000, help='Bind port')
    parser.add_argument('--reload', action='store_true', 
                       help='Enable auto-reload')
    parser.add_argument('--reload-dir', action='append', dest='reload_dirs',
                       help='Directories to watch for changes')
    parser.add_argument('--log-level', default='info',
                       choices=['critical', 'error', 'warning', 'info', 'debug'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    UvicornEmulator.run(
        app=args.app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=args.reload_dirs,
        log_level=args.log_level
    )


if __name__ == '__main__':
    main()
