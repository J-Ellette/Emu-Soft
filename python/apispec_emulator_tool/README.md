# APISpec Emulator - OpenAPI Specification Generator

This module emulates the **apispec** library, which is a pluggable API specification generator that supports the OpenAPI Specification (formerly Swagger).

## What is APISpec?

APISpec is a Python library for generating OpenAPI specifications for REST APIs. It's commonly used for:
- Documenting REST APIs
- Generating API documentation (Swagger UI, ReDoc)
- API client generation
- API testing and validation
- Contract-first API development

## Features

This emulator implements:

### OpenAPI Specification Generation
- OpenAPI 3.0.x specification generation
- Complete spec structure (info, servers, paths, components, security)
- Ordered output for consistency

### Path Operations
- Path definition with operations
- Operation documentation (summary, description, operationId)
- HTTP method support (GET, POST, PUT, DELETE, PATCH, etc.)
- Tags and categorization
- Deprecated operation marking

### Parameters
- Path parameters
- Query parameters
- Header parameters
- Cookie parameters
- Parameter schemas and validation

### Request Bodies
- Request body specifications
- Media type support (JSON, XML, etc.)
- Required/optional bodies
- Schema references

### Responses
- Response documentation
- Multiple status codes
- Response content and schemas
- Response headers
- Reusable response components

### Schema Definitions
- Component schema definitions
- Schema properties and types
- Required fields
- Schema references ($ref)
- Nested schemas

### Security
- Security scheme definitions (API key, Bearer, OAuth2, OpenID Connect)
- Operation-level security requirements
- Multiple security schemes

### Components
- Reusable schemas
- Reusable responses
- Reusable parameters
- Reusable request bodies
- Security schemes

### Output Formats
- Python dictionary
- JSON string
- YAML string (basic)

## Usage Examples

### Basic API Specification

```python
from apispec_emulator import APISpec

spec = APISpec(
    title='My API',
    version='1.0.0',
    openapi_version='3.0.2',
    info={
        'description': 'A sample API',
        'contact': {'email': 'api@example.com'},
        'license': {'name': 'MIT'}
    }
)

# Get as dict
spec_dict = spec.to_dict()

# Get as JSON
spec_json = spec.to_json()

# Get as YAML
spec_yaml = spec.to_yaml()
```

### Adding Paths and Operations

```python
from apispec_emulator import APISpec, parameter, response

spec = APISpec(title='User API', version='1.0.0')

# Add an operation
spec.operation(
    path='/users',
    method='get',
    summary='List all users',
    operationId='listUsers',
    tags=['users'],
    parameters=[
        parameter('limit', 'query', type='integer', description='Max results'),
        parameter('offset', 'query', type='integer', description='Offset')
    ],
    responses={
        '200': response(description='Success')
    }
)

# Add another operation
spec.operation(
    path='/users/{id}',
    method='get',
    summary='Get user by ID',
    operationId='getUser',
    tags=['users'],
    parameters=[
        parameter('id', 'path', required=True, type='integer')
    ],
    responses={
        '200': response(description='User found'),
        '404': response(description='User not found')
    }
)
```

### Defining Schemas

```python
from apispec_emulator import APISpec, schema_ref

spec = APISpec(title='API', version='1.0.0')

# Define a schema
spec.definition(
    'User',
    type='object',
    properties={
        'id': {'type': 'integer'},
        'username': {'type': 'string'},
        'email': {'type': 'string', 'format': 'email'},
        'created_at': {'type': 'string', 'format': 'date-time'}
    },
    required=['username', 'email']
)

# Use schema reference in operation
spec.operation(
    path='/users',
    method='post',
    summary='Create user',
    requestBody={
        'content': {
            'application/json': {
                'schema': schema_ref('User')
            }
        },
        'required': True
    },
    responses={
        '201': {
            'description': 'User created',
            'content': {
                'application/json': {
                    'schema': schema_ref('User')
                }
            }
        }
    }
)
```

### Adding Tags

```python
spec = APISpec(title='API', version='1.0.0')

# Add tags with descriptions
spec.tag('users', description='User management operations')
spec.tag('products', description='Product catalog operations')
spec.tag('orders', description='Order processing operations')

# Operations will reference these tags
spec.operation('/users', 'get', tags=['users'])
spec.operation('/products', 'get', tags=['products'])
```

### Security Schemes

```python
from apispec_emulator import APISpec

spec = APISpec(title='API', version='1.0.0')

# API Key authentication
spec.security_scheme(
    'api_key',
    type='apiKey',
    in_='header',
    name_='X-API-Key'
)

# Bearer token (JWT)
spec.security_scheme(
    'bearer',
    type='http',
    scheme='bearer',
    bearerFormat='JWT'
)

# OAuth2
spec.security_scheme(
    'oauth2',
    type='oauth2',
    flows={
        'authorizationCode': {
            'authorizationUrl': 'https://example.com/oauth/authorize',
            'tokenUrl': 'https://example.com/oauth/token',
            'scopes': {
                'read': 'Read access',
                'write': 'Write access'
            }
        }
    }
)

# Use security in operation
spec.operation(
    '/users',
    'post',
    security=[{'bearer': []}],  # Require bearer token
    summary='Create user (authenticated)'
)
```

### Complete Example

```python
from apispec_emulator import APISpec, parameter, request_body, response, schema_ref

# Create spec
spec = APISpec(
    title='Pet Store API',
    version='1.0.0',
    info={
        'description': 'A sample Pet Store API',
        'contact': {'email': 'support@petstore.com'}
    },
    servers=[
        {'url': 'https://api.petstore.com/v1', 'description': 'Production'},
        {'url': 'https://staging.petstore.com/v1', 'description': 'Staging'}
    ]
)

# Add security
spec.security_scheme(
    'api_key',
    type='apiKey',
    in_='header',
    name_='X-API-Key'
)

# Define schemas
spec.definition(
    'Pet',
    type='object',
    properties={
        'id': {'type': 'integer', 'format': 'int64'},
        'name': {'type': 'string'},
        'tag': {'type': 'string'},
        'status': {
            'type': 'string',
            'enum': ['available', 'pending', 'sold']
        }
    },
    required=['name']
)

spec.definition(
    'Error',
    type='object',
    properties={
        'code': {'type': 'integer'},
        'message': {'type': 'string'}
    },
    required=['code', 'message']
)

# Add operations
spec.operation(
    path='/pets',
    method='get',
    summary='List all pets',
    operationId='listPets',
    tags=['pets'],
    parameters=[
        parameter('limit', 'query', type='integer', description='How many items to return')
    ],
    responses={
        '200': response(
            description='A list of pets',
            content={
                'application/json': {
                    'schema': {
                        'type': 'array',
                        'items': schema_ref('Pet')
                    }
                }
            }
        )
    }
)

spec.operation(
    path='/pets',
    method='post',
    summary='Create a pet',
    operationId='createPet',
    tags=['pets'],
    requestBody=request_body(
        content={
            'application/json': {
                'schema': schema_ref('Pet')
            }
        },
        required=True
    ),
    responses={
        '201': response(description='Pet created'),
        '400': response(
            description='Invalid input',
            content={
                'application/json': {
                    'schema': schema_ref('Error')
                }
            }
        )
    },
    security=[{'api_key': []}]
)

spec.operation(
    path='/pets/{petId}',
    method='get',
    summary='Get a pet by ID',
    operationId='getPet',
    tags=['pets'],
    parameters=[
        parameter('petId', 'path', required=True, type='integer', description='Pet ID')
    ],
    responses={
        '200': response(
            description='Pet details',
            content={
                'application/json': {
                    'schema': schema_ref('Pet')
                }
            }
        ),
        '404': response(description='Pet not found')
    }
)

# Output as JSON
print(spec.to_json(indent=2))

# Output as YAML
print(spec.to_yaml())
```

## Helper Functions

The module provides helper functions for common patterns:

- `parameter()` - Create parameter objects
- `request_body()` - Create request body objects
- `response()` - Create response objects
- `schema_ref()` - Create schema references
- `parameter_ref()` - Create parameter references
- `response_ref()` - Create response references
- `request_body_ref()` - Create request body references

## Testing

Run the comprehensive test suite:

```bash
python test_apispec_emulator.py
```

Tests cover:
- Basic spec creation
- Path and operation definition
- Schema definitions
- Parameters and request bodies
- Responses and status codes
- Tags and metadata
- Security schemes
- Component reuse
- Output formats (dict, JSON, YAML)
- Complete API examples

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for apispec in development and testing:

```python
# Instead of:
# from apispec import APISpec

# Use:
from apispec_emulator import APISpec
```

## Use Cases

Perfect for:
- **API Documentation**: Generate OpenAPI specs for documentation tools
- **Contract-First Development**: Define API contracts before implementation
- **Testing**: Test API specifications without external dependencies
- **Code Generation**: Generate API clients from specifications
- **API Validation**: Validate API requests and responses
- **Development**: Local development without apispec dependency

## Compatibility

Emulates core features of:
- apispec 6.x API
- OpenAPI 3.0.x specification format
- Common documentation patterns

## License

Part of the Emu-Soft project. See main repository LICENSE.
