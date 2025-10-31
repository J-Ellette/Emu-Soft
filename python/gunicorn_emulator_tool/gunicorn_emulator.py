"""
Gunicorn Emulator - WSGI Server
Emulates Gunicorn functionality for serving WSGI applications with worker processes
"""

import socket
import sys
import signal
import os
import time
import importlib
import multiprocessing
from typing import Dict, Any, Callable, Optional, List, Tuple
from pathlib import Path
from urllib.parse import parse_qs, unquote
import io
import traceback


class WSGIRequest:
    """Represents a WSGI HTTP request"""
    
    def __init__(self, raw_request: bytes, client_addr: tuple, server_addr: tuple):
        self.raw_request = raw_request
        self.client_addr = client_addr
        self.server_addr = server_addr
        self.method = "GET"
        self.path = "/"
        self.query_string = ""
        self.headers = {}
        self.body = b""
        self.protocol = "HTTP/1.1"
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
            if len(parts) >= 3:
                self.method = parts[0]
                url = parts[1]
                self.protocol = parts[2]
                
                # Parse URL
                if '?' in url:
                    self.path, self.query_string = url.split('?', 1)
                else:
                    self.path = url
                    self.query_string = ""
            
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
                # Find where the body actually starts in the raw request
                # The body comes after \r\n\r\n
                body_marker = b'\r\n\r\n'
                if body_marker in self.raw_request:
                    self.body = self.raw_request.split(body_marker, 1)[1]
                else:
                    self.body = b'\r\n'.join(lines[body_start:])
                
                # Handle content-length
                content_length = self.headers.get('content-length')
                if content_length:
                    try:
                        length = int(content_length)
                        self.body = self.body[:length]
                    except ValueError:
                        pass
        
        except Exception as e:
            print(f"Error parsing request: {e}")
    
    def to_wsgi_environ(self) -> Dict[str, Any]:
        """Convert to WSGI environ dictionary"""
        # Build CGI-style headers
        environ = {
            'REQUEST_METHOD': self.method,
            'SCRIPT_NAME': '',
            'PATH_INFO': unquote(self.path),
            'QUERY_STRING': self.query_string,
            'CONTENT_TYPE': self.headers.get('content-type', ''),
            'CONTENT_LENGTH': self.headers.get('content-length', ''),
            'SERVER_NAME': self.server_addr[0],
            'SERVER_PORT': str(self.server_addr[1]),
            'SERVER_PROTOCOL': self.protocol,
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': io.BytesIO(self.body),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
            'REMOTE_ADDR': self.client_addr[0],
            'REMOTE_PORT': str(self.client_addr[1]),
        }
        
        # Add HTTP headers
        for key, value in self.headers.items():
            # Convert header name to CGI format
            key_upper = key.upper().replace('-', '_')
            if key_upper not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{key_upper}'] = value
        
        return environ


class WSGIResponse:
    """Builds HTTP response from WSGI application"""
    
    def __init__(self):
        self.status = "200 OK"
        self.headers = []
        self.body_parts = []
    
    def start_response(self, status: str, response_headers: List[Tuple[str, str]], exc_info=None):
        """WSGI start_response callable"""
        if exc_info:
            try:
                if self.headers:
                    raise exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None
        
        self.status = status
        self.headers = response_headers
        return self.write
    
    def write(self, data: bytes):
        """Write response body data"""
        self.body_parts.append(data)
    
    def to_http_response(self) -> bytes:
        """Convert to HTTP response bytes"""
        # Build status line
        response_lines = [f"HTTP/1.1 {self.status}".encode('utf-8')]
        
        # Add headers
        for name, value in self.headers:
            response_lines.append(f"{name}: {value}".encode('utf-8'))
        
        # Add blank line
        response_lines.append(b"")
        
        # Build response
        response = b'\r\n'.join(response_lines)
        
        # Add body
        if self.body_parts:
            response += b'\r\n' + b''.join(self.body_parts)
        
        return response


class Worker:
    """Worker process for handling requests"""
    
    def __init__(self, worker_id: int, app_path: str, host: str, port: int, 
                 worker_connections: int = 1000):
        self.worker_id = worker_id
        self.app_path = app_path
        self.host = host
        self.port = port
        self.worker_connections = worker_connections
        self.running = True
        self.app = None
        self.requests_handled = 0
    
    def load_application(self):
        """Load WSGI application"""
        try:
            module_name, app_name = self.app_path.split(':')
            module = importlib.import_module(module_name)
            self.app = getattr(module, app_name)
            print(f"[Worker {self.worker_id}] Application loaded: {self.app_path}")
        except Exception as e:
            print(f"[Worker {self.worker_id}] Error loading application: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    def handle_request(self, conn: socket.socket, addr: tuple, server_addr: tuple):
        """Handle a single HTTP request"""
        try:
            # Receive request
            data = conn.recv(16384)
            if not data:
                return
            
            # Parse request
            request = WSGIRequest(data, addr, server_addr)
            
            # Create response
            response = WSGIResponse()
            
            # Call WSGI application
            environ = request.to_wsgi_environ()
            result = self.app(environ, response.start_response)
            
            # Collect response body
            try:
                for data in result:
                    if data:
                        response.body_parts.append(data)
            finally:
                # Close iterator if it has a close method
                if hasattr(result, 'close'):
                    result.close()
            
            # Send response
            http_response = response.to_http_response()
            conn.sendall(http_response)
            
            self.requests_handled += 1
            
        except Exception as e:
            print(f"[Worker {self.worker_id}] Error handling request: {e}")
            traceback.print_exc()
            
            # Send error response
            try:
                error_response = b"HTTP/1.1 500 Internal Server Error\r\n"
                error_response += b"Content-Type: text/plain\r\n"
                error_response += b"\r\n"
                error_response += b"Internal Server Error"
                conn.sendall(error_response)
            except:
                pass
        finally:
            try:
                conn.close()
            except:
                pass
    
    def run(self):
        """Main worker loop"""
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        
        # Load application
        self.load_application()
        
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(self.worker_connections)
        sock.settimeout(1.0)  # Timeout to check for shutdown
        
        server_addr = (self.host, self.port)
        
        print(f"[Worker {self.worker_id}] Listening on {self.host}:{self.port}")
        
        # Accept connections
        while self.running:
            try:
                conn, addr = sock.accept()
                self.handle_request(conn, addr, server_addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[Worker {self.worker_id}] Error accepting connection: {e}")
        
        print(f"[Worker {self.worker_id}] Shutting down (handled {self.requests_handled} requests)")
        sock.close()
    
    def _handle_signal(self, signum, frame):
        """Handle shutdown signal"""
        print(f"[Worker {self.worker_id}] Received signal {signum}")
        self.running = False


class Arbiter:
    """Master process that manages workers"""
    
    def __init__(self, app_path: str, workers: int = 1, host: str = '127.0.0.1',
                 port: int = 8000, worker_connections: int = 1000,
                 daemon: bool = False, timeout: int = 30):
        self.app_path = app_path
        self.workers = workers
        self.host = host
        self.port = port
        self.worker_connections = worker_connections
        self.daemon = daemon
        self.timeout = timeout
        self.worker_processes: List[multiprocessing.Process] = []
        self.running = True
    
    def start_worker(self, worker_id: int):
        """Start a worker process"""
        worker = Worker(worker_id, self.app_path, self.host, self.port, 
                       self.worker_connections)
        
        process = multiprocessing.Process(target=worker.run, name=f"worker-{worker_id}")
        process.start()
        self.worker_processes.append(process)
        print(f"[Master] Started worker {worker_id} (PID: {process.pid})")
    
    def start_workers(self):
        """Start all worker processes"""
        print(f"[Master] Starting {self.workers} workers")
        for i in range(self.workers):
            self.start_worker(i + 1)
    
    def monitor_workers(self):
        """Monitor and restart failed workers"""
        while self.running:
            time.sleep(1)
            
            # Check for dead workers
            for i, process in enumerate(self.worker_processes):
                if not process.is_alive():
                    print(f"[Master] Worker {i + 1} died, restarting...")
                    self.worker_processes[i] = None
                    self.start_worker(i + 1)
            
            # Remove None entries
            self.worker_processes = [p for p in self.worker_processes if p is not None]
    
    def shutdown(self):
        """Shutdown all workers"""
        print("[Master] Shutting down...")
        self.running = False
        
        # Terminate workers
        for process in self.worker_processes:
            if process and process.is_alive():
                process.terminate()
        
        # Wait for workers to finish
        for process in self.worker_processes:
            if process:
                process.join(timeout=self.timeout)
                if process.is_alive():
                    print(f"[Master] Force killing worker {process.pid}")
                    process.kill()
        
        print("[Master] Shutdown complete")
    
    def _handle_signal(self, signum, frame):
        """Handle shutdown signal"""
        print(f"[Master] Received signal {signum}")
        self.shutdown()
        sys.exit(0)
    
    def run(self):
        """Main arbiter loop"""
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        
        print(f"[Master] Gunicorn emulator starting")
        print(f"[Master] Listening at: http://{self.host}:{self.port}")
        print(f"[Master] Using {self.workers} worker(s)")
        
        # Start workers
        self.start_workers()
        
        # Monitor workers
        try:
            self.monitor_workers()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()


class GunicornEmulator:
    """Main interface for running WSGI applications"""
    
    @staticmethod
    def run(app: str, bind: str = '127.0.0.1:8000', workers: int = None,
            worker_connections: int = 1000, daemon: bool = False,
            timeout: int = 30, log_level: str = 'info'):
        """
        Run a WSGI application
        
        Args:
            app: Application import string (e.g., "main:app")
            bind: The socket to bind (format: HOST:PORT)
            workers: Number of worker processes (default: CPU count)
            worker_connections: Max simultaneous clients per worker
            daemon: Daemonize the Gunicorn process
            timeout: Workers silent for more than this many seconds are killed
            log_level: Logging level (debug, info, warning, error, critical)
        """
        # Parse bind address
        if ':' in bind:
            host, port_str = bind.rsplit(':', 1)
            port = int(port_str)
        else:
            host = bind
            port = 8000
        
        # Default workers to CPU count
        if workers is None:
            workers = multiprocessing.cpu_count()
        
        # Create and run arbiter
        arbiter = Arbiter(
            app_path=app,
            workers=workers,
            host=host,
            port=port,
            worker_connections=worker_connections,
            daemon=daemon,
            timeout=timeout
        )
        
        arbiter.run()


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gunicorn WSGI Server Emulator')
    parser.add_argument('app', help='Application import string (module:app)')
    parser.add_argument('-b', '--bind', default='127.0.0.1:8000',
                       help='The socket to bind (default: 127.0.0.1:8000)')
    parser.add_argument('-w', '--workers', type=int, default=None,
                       help='Number of worker processes (default: CPU count)')
    parser.add_argument('--worker-connections', type=int, default=1000,
                       help='Max simultaneous clients (default: 1000)')
    parser.add_argument('-D', '--daemon', action='store_true',
                       help='Daemonize the Gunicorn process')
    parser.add_argument('-t', '--timeout', type=int, default=30,
                       help='Workers timeout in seconds (default: 30)')
    parser.add_argument('--log-level', default='info',
                       choices=['debug', 'info', 'warning', 'error', 'critical'],
                       help='Logging level (default: info)')
    
    args = parser.parse_args()
    
    GunicornEmulator.run(
        app=args.app,
        bind=args.bind,
        workers=args.workers,
        worker_connections=args.worker_connections,
        daemon=args.daemon,
        timeout=args.timeout,
        log_level=args.log_level
    )


if __name__ == '__main__':
    main()
