# Nginx Emulator

A lightweight emulation of Nginx functionality for configuration parsing, reverse proxy, and load balancing.

## Features

- **Configuration Parser**: Parse Nginx configuration files
- **Reverse Proxy**: Forward requests to backend servers
- **Load Balancing**: Round-robin, least connections strategies
- **Upstream Support**: Backend server pools
- **Location Matching**: Path-based routing
- **Multi-Server Support**: Multiple virtual servers on different ports
- **Simple Interface**: Easy-to-use API matching Nginx concepts

## What It Emulates

This tool emulates core functionality of [Nginx](https://nginx.org/), the high-performance HTTP server and reverse proxy.

### Core Components Implemented

1. **Configuration Parser**
   - Server blocks
   - Location blocks
   - Upstream definitions
   - Directive parsing
   - Comment handling

2. **Reverse Proxy**
   - Request forwarding
   - Backend server selection
   - Header manipulation
   - Response relaying

3. **Load Balancing**
   - Round-robin algorithm
   - Upstream server pools
   - Backend health (simplified)

4. **HTTP Server**
   - Multi-port listening
   - Virtual server routing
   - Location matching
   - Path-based routing

## Usage

### Configuration File

```nginx
# nginx.conf

upstream backend {
    server backend1:8080;
    server backend2:8080;
    server backend3:8080;
}

server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://backend;
    }
    
    location /api {
        proxy_pass http://api-server:9000;
    }
}

server {
    listen 8080;
    server_name admin.example.com;
    
    location / {
        proxy_pass http://admin-backend:3000;
    }
}
```

### As a Module

```python
from nginx_emulator import NginxConfig, NginxEmulator

# Load configuration
config = NginxConfig.from_file('nginx.conf')

# Run emulator
emulator = NginxEmulator(config)
emulator.start()

# Keep running...
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    emulator.stop()
```

### From Dictionary

```python
from nginx_emulator import NginxConfig, NginxEmulator

# Create config from dictionary
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
NginxEmulator.run(config)
```

### Command Line

```bash
# Run with configuration file
python nginx_emulator.py -c nginx.conf

# Test configuration
python nginx_emulator.py -c nginx.conf -t
```

## Examples

### Simple Reverse Proxy

```nginx
server {
    listen 80;
    
    location / {
        proxy_pass http://localhost:8080;
    }
}
```

This forwards all requests on port 80 to a backend server on port 8080.

### Load Balancing

```nginx
upstream app_servers {
    server app1:8080;
    server app2:8080;
    server app3:8080;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://app_servers;
    }
}
```

Distributes requests across three backend servers using round-robin.

### Path-Based Routing

```nginx
server {
    listen 80;
    
    location / {
        proxy_pass http://frontend:3000;
    }
    
    location /api {
        proxy_pass http://api:8080;
    }
    
    location /admin {
        proxy_pass http://admin:9000;
    }
}
```

Routes different paths to different backends.

### Multiple Virtual Servers

```nginx
server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://api-backend:8080;
    }
}

server {
    listen 80;
    server_name www.example.com;
    
    location / {
        proxy_pass http://web-backend:3000;
    }
}
```

Different domains route to different backends (host-based routing).

### API Gateway Pattern

```nginx
upstream user_service {
    server user1:8080;
    server user2:8080;
}

upstream order_service {
    server order1:8081;
    server order2:8081;
}

upstream payment_service {
    server payment1:8082;
    server payment2:8082;
}

server {
    listen 80;
    server_name api.example.com;
    
    location /api/users {
        proxy_pass http://user_service;
    }
    
    location /api/orders {
        proxy_pass http://order_service;
    }
    
    location /api/payments {
        proxy_pass http://payment_service;
    }
}
```

API gateway routing to microservices with load balancing.

## API Reference

### NginxConfig

Configuration parser and container.

**Methods:**
- `__init__(config_text='')`: Create from configuration string
- `parse()`: Parse configuration text
- `from_file(filepath)`: Load from file (class method)
- `from_dict(config)`: Create from dictionary (class method)

**Attributes:**
- `servers` (List[Dict]): Parsed server blocks
- `upstreams` (Dict[str, List[str]]): Upstream definitions
- `http_directives` (Dict): HTTP-level directives

### NginxEmulator

Main emulator class.

**Methods:**
- `__init__(config, load_balancer=None)`
- `start()`: Start all servers
- `stop()`: Stop all servers
- `run(config, daemon=False)`: Run emulator (static method)

### LoadBalancer

Load balancing strategies.

**Methods:**
- `__init__(strategy='round_robin')`
- `select_backend(upstream_name, backends)`: Select backend server

**Strategies:**
- `round_robin`: Distribute requests evenly
- `least_conn`: Select least-connected server (simplified)
- `ip_hash`: Hash-based selection (simplified)

### ReverseProxy

Reverse proxy implementation.

**Methods:**
- `__init__(config, load_balancer=None)`
- `find_matching_server(host, port)`: Find server config
- `find_matching_location(server, path)`: Find location config
- `resolve_proxy_pass(proxy_pass)`: Resolve backend address
- `proxy_request(...)`: Forward request to backend

## Configuration Syntax

### Server Block

```nginx
server {
    listen 80;                    # Port to listen on
    server_name example.com;      # Server name(s)
    
    location / {                  # Location block
        proxy_pass http://backend;
    }
}
```

### Upstream Block

```nginx
upstream name {
    server backend1:8080;
    server backend2:8080;
}
```

### Location Block

```nginx
location /path {
    proxy_pass http://backend:8080;
    proxy_set_header Host $host;
}
```

### Supported Directives

- `listen`: Port number or host:port
- `server_name`: Virtual server names
- `location`: Path-based routing
- `proxy_pass`: Backend server URL
- `proxy_set_header`: Set request headers (parsed but not fully applied)

## Load Balancing

### Round-Robin

Default strategy. Distributes requests evenly across backends:

```nginx
upstream backend {
    server server1:8080;
    server server2:8080;
    server server3:8080;
}
```

Request flow:
1. Request 1 → server1:8080
2. Request 2 → server2:8080
3. Request 3 → server3:8080
4. Request 4 → server1:8080 (wraps around)

## Location Matching

Locations are matched by specificity:

1. **Exact match**: `location = /path`
2. **Prefix match (priority)**: `location ^~ /path`
3. **Regex match**: `location ~ pattern`
4. **Prefix match**: `location /path`

More specific (longer) paths are matched first.

## Limitations

This is an educational emulation with some limitations:

1. **HTTP/1.1 Only**: No HTTP/2 or HTTP/3 support
2. **No SSL/TLS**: HTTPS not supported
3. **Limited Directives**: Only core proxy directives
4. **No Caching**: Response caching not implemented
5. **Simplified Health Checks**: No active health monitoring
6. **No Compression**: gzip compression not supported
7. **No Rewrite Rules**: URL rewriting not implemented
8. **Basic Header Handling**: Limited header manipulation

## Testing

Run the test suite:

```bash
python test_nginx_emulator.py
```

Tests cover:
- Configuration parsing
- Server blocks
- Location blocks
- Upstream definitions
- Load balancing
- Reverse proxy routing
- Path matching

## Complexity

**Implementation Complexity**: High

This emulator involves:
- Configuration parsing (lexing/parsing)
- HTTP protocol handling
- Socket programming
- Multi-threading
- Load balancing algorithms
- Request routing
- Reverse proxy logic

The implementation requires understanding of web servers, HTTP, and network programming.

## Integration

Use cases:
- Development reverse proxy
- Testing API gateways
- Learning Nginx concepts
- Microservices routing
- Load balancing testing
- Configuration validation

## Performance

Not intended for high-performance production use. For production, use:
- Real Nginx
- HAProxy
- Traefik
- Other production proxies

## Dependencies

- Python 3.6+
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
