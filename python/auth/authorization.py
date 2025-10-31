"""Authorization and permission checking."""

from typing import Callable, Optional
from functools import wraps
from auth.models import User, Permission


async def has_permission(user: User, permission_codename: str) -> bool:
    """Check if a user has a specific permission.

    Args:
        user: User instance
        permission_codename: Permission codename to check

    Returns:
        True if user has permission, False otherwise
    """
    return await user.has_permission(permission_codename)


async def has_role(user: User, role_name: str) -> bool:
    """Check if a user has a specific role.

    Args:
        user: User instance
        role_name: Role name to check

    Returns:
        True if user has role, False otherwise
    """
    roles = await user.get_roles()
    return any(role.name == role_name for role in roles)


def require_permission(permission_codename: str) -> Callable:
    """Decorator to require a specific permission for a view.

    Args:
        permission_codename: Permission codename required

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs or args
            user = kwargs.get("user")
            if not user:
                # Try to get from request if present
                request = kwargs.get("request")
                if request and hasattr(request, "user"):
                    user = request.user

            if not user:
                from framework.response import Response

                return Response({"error": "Authentication required"}, status_code=401)

            if not await has_permission(user, permission_codename):
                from framework.response import Response

                return Response({"error": "Permission denied"}, status_code=403)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role_name: str) -> Callable:
    """Decorator to require a specific role for a view.

    Args:
        role_name: Role name required

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs or args
            user = kwargs.get("user")
            if not user:
                # Try to get from request if present
                request = kwargs.get("request")
                if request and hasattr(request, "user"):
                    user = request.user

            if not user:
                from framework.response import Response

                return Response({"error": "Authentication required"}, status_code=401)

            if not await has_role(user, role_name):
                from framework.response import Response

                return Response({"error": "Role required: " + role_name}, status_code=403)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_staff() -> Callable:
    """Decorator to require staff status for a view.

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs or args
            user = kwargs.get("user")
            if not user:
                # Try to get from request if present
                request = kwargs.get("request")
                if request and hasattr(request, "user"):
                    user = request.user

            if not user:
                from framework.response import Response

                return Response({"error": "Authentication required"}, status_code=401)

            if not user.is_staff:
                from framework.response import Response

                return Response({"error": "Staff access required"}, status_code=403)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_superuser() -> Callable:
    """Decorator to require superuser status for a view.

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs or args
            user = kwargs.get("user")
            if not user:
                # Try to get from request if present
                request = kwargs.get("request")
                if request and hasattr(request, "user"):
                    user = request.user

            if not user:
                from framework.response import Response

                return Response({"error": "Authentication required"}, status_code=401)

            if not user.is_superuser:
                from framework.response import Response

                return Response({"error": "Superuser access required"}, status_code=403)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def create_permission(
    name: str, codename: str, description: Optional[str] = None
) -> Permission:
    """Create a new permission.

    Args:
        name: Human-readable permission name
        codename: Unique permission codename
        description: Optional description

    Returns:
        Created Permission instance
    """
    permission = Permission(name=name, codename=codename, description=description)
    await permission.save()
    return permission
