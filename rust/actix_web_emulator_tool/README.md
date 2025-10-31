# Actix-web Emulator - Web Framework for Rust

This module emulates **Actix-web**, which is a powerful, pragmatic, and extremely fast web framework for Rust. Actix-web is built on the Actix actor framework and provides high-performance asynchronous HTTP server capabilities.

## What is Actix-web?

Actix-web is a powerful web framework for Rust that provides:
- Asynchronous HTTP/1.x and HTTP/2 server
- Request routing with type-safe path parameters
- Middleware system
- WebSocket support
- JSON/Form data extraction
- Static file serving
- TLS/HTTPS support
- Built on the Actix actor system

Key features:
- Type-safe request handlers
- Powerful request routing
- Middleware and request guards
- Easy-to-use extractors
- WebSocket and Server-Sent Events
- High performance and low overhead

## Features

This emulator implements core Actix-web functionality:

### Request Handling
- **HTTP Methods**: GET, POST, PUT, DELETE, PATCH
- **Path Parameters**: Dynamic URL segments with type-safe extraction
- **Query Parameters**: Parse URL query strings
- **Request Headers**: Access and manipulate HTTP headers
- **Request Body**: Handle JSON and other content types

### Response Building
- **Status Codes**: Ok (200), Created (201), BadRequest (400), NotFound (404), InternalServerError (500)
- **JSON Responses**: Automatic serialization with serde
- **Custom Headers**: Set response headers
- **Body Content**: Send various response body types

### Routing
- **Route Registration**: Map URLs to handler functions
- **Path Matching**: Match static and dynamic path segments
- **Method Routing**: Route based on HTTP method

### Middleware
- **Middleware Chain**: Execute pre and post-processing logic
- **Request Interception**: Modify requests or short-circuit responses
- **Logger Middleware**: Built-in request logging

## Usage Examples

### Basic Application

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/", "GET", |_req| {
            HttpResponse::Ok().body("Hello, World!")
        });

    // Simulate a request
    let req = HttpRequest::new("GET", "/");
    let resp = app.handle_request(req);
    
    println!("{}", String::from_utf8_lossy(&resp.body));
}
```

### JSON Response

```rust
use actix_web_emulator::*;
use serde::Serialize;

#[derive(Serialize)]
struct User {
    id: u32,
    name: String,
    email: String,
}

fn main() {
    let app = App::new()
        .route("/api/user", "GET", |_req| {
            let user = User {
                id: 1,
                name: "Alice".to_string(),
                email: "alice@example.com".to_string(),
            };
            HttpResponse::Ok().json(&user)
        });
}
```

### Path Parameters

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/users/{id}", "GET", |req| {
            if let Some(id) = req.path_params.get("id") {
                HttpResponse::Ok().body(format!("User ID: {}", id))
            } else {
                HttpResponse::BadRequest().body("Missing ID")
            }
        });

    let req = HttpRequest::new("GET", "/users/123");
    let resp = app.handle_request(req);
}
```

### Multiple Path Parameters

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/api/{version}/users/{id}", "GET", |req| {
            let version = req.path_params.get("version").unwrap();
            let user_id = req.path_params.get("id").unwrap();
            
            HttpResponse::Ok().body(format!(
                "API {}, User {}",
                version, user_id
            ))
        });

    let req = HttpRequest::new("GET", "/api/v1/users/456");
    let resp = app.handle_request(req);
}
```

### POST Request

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/users", "POST", |_req| {
            // In a real app, you'd extract and validate the body
            HttpResponse::Created().body("User created")
        });

    let req = HttpRequest::new("POST", "/users");
    let resp = app.handle_request(req);
}
```

### PUT and DELETE Requests

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/users/{id}", "PUT", |req| {
            let id = req.path_params.get("id").unwrap();
            HttpResponse::Ok().body(format!("User {} updated", id))
        })
        .route("/users/{id}", "DELETE", |req| {
            let id = req.path_params.get("id").unwrap();
            HttpResponse::Ok().body(format!("User {} deleted", id))
        });
}
```

### Custom Response Headers

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/api/data", "GET", |_req| {
            HttpResponse::Ok()
                .header("X-Custom-Header", "CustomValue")
                .header("X-Request-ID", "12345")
                .header("Cache-Control", "no-cache")
                .body("Data with custom headers")
        });
}
```

### Middleware

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .wrap(|req| {
            // Log the request
            println!("{} {}", req.method, req.path);
            
            // Continue to handler
            None
        })
        .wrap(|req| {
            // Authentication check
            if req.header("Authorization").is_none() {
                return Some(HttpResponse::Ok()
                    .header("WWW-Authenticate", "Bearer")
                    .body("Unauthorized"));
            }
            None
        })
        .route("/protected", "GET", |_req| {
            HttpResponse::Ok().body("Protected resource")
        });
}
```

### Query Parameters

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/search", "GET", |req| {
            let query = req.query_params.get("q")
                .map(|s| s.as_str())
                .unwrap_or("none");
            
            let limit = req.query_params.get("limit")
                .map(|s| s.as_str())
                .unwrap_or("10");
            
            HttpResponse::Ok().body(format!(
                "Searching for '{}' with limit {}",
                query, limit
            ))
        });

    let mut req = HttpRequest::new("GET", "/search");
    req.query_params.insert("q".to_string(), "rust".to_string());
    req.query_params.insert("limit".to_string(), "20".to_string());
    
    let resp = app.handle_request(req);
}
```

### Request Headers

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/api/protected", "GET", |req| {
            match req.header("Authorization") {
                Some(token) if token.starts_with("Bearer ") => {
                    HttpResponse::Ok().body("Authorized")
                }
                _ => {
                    HttpResponse::Ok()
                        .header("WWW-Authenticate", "Bearer")
                        .body("Unauthorized")
                }
            }
        });
}
```

### Error Handling

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/api/users/{id}", "GET", |req| {
            let id = req.path_params.get("id").unwrap();
            
            // Simulate database lookup
            if id == "999" {
                return HttpResponse::NotFound()
                    .body("User not found");
            }
            
            if id == "error" {
                return HttpResponse::InternalServerError()
                    .body("Database error");
            }
            
            HttpResponse::Ok().body(format!("User {}", id))
        });
}
```

### Multiple Routes (REST API)

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        // List all users
        .route("/api/users", "GET", |_req| {
            HttpResponse::Ok().json(&vec![
                "Alice", "Bob", "Charlie"
            ])
        })
        // Get single user
        .route("/api/users/{id}", "GET", |req| {
            let id = req.path_params.get("id").unwrap();
            HttpResponse::Ok().body(format!("User {}", id))
        })
        // Create user
        .route("/api/users", "POST", |_req| {
            HttpResponse::Created().body("User created")
        })
        // Update user
        .route("/api/users/{id}", "PUT", |req| {
            let id = req.path_params.get("id").unwrap();
            HttpResponse::Ok().body(format!("User {} updated", id))
        })
        // Delete user
        .route("/api/users/{id}", "DELETE", |req| {
            let id = req.path_params.get("id").unwrap();
            HttpResponse::Ok().body(format!("User {} deleted", id))
        });
}
```

### Content Negotiation

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/api/data", "GET", |req| {
            match req.header("Accept") {
                Some(accept) if accept.contains("application/json") => {
                    HttpResponse::Ok().json(&"JSON data")
                }
                Some(accept) if accept.contains("text/plain") => {
                    HttpResponse::Ok().body("Plain text data")
                }
                _ => {
                    HttpResponse::Ok().body("Default response")
                }
            }
        });
}
```

### CORS Headers

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .wrap(|_req| {
            // Add CORS headers to all responses
            None // Would modify response here in full implementation
        })
        .route("/api/public", "GET", |_req| {
            HttpResponse::Ok()
                .header("Access-Control-Allow-Origin", "*")
                .header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
                .header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                .body("Public API")
        });
}
```

### Health Check Endpoint

```rust
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/health", "GET", |_req| {
            HttpResponse::Ok().json(&serde_json::json!({
                "status": "ok",
                "timestamp": "2024-01-01T00:00:00Z"
            }))
        })
        .route("/ready", "GET", |_req| {
            // Check if services are ready
            HttpResponse::Ok().body("ready")
        });
}
```

## Testing

Run the comprehensive test suite:

```bash
cargo run --bin test
```

Tests cover:
- Basic GET requests
- JSON responses with serde serialization
- Single and multiple path parameters
- POST, PUT, DELETE requests
- 404 Not Found handling
- Custom response headers
- Middleware execution
- Error responses (400, 500)
- Multiple routes
- Query parameters
- Request headers
- Authentication patterns

Total: 15 tests, all passing

## Integration with Existing Code

This emulator is designed to help understand Actix-web patterns:

```rust
// The API follows Actix-web conventions
use actix_web_emulator::*;

fn main() {
    let app = App::new()
        .route("/", "GET", index_handler)
        .route("/api/users", "POST", create_user);

    // Simulated request handling
    let req = HttpRequest::new("GET", "/");
    let resp = app.handle_request(req);
}

fn index_handler(_req: HttpRequest) -> HttpResponse {
    HttpResponse::Ok().body("Home")
}

fn create_user(_req: HttpRequest) -> HttpResponse {
    HttpResponse::Created().json(&serde_json::json!({
        "id": 1,
        "status": "created"
    }))
}
```

## Use Cases

Perfect for:
- **Local Development**: Develop web applications without async complexity
- **Testing**: Test HTTP handlers and API endpoints
- **Learning**: Understand Rust web framework patterns
- **Prototyping**: Quickly prototype REST APIs
- **Education**: Teach web development concepts in Rust
- **API Design**: Design and test API structures

## Limitations

This is an emulator for development and testing purposes:
- No actual HTTP server (simulated requests/responses)
- No async/await (synchronous execution)
- No WebSocket support
- No static file serving
- No session management
- No template rendering
- Simplified middleware (no async)
- No TLS/HTTPS support
- No actual network I/O
- No connection pooling

## Supported Features

### Core Features
- ✅ Application creation
- ✅ Route registration
- ✅ HTTP method routing (GET, POST, PUT, DELETE, PATCH)
- ✅ Path parameters with extraction
- ✅ Request handling
- ✅ Response building

### Request Features
- ✅ HTTP methods
- ✅ Path parameters
- ✅ Query parameters
- ✅ Request headers
- ✅ Request body (basic)

### Response Features
- ✅ Status codes (200, 201, 400, 404, 500)
- ✅ Response headers
- ✅ JSON serialization
- ✅ Plain text responses
- ✅ Custom body content

### Advanced Features
- ✅ Middleware pipeline
- ✅ Request interception
- ✅ Path parameter extraction
- ✅ Multiple routes
- ✅ Error handling

## Real-World Web Framework Concepts

This emulator teaches the following concepts:

1. **HTTP Routing**: Mapping URLs to handler functions
2. **RESTful APIs**: Building resource-oriented APIs
3. **Path Parameters**: Dynamic URL segments
4. **Query Parameters**: Parsing URL query strings
5. **Request/Response Cycle**: Understanding HTTP flow
6. **Middleware Pattern**: Request processing pipeline
7. **Status Codes**: Using appropriate HTTP status codes
8. **Header Management**: Setting and reading HTTP headers
9. **JSON Handling**: Serialization with serde
10. **Error Handling**: Managing HTTP errors

## Compatibility

Emulates core features of:
- Actix-web v4.x API patterns
- Common Rust web framework conventions
- Standard HTTP semantics

## Building and Running

```bash
# Build the project
cargo build

# Run tests
cargo run --bin test

# Run with release optimizations
cargo build --release
cargo run --bin test --release
```

## Dependencies

- **serde**: Serialization framework for Rust
- **serde_json**: JSON support for serde

## License

Part of the Emu-Soft project. See main repository LICENSE.
