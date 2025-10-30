"""
Tests for APISpec Emulator

Comprehensive test suite for OpenAPI specification generation.
"""

import unittest
import json
from apispec_emulator import (
    APISpec,
    parameter,
    request_body,
    response,
    schema_ref,
    parameter_ref,
    response_ref,
)


class TestAPISpecBasic(unittest.TestCase):
    """Test basic APISpec operations."""
    
    def test_create_spec(self):
        """Test creating a basic spec."""
        spec = APISpec(
            title='My API',
            version='1.0.0',
            openapi_version='3.0.2'
        )
        
        result = spec.to_dict()
        
        self.assertEqual(result['openapi'], '3.0.2')
        self.assertEqual(result['info']['title'], 'My API')
        self.assertEqual(result['info']['version'], '1.0.0')
    
    def test_spec_with_info(self):
        """Test spec with additional info."""
        spec = APISpec(
            title='My API',
            version='1.0.0',
            info={
                'description': 'A test API',
                'contact': {'email': 'api@example.com'},
                'license': {'name': 'MIT'}
            }
        )
        
        result = spec.to_dict()
        info = result['info']
        
        self.assertEqual(info['description'], 'A test API')
        self.assertEqual(info['contact']['email'], 'api@example.com')
        self.assertEqual(info['license']['name'], 'MIT')
    
    def test_spec_with_servers(self):
        """Test spec with servers."""
        servers = [
            {'url': 'https://api.example.com', 'description': 'Production'},
            {'url': 'https://staging.example.com', 'description': 'Staging'}
        ]
        
        spec = APISpec(
            title='My API',
            version='1.0.0',
            servers=servers
        )
        
        result = spec.to_dict()
        self.assertEqual(len(result['servers']), 2)
        self.assertEqual(result['servers'][0]['url'], 'https://api.example.com')


class TestPaths(unittest.TestCase):
    """Test path operations."""
    
    def test_add_path(self):
        """Test adding a path."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.path('/users', summary='User operations')
        
        result = spec.to_dict()
        self.assertIn('/users', result['paths'])
        self.assertEqual(result['paths']['/users']['summary'], 'User operations')
    
    def test_add_operation(self):
        """Test adding an operation."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.operation(
            path='/users',
            method='get',
            summary='Get users',
            operationId='getUsers',
            responses={'200': {'description': 'Success'}}
        )
        
        result = spec.to_dict()
        operation = result['paths']['/users']['get']
        
        self.assertEqual(operation['summary'], 'Get users')
        self.assertEqual(operation['operationId'], 'getUsers')
        self.assertIn('200', operation['responses'])
    
    def test_multiple_operations(self):
        """Test adding multiple operations to same path."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.operation('/users', 'get', summary='Get users')
        spec.operation('/users', 'post', summary='Create user')
        
        result = spec.to_dict()
        path = result['paths']['/users']
        
        self.assertIn('get', path)
        self.assertIn('post', path)
        self.assertEqual(path['get']['summary'], 'Get users')
        self.assertEqual(path['post']['summary'], 'Create user')
    
    def test_operation_with_parameters(self):
        """Test operation with parameters."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.operation(
            path='/users/{id}',
            method='get',
            parameters=[
                parameter('id', 'path', required=True, type='integer')
            ]
        )
        
        result = spec.to_dict()
        params = result['paths']['/users/{id}']['get']['parameters']
        
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]['name'], 'id')
        self.assertEqual(params[0]['in'], 'path')
        self.assertTrue(params[0]['required'])
    
    def test_operation_with_request_body(self):
        """Test operation with request body."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.operation(
            path='/users',
            method='post',
            requestBody=request_body(
                content={
                    'application/json': {
                        'schema': {'$ref': '#/components/schemas/User'}
                    }
                },
                required=True
            )
        )
        
        result = spec.to_dict()
        req_body = result['paths']['/users']['post']['requestBody']
        
        self.assertTrue(req_body['required'])
        self.assertIn('application/json', req_body['content'])


class TestDefinitions(unittest.TestCase):
    """Test schema definitions."""
    
    def test_add_definition(self):
        """Test adding a schema definition."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.definition(
            'User',
            type='object',
            properties={
                'id': {'type': 'integer'},
                'name': {'type': 'string'}
            },
            required=['id', 'name']
        )
        
        result = spec.to_dict()
        user_schema = result['components']['schemas']['User']
        
        self.assertEqual(user_schema['type'], 'object')
        self.assertIn('id', user_schema['properties'])
        self.assertEqual(len(user_schema['required']), 2)
    
    def test_definition_with_complete_schema(self):
        """Test adding definition with complete schema object."""
        spec = APISpec(title='API', version='1.0.0')
        
        user_schema = {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'}
            },
            'required': ['id', 'name']
        }
        
        spec.definition('User', schema=user_schema)
        
        result = spec.to_dict()
        self.assertEqual(result['components']['schemas']['User'], user_schema)
    
    def test_schema_references(self):
        """Test schema references."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.definition('User', type='object', properties={'name': {'type': 'string'}})
        
        spec.operation(
            path='/users',
            method='get',
            responses={
                '200': response(
                    description='Success',
                    content={
                        'application/json': {
                            'schema': schema_ref('User')
                        }
                    }
                )
            }
        )
        
        result = spec.to_dict()
        schema = result['paths']['/users']['get']['responses']['200']['content']['application/json']['schema']
        
        self.assertEqual(schema['$ref'], '#/components/schemas/User')


class TestTags(unittest.TestCase):
    """Test tag operations."""
    
    def test_add_tag(self):
        """Test adding a tag."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.tag('users', description='User operations')
        
        result = spec.to_dict()
        tags = result['tags']
        
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]['name'], 'users')
        self.assertEqual(tags[0]['description'], 'User operations')
    
    def test_operation_with_tags(self):
        """Test operation with tags."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.operation('/users', 'get', tags=['users', 'public'])
        
        result = spec.to_dict()
        operation_tags = result['paths']['/users']['get']['tags']
        
        self.assertEqual(len(operation_tags), 2)
        self.assertIn('users', operation_tags)
        self.assertIn('public', operation_tags)
        
        # Tags should be added to global tags
        self.assertIn('tags', result)
        tag_names = [tag['name'] for tag in result['tags']]
        self.assertIn('users', tag_names)
        self.assertIn('public', tag_names)
    
    def test_initial_tags(self):
        """Test spec with initial tags."""
        tags = [
            {'name': 'users', 'description': 'User operations'},
            {'name': 'products', 'description': 'Product operations'}
        ]
        
        spec = APISpec(title='API', version='1.0.0', tags=tags)
        
        result = spec.to_dict()
        self.assertEqual(len(result['tags']), 2)


class TestSecuritySchemes(unittest.TestCase):
    """Test security scheme operations."""
    
    def test_api_key_security(self):
        """Test API key security scheme."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.security_scheme(
            'api_key',
            type='apiKey',
            in_='header',
            name_='X-API-Key'
        )
        
        result = spec.to_dict()
        security = result['components']['securitySchemes']['api_key']
        
        self.assertEqual(security['type'], 'apiKey')
        self.assertEqual(security['in'], 'header')
        self.assertEqual(security['name'], 'X-API-Key')
    
    def test_bearer_token_security(self):
        """Test Bearer token security scheme."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.security_scheme(
            'bearer',
            type='http',
            scheme='bearer',
            bearerFormat='JWT'
        )
        
        result = spec.to_dict()
        security = result['components']['securitySchemes']['bearer']
        
        self.assertEqual(security['type'], 'http')
        self.assertEqual(security['scheme'], 'bearer')
        self.assertEqual(security['bearerFormat'], 'JWT')
    
    def test_oauth2_security(self):
        """Test OAuth2 security scheme."""
        spec = APISpec(title='API', version='1.0.0')
        
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
        
        result = spec.to_dict()
        security = result['components']['securitySchemes']['oauth2']
        
        self.assertEqual(security['type'], 'oauth2')
        self.assertIn('authorizationCode', security['flows'])


class TestComponents(unittest.TestCase):
    """Test component operations."""
    
    def test_add_response_component(self):
        """Test adding a reusable response."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.component(
            'responses',
            'NotFound',
            {
                'description': 'Resource not found',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        )
        
        result = spec.to_dict()
        not_found = result['components']['responses']['NotFound']
        
        self.assertEqual(not_found['description'], 'Resource not found')
    
    def test_add_parameter_component(self):
        """Test adding a reusable parameter."""
        spec = APISpec(title='API', version='1.0.0')
        
        spec.component(
            'parameters',
            'PageParam',
            parameter('page', 'query', type='integer', description='Page number')
        )
        
        result = spec.to_dict()
        page_param = result['components']['parameters']['PageParam']
        
        self.assertEqual(page_param['name'], 'page')
        self.assertEqual(page_param['in'], 'query')


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""
    
    def test_parameter_helper(self):
        """Test parameter helper function."""
        param = parameter(
            'id',
            'path',
            description='User ID',
            required=True,
            schema={'type': 'integer'}
        )
        
        self.assertEqual(param['name'], 'id')
        self.assertEqual(param['in'], 'path')
        self.assertTrue(param['required'])
        self.assertEqual(param['schema']['type'], 'integer')
    
    def test_request_body_helper(self):
        """Test request_body helper function."""
        body = request_body(
            content={
                'application/json': {
                    'schema': {'type': 'object'}
                }
            },
            description='User data',
            required=True
        )
        
        self.assertTrue(body['required'])
        self.assertEqual(body['description'], 'User data')
        self.assertIn('application/json', body['content'])
    
    def test_response_helper(self):
        """Test response helper function."""
        resp = response(
            description='Success',
            content={
                'application/json': {
                    'schema': {'type': 'object'}
                }
            }
        )
        
        self.assertEqual(resp['description'], 'Success')
        self.assertIn('application/json', resp['content'])
    
    def test_schema_ref_helper(self):
        """Test schema_ref helper function."""
        ref = schema_ref('User')
        self.assertEqual(ref['$ref'], '#/components/schemas/User')
    
    def test_parameter_ref_helper(self):
        """Test parameter_ref helper function."""
        ref = parameter_ref('PageParam')
        self.assertEqual(ref['$ref'], '#/components/parameters/PageParam')
    
    def test_response_ref_helper(self):
        """Test response_ref helper function."""
        ref = response_ref('NotFound')
        self.assertEqual(ref['$ref'], '#/components/responses/NotFound')


class TestOutputFormats(unittest.TestCase):
    """Test output formats."""
    
    def test_to_dict(self):
        """Test to_dict output."""
        spec = APISpec(title='API', version='1.0.0')
        spec.operation('/test', 'get', summary='Test')
        
        result = spec.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['info']['title'], 'API')
        self.assertIn('/test', result['paths'])
    
    def test_to_json(self):
        """Test to_json output."""
        spec = APISpec(title='API', version='1.0.0')
        spec.operation('/test', 'get', summary='Test')
        
        result = spec.to_json()
        
        self.assertIsInstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed['info']['title'], 'API')
    
    def test_to_yaml(self):
        """Test to_yaml output."""
        spec = APISpec(title='API', version='1.0.0')
        spec.operation('/test', 'get', summary='Test')
        
        result = spec.to_yaml()
        
        self.assertIsInstance(result, str)
        self.assertIn('openapi:', result)
        self.assertIn('title:', result)
        self.assertIn('version:', result)


class TestCompleteExample(unittest.TestCase):
    """Test complete API specification."""
    
    def test_complete_api(self):
        """Test creating a complete API specification."""
        spec = APISpec(
            title='Pet Store API',
            version='1.0.0',
            info={
                'description': 'A sample Pet Store API',
                'contact': {'email': 'api@petstore.com'}
            },
            servers=[
                {'url': 'https://api.petstore.com/v1', 'description': 'Production'}
            ]
        )
        
        # Add security scheme
        spec.security_scheme(
            'api_key',
            type='apiKey',
            in_='header',
            name_='X-API-Key'
        )
        
        # Add schema
        spec.definition(
            'Pet',
            type='object',
            properties={
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'status': {'type': 'string', 'enum': ['available', 'pending', 'sold']}
            },
            required=['name']
        )
        
        # Add operations
        spec.operation(
            path='/pets',
            method='get',
            summary='List all pets',
            operationId='listPets',
            tags=['pets'],
            parameters=[
                parameter('limit', 'query', type='integer', description='Max results')
            ],
            responses={
                '200': response(
                    description='Success',
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
                '201': response(description='Created')
            },
            security=[{'api_key': []}]
        )
        
        result = spec.to_dict()
        
        # Verify structure
        self.assertEqual(result['info']['title'], 'Pet Store API')
        self.assertEqual(len(result['servers']), 1)
        self.assertIn('Pet', result['components']['schemas'])
        self.assertIn('api_key', result['components']['securitySchemes'])
        self.assertIn('/pets', result['paths'])
        self.assertIn('get', result['paths']['/pets'])
        self.assertIn('post', result['paths']['/pets'])
        
        # Verify tags
        tag_names = [tag['name'] for tag in result['tags']]
        self.assertIn('pets', tag_names)


if __name__ == '__main__':
    unittest.main()
