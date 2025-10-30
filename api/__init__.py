"""API Layer.

This module provides a RESTful API framework with support for:
- RESTful endpoint routing
- JSON serialization
- API key and token authentication
- Permission-based access control
- Result pagination
- Automatic documentation generation
"""

from api.framework import APIRouter, APIEndpoint, APIView
from api.serializers import APISerializer, ModelSerializer
from api.authentication import APIKeyAuth, TokenAuth, require_api_auth
from api.permissions import APIPermission, require_api_permission
from api.pagination import Paginator, PageNumberPagination
from api.documentation import APIDocGenerator

__all__ = [
    "APIRouter",
    "APIEndpoint",
    "APIView",
    "APISerializer",
    "ModelSerializer",
    "APIKeyAuth",
    "TokenAuth",
    "require_api_auth",
    "APIPermission",
    "require_api_permission",
    "Paginator",
    "PageNumberPagination",
    "APIDocGenerator",
]
