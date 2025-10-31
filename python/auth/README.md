# Authentication System

Complete authentication and authorization system without external dependencies.

## What This Emulates

**Emulates:** Django Auth, django-allauth, Authlib, PassLib, JWT libraries
**Purpose:** Secure user management and access control

## Features

- User authentication with username/password
- Password hashing using bcrypt
- Session management
- JWT token generation and validation
- Role-based access control (RBAC)
- Two-factor authentication (TOTP)
- API key authentication
- Brute force protection

## Components

### Core Authentication
- **authentication.py** - Login/logout logic
  - User credential validation
  - Session creation
  - Authentication flow

### Authorization & Permissions
- **authorization.py** - Permission checking
  - Role-based access control (RBAC)
  - Permission validation
  - Access control decorators

### User Models
- **models.py** - User, Role, Permission models
  - User data structures
  - Role definitions
  - Permission associations

### Session Management
- **session.py** - Session handling
  - Session creation and validation
  - Session storage (in-memory or persistent)
  - Session timeout and cleanup

### Password Security
- **password.py** - Password hashing and validation
  - Bcrypt-based hashing
  - Password strength validation
  - Secure storage practices

### Token Management
- **tokens.py** - JWT token handling
  - Token generation with claims
  - Token validation and verification
  - Token refresh mechanism
  - Expiration handling

### Two-Factor Authentication
- **two_factor.py** - 2FA implementation
  - TOTP (Time-based One-Time Password)
  - QR code generation for authenticator apps
  - Backup codes generation
  - 2FA verification

### Middleware
- **middleware.py** - Authentication middleware
  - Request authentication
  - User context injection
  - Protected route handling
  - Session validation

## Usage Examples

### User Authentication
```python
from auth.authentication import authenticate, login, logout
from auth.session import SessionManager

# Authenticate user
user = await authenticate(username="john", password="secret")
if user:
    session = await login(request, user)
    print(f"User {user.username} logged in")
```

### Permission Checking
```python
from auth.authorization import require_permission

@require_permission("posts.create")
async def create_post(request):
    # Only users with posts.create permission can access
    pass
```

### JWT Tokens
```python
from auth.tokens import JWTTokenManager

token_manager = JWTTokenManager(secret_key="your-secret")
token = token_manager.generate_token(user_id=123, claims={"role": "admin"})
payload = token_manager.validate_token(token)
```

### Two-Factor Authentication
```python
from auth.two_factor import TwoFactorAuth

tfa = TwoFactorAuth()
secret = tfa.generate_secret()
qr_code = tfa.generate_qr_code(secret, "user@example.com")

# Verify code
is_valid = tfa.verify_code(secret, user_input_code)
```

## Security Features

- **Password Hashing**: Bcrypt with configurable rounds
- **Session Security**: Secure session tokens, timeout handling
- **JWT Security**: Signed tokens with expiration
- **2FA**: TOTP-based second factor
- **Brute Force Protection**: Login attempt limiting
- **API Key Auth**: Secure API authentication

## Integration

Works seamlessly with:
- Web framework (framework/ module)
- API framework (api/ module)
- Admin interface (admin/ module)
- Database layer (database/ module)

## Why This Was Created

Part of the CIV-ARCOS project to provide military-grade authentication and authorization without external dependencies, ensuring security and self-containment.
