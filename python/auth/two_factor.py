"""
Developed by PowerShield, as an alternative to Django Auth
"""

"""Two-Factor Authentication (2FA) system for enhanced security.

This module implements TOTP-based two-factor authentication without external
framework dependencies, following the homegrown philosophy.
"""

import hashlib
import hmac
import secrets
import struct
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone


class TOTPGenerator:
    """Time-based One-Time Password (TOTP) generator.

    Implements RFC 6238 TOTP algorithm without external dependencies.
    """

    def __init__(self, secret: str, time_step: int = 30, digits: int = 6) -> None:
        """Initialize TOTP generator.

        Args:
            secret: Base32-encoded secret key
            time_step: Time step in seconds (default: 30)
            digits: Number of digits in OTP (default: 6)
        """
        self.secret = secret
        self.time_step = time_step
        self.digits = digits

    def _base32_decode(self, encoded: str) -> bytes:
        """Decode base32 string to bytes.

        Args:
            encoded: Base32-encoded string

        Returns:
            Decoded bytes
        """
        # Remove padding and convert to uppercase
        encoded = encoded.upper().rstrip("=")

        # Base32 alphabet
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

        # Convert to binary string
        binary = ""
        for char in encoded:
            if char not in alphabet:
                raise ValueError(f"Invalid base32 character: {char}")
            binary += format(alphabet.index(char), "05b")

        # Convert binary to bytes
        result = bytearray()
        for i in range(0, len(binary) - 7, 8):
            result.append(int(binary[i : i + 8], 2))

        return bytes(result)

    def _hotp(self, counter: int) -> int:
        """Generate HMAC-based One-Time Password.

        Args:
            counter: Counter value

        Returns:
            OTP as integer
        """
        # Decode secret from base32
        key = self._base32_decode(self.secret)

        # Convert counter to 8-byte big-endian
        counter_bytes = struct.pack(">Q", counter)

        # Calculate HMAC-SHA1
        hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()

        # Dynamic truncation (RFC 4226)
        offset = hmac_hash[-1] & 0x0F
        truncated = struct.unpack(">I", hmac_hash[offset : offset + 4])[0]
        truncated &= 0x7FFFFFFF

        # Generate OTP
        otp = truncated % (10**self.digits)
        return otp

    def generate(self, timestamp: Optional[int] = None) -> str:
        """Generate TOTP code.

        Args:
            timestamp: Unix timestamp (default: current time)

        Returns:
            OTP code as string
        """
        if timestamp is None:
            timestamp = int(time.time())

        counter = timestamp // self.time_step
        otp = self._hotp(counter)

        # Zero-pad to correct length
        return str(otp).zfill(self.digits)

    def verify(self, code: str, timestamp: Optional[int] = None, window: int = 1) -> bool:
        """Verify TOTP code.

        Args:
            code: OTP code to verify
            timestamp: Unix timestamp (default: current time)
            window: Number of time steps to check before and after (default: 1)

        Returns:
            True if code is valid, False otherwise
        """
        if timestamp is None:
            timestamp = int(time.time())

        # Check current and adjacent time windows
        for i in range(-window, window + 1):
            check_time = timestamp + (i * self.time_step)
            if self.generate(check_time) == code:
                return True

        return False


class BackupCodeGenerator:
    """Generator for backup recovery codes."""

    @staticmethod
    def generate_codes(count: int = 10, length: int = 8) -> List[str]:
        """Generate backup recovery codes.

        Args:
            count: Number of codes to generate
            length: Length of each code

        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate random alphanumeric code
            code = secrets.token_hex(length // 2).upper()
            codes.append(code)
        return codes

    @staticmethod
    def hash_code(code: str) -> str:
        """Hash a backup code for secure storage.

        Args:
            code: Backup code to hash

        Returns:
            Hashed code
        """
        return hashlib.sha256(code.encode()).hexdigest()

    @staticmethod
    def verify_code(code: str, hashed_code: str) -> bool:
        """Verify a backup code against its hash.

        Args:
            code: Code to verify
            hashed_code: Stored hash

        Returns:
            True if code matches, False otherwise
        """
        return BackupCodeGenerator.hash_code(code) == hashed_code


@dataclass
class TwoFactorAuth:
    """Two-Factor Authentication configuration for a user."""

    user_id: int
    secret: str
    enabled: bool = False
    backup_codes: List[str] = None  # Stored as hashed values
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.backup_codes is None:
            self.backup_codes = []


class TwoFactorAuthManager:
    """Manager for Two-Factor Authentication operations."""

    def __init__(self) -> None:
        """Initialize 2FA manager."""
        self._configs = {}  # In-memory storage: user_id -> TwoFactorAuth

    def generate_secret(self) -> str:
        """Generate a new TOTP secret key.

        Returns:
            Base32-encoded secret
        """
        # Generate 160-bit (20 byte) secret
        random_bytes = secrets.token_bytes(20)

        # Base32 encode
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
        binary = "".join(format(byte, "08b") for byte in random_bytes)

        # Pad to multiple of 5
        padding = (5 - len(binary) % 5) % 5
        binary += "0" * padding

        # Convert to base32
        result = ""
        for i in range(0, len(binary), 5):
            chunk = binary[i : i + 5]
            result += alphabet[int(chunk, 2)]

        return result

    def setup_2fa(self, user_id: int) -> Tuple[str, str]:
        """Set up 2FA for a user.

        Args:
            user_id: User ID

        Returns:
            Tuple of (secret, provisioning_uri)
        """
        secret = self.generate_secret()

        # Create provisioning URI for QR code
        # Format: otpauth://totp/CMS:user@example.com?secret=SECRET&issuer=CMS
        provisioning_uri = (
            f"otpauth://totp/MyCMS:user_{user_id}"
            f"?secret={secret}"
            f"&issuer=MyCMS"
            f"&digits=6"
            f"&period=30"
        )

        # Store configuration (not enabled until verified)
        config = TwoFactorAuth(
            user_id=user_id,
            secret=secret,
            enabled=False,
        )
        self._configs[user_id] = config

        return secret, provisioning_uri

    def enable_2fa(self, user_id: int, verification_code: str) -> Tuple[bool, Optional[List[str]]]:
        """Enable 2FA for a user after verifying initial setup.

        Args:
            user_id: User ID
            verification_code: TOTP code to verify

        Returns:
            Tuple of (success, backup_codes)
        """
        config = self._configs.get(user_id)
        if not config:
            return False, None

        # Verify the code
        totp = TOTPGenerator(config.secret)
        if not totp.verify(verification_code):
            return False, None

        # Generate backup codes
        backup_codes = BackupCodeGenerator.generate_codes()
        hashed_codes = [BackupCodeGenerator.hash_code(code) for code in backup_codes]

        # Enable 2FA
        config.enabled = True
        config.backup_codes = hashed_codes

        return True, backup_codes

    def disable_2fa(self, user_id: int) -> bool:
        """Disable 2FA for a user.

        Args:
            user_id: User ID

        Returns:
            True if disabled successfully
        """
        if user_id in self._configs:
            del self._configs[user_id]
            return True
        return False

    def verify_2fa_code(self, user_id: int, code: str) -> bool:
        """Verify a 2FA code for a user.

        Args:
            user_id: User ID
            code: TOTP or backup code

        Returns:
            True if code is valid
        """
        config = self._configs.get(user_id)
        if not config or not config.enabled:
            return False

        # Try TOTP first
        totp = TOTPGenerator(config.secret)
        if totp.verify(code):
            config.last_used = datetime.now(timezone.utc)
            return True

        # Try backup codes
        for i, hashed_code in enumerate(config.backup_codes):
            if BackupCodeGenerator.verify_code(code, hashed_code):
                # Remove used backup code
                config.backup_codes.pop(i)
                config.last_used = datetime.now(timezone.utc)
                return True

        return False

    def is_2fa_enabled(self, user_id: int) -> bool:
        """Check if 2FA is enabled for a user.

        Args:
            user_id: User ID

        Returns:
            True if 2FA is enabled
        """
        config = self._configs.get(user_id)
        return config is not None and config.enabled

    def regenerate_backup_codes(self, user_id: int) -> Optional[List[str]]:
        """Regenerate backup codes for a user.

        Args:
            user_id: User ID

        Returns:
            New backup codes or None if 2FA not enabled
        """
        config = self._configs.get(user_id)
        if not config or not config.enabled:
            return None

        backup_codes = BackupCodeGenerator.generate_codes()
        hashed_codes = [BackupCodeGenerator.hash_code(code) for code in backup_codes]
        config.backup_codes = hashed_codes

        return backup_codes

    def get_remaining_backup_codes(self, user_id: int) -> int:
        """Get number of remaining backup codes for a user.

        Args:
            user_id: User ID

        Returns:
            Number of remaining backup codes
        """
        config = self._configs.get(user_id)
        if not config or not config.enabled:
            return 0
        return len(config.backup_codes)


# Global 2FA manager instance
_twofa_manager: Optional[TwoFactorAuthManager] = None


def get_twofa_manager() -> TwoFactorAuthManager:
    """Get the global 2FA manager instance.

    Returns:
        Global TwoFactorAuthManager instance
    """
    global _twofa_manager
    if _twofa_manager is None:
        _twofa_manager = TwoFactorAuthManager()
    return _twofa_manager
