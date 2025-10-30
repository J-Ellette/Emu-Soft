"""
APISpec Emulator - OpenAPI Specification Generator

This module emulates the apispec library functionality for generating OpenAPI
(formerly Swagger) specifications for REST APIs.

Key Features:
- OpenAPI 3.0.x specification generation
- Path and operation documentation
- Schema definitions and references
- Parameter and request body specifications
- Response documentation
- Security schemes
- Tags and metadata
- YAML and JSON output
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from collections import OrderedDict
import json
import re


class APISpec:
    """OpenAPI specification generator."""
    
    def __init__(
        self,
        title: str,
        version: str,
        openapi_version: str = '3.0.2',
        info: Optional[Dict[str, Any]] = None,
        servers: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[Dict[str, Any]]] = None,
        security: Optional[List[Dict[str, List]]] = None,
        **options
    ):
        """
        Initialize OpenAPI specification.
        
        Args:
            title: API title
            version: API version
            openapi_version: OpenAPI version (default: 3.0.2)
            info: Additional info fields (description, terms, contact, license)
            servers: List of server objects
            tags: List of tag objects
            security: Security requirements
            **options: Additional options
        """
        self.title = title
        self.version = version
        self.openapi_version = openapi_version
        self.options = options
        
        # Build info object
        self.info = {
            'title': title,
            'version': version,
            **(info or {})
        }
        
        # Initialize spec structure
        self.spec = OrderedDict([
            ('openapi', openapi_version),
            ('info', self.info),
        ])
        
        if servers:
            self.spec['servers'] = servers
        
        if tags:
            self.spec['tags'] = tags
        
        if security:
            self.spec['security'] = security
        
        # Collections
        self.spec['paths'] = OrderedDict()
        self.spec['components'] = {
            'schemas': OrderedDict(),
            'responses': OrderedDict(),
            'parameters': OrderedDict(),
            'examples': OrderedDict(),
            'requestBodies': OrderedDict(),
            'headers': OrderedDict(),
            'securitySchemes': OrderedDict(),
            'links': OrderedDict(),
            'callbacks': OrderedDict(),
        }
        
        # Track tags
        self._tags = set()
        if tags:
            for tag in tags:
                self._tags.add(tag['name'])
    
    def path(
        self,
        path: str,
        *,
        operations: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """
        Add a path to the spec.
        
        Args:
            path: URL path (e.g., '/users/{id}')
            operations: Dict of operations keyed by HTTP method
            summary: Path summary
            description: Path description
            parameters: Common parameters for all operations
            **kwargs: Additional path-level fields
        """
        if path not in self.spec['paths']:
            self.spec['paths'][path] = OrderedDict()
        
        path_obj = self.spec['paths'][path]
        
        if summary:
            path_obj['summary'] = summary
        if description:
            path_obj['description'] = description
        if parameters:
            path_obj['parameters'] = parameters
        
        # Add operations
        if operations:
            for method, operation in operations.items():
                path_obj[method.lower()] = operation
        
        # Add any other fields
        for key, value in kwargs.items():
            if key not in ('operations', 'summary', 'description', 'parameters'):
                path_obj[key] = value
    
    def operation(
        self,
        path: str,
        method: str,
        *,
        operationId: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        requestBody: Optional[Dict[str, Any]] = None,
        responses: Optional[Dict[str, Any]] = None,
        security: Optional[List[Dict[str, List]]] = None,
        deprecated: bool = False,
        **kwargs
    ):
        """
        Add an operation to a path.
        
        Args:
            path: URL path
            method: HTTP method (get, post, put, delete, etc.)
            operationId: Unique operation identifier
            summary: Short summary
            description: Detailed description
            tags: List of tags
            parameters: List of parameters
            requestBody: Request body specification
            responses: Response specifications
            security: Security requirements
            deprecated: Whether operation is deprecated
            **kwargs: Additional operation fields
        """
        # Ensure path exists
        if path not in self.spec['paths']:
            self.spec['paths'][path] = OrderedDict()
        
        # Build operation object
        operation = OrderedDict()
        
        if tags:
            operation['tags'] = tags
            # Add to global tags if not exists
            for tag in tags:
                if tag not in self._tags:
                    self._tags.add(tag)
                    if 'tags' not in self.spec:
                        self.spec['tags'] = []
                    self.spec['tags'].append({'name': tag})
        
        if summary:
            operation['summary'] = summary
        if description:
            operation['description'] = description
        if operationId:
            operation['operationId'] = operationId
        if parameters:
            operation['parameters'] = parameters
        if requestBody:
            operation['requestBody'] = requestBody
        
        # Responses (required in OpenAPI)
        if responses:
            operation['responses'] = responses
        else:
            operation['responses'] = {'200': {'description': 'Success'}}
        
        if security:
            operation['security'] = security
        if deprecated:
            operation['deprecated'] = True
        
        # Add any additional fields
        for key, value in kwargs.items():
            if key not in operation:
                operation[key] = value
        
        # Add to path
        self.spec['paths'][path][method.lower()] = operation
    
    def definition(
        self,
        name: str,
        *,
        schema: Optional[Dict[str, Any]] = None,
        properties: Optional[Dict[str, Any]] = None,
        required: Optional[List[str]] = None,
        type: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Add a schema definition to components.
        
        Args:
            name: Schema name
            schema: Complete schema object
            properties: Schema properties
            required: Required properties
            type: Schema type (usually 'object')
            description: Schema description
            **kwargs: Additional schema fields
        """
        if schema:
            self.spec['components']['schemas'][name] = schema
        else:
            schema_obj = OrderedDict()
            
            if type:
                schema_obj['type'] = type
            if description:
                schema_obj['description'] = description
            if properties:
                schema_obj['properties'] = properties
            if required:
                schema_obj['required'] = required
            
            # Add additional fields
            for key, value in kwargs.items():
                if key not in schema_obj:
                    schema_obj[key] = value
            
            self.spec['components']['schemas'][name] = schema_obj
    
    def component(
        self,
        component_type: str,
        name: str,
        component: Dict[str, Any]
    ):
        """
        Add a component of any type.
        
        Args:
            component_type: Type (schemas, responses, parameters, etc.)
            name: Component name
            component: Component specification
        """
        if component_type in self.spec['components']:
            self.spec['components'][component_type][name] = component
    
    def tag(self, name: str, description: Optional[str] = None, **kwargs):
        """
        Add a tag definition.
        
        Args:
            name: Tag name
            description: Tag description
            **kwargs: Additional tag fields
        """
        if 'tags' not in self.spec:
            self.spec['tags'] = []
        
        tag_obj = {'name': name}
        if description:
            tag_obj['description'] = description
        
        for key, value in kwargs.items():
            if key != 'name':
                tag_obj[key] = value
        
        # Update or add tag
        for i, existing_tag in enumerate(self.spec['tags']):
            if existing_tag['name'] == name:
                self.spec['tags'][i] = tag_obj
                return
        
        self.spec['tags'].append(tag_obj)
        self._tags.add(name)
    
    def security_scheme(
        self,
        name: str,
        *,
        type: str,
        scheme: Optional[str] = None,
        bearerFormat: Optional[str] = None,
        flows: Optional[Dict[str, Any]] = None,
        openIdConnectUrl: Optional[str] = None,
        in_: Optional[str] = None,
        name_: Optional[str] = None,
        **kwargs
    ):
        """
        Add a security scheme.
        
        Args:
            name: Security scheme name
            type: Security type (apiKey, http, oauth2, openIdConnect)
            scheme: HTTP authorization scheme (for http type)
            bearerFormat: Bearer token format (for http type)
            flows: OAuth2 flows (for oauth2 type)
            openIdConnectUrl: OpenID Connect URL
            in_: Location of API key (query, header, cookie)
            name_: Name of API key parameter
            **kwargs: Additional fields
        """
        security_scheme = {'type': type}
        
        if scheme:
            security_scheme['scheme'] = scheme
        if bearerFormat:
            security_scheme['bearerFormat'] = bearerFormat
        if flows:
            security_scheme['flows'] = flows
        if openIdConnectUrl:
            security_scheme['openIdConnectUrl'] = openIdConnectUrl
        if in_:
            security_scheme['in'] = in_
        if name_:
            security_scheme['name'] = name_
        
        for key, value in kwargs.items():
            if key not in security_scheme:
                security_scheme[key] = value
        
        self.spec['components']['securitySchemes'][name] = security_scheme
    
    def to_dict(self) -> Dict[str, Any]:
        """Return specification as dictionary."""
        # Clean up empty components
        spec_copy = dict(self.spec)
        components = {}
        
        for comp_type, comp_dict in self.spec['components'].items():
            if comp_dict:
                components[comp_type] = comp_dict
        
        if components:
            spec_copy['components'] = components
        else:
            del spec_copy['components']
        
        return spec_copy
    
    def to_json(self, indent: int = 2) -> str:
        """Return specification as JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def to_yaml(self) -> str:
        """
        Return specification as YAML string.
        
        Note: This is a simple YAML generator. For complex specs,
        consider using a real YAML library.
        """
        return self._dict_to_yaml(self.to_dict())
    
    def _dict_to_yaml(self, obj: Any, indent: int = 0) -> str:
        """Simple dict to YAML converter."""
        lines = []
        indent_str = '  ' * indent
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{indent_str}{key}:")
                    lines.append(self._dict_to_yaml(value, indent + 1))
                elif value is None:
                    lines.append(f"{indent_str}{key}: null")
                elif isinstance(value, bool):
                    lines.append(f"{indent_str}{key}: {str(value).lower()}")
                elif isinstance(value, str):
                    # Handle multiline strings
                    if '\n' in value:
                        lines.append(f"{indent_str}{key}: |")
                        for line in value.split('\n'):
                            lines.append(f"{indent_str}  {line}")
                    else:
                        lines.append(f"{indent_str}{key}: \"{value}\"")
                else:
                    lines.append(f"{indent_str}{key}: {value}")
        
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent_str}-")
                    lines.append(self._dict_to_yaml(item, indent + 1))
                elif isinstance(item, str):
                    lines.append(f"{indent_str}- \"{item}\"")
                else:
                    lines.append(f"{indent_str}- {item}")
        
        return '\n'.join(lines)


# Helper functions for common patterns
def parameter(
    name: str,
    in_: str,
    *,
    description: Optional[str] = None,
    required: bool = False,
    schema: Optional[Dict[str, Any]] = None,
    type: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a parameter object.
    
    Args:
        name: Parameter name
        in_: Parameter location (path, query, header, cookie)
        description: Parameter description
        required: Whether parameter is required
        schema: Parameter schema
        type: Parameter type (shorthand for schema)
        **kwargs: Additional fields
    """
    param = {
        'name': name,
        'in': in_,
        'required': required,
    }
    
    if description:
        param['description'] = description
    
    if schema:
        param['schema'] = schema
    elif type:
        param['schema'] = {'type': type}
    
    for key, value in kwargs.items():
        if key not in param:
            param[key] = value
    
    return param


def request_body(
    content: Dict[str, Any],
    *,
    description: Optional[str] = None,
    required: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a request body object.
    
    Args:
        content: Content type mapping to media type object
        description: Request body description
        required: Whether request body is required
        **kwargs: Additional fields
    """
    body = {
        'content': content,
        'required': required,
    }
    
    if description:
        body['description'] = description
    
    for key, value in kwargs.items():
        if key not in body:
            body[key] = value
    
    return body


def response(
    description: str,
    *,
    content: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a response object.
    
    Args:
        description: Response description
        content: Content type mapping to media type object
        headers: Response headers
        **kwargs: Additional fields
    """
    resp = {
        'description': description,
    }
    
    if content:
        resp['content'] = content
    if headers:
        resp['headers'] = headers
    
    for key, value in kwargs.items():
        if key not in resp:
            resp[key] = value
    
    return resp


def schema_ref(name: str) -> Dict[str, str]:
    """Create a schema reference."""
    return {'$ref': f'#/components/schemas/{name}'}


def parameter_ref(name: str) -> Dict[str, str]:
    """Create a parameter reference."""
    return {'$ref': f'#/components/parameters/{name}'}


def response_ref(name: str) -> Dict[str, str]:
    """Create a response reference."""
    return {'$ref': f'#/components/responses/{name}'}


def request_body_ref(name: str) -> Dict[str, str]:
    """Create a request body reference."""
    return {'$ref': f'#/components/requestBodies/{name}'}


# Expose common classes at module level
__all__ = [
    'APISpec',
    'parameter',
    'request_body',
    'response',
    'schema_ref',
    'parameter_ref',
    'response_ref',
    'request_body_ref',
]
