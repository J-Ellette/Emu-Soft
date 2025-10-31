# Nginx Emulator - Web Server and Reverse Proxy

A lightweight emulation of **Nginx**, the high-performance web server and reverse proxy used by millions of websites worldwide.

## Features

This emulator implements core Nginx functionality:

### Web Server
- **HTTP Server**: Handle HTTP/1.1 requests and responses
- **Virtual Hosts**: Multiple server blocks on different ports
- **Server Names**: Route requests based on Host header
- **Static File Serving**: Serve static content from filesystem
- **Index Files**: Default index file handling

### Reverse Proxy
- **Proxy Pass**: Forward requests to backend servers
- **Upstream Groups**: Define backend server pools
- **Load Balancing**: Distribute traffic across multiple backends
- **Request Headers**: Proxy headers to upstream servers
- **Upstream Tracking**: Track which backend handled request

### Load Balancing
- **Round Robin**: Distribute requests evenly
- **Least Connections**: Send to server with fewest connections
- **IP Hash**: Consistent hashing for session affinity
- **Server Weights**: Weighted load distribution
- **Health Checks**: Mark servers as up/down

### Location Blocks
- **Path Matching**: Match URLs to location blocks
- **Exact Match**: Match exact paths
- **Prefix Match**: Match path prefixes (longest wins)
- **Root Directive**: Set document root
- **Alias Directive**: Map URL to filesystem path
- **Try Files**: Attempt multiple file paths

### Configuration
- **Server Blocks**: Virtual host configuration
- **Location Blocks**: URL-based routing
- **Upstream Blocks**: Backend server groups
- **Return Directives**: Redirects and custom responses
- **Header Manipulation**: Add custom response headers

## What It Emulates

This tool emulates core functionality of [Nginx](https://nginx.org/), one of the most popular web servers and reverse proxies in the world.

### Core Components Implemented

1. **HTTP Server**
   - Request parsing and routing
   - Response generation
   - Header management
   - Connection handling

2. **Reverse Proxy**
   - Upstream server selection
   - Request forwarding
   - Load balancing algorithms
   - Backend health tracking

3. **Virtual Hosting**
   - Server name matching
   - Port-based routing
   - Location-based routing
   - Path matching rules

4. **Configuration System**
   - Server blocks (virtual hosts)
   - Location blocks (URL routing)
   - Upstream blocks (backend pools)
   - Directives (return, proxy_pass, root, etc.)

## Usage

### Basic Web Server

```python
from nginx_emulator import NginxEmulator, create_server, create_location

# Create Nginx instance
nginx = NginxEmulator()

# Create server block
server = create_server(listen=8080, server_name=["localhost"])

# Add location for root
server.locations.append(create_location("/", root="/var/www/html"))

# Add server to nginx
nginx.add_server(server)

# Start server
nginx.start()
```

### Reverse Proxy

```python
from nginx_emulator import NginxEmulator, create_server, create_location

nginx = NginxEmulator()

# Create server
server = create_server(listen=80)

# Proxy API requests to backend
server.locations.append(
    create_location("/api", proxy_pass="http://127.0.0.1:8000")
)

# Serve static files
server.locations.append(
    create_location("/static", root="/var/www/static")
)

nginx.add_server(server)
nginx.start()
```

### Load Balancing

```python
from nginx_emulator import (
    NginxEmulator, create_server, create_location,
    create_upstream, add_upstream_server, LoadBalanceMethod
)

nginx = NginxEmulator()

# Create upstream group with round-robin
app_upstream = create_upstream("app_servers", LoadBalanceMethod.ROUND_ROBIN)
add_upstream_server(app_upstream, "10.0.0.1", 8001)
add_upstream_server(app_upstream, "10.0.0.2", 8002)
add_upstream_server(app_upstream, "10.0.0.3", 8003, weight=2)  # Double weight
nginx.add_upstream(app_upstream)

# Create server that uses upstream
server = create_server(listen=80)
server.locations.append(
    create_location("/", proxy_pass="http://app_servers")
)
nginx.add_server(server)

nginx.start()
```

### Multiple Server Blocks (Virtual Hosts)

```python
from nginx_emulator import NginxEmulator, create_server, create_location

nginx = NginxEmulator()

# Server for site1.com
server1 = create_server(listen=8080, server_name=["site1.com", "www.site1.com"])
server1.locations.append(create_location("/", root="/var/www/site1"))
nginx.add_server(server1)

# Server for site2.com
server2 = create_server(listen=8080, server_name=["site2.com", "www.site2.com"])
server2.locations.append(create_location("/", root="/var/www/site2"))
nginx.add_server(server2)

nginx.start()
```

### Redirects and Custom Responses

```python
from nginx_emulator import NginxEmulator, create_server, create_location

nginx = NginxEmulator()
server = create_server(listen=80)

# 301 redirect
server.locations.append(
    create_location("/old-page", return_code=301, return_url="/new-page")
)

# 404 page
server.locations.append(
    create_location("/404", return_code=404)
)

nginx.add_server(server)
nginx.start()
```

### Custom Headers

```python
from nginx_emulator import NginxEmulator, create_server, create_location

nginx = NginxEmulator()
server = create_server(listen=80)

# Add custom headers to response
loc = create_location("/api")
loc.add_headers["Access-Control-Allow-Origin"] = "*"
loc.add_headers["X-Frame-Options"] = "DENY"
loc.add_headers["X-Content-Type-Options"] = "nosniff"
server.locations.append(loc)

nginx.add_server(server)
nginx.start()
```

### Custom Request Handler

```python
from nginx_emulator import NginxEmulator, create_server, create_location, Response

def api_handler(request):
    """Custom handler for API requests"""
    response = Response(200, "OK")
    response.json({
        "method": request.method,
        "path": request.path,
        "client_ip": request.client_ip
    })
    return response

nginx = NginxEmulator()
server = create_server(listen=8080)

# Use custom handler
loc = create_location("/api")
loc.handler = api_handler
server.locations.append(loc)

nginx.add_server(server)
nginx.start()
```

### Least Connections Load Balancing

```python
from nginx_emulator import (
    NginxEmulator, create_upstream, add_upstream_server,
    create_server, create_location, LoadBalanceMethod
)

nginx = NginxEmulator()

# Upstream with least-connections algorithm
upstream = create_upstream("backends", LoadBalanceMethod.LEAST_CONN)
add_upstream_server(upstream, "10.0.0.1", 8001)
add_upstream_server(upstream, "10.0.0.2", 8002)
add_upstream_server(upstream, "10.0.0.3", 8003)
nginx.add_upstream(upstream)

server = create_server(listen=80)
server.locations.append(
    create_location("/", proxy_pass="http://backends")
)
nginx.add_server(server)

nginx.start()
```

## API Reference

### Main Classes

#### `NginxEmulator`
Main server class.

**Methods:**
- `add_server(server)` - Add server block
- `add_upstream(upstream)` - Add upstream group
- `start()` - Start all server blocks
- `stop()` - Stop all server blocks
- `reload()` - Reload configuration

#### `ServerBlock`
Virtual host configuration.

**Attributes:**
- `listen` (int) - Port to listen on
- `server_name` (list) - Server names (domains)
- `root` (str) - Document root path
- `index` (list) - Index files
- `locations` (list) - Location blocks

#### `Location`
URL routing configuration.

**Attributes:**
- `path` (str) - URL path to match
- `root` (str) - Document root
- `proxy_pass` (str) - Backend URL
- `alias` (str) - Filesystem alias
- `return_code` (int) - HTTP status code
- `return_url` (str) - Redirect URL
- `add_headers` (dict) - Custom headers
- `handler` (callable) - Custom handler function

#### `Upstream`
Backend server pool.

**Attributes:**
- `name` (str) - Upstream name
- `servers` (list) - List of UpstreamServer
- `method` (LoadBalanceMethod) - Load balancing algorithm
- `keepalive` (int) - Keepalive connections

#### `UpstreamServer`
Backend server in pool.

**Attributes:**
- `host` (str) - Server hostname/IP
- `port` (int) - Server port
- `weight` (int) - Load balancing weight
- `max_fails` (int) - Health check failures
- `backup` (bool) - Backup server flag
- `down` (bool) - Server is down

#### `Request`
HTTP request object.

**Attributes:**
- `method` (str) - HTTP method
- `path` (str) - URL path
- `headers` (dict) - Request headers
- `body` (str) - Request body
- `query_string` (str) - Query parameters
- `client_ip` (str) - Client IP address

#### `Response`
HTTP response builder.

**Methods:**
- `set_header(key, value)` - Set response header
- `set_body(body)` - Set response body
- `json(data)` - Set JSON response
- `to_bytes()` - Convert to HTTP wire format

### Helper Functions

- `create_server(listen, server_name)` - Create ServerBlock
- `create_location(path, **kwargs)` - Create Location
- `create_upstream(name, method)` - Create Upstream
- `add_upstream_server(upstream, host, port, weight)` - Add server to upstream

### Load Balancing Methods

**`LoadBalanceMethod` Enum:**
- `ROUND_ROBIN` - Distribute evenly
- `LEAST_CONN` - Fewest connections
- `IP_HASH` - Consistent hashing

## Configuration Examples

### Full Configuration Example

```python
from nginx_emulator import *

nginx = NginxEmulator()

# Create upstream
backend = create_upstream("backend", LoadBalanceMethod.ROUND_ROBIN)
add_upstream_server(backend, "10.0.1.10", 8001)
add_upstream_server(backend, "10.0.1.11", 8002)
add_upstream_server(backend, "10.0.1.12", 8003)
nginx.add_upstream(backend)

# Main server
server = create_server(listen=80, server_name=["example.com", "www.example.com"])

# Static files
server.locations.append(create_location("/", root="/var/www/html"))
server.locations.append(create_location("/images", root="/var/www/images"))

# API proxy
server.locations.append(create_location("/api", proxy_pass="http://backend"))

# Redirect old URL
server.locations.append(
    create_location("/old", return_code=301, return_url="/new")
)

# HTTPS redirect server
https_redirect = create_server(listen=80)
loc = create_location("/", return_code=301, return_url="https://example.com")
https_redirect.locations.append(loc)

nginx.add_server(server)
nginx.add_server(https_redirect)

nginx.start()

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    nginx.stop()
```

## Testing

Run the test suite:

```bash
python test_nginx_emulator.py
```

Tests cover:
- Request parsing
- Response generation
- Location matching
- Load balancing algorithms
- Reverse proxy functionality
- Server block routing
- HTTP request/response cycle

## Limitations

This is an educational emulation with some limitations:

1. **HTTP/1.1 Only**: No HTTP/2 or HTTP/3
2. **No SSL/TLS**: HTTPS not implemented
3. **Basic Load Balancing**: Simplified algorithms
4. **No File Operations**: Static file serving is emulated
5. **No Modules**: No dynamic module system
6. **Simplified Parsing**: Basic HTTP parsing
7. **No Caching**: No proxy cache or fastcgi cache
8. **No Compression**: No gzip compression
9. **No Rate Limiting**: Request rate limiting not implemented
10. **No Access Control**: No IP-based access control

## Real-World Nginx

To use real Nginx, see the [official documentation](https://nginx.org/en/docs/).

### Nginx Configuration Example

```nginx
# nginx.conf equivalent

upstream backend {
    server 10.0.1.10:8001;
    server 10.0.1.11:8002;
    server 10.0.1.12:8003;
}

server {
    listen 80;
    server_name example.com www.example.com;
    
    location / {
        root /var/www/html;
        index index.html;
    }
    
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /old {
        return 301 /new;
    }
}
```

## Use Cases

- Learning web server architecture
- Understanding reverse proxy concepts
- Testing load balancing algorithms
- Prototyping proxy configurations
- Educational purposes
- Development environments

## Complexity

**Implementation Complexity**: Medium-High

This emulator involves:
- HTTP protocol handling
- Socket programming
- Multi-threading for concurrent connections
- Request routing and matching
- Load balancing algorithms
- Configuration management

## Comparison with Real Nginx

### Similarities
- Server blocks concept
- Location-based routing
- Upstream groups
- Load balancing methods
- Reverse proxy pattern

### Differences
- Real Nginx is C-based, extremely fast
- Real Nginx has worker processes and event-driven architecture
- Real Nginx supports thousands of features and directives
- Real Nginx has advanced caching and SSL/TLS
- Real Nginx has module system for extensions

## Dependencies

- Python 3.6+
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
