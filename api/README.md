# API Layer

The MyCMS API Layer provides a complete RESTful API framework for building API endpoints with authentication, permissions, pagination, and automatic documentation.

## Overview

The API layer consists of six main components:

1. **Framework** - Core API routing and endpoint handling
2. **Serializers** - Data serialization and validation
3. **Authentication** - API key and token-based authentication
4. **Permissions** - Fine-grained access control
5. **Pagination** - Result pagination support
6. **Documentation** - Automatic API documentation generation

## Quick Start

### Creating a Simple API Endpoint

```python
from mycms.api import APIRouter, APIView
from mycms.core.framework.request import Request
from mycms.core.framework.response import JSONResponse

# Create a router
router = APIRouter(prefix="/api/v1")

# Method 1: Function-based endpoint
@router.route("/hello", methods=["GET"])
async def hello_world(request: Request) -> JSONResponse:
    return JSONResponse({"message": "Hello, World!"})

# Method 2: Class-based view
class UserView(APIView):
    async def get(self, request: Request, **kwargs) -> JSONResponse:
        return JSONResponse({"users": []})
    
    async def post(self, request: Request, **kwargs) -> JSONResponse:
        data = await request.json()
        return JSONResponse({"created": data}, status_code=201)

router.add_view("/users", UserView())
```

## Framework

The framework provides the core infrastructure for building API endpoints.

### APIRouter

The router manages API endpoints and handles request dispatching.

```python
from mycms.api import APIRouter

# Create a router with a prefix
router = APIRouter(prefix="/api/v1")

# Add endpoints
router.add_endpoint("/users", methods=["GET", "POST"], handler=user_handler)

# Handle a request
response = await router.handle(request)
```

### APIView

Base class for class-based API views with RESTful method handlers.

```python
from mycms.api import APIView

class PostView(APIView):
    allowed_methods = ["GET", "POST", "PUT", "DELETE"]
    
    async def get(self, request: Request, **kwargs) -> Response:
        # Handle GET request
        return JSONResponse({"posts": []})
    
    async def post(self, request: Request, **kwargs) -> Response:
        # Handle POST request
        data = await request.json()
        return JSONResponse({"created": True}, status_code=201)
```

### APIEndpoint

Represents a single API endpoint with method-specific handlers.

```python
from mycms.api import APIEndpoint

endpoint = APIEndpoint("/api/users", methods=["GET", "POST"])
endpoint.add_handler("GET", get_users_handler)
endpoint.add_handler("POST", create_user_handler)
```

## Serializers

Serializers convert between Python objects and JSON.

### APISerializer

Basic serializer for any Python object.

```python
from mycms.api import APISerializer

# Serialize a single object
serializer = APISerializer(instance=user)
data = serializer.to_dict()
json_str = serializer.to_json()

# Serialize multiple objects
serializer = APISerializer(instance=users, many=True)
data_list = serializer.to_dict()

# Field filtering
serializer.fields = ["id", "name"]  # Only include these fields
serializer.exclude = ["password"]   # Exclude these fields
```

### ModelSerializer

Specialized serializer for ORM models.

```python
from mycms.api import ModelSerializer

class UserSerializer(ModelSerializer):
    model_class = User
    fields = ["id", "username", "email"]  # Optional: specify fields
    exclude = ["password"]                # Optional: exclude fields
    read_only_fields = ["id", "created_at"]  # Optional: read-only fields

# Serialize
serializer = UserSerializer(instance=user)
data = serializer.to_dict()

# Deserialize and validate
serializer = UserSerializer(data={"username": "john", "email": "john@example.com"})
if serializer.validate():
    user = await serializer.save()
```

### Convenience Functions

```python
from mycms.api.serializers import serialize, serialize_many

# Quick serialization
data = serialize(user, fields=["id", "name"])
data_list = serialize_many(users, exclude=["password"])
```

## Authentication

The API layer supports two authentication methods: API keys and JWT tokens.

### API Key Authentication

```python
from mycms.api import APIKeyAuth, require_api_auth

# Create auth handler
api_key_auth = APIKeyAuth()

# Generate an API key for a user
raw_key, api_key = api_key_auth.create_api_key(
    user_id="user-123",
    name="Production API Key",
    expires_in_days=365
)

# Save the raw_key - it won't be accessible again!
print(f"Your API key: {raw_key}")

# Protect an endpoint
@require_api_auth(api_key_auth)
async def protected_endpoint(request: Request) -> Response:
    user_id = request.user_id  # Available after authentication
    return JSONResponse({"user_id": user_id})
```

### Token Authentication

```python
from mycms.api import TokenAuth

# Create token auth handler
token_auth = TokenAuth(secret_key="your-secret-key")

# Generate tokens
access_token = token_auth.create_access_token(user_id="user-123")
refresh_token = token_auth.create_refresh_token(user_id="user-123")

# Verify token
payload = token_auth.verify_token(access_token)
if payload:
    user_id = payload["user_id"]

# Protect endpoint with bearer token
from mycms.api.authentication import require_bearer_token

@require_bearer_token(secret_key="your-secret-key")
async def protected_endpoint(request: Request) -> Response:
    return JSONResponse({"message": "Authenticated!"})
```

## Permissions

Control access to API endpoints with permissions.

### Built-in Permission Classes

```python
from mycms.api.permissions import (
    IsAuthenticated,
    IsStaff,
    IsSuperuser,
    HasPermission,
    IsReadOnly,
)

# Require authentication
from mycms.api import require_authenticated

@require_authenticated()
async def user_profile(request: Request) -> Response:
    user = request.user
    return JSONResponse({"username": user.username})

# Require staff access
from mycms.api import require_staff

@require_staff()
async def admin_panel(request: Request) -> Response:
    return JSONResponse({"admin": True})

# Require specific permission
from mycms.api import require_permission

@require_permission("edit_posts")
async def edit_post(request: Request) -> Response:
    return JSONResponse({"can_edit": True})

# Allow only read operations
from mycms.api import require_read_only

@require_read_only()
async def public_data(request: Request) -> Response:
    return JSONResponse({"data": []})
```

### Custom Permissions

```python
from mycms.api import APIPermission, require_api_permission

class IsOwner(APIPermission):
    async def has_permission_async(self, request: Request, user: User) -> bool:
        obj_id = request.query_params.get("id")
        obj = await SomeModel.get(id=obj_id)
        return obj.owner_id == user.id
    
    def get_error_message(self) -> str:
        return "You must be the owner to access this resource"

# Use custom permission
@require_api_permission(IsAuthenticated(), IsOwner())
async def owner_only_endpoint(request: Request) -> Response:
    return JSONResponse({"access": "granted"})
```

## Pagination

Paginate large result sets efficiently.

### Basic Pagination

```python
from mycms.api import Paginator

# Simple list pagination
items = list(range(100))
paginator = Paginator(items, page_size=10)

# Get a specific page
result = paginator.get_page(page=1)
print(f"Items: {result.items}")
print(f"Page {result.page} of {result.total_pages}")
print(f"Has next: {result.has_next()}")
```

### Page Number Pagination

```python
from mycms.api import PageNumberPagination

pagination = PageNumberPagination(page_size=10, max_page_size=100)

# In your endpoint
async def list_items(request: Request) -> Response:
    items = await get_all_items()
    result = pagination.paginate(items, request.query_params)
    
    return JSONResponse(result.to_dict())

# Client requests: /api/items?page=2&page_size=20
```

### Cursor Pagination

For large datasets where page numbers become inefficient:

```python
from mycms.api import CursorPagination

pagination = CursorPagination(page_size=10)

async def list_items(request: Request) -> Response:
    items = await get_all_items()
    result = pagination.paginate(items, request.query_params)
    
    return JSONResponse(result)

# Client requests: /api/items?cursor=eyJpZCI6MTIzfQ==
```

## Documentation

Automatically generate API documentation.

### Creating Documentation

```python
from mycms.api import APIDocGenerator

# Create generator
doc_gen = APIDocGenerator(
    title="My API",
    version="1.0.0",
    description="A comprehensive API for my application",
    base_url="https://api.example.com"
)

# Add endpoint documentation
doc_gen.add_endpoint(
    path="/api/users",
    methods=["GET", "POST"],
    name="User Management",
    description="Manage user accounts",
    parameters=[
        {
            "name": "limit",
            "type": "integer",
            "required": False,
            "description": "Number of results to return"
        }
    ],
    request_body={
        "type": "object",
        "properties": {
            "username": {"type": "string"},
            "email": {"type": "string"}
        }
    },
    responses={
        200: {
            "description": "Success",
            "schema": {"type": "array", "items": {"type": "object"}}
        }
    },
    authentication="BearerAuth",
    permissions=["read_users"]
)
```

### Generate Documentation Formats

```python
# OpenAPI 3.0 specification
openapi_spec = doc_gen.generate_openapi()
with open("openapi.json", "w") as f:
    json.dump(openapi_spec, f, indent=2)

# Markdown documentation
markdown = doc_gen.generate_markdown()
with open("API.md", "w") as f:
    f.write(markdown)

# HTML documentation
html = doc_gen.generate_html()
with open("api-docs.html", "w") as f:
    f.write(html)
```

## Complete Example

Here's a complete example combining all components:

```python
from mycms.api import (
    APIRouter,
    APIView,
    ModelSerializer,
    APIKeyAuth,
    require_api_auth,
    require_staff,
    PageNumberPagination,
    APIDocGenerator,
)
from mycms.core.framework.request import Request
from mycms.core.framework.response import JSONResponse

# Setup
router = APIRouter(prefix="/api/v1")
api_key_auth = APIKeyAuth()
pagination = PageNumberPagination(page_size=20)

# Serializer
class UserSerializer(ModelSerializer):
    model_class = User
    exclude = ["password"]

# API View
class UserListView(APIView):
    @require_api_auth(api_key_auth)
    async def get(self, request: Request, **kwargs) -> JSONResponse:
        # Get all users
        users = await User.all()
        
        # Paginate
        result = pagination.paginate(users, request.query_params)
        
        # Serialize
        serializer = UserSerializer(instance=result.items, many=True)
        
        return JSONResponse({
            "users": serializer.to_dict(),
            "pagination": {
                "page": result.page,
                "total_pages": result.total_pages,
                "has_next": result.has_next()
            }
        })
    
    @require_staff()
    @require_api_auth(api_key_auth)
    async def post(self, request: Request, **kwargs) -> JSONResponse:
        # Deserialize and validate
        data = await request.json()
        serializer = UserSerializer(data=data)
        
        if not serializer.validate():
            return JSONResponse(
                {"errors": serializer.errors},
                status_code=400
            )
        
        # Save
        user = await serializer.save()
        
        # Return created user
        return JSONResponse(
            UserSerializer(instance=user).to_dict(),
            status_code=201
        )

# Register view
router.add_view("/users", UserListView())

# Generate documentation
doc_gen = APIDocGenerator(title="User API", version="1.0.0")
doc_gen.add_endpoint(
    path="/api/v1/users",
    methods=["GET", "POST"],
    name="User List",
    description="List and create users",
    authentication="ApiKeyAuth"
)

# In your application
async def handle_request(request):
    return await router.handle(request)
```

## Best Practices

1. **Use serializers** for all data input/output to ensure consistency
2. **Always validate** user input with serializer validation
3. **Apply appropriate permissions** to protect sensitive endpoints
4. **Paginate large datasets** to improve performance
5. **Document your API** using the documentation generator
6. **Use API keys for server-to-server** communication
7. **Use JWT tokens for user authentication** in client applications
8. **Set reasonable rate limits** (to be implemented in future versions)
9. **Version your API** using the router prefix (e.g., `/api/v1`)
10. **Return appropriate HTTP status codes** (200, 201, 400, 401, 403, 404, 500)

## Testing

The API layer includes comprehensive tests. Run them with:

```bash
pytest tests/test_api_*.py -v
```

All API components have 100% test coverage to ensure reliability.
