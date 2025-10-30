"""Authentication and authorization system for MyCMS."""

from mycms.auth.models import User, Role, Permission
from mycms.auth.authentication import authenticate, login, logout
from mycms.auth.authorization import has_permission, require_permission
from mycms.auth.password import hash_password, verify_password
from mycms.auth.session import SessionManager
from mycms.auth.middleware import AuthMiddleware
from mycms.auth.tokens import JWTTokenManager, create_token_pair
from mycms.auth.two_factor import (
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
