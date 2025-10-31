"""
graphene Emulator - GraphQL Framework for Python

This module emulates the graphene library, which is a Python library for building
GraphQL APIs. It provides an elegant way to define GraphQL schemas using Python
classes and allows for easy integration with various web frameworks.

Key Features:
- Schema definition with Types and Fields
- Query and Mutation support
- Object types, Scalars, and Lists
- Field resolvers
- Schema execution
- Argument handling
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable, Union, Type
from datetime import datetime
import json


class GraphQLError(Exception):
    """Base exception for GraphQL errors."""
    pass


class ValidationError(GraphQLError):
    """Raised when validation fails."""
    pass


# Base Scalar Types
class Scalar:
    """Base class for scalar types."""
    
    @staticmethod
    def serialize(value: Any) -> Any:
        """Serialize value for output."""
        return value
    
    @staticmethod
    def parse_value(value: Any) -> Any:
        """Parse input value."""
        return value


class String(Scalar):
    """GraphQL String scalar type."""
    
    @staticmethod
    def serialize(value: Any) -> str:
        return str(value)
    
    @staticmethod
    def parse_value(value: Any) -> str:
        return str(value)


class Int(Scalar):
    """GraphQL Int scalar type."""
    
    @staticmethod
    def serialize(value: Any) -> int:
        return int(value)
    
    @staticmethod
    def parse_value(value: Any) -> int:
        return int(value)


class Float(Scalar):
    """GraphQL Float scalar type."""
    
    @staticmethod
    def serialize(value: Any) -> float:
        return float(value)
    
    @staticmethod
    def parse_value(value: Any) -> float:
        return float(value)


class Boolean(Scalar):
    """GraphQL Boolean scalar type."""
    
    @staticmethod
    def serialize(value: Any) -> bool:
        return bool(value)
    
    @staticmethod
    def parse_value(value: Any) -> bool:
        return bool(value)


class ID(Scalar):
    """GraphQL ID scalar type."""
    
    @staticmethod
    def serialize(value: Any) -> str:
        return str(value)
    
    @staticmethod
    def parse_value(value: Any) -> str:
        return str(value)


class DateTime(Scalar):
    """GraphQL DateTime scalar type."""
    
    @staticmethod
    def serialize(value: datetime) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
    
    @staticmethod
    def parse_value(value: str) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)


# Field class
class Field:
    """Represents a field in a GraphQL type."""
    
    def __init__(
        self,
        type_: Type,
        required: bool = False,
        resolver: Optional[Callable] = None,
        description: Optional[str] = None,
        default_value: Any = None,
        **kwargs
    ):
        self.type = type_
        self.required = required
        self.resolver = resolver
        self.description = description
        self.default_value = default_value
        self.args = kwargs
    
    def resolve(self, root: Any, info: Any, **kwargs) -> Any:
        """Resolve the field value."""
        if self.resolver:
            return self.resolver(root, info, **kwargs)
        
        # Default resolver: try to get attribute from root
        field_name = getattr(info, 'field_name', None)
        if field_name and hasattr(root, field_name):
            return getattr(root, field_name)
        
        return self.default_value


class Argument:
    """Represents an argument to a field."""
    
    def __init__(
        self,
        type_: Type,
        required: bool = False,
        default_value: Any = None,
        description: Optional[str] = None
    ):
        self.type = type_
        self.required = required
        self.default_value = default_value
        self.description = description


class List:
    """Represents a GraphQL list type."""
    
    def __init__(self, of_type: Type):
        self.of_type = of_type
    
    def __repr__(self):
        return f"[{self.of_type}]"


class NonNull:
    """Represents a non-nullable GraphQL type."""
    
    def __init__(self, of_type: Type):
        self.of_type = of_type
    
    def __repr__(self):
        return f"{self.of_type}!"


# Object Type
class ObjectTypeMeta(type):
    """Metaclass for ObjectType."""
    
    def __new__(mcs, name, bases, namespace):
        # Collect fields from the class
        fields = {}
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                fields[key] = value
                # Store field name for resolver
                value.field_name = key
        
        namespace['_fields'] = fields
        return super().__new__(mcs, name, bases, namespace)


class ObjectType(metaclass=ObjectTypeMeta):
    """Base class for GraphQL object types."""
    
    _fields: Dict[str, Field] = {}
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def get_fields(cls) -> Dict[str, Field]:
        """Get all fields defined on this type."""
        return cls._fields


class Interface:
    """Base class for GraphQL interfaces."""
    pass


# Query and Mutation base classes
class Query(ObjectType):
    """Base class for GraphQL queries."""
    pass


class Mutation(ObjectType):
    """Base class for GraphQL mutations."""
    pass


# ResolveInfo class
class ResolveInfo:
    """Information provided to field resolvers."""
    
    def __init__(
        self,
        field_name: str,
        parent_type: Type,
        return_type: Type,
        schema: 'Schema',
        context: Optional[Any] = None
    ):
        self.field_name = field_name
        self.parent_type = parent_type
        self.return_type = return_type
        self.schema = schema
        self.context = context


# Schema class
class Schema:
    """GraphQL schema definition."""
    
    def __init__(
        self,
        query: Optional[Type[Query]] = None,
        mutation: Optional[Type[Mutation]] = None,
        types: Optional[List[Type]] = None
    ):
        self.query = query
        self.mutation = mutation
        self.types = types or []
        self._type_map = {}
        
        # Build type map
        if query:
            self._type_map['Query'] = query
        if mutation:
            self._type_map['Mutation'] = mutation
        
        for type_ in self.types:
            if hasattr(type_, '__name__'):
                self._type_map[type_.__name__] = type_
    
    def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Any] = None,
        root: Optional[Any] = None,
        operation_name: Optional[str] = None
    ) -> 'ExecutionResult':
        """Execute a GraphQL query."""
        try:
            # Parse the query (simplified parsing)
            parsed = self._parse_query(query)
            
            # Determine operation type
            operation_type = parsed.get('operation', 'query')
            
            # Get the root type
            if operation_type == 'query':
                root_type = self.query
            elif operation_type == 'mutation':
                root_type = self.mutation
            else:
                raise GraphQLError(f"Unsupported operation type: {operation_type}")
            
            if not root_type:
                raise GraphQLError(f"Schema does not support {operation_type}")
            
            # Execute the operation
            result_data = self._execute_fields(
                root_type,
                parsed.get('fields', {}),
                root or {},
                context,
                variables or {}
            )
            
            return ExecutionResult(data=result_data, errors=[])
        
        except Exception as e:
            return ExecutionResult(data=None, errors=[str(e)])
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """Parse GraphQL query (simplified)."""
        query = query.strip()
        
        # Detect operation type
        operation = 'query'
        if query.startswith('mutation'):
            operation = 'mutation'
            query = query[8:].strip()
        elif query.startswith('query'):
            query = query[5:].strip()
        
        # Remove operation name if present
        if query.startswith('{'):
            query = query[1:-1].strip()
        else:
            # Has operation name
            brace_idx = query.find('{')
            if brace_idx > 0:
                query = query[brace_idx + 1:-1].strip()
        
        # Parse fields (simplified)
        fields = self._parse_fields(query)
        
        return {
            'operation': operation,
            'fields': fields
        }
    
    def _parse_fields(self, fields_str: str) -> Dict[str, Any]:
        """Parse field selections (simplified)."""
        fields = {}
        
        # Split by newlines and commas
        lines = [line.strip() for line in fields_str.replace(',', '\n').split('\n')]
        
        for line in lines:
            if not line or line.startswith('#'):
                continue
            
            # Check for arguments
            if '(' in line:
                field_name = line[:line.index('(')].strip()
                args_str = line[line.index('(') + 1:line.index(')')].strip()
                args = self._parse_arguments(args_str)
                fields[field_name] = {'args': args}
            else:
                field_name = line.strip()
                if field_name:
                    fields[field_name] = {}
        
        return fields
    
    def _parse_arguments(self, args_str: str) -> Dict[str, Any]:
        """Parse field arguments (simplified)."""
        args = {}
        
        # Split by commas
        for arg_pair in args_str.split(','):
            if ':' in arg_pair:
                key, value = arg_pair.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # Try to convert to appropriate type
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
                elif value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                
                args[key] = value
        
        return args
    
    def _execute_fields(
        self,
        parent_type: Type,
        field_selections: Dict[str, Any],
        root: Any,
        context: Any,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute field selections."""
        result = {}
        
        # Get fields from parent type
        if hasattr(parent_type, 'get_fields'):
            type_fields = parent_type.get_fields()
        else:
            type_fields = {}
        
        for field_name, field_data in field_selections.items():
            if field_name not in type_fields:
                # Try to get from root object directly
                if hasattr(root, field_name):
                    result[field_name] = getattr(root, field_name)
                continue
            
            field = type_fields[field_name]
            args = field_data.get('args', {})
            
            # Create ResolveInfo
            info = ResolveInfo(
                field_name=field_name,
                parent_type=parent_type,
                return_type=field.type,
                schema=self,
                context=context
            )
            info.field_name = field_name
            
            # Resolve field
            field_value = field.resolve(root, info, **args)
            
            # Handle List types
            if isinstance(field.type, List):
                if isinstance(field_value, list):
                    result[field_name] = field_value
                else:
                    result[field_name] = [field_value] if field_value is not None else []
            else:
                result[field_name] = field_value
        
        return result


class ExecutionResult:
    """Result of executing a GraphQL query."""
    
    def __init__(self, data: Optional[Dict[str, Any]], errors: List[str]):
        self.data = data
        self.errors = errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.data is not None:
            result['data'] = self.data
        if self.errors:
            result['errors'] = [{'message': e} for e in self.errors]
        return result


# Utility functions
def resolve_only_args(func: Callable) -> Callable:
    """Decorator to mark that a resolver only uses arguments."""
    func._resolve_only_args = True
    return func


# Export all public APIs
__all__ = [
    'Field',
    'Argument',
    'ObjectType',
    'Interface',
    'Query',
    'Mutation',
    'Schema',
    'String',
    'Int',
    'Float',
    'Boolean',
    'ID',
    'DateTime',
    'List',
    'NonNull',
    'ResolveInfo',
    'ExecutionResult',
    'GraphQLError',
    'ValidationError',
    'resolve_only_args',
]
