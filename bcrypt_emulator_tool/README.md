# bcrypt Emulator - Password Hashing Library

A Python implementation that emulates the core functionality of bcrypt, the industry-standard library for secure password hashing based on the Blowfish cipher.

## Overview

This emulator provides bcrypt-compatible password hashing using PBKDF2-HMAC-SHA256 as the underlying algorithm, maintaining the bcrypt API while being implementable without C extensions.

## Features

### Core Functionality
- **Password Hashing**: Secure password hashing with salt
- **Password Verification**: Constant-time password checking
- **Configurable Cost Factor**: Adjustable work factor (rounds 4-31)
- **Salt Generation**: Cryptographically random salt generation
- **Key Derivation**: KDF for deriving cryptographic keys
- **bcrypt Format**: Compatible bcrypt hash format ($2b$...)

### Security Features
- Constant-time comparison (timing attack resistant)
- Cryptographically secure random salts
- Exponential work factor (2^rounds iterations)
- Automatic UTF-8 encoding
- Protection against rainbow table attacks

## Usage

### Basic Password Hashing

```python
from bcrypt_emulator import hashpw, gensalt

# Hash a password
password = "my_secure_password"
salt = gensalt()
hashed = hashpw(password, salt)

print(hashed)
# b'$2b$12$salt22charsxxxxxxhash31charsxxxxxxxxxxxxxx'
```

### Password Verification

```python
from bcrypt_emulator import hashpw, checkpw, gensalt

# Hash a password
password = "my_secure_password"
salt = gensalt()
hashed = hashpw(password, salt)

# Verify correct password
if checkpw(password, hashed):
    print("Password correct!")

# Verify incorrect password
if not checkpw("wrong_password", hashed):
    print("Password incorrect!")
```

### Convenience Functions

```python
from bcrypt_emulator import hash_password, verify_password

# Hash a password (combines gensalt and hashpw)
password = "my_password"
hashed = hash_password(password)  # Returns string

# Verify password (convenience wrapper)
if verify_password(password, hashed):
    print("Password correct!")
```

### Custom Cost Factor (Rounds)

```python
from bcrypt_emulator import gensalt, hashpw

# Higher rounds = more secure but slower
# Default is 12, recommended range is 10-14 for most applications

# Fast (development/testing)
salt_fast = gensalt(rounds=8)

# Standard (default)
salt_standard = gensalt(rounds=12)

# High security
salt_secure = gensalt(rounds=14)

password = "my_password"
hashed = hashpw(password, salt_secure)
```

### Key Derivation Function

```python
from bcrypt_emulator import kdf

# Derive a cryptographic key from a password
password = "my_password"
salt = b"random_salt_data"  # 16+ bytes recommended
desired_length = 32  # 256-bit key

key = kdf(password, salt, desired_key_bytes=desired_length, rounds=12)

# Use key for encryption, HMAC, etc.
```

### Complete Authentication Example

```python
from bcrypt_emulator import hash_password, verify_password

class UserAuth:
    def __init__(self):
        self.users = {}
    
    def register(self, username, password):
        """Register a new user"""
        if username in self.users:
            raise ValueError("User already exists")
        
        # Hash the password
        hashed = hash_password(password, rounds=12)
        self.users[username] = hashed
        print(f"User {username} registered successfully")
    
    def login(self, username, password):
        """Authenticate a user"""
        if username not in self.users:
            return False
        
        # Verify password
        hashed = self.users[username]
        return verify_password(password, hashed)

# Usage
auth = UserAuth()
auth.register("john_doe", "SecurePassword123!")

if auth.login("john_doe", "SecurePassword123!"):
    print("Login successful!")
else:
    print("Invalid credentials")
```

### Bytes vs Strings

```python
from bcrypt_emulator import hashpw, checkpw, gensalt

# Works with strings (automatically converted to UTF-8)
password_str = "my_password"
salt = gensalt()
hashed = hashpw(password_str, salt)

# Also works with bytes
password_bytes = b"my_password"
hashed = hashpw(password_bytes, salt)

# Verification works with both
checkpw("my_password", hashed)  # True
checkpw(b"my_password", hashed)  # True
```

## Hash Format

bcrypt hashes follow this format:

```
$2b$12$saltxxxxxxxxxxxxxx (22 chars) hashxxxxxxxxxxxxxxxxxxxxxxx (31 chars)
│  │  │                            │
│  │  │                            └─ Hash (31 bcrypt-base64 chars)
│  │  └─ Salt (22 bcrypt-base64 chars)
│  └─ Cost factor (04-31)
└─ Version identifier ($2b$ = bcrypt version 2b)
```

Example:
```
$2b$12$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
```

## Cost Factor Selection

The cost factor (rounds) determines how many iterations are performed. Higher is more secure but slower:

| Rounds | Iterations | Time (approx) | Use Case |
|--------|-----------|---------------|-----------|
| 4      | 16        | < 10ms       | Testing only |
| 8      | 256       | < 50ms       | Development |
| 10     | 1,024     | 100ms        | Low security |
| 12     | 4,096     | 350ms        | Standard (default) |
| 14     | 16,384    | 1.5s         | High security |
| 16     | 65,536    | 6s           | Very high security |

**Recommendation**: Use 12 for most applications. Adjust based on your security requirements and acceptable login times.

```python
from bcrypt_emulator import gensalt, hashpw

# For production
salt = gensalt(rounds=12)  # ~350ms per hash

# For high-security applications (slower logins acceptable)
salt = gensalt(rounds=14)  # ~1.5s per hash
```

## Security Considerations

### Why bcrypt?

bcrypt is designed to be:
1. **Slow**: Intentionally slow to prevent brute-force attacks
2. **Adaptive**: Cost factor can be increased over time as hardware improves
3. **Salted**: Each password has a unique salt to prevent rainbow table attacks
4. **One-way**: Impossible to reverse the hash to get the original password

### Best Practices

1. **Never store plain passwords**: Always hash before storing
2. **Use appropriate cost factor**: Balance security and performance (12-14 recommended)
3. **Don't truncate passwords**: bcrypt handles long passwords safely
4. **Use constant-time comparison**: Built into `checkpw()` to prevent timing attacks
5. **Update cost factor over time**: As hardware improves, increase rounds
6. **Use strong passwords**: bcrypt doesn't make weak passwords strong

### Migration from Plain Passwords

```python
from bcrypt_emulator import hash_password

def migrate_user_password(user_id, plain_password):
    """Migrate from plain text to bcrypt"""
    hashed = hash_password(plain_password)
    
    # Update database
    update_user_password(user_id, hashed)
    
    # Recommend user changes password at next login
    flag_password_change_required(user_id)
```

### Updating Cost Factor

```python
from bcrypt_emulator import hash_password, verify_password

def check_and_rehash(user, password):
    """Check password and rehash if using old cost factor"""
    current_hash = user.password_hash
    
    # Verify password
    if not verify_password(password, current_hash):
        return False
    
    # Check if hash uses old cost factor
    parts = current_hash.split('$')
    current_rounds = int(parts[2])
    
    if current_rounds < 12:
        # Rehash with current standard
        new_hash = hash_password(password, rounds=12)
        user.password_hash = new_hash
        user.save()
    
    return True
```

## Implementation Notes

### Simulated vs. Real Implementation

This is an **emulator** designed for:
- Learning bcrypt concepts and implementation
- Testing password hashing without C extensions
- Understanding password security
- Prototyping authentication systems
- Environments where bcrypt C library unavailable

**Key differences from real bcrypt**:
1. **Algorithm**: Uses PBKDF2-HMAC-SHA256 instead of EKSBlowfish
2. **Performance**: May be slower or faster depending on platform
3. **Hash Values**: Produces different hashes than real bcrypt (same password + salt)
4. **Compatibility**: Hash format is compatible, but hash values are not

**For production use**: Use the real bcrypt library with C extensions for better performance and proven security.

### When to Use This Emulator

✅ **Good for**:
- Development and testing
- Learning about password hashing
- Python-only environments
- Prototyping
- Academic purposes

❌ **Not recommended for**:
- Production systems (use real bcrypt)
- High-traffic applications
- Hashes that need to be compatible with other systems
- Security-critical applications

## Testing

Run the test suite:

```bash
cd bcrypt_emulator_tool
python -m pytest test_bcrypt_emulator.py -v
```

Or using unittest:

```bash
python test_bcrypt_emulator.py
```

Test coverage includes:
- Salt generation and uniqueness
- Password hashing with various inputs
- Password verification (correct and incorrect)
- Different cost factors
- Key derivation function
- Convenience functions
- Special characters and Unicode
- Security properties (timing attacks, randomness)
- Edge cases (empty passwords, long passwords, etc.)

## Compatibility

- Python 3.6+
- No external dependencies (uses only standard library)
- Cross-platform (Windows, macOS, Linux)

## Common Patterns

### Registration Flow

```python
from bcrypt_emulator import hash_password

def register_user(username, email, password):
    # Validate password strength first
    if len(password) < 8:
        raise ValueError("Password too short")
    
    # Hash password
    hashed = hash_password(password, rounds=12)
    
    # Store in database
    user = User(
        username=username,
        email=email,
        password_hash=hashed
    )
    user.save()
    
    return user
```

### Login Flow

```python
from bcrypt_emulator import verify_password

def login_user(username, password):
    # Fetch user from database
    user = User.get(username=username)
    if not user:
        return None
    
    # Verify password
    if not verify_password(password, user.password_hash):
        return None
    
    return user
```

### Password Reset

```python
from bcrypt_emulator import hash_password

def reset_password(user_id, new_password):
    # Validate new password
    if len(new_password) < 8:
        raise ValueError("Password too short")
    
    # Hash new password
    hashed = hash_password(new_password)
    
    # Update user
    user = User.get(id=user_id)
    user.password_hash = hashed
    user.save()
```

## Performance Tips

1. **Don't hash on every request**: Cache authentication results in sessions
2. **Choose appropriate rounds**: Balance security and UX (12 is good default)
3. **Hash asynchronously**: Don't block main thread during registration/login
4. **Monitor hash time**: Increase rounds if hashes complete too quickly
5. **Consider rate limiting**: Prevent brute-force attempts at the application level

## Comparison with Other Hashing Methods

| Method | Security | Speed | Recommended |
|--------|----------|-------|-------------|
| MD5 | ❌ Broken | Very Fast | Never |
| SHA-256 | ⚠️ Too fast | Fast | No |
| PBKDF2 | ✅ Good | Medium | Yes |
| bcrypt | ✅ Excellent | Slow (good) | Yes ✓ |
| scrypt | ✅ Excellent | Slow | Yes |
| Argon2 | ✅ Best | Adjustable | Yes (modern) |

bcrypt remains one of the best choices for password hashing due to its proven track record and wide support.

## References

- [bcrypt Wikipedia](https://en.wikipedia.org/wiki/Bcrypt)
- [bcrypt Python Library](https://github.com/pyca/bcrypt)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

## License

This is an original implementation created for educational and development purposes. It emulates the API of bcrypt but contains no code from the original project.
