"""
Developed by PowerShield, as an alternative to Django Security
"""

"""Input sanitization utilities to prevent security vulnerabilities."""

import re
import html
from typing import Any, List
from pathlib import Path


def sanitize_html(input_text: str, allowed_tags: List[str] = None) -> str:
    """Sanitize HTML input to prevent XSS attacks.

    Args:
        input_text: HTML string to sanitize
        allowed_tags: List of allowed HTML tags (if None, all tags removed)

    Returns:
        Sanitized HTML string
    """
    if not input_text:
        return ""

    # If no allowed tags, escape all HTML
    if allowed_tags is None:
        return html.escape(input_text)

    # Basic implementation - escape everything except allowed tags
    # Note: For production, consider using a library like bleach
    sanitized = html.escape(input_text)

    # Unescape allowed tags
    for tag in allowed_tags:
        # Unescape opening tags
        sanitized = sanitized.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        sanitized = sanitized.replace(f"&lt;{tag} ", f"<{tag} ")

        # Unescape closing tags
        sanitized = sanitized.replace(f"&lt;/{tag}&gt;", f"</{tag}>")

    return sanitized


def sanitize_sql(input_value: Any) -> str:
    """Sanitize input to prevent SQL injection.

    Note: This is a basic sanitizer. Always use parameterized queries
    instead of string concatenation.

    Args:
        input_value: Value to sanitize

    Returns:
        Sanitized string safe for SQL
    """
    if input_value is None:
        return "NULL"

    if isinstance(input_value, (int, float)):
        return str(input_value)

    if isinstance(input_value, bool):
        return "TRUE" if input_value else "FALSE"

    # Convert to string and escape single quotes
    str_value = str(input_value)

    # Escape single quotes by doubling them
    str_value = str_value.replace("'", "''")

    # Remove null bytes
    str_value = str_value.replace("\x00", "")

    # Remove common SQL injection patterns (case-insensitive)
    dangerous_patterns = [
        (r"--", ""),  # SQL comment
        (r";", ""),  # Statement separator
        (r"\/\*", ""),  # Block comment start
        (r"\*\/", ""),  # Block comment end
        (r"\bxp_\w+", ""),  # Extended stored procedures
        (r"\bsp_\w+", ""),  # System stored procedures
        (r"\bDROP\s+TABLE\b", ""),  # DROP TABLE
        (r"\bDROP\s+DATABASE\b", ""),  # DROP DATABASE
        (r"\bDELETE\s+FROM\b", ""),  # DELETE FROM
        (r"\bTRUNCATE\b", ""),  # TRUNCATE
    ]

    for pattern, replacement in dangerous_patterns:
        str_value = re.sub(pattern, replacement, str_value, flags=re.IGNORECASE)

    return f"'{str_value}'"


def sanitize_path(input_path: str, base_path: str = None) -> str:
    """Sanitize file path to prevent path traversal attacks.

    Args:
        input_path: Path to sanitize
        base_path: Optional base path to restrict access to

    Returns:
        Sanitized path

    Raises:
        ValueError: If path is invalid or contains traversal attempts
    """
    if not input_path:
        raise ValueError("Path cannot be empty")

    # Remove null bytes
    input_path = input_path.replace("\x00", "")

    # Convert to Path object for normalization
    try:
        path = Path(input_path).resolve()
    except (ValueError, OSError) as e:
        raise ValueError(f"Invalid path: {e}")

    # Check for path traversal attempts
    if ".." in input_path or input_path.startswith("/"):
        raise ValueError("Path traversal detected")

    # If base path provided, ensure path is within it
    if base_path:
        base = Path(base_path).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            raise ValueError("Path outside of allowed directory")

    return str(path)


def sanitize_command(command: str, allowed_commands: List[str] = None) -> str:
    """Sanitize shell command to prevent command injection.

    Note: Avoid executing shell commands when possible. Use subprocess
    with shell=False and explicit argument lists instead.

    Args:
        command: Command to sanitize
        allowed_commands: List of allowed command names

    Returns:
        Sanitized command

    Raises:
        ValueError: If command contains dangerous patterns
    """
    if not command:
        raise ValueError("Command cannot be empty")

    # Remove null bytes
    command = command.replace("\x00", "")

    # Get the base command (first word)
    base_command = command.split()[0] if command.split() else ""

    # Check against allowed commands if provided
    if allowed_commands and base_command not in allowed_commands:
        raise ValueError(f"Command not allowed: {base_command}")

    # Check for dangerous shell metacharacters
    dangerous_chars = [
        ";",  # Command separator
        "&",  # Background execution / AND
        "|",  # Pipe
        "$",  # Variable expansion
        "`",  # Command substitution
        "(",  # Subshell
        ")",  # Subshell
        "<",  # Input redirection
        ">",  # Output redirection
        "\n",  # Newline
        "\r",  # Carriage return
    ]

    for char in dangerous_chars:
        if char in command:
            raise ValueError(f"Dangerous character detected: {char}")

    # Check for command substitution patterns
    if "$(" in command or "${" in command:
        raise ValueError("Command substitution detected")

    return command


def sanitize_email(email: str) -> str:
    """Sanitize and validate email address.

    Args:
        email: Email address to sanitize

    Returns:
        Sanitized email address

    Raises:
        ValueError: If email format is invalid
    """
    if not email:
        raise ValueError("Email cannot be empty")

    # Remove whitespace
    email = email.strip()

    # Basic email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        raise ValueError("Invalid email format")

    # Convert to lowercase
    email = email.lower()

    return email


def sanitize_username(username: str, min_length: int = 3, max_length: int = 30) -> str:
    """Sanitize and validate username.

    Args:
        username: Username to sanitize
        min_length: Minimum username length
        max_length: Maximum username length

    Returns:
        Sanitized username

    Raises:
        ValueError: If username is invalid
    """
    if not username:
        raise ValueError("Username cannot be empty")

    # Remove whitespace
    username = username.strip()

    # Check length
    if len(username) < min_length:
        raise ValueError(f"Username must be at least {min_length} characters")

    if len(username) > max_length:
        raise ValueError(f"Username must be at most {max_length} characters")

    # Only allow alphanumeric and underscore
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValueError("Username can only contain letters, numbers, and underscores")

    return username


def sanitize_url(url: str, allowed_schemes: List[str] = None) -> str:
    """Sanitize and validate URL.

    Args:
        url: URL to sanitize
        allowed_schemes: List of allowed URL schemes (default: http, https)

    Returns:
        Sanitized URL

    Raises:
        ValueError: If URL is invalid or uses disallowed scheme
    """
    if not url:
        raise ValueError("URL cannot be empty")

    # Remove whitespace
    url = url.strip()

    # Default allowed schemes
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    # Basic URL pattern
    pattern = r"^([a-zA-Z][a-zA-Z0-9+.-]*):\/\/"

    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid URL format")

    scheme = match.group(1).lower()
    if scheme not in allowed_schemes:
        raise ValueError(f"URL scheme not allowed: {scheme}")

    # Check for dangerous patterns
    if "javascript:" in url.lower() or "data:" in url.lower():
        raise ValueError("Potentially dangerous URL scheme")

    return url
