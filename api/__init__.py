"""API Layer for MyCMS.

This module provides a RESTful API framework with support for:
- RESTful endpoint routing
- JSON serialization
- API key and token authentication
- Permission-based access control
- Result pagination
- Automatic documentation generation
"""

from mycms.api.framework import APIRouter, APIEndpoint, APIView
from mycms.api.serializers import APISerializer, ModelSerializer
from mycms.api.authentication import APIKeyAuth, TokenAuth, require_api_auth
from mycms.api.permissions import APIPermission, require_api_permission
from mycms.api.pagination import Paginator, PageNumberPagination
from mycms.api.documentation import APIDocGenerator

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
