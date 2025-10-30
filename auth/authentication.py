"""Authentication logic for login and logout."""

from typing import Optional
from datetime import datetime
from mycms.auth.models import User
from mycms.auth.session import Session, SessionManager


async def authenticate(username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password.

    Args:
        username: Username or email
        password: Plain text password

    Returns:
        User instance if authentication successful, None otherwise
    """
    # Try to find user by username
    user = await User.get(username=username)

    # If not found by username, try email
    if not user:
        user = await User.get(email=username)

    # Verify user exists, is active, and password is correct
    if user and user.is_active and user.check_password(password):
        return user

    return None


async def login(
    user: User, session_manager: SessionManager, request: Optional[object] = None
) -> Session:
    """Log in a user and create a session.

    Args:
        user: User instance to log in
        session_manager: SessionManager instance
        request: Optional request object to store additional context

    Returns:
        Session instance
    """
    # Create session
    session = await session_manager.create_session(user_id=user.id)

    # Store user info in session
    session.set("user_id", user.id)
    session.set("username", user.username)
    session.set("is_authenticated", True)

    # Update last login time
    user.last_login = datetime.utcnow()
    await user.save()

    return session


async def logout(session: Session, session_manager: SessionManager) -> None:
    """Log out a user and destroy the session.

    Args:
        session: Session instance to destroy
        session_manager: SessionManager instance
    """
    # Clear session data
    session.clear()

    # Delete session
    await session_manager.delete_session(session.session_id)


async def get_current_user(session: Session) -> Optional[User]:
    """Get the currently authenticated user from session.

    Args:
        session: Current session

    Returns:
        User instance if authenticated, None otherwise
    """
    if not session or not session.get("is_authenticated"):
        return None

    user_id = session.get("user_id")
    if not user_id:
        return None

    user = await User.get(id=user_id)
    return user if user and user.is_active else None


async def change_password(user: User, old_password: str, new_password: str) -> tuple[bool, str]:
    """Change user password.

    Args:
        user: User instance
        old_password: Current password
        new_password: New password

    Returns:
        Tuple of (success, message)
    """
    from mycms.auth.password import validate_password_strength

    # Verify old password
    if not user.check_password(old_password):
        return False, "Current password is incorrect"

    # Validate new password strength
    is_valid, error = validate_password_strength(new_password)
    if not is_valid:
        return False, error

    # Set new password and save
    user.set_password(new_password)
    await user.save()

    return True, "Password changed successfully"


async def reset_password(user: User, new_password: str) -> tuple[bool, str]:
    """Reset user password (admin function).

    Args:
        user: User instance
        new_password: New password

    Returns:
        Tuple of (success, message)
    """
    from mycms.auth.password import validate_password_strength

    # Validate new password strength
    is_valid, error = validate_password_strength(new_password)
    if not is_valid:
        return False, error

    # Set new password and save
    user.set_password(new_password)
    await user.save()

    return True, "Password reset successfully"
