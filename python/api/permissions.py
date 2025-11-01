"""
Developed by PowerShield, as an alternative to Django REST Framework
"""

"""API permission checking and access control."""

from typing import Callable, Optional
from functools import wraps
from framework.request import Request
from framework.response import Response, JSONResponse
from auth.models import User


class APIPermission:
    """Base class for API permissions."""

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        """Check if request has permission.

        Args:
            request: Request object
            user: User object (if authenticated)

        Returns:
            True if permitted, False otherwise
        """
        return True

    def get_error_message(self) -> str:
        """Get error message for permission denial.

        Returns:
            Error message
        """
        return "Permission denied"


class IsAuthenticated(APIPermission):
    """Permission that requires authentication."""

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        """Check if user is authenticated.

        Args:
            request: Request object
            user: User object

        Returns:
            True if authenticated
        """
        return user is not None and hasattr(request, "user")

    def get_error_message(self) -> str:
        """Get error message."""
        return "Authentication required"


class IsStaff(APIPermission):
    """Permission that requires staff status."""

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        """Check if user is staff.

        Args:
            request: Request object
            user: User object

        Returns:
            True if staff
        """
        return user is not None and bool(user.is_staff)

    def get_error_message(self) -> str:
        """Get error message."""
        return "Staff access required"


class IsSuperuser(APIPermission):
    """Permission that requires superuser status."""

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        """Check if user is superuser.

        Args:
            request: Request object
            user: User object

        Returns:
            True if superuser
        """
        return user is not None and bool(user.is_superuser)

    def get_error_message(self) -> str:
        """Get error message."""
        return "Superuser access required"


class HasPermission(APIPermission):
    """Permission that requires specific permission."""

    def __init__(self, permission_codename: str) -> None:
        """Initialize permission checker.

        Args:
            permission_codename: Required permission codename
        """
        self.permission_codename = permission_codename

    async def has_permission_async(self, request: Request, user: Optional[User] = None) -> bool:
        """Async check for permission.

        Args:
            request: Request object
            user: User object

        Returns:
            True if has permission
        """
        if not user:
            return False
        return await user.has_permission(self.permission_codename)

    def get_error_message(self) -> str:
        """Get error message."""
        return f"Permission '{self.permission_codename}' required"


class IsReadOnly(APIPermission):
    """Permission that allows only safe methods (GET, HEAD, OPTIONS)."""

    SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        """Check if method is read-only.

        Args:
            request: Request object
            user: User object

        Returns:
            True if safe method
        """
        return request.method.upper() in self.SAFE_METHODS

    def get_error_message(self) -> str:
        """Get error message."""
        return "Read-only access"


def require_api_permission(
    *permissions: APIPermission,
) -> Callable:
    """Decorator to require API permissions for an endpoint.

    Args:
        *permissions: One or more APIPermission instances

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
            # Get user from request if available
            user = getattr(request, "user", None)

            # Check all permissions
            for permission in permissions:
                # Check async permissions
                if hasattr(permission, "has_permission_async"):
                    has_perm = await permission.has_permission_async(request, user)
                else:
                    has_perm = permission.has_permission(request, user)

                if not has_perm:
                    return JSONResponse(
                        {"error": permission.get_error_message()},
                        status_code=403,
                    )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_authenticated() -> Callable:
    """Decorator to require authentication.

    Returns:
        Decorator function
    """
    return require_api_permission(IsAuthenticated())


def require_staff() -> Callable:
    """Decorator to require staff access.

    Returns:
        Decorator function
    """
    return require_api_permission(IsAuthenticated(), IsStaff())


def require_superuser() -> Callable:
    """Decorator to require superuser access.

    Returns:
        Decorator function
    """
    return require_api_permission(IsAuthenticated(), IsSuperuser())


def require_permission(permission_codename: str) -> Callable:
    """Decorator to require a specific permission.

    Args:
        permission_codename: Permission codename

    Returns:
        Decorator function
    """
    return require_api_permission(IsAuthenticated(), HasPermission(permission_codename))


def require_read_only() -> Callable:
    """Decorator to allow only read-only access.

    Returns:
        Decorator function
    """
    return require_api_permission(IsReadOnly())


class PermissionChecker:
    """Helper class for checking multiple permissions."""

    def __init__(self, *permissions: APIPermission) -> None:
        """Initialize with permissions to check.

        Args:
            *permissions: Permission instances
        """
        self.permissions = permissions

    async def check(self, request: Request, user: Optional[User] = None) -> bool:
        """Check all permissions.

        Args:
            request: Request object
            user: User object

        Returns:
            True if all permissions pass
        """
        for permission in self.permissions:
            if hasattr(permission, "has_permission_async"):
                if not await permission.has_permission_async(request, user):
                    return False
            elif not permission.has_permission(request, user):
                return False
        return True

    async def check_and_raise(self, request: Request, user: Optional[User] = None) -> None:
        """Check permissions and raise error if denied.

        Args:
            request: Request object
            user: User object

        Raises:
            PermissionError: If permission denied
        """
        for permission in self.permissions:
            if hasattr(permission, "has_permission_async"):
                if not await permission.has_permission_async(request, user):
                    raise PermissionError(permission.get_error_message())
            elif not permission.has_permission(request, user):
                raise PermissionError(permission.get_error_message())
