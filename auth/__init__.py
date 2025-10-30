"""Authentication and authorization system for MyCMS."""

from auth.models import User, Role, Permission
from auth.authentication import authenticate, login, logout
from auth.authorization import has_permission, require_permission
from auth.password import hash_password, verify_password
from auth.session import SessionManager
from auth.middleware import AuthMiddleware
from auth.tokens import JWTTokenManager, create_token_pair
from auth.two_factor import (
    TOTPGenerator,
    TwoFactorAuthManager,
    get_twofa_manager,
)

__all__ = [
    "User",
    "Role",
    "Permission",
    "authenticate",
    "login",
    "logout",
    "has_permission",
    "require_permission",
    "hash_password",
    "verify_password",
    "SessionManager",
    "AuthMiddleware",
    "JWTTokenManager",
    "create_token_pair",
    "TOTPGenerator",
    "TwoFactorAuthManager",
    "get_twofa_manager",
]
