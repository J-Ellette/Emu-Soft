# Web Framework Core

Core HTTP framework components emulating Flask/FastAPI/Django.

## What This Emulates

**Emulates:** Flask, FastAPI, Django (core framework components)
**Purpose:** HTTP server and request/response handling

## Features

- ASGI application framework
- HTTP request and response objects
- URL routing with path parameters
- Middleware pipeline
- JSON serialization
- Error handling
- Static file serving

## Components

### Application Core
- **application.py** - Main ASGI application
  - Application lifecycle management
  - Request routing to handlers
  - Middleware pipeline coordination
  - Error handling and responses

### Request Handling
- **request.py** - HTTP request object
  - Request parsing (headers, body, query params)
  - Form data and JSON parsing
  - File upload handling
  - Cookie management
  - Session access

### Response Building
- **response.py** - HTTP response object
  - Response building with status codes
  - Content type handling
  - JSON serialization (JSONResponse)
  - HTML rendering (HTMLResponse)
  - Redirect responses
  - File downloads

### URL Routing
- **routing.py** - URL routing and pattern matching
  - Route registration with decorators
  - Path parameter extraction
  - HTTP method routing (GET, POST, PUT, DELETE, etc.)
  - Regular expression patterns
  - Route groups and prefixes

### Middleware
- **middleware.py** - Middleware pipeline
  - Request preprocessing
  - Response postprocessing
  - Middleware chaining
  - Error handling middleware
  - Logging middleware
  - CORS middleware

## Usage Examples

### Basic Application
```python
from framework.application import Application
from framework.response import JSONResponse

app = Application()

@app.route("/")
async def home(request):
    return JSONResponse({"message": "Hello, World!"})

@app.route("/users/{user_id}")
async def get_user(request, user_id):
    return JSONResponse({"user_id": user_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Request and Response
```python
from framework.request import Request
from framework.response import Response, JSONResponse, HTMLResponse

async def handler(request: Request):
    # Access request data
    method = request.method
    path = request.path
    headers = request.headers
    query = request.query_params
    body = await request.body()
    json_data = await request.json()
    
    # Return different response types
    return JSONResponse({"status": "ok"})
    # or
    return HTMLResponse("<h1>Hello</h1>")
    # or
    return Response("Plain text", status=200)
```

### Routing with Parameters
```python
@app.route("/posts/{post_id}/comments/{comment_id}")
async def get_comment(request, post_id, comment_id):
    return JSONResponse({
        "post_id": post_id,
        "comment_id": comment_id
    })

@app.route("/search")
async def search(request):
    query = request.query_params.get("q", "")
    return JSONResponse({"query": query})
```

### Middleware
```python
from framework.middleware import Middleware

class LoggingMiddleware(Middleware):
    async def process_request(self, request):
        print(f"{request.method} {request.path}")
        return None  # Continue to next middleware
    
    async def process_response(self, request, response):
        print(f"Response: {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware())
```

### Router with Prefix
```python
from framework.routing import Router

api_router = Router(prefix="/api/v1")

@api_router.route("/users")
async def list_users(request):
    return JSONResponse([{"id": 1, "name": "John"}])

@api_router.route("/users/{user_id}")
async def get_user(request, user_id):
    return JSONResponse({"id": user_id, "name": "John"})

app.include_router(api_router)
```

## HTTP Methods

Supports all standard HTTP methods:
- GET - Retrieve resources
- POST - Create resources
- PUT - Update resources (full)
- PATCH - Update resources (partial)
- DELETE - Delete resources
- HEAD - Get headers only
- OPTIONS - Get allowed methods

## Response Types

- **Response** - Basic response with status and headers
- **JSONResponse** - Automatic JSON serialization
- **HTMLResponse** - HTML content with proper content-type
- **RedirectResponse** - HTTP redirects (301, 302)
- **FileResponse** - File downloads
- **StreamResponse** - Streaming responses

## Middleware Types

- **Authentication** - User authentication
- **CORS** - Cross-origin resource sharing
- **Logging** - Request/response logging
- **Error Handling** - Exception catching
- **Compression** - Response compression
- **Rate Limiting** - Request throttling

## Integration

This framework is the foundation for:
- API framework (api/ module)
- Admin interface (admin/ module)
- Frontend views (frontend/ module)
- All web-based modules

## Performance

- Async/await support for concurrent requests
- Efficient routing with compiled patterns
- Minimal overhead middleware pipeline
- Connection pooling for databases

## Why This Was Created

Part of the CIV-ARCOS project to provide web framework capabilities without external framework dependencies, enabling HTTP service development while maintaining self-containment.
