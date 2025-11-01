"""
Secret Rotation Automation for Local Development

A tool for automating secret rotation in local development environments,
including API keys, passwords, tokens, and other sensitive credentials.
"""

import json
import os
import secrets
import string
import hashlib
import hmac
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import base64


class SecretType(Enum):
    """Types of secrets that can be managed"""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    DATABASE_PASSWORD = "database_password"
    ENCRYPTION_KEY = "encryption_key"
    SIGNING_KEY = "signing_key"
    CERTIFICATE = "certificate"
    GENERIC = "generic"


class RotationStrategy(Enum):
    """Secret rotation strategies"""
    RANDOM = "random"
    DERIVED = "derived"
    CUSTOM = "custom"


@dataclass
class SecretMetadata:
    """Metadata for a managed secret"""
    name: str
    secret_type: SecretType
    created_at: str
    last_rotated: Optional[str] = None
    rotation_count: int = 0
    rotation_interval_days: Optional[int] = None
    next_rotation: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class RotationHistory:
    """History record of secret rotation"""
    secret_name: str
    rotated_at: str
    rotation_count: int
    strategy: str
    success: bool
    notes: str = ""


class SecretRotation:
    """
    Secret Rotation Automation for Local Development
    
    Manages and automates the rotation of secrets in local development environments.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize SecretRotation manager
        
        Args:
            storage_path: Path to store secrets and metadata (default: .secrets/)
        """
        self.storage_path = storage_path or os.path.join(os.getcwd(), '.secrets')
        self.secrets: Dict[str, str] = {}
        self.metadata: Dict[str, SecretMetadata] = {}
        self.history: List[RotationHistory] = []
        self.rotation_callbacks: Dict[str, Callable] = {}
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
    
    def generate_api_key(self, length: int = 32) -> str:
        """
        Generate a random API key
        
        Args:
            length: Length of the API key
            
        Returns:
            Generated API key
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_password(self, length: int = 16, use_special: bool = True) -> str:
        """
        Generate a secure random password
        
        Args:
            length: Length of the password
            use_special: Include special characters
            
        Returns:
            Generated password
        """
        alphabet = string.ascii_letters + string.digits
        if use_special:
            alphabet += string.punctuation
        
        # Ensure at least one of each required type
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
        ]
        
        if use_special:
            password.append(secrets.choice(string.punctuation))
        
        # Fill the rest
        password.extend(secrets.choice(alphabet) for _ in range(length - len(password)))
        
        # Shuffle
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)
    
    def generate_token(self, length: int = 32) -> str:
        """
        Generate a secure random token
        
        Args:
            length: Length of the token in bytes
            
        Returns:
            Base64-encoded token
        """
        token_bytes = secrets.token_bytes(length)
        return base64.urlsafe_b64encode(token_bytes).decode('utf-8').rstrip('=')
    
    def generate_encryption_key(self, key_size: int = 32) -> str:
        """
        Generate an encryption key
        
        Args:
            key_size: Size in bytes (32 for AES-256)
            
        Returns:
            Hex-encoded encryption key
        """
        return secrets.token_hex(key_size)
    
    def generate_signing_key(self, length: int = 64) -> str:
        """
        Generate a signing key for HMAC or JWT
        
        Args:
            length: Length of the key in bytes
            
        Returns:
            Base64-encoded signing key
        """
        key_bytes = secrets.token_bytes(length)
        return base64.b64encode(key_bytes).decode('utf-8')
    
    def add_secret(
        self,
        name: str,
        value: Optional[str] = None,
        secret_type: SecretType = SecretType.GENERIC,
        rotation_interval_days: Optional[int] = None,
        tags: Optional[List[str]] = None,
        auto_generate: bool = True
    ) -> str:
        """
        Add a secret to the manager
        
        Args:
            name: Secret name
            value: Secret value (will be generated if None and auto_generate=True)
            secret_type: Type of secret
            rotation_interval_days: Days until next rotation
            tags: Tags for categorization
            auto_generate: Auto-generate secret if value is None
            
        Returns:
            The secret value
        """
        if value is None and auto_generate:
            value = self._generate_secret_by_type(secret_type)
        elif value is None:
            raise ValueError("Secret value must be provided or auto_generate must be True")
        
        self.secrets[name] = value
        
        now = datetime.utcnow().isoformat()
        next_rotation = None
        if rotation_interval_days:
            next_rotation = (datetime.utcnow() + timedelta(days=rotation_interval_days)).isoformat()
        
        self.metadata[name] = SecretMetadata(
            name=name,
            secret_type=secret_type,
            created_at=now,
            last_rotated=now,
            rotation_count=0,
            rotation_interval_days=rotation_interval_days,
            next_rotation=next_rotation,
            tags=tags or []
        )
        
        return value
    
    def _generate_secret_by_type(self, secret_type: SecretType) -> str:
        """Generate a secret based on its type"""
        generators = {
            SecretType.API_KEY: lambda: self.generate_api_key(),
            SecretType.PASSWORD: lambda: self.generate_password(),
            SecretType.TOKEN: lambda: self.generate_token(),
            SecretType.DATABASE_PASSWORD: lambda: self.generate_password(length=24),
            SecretType.ENCRYPTION_KEY: lambda: self.generate_encryption_key(),
            SecretType.SIGNING_KEY: lambda: self.generate_signing_key(),
            SecretType.GENERIC: lambda: self.generate_token(),
        }
        
        generator = generators.get(secret_type, lambda: self.generate_token())
        return generator()
    
    def rotate_secret(
        self,
        name: str,
        new_value: Optional[str] = None,
        strategy: RotationStrategy = RotationStrategy.RANDOM
    ) -> str:
        """
        Rotate a secret
        
        Args:
            name: Secret name
            new_value: New secret value (generated if None)
            strategy: Rotation strategy
            
        Returns:
            New secret value
        """
        if name not in self.secrets:
            raise ValueError(f"Secret '{name}' not found")
        
        metadata = self.metadata[name]
        old_value = self.secrets[name]
        
        # Generate or use provided new value
        if new_value is None:
            if strategy == RotationStrategy.RANDOM:
                new_value = self._generate_secret_by_type(metadata.secret_type)
            elif strategy == RotationStrategy.DERIVED:
                new_value = self._derive_secret(old_value)
            else:
                raise ValueError("Custom strategy requires new_value to be provided")
        
        # Update secret
        self.secrets[name] = new_value
        
        # Update metadata
        now = datetime.utcnow().isoformat()
        metadata.last_rotated = now
        metadata.rotation_count += 1
        
        if metadata.rotation_interval_days:
            metadata.next_rotation = (
                datetime.utcnow() + timedelta(days=metadata.rotation_interval_days)
            ).isoformat()
        
        # Record history
        self.history.append(RotationHistory(
            secret_name=name,
            rotated_at=now,
            rotation_count=metadata.rotation_count,
            strategy=strategy.value,
            success=True
        ))
        
        # Call rotation callback if registered
        if name in self.rotation_callbacks:
            try:
                self.rotation_callbacks[name](name, old_value, new_value)
            except Exception as e:
                self.history[-1].success = False
                self.history[-1].notes = f"Callback error: {str(e)}"
        
        return new_value
    
    def _derive_secret(self, old_value: str) -> str:
        """Derive a new secret from an old one using HMAC"""
        key = secrets.token_bytes(32)
        derived = hmac.new(key, old_value.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(derived).decode('utf-8').rstrip('=')
    
    def register_rotation_callback(self, secret_name: str, callback: Callable) -> None:
        """
        Register a callback to be called when a secret is rotated
        
        Args:
            secret_name: Name of the secret
            callback: Function to call (receives: name, old_value, new_value)
        """
        self.rotation_callbacks[secret_name] = callback
    
    def get_secret(self, name: str) -> Optional[str]:
        """
        Get a secret value
        
        Args:
            name: Secret name
            
        Returns:
            Secret value or None if not found
        """
        return self.secrets.get(name)
    
    def get_metadata(self, name: str) -> Optional[SecretMetadata]:
        """
        Get secret metadata
        
        Args:
            name: Secret name
            
        Returns:
            SecretMetadata or None if not found
        """
        return self.metadata.get(name)
    
    def list_secrets(self, secret_type: Optional[SecretType] = None) -> List[str]:
        """
        List all secret names
        
        Args:
            secret_type: Filter by secret type (optional)
            
        Returns:
            List of secret names
        """
        if secret_type is None:
            return list(self.secrets.keys())
        
        return [
            name for name, meta in self.metadata.items()
            if meta.secret_type == secret_type
        ]
    
    def check_rotation_needed(self) -> List[str]:
        """
        Check which secrets need rotation
        
        Returns:
            List of secret names that need rotation
        """
        now = datetime.utcnow()
        needs_rotation = []
        
        for name, meta in self.metadata.items():
            if meta.next_rotation:
                next_rotation = datetime.fromisoformat(meta.next_rotation)
                if now >= next_rotation:
                    needs_rotation.append(name)
        
        return needs_rotation
    
    def rotate_all_due(self) -> Dict[str, bool]:
        """
        Rotate all secrets that are due for rotation
        
        Returns:
            Dictionary mapping secret names to success status
        """
        due_secrets = self.check_rotation_needed()
        results = {}
        
        for name in due_secrets:
            try:
                self.rotate_secret(name)
                results[name] = True
            except Exception as e:
                results[name] = False
                self.history.append(RotationHistory(
                    secret_name=name,
                    rotated_at=datetime.utcnow().isoformat(),
                    rotation_count=self.metadata[name].rotation_count,
                    strategy='auto',
                    success=False,
                    notes=str(e)
                ))
        
        return results
    
    def delete_secret(self, name: str) -> bool:
        """
        Delete a secret
        
        Args:
            name: Secret name
            
        Returns:
            True if deleted, False if not found
        """
        if name not in self.secrets:
            return False
        
        del self.secrets[name]
        del self.metadata[name]
        if name in self.rotation_callbacks:
            del self.rotation_callbacks[name]
        
        return True
    
    def export_secrets(self, filepath: str, include_metadata: bool = True) -> None:
        """
        Export secrets to a JSON file
        
        Args:
            filepath: Path to export file
            include_metadata: Include metadata in export
        """
        data = {'secrets': self.secrets}
        
        if include_metadata:
            data['metadata'] = {
                name: {
                    'name': meta.name,
                    'secret_type': meta.secret_type.value,
                    'created_at': meta.created_at,
                    'last_rotated': meta.last_rotated,
                    'rotation_count': meta.rotation_count,
                    'rotation_interval_days': meta.rotation_interval_days,
                    'next_rotation': meta.next_rotation,
                    'tags': meta.tags
                }
                for name, meta in self.metadata.items()
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_secrets(self, filepath: str) -> None:
        """
        Import secrets from a JSON file
        
        Args:
            filepath: Path to import file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Import secrets
        self.secrets.update(data.get('secrets', {}))
        
        # Import metadata if available
        if 'metadata' in data:
            for name, meta_dict in data['metadata'].items():
                self.metadata[name] = SecretMetadata(
                    name=meta_dict['name'],
                    secret_type=SecretType(meta_dict['secret_type']),
                    created_at=meta_dict['created_at'],
                    last_rotated=meta_dict.get('last_rotated'),
                    rotation_count=meta_dict.get('rotation_count', 0),
                    rotation_interval_days=meta_dict.get('rotation_interval_days'),
                    next_rotation=meta_dict.get('next_rotation'),
                    tags=meta_dict.get('tags', [])
                )
    
    def get_rotation_history(self, secret_name: Optional[str] = None) -> List[RotationHistory]:
        """
        Get rotation history
        
        Args:
            secret_name: Filter by secret name (optional)
            
        Returns:
            List of rotation history records
        """
        if secret_name is None:
            return self.history
        
        return [h for h in self.history if h.secret_name == secret_name]
    
    def generate_env_file(self, filepath: str, secrets: Optional[List[str]] = None) -> None:
        """
        Generate a .env file with secrets
        
        Args:
            filepath: Path to .env file
            secrets: List of secret names to include (all if None)
        """
        secret_names = secrets or list(self.secrets.keys())
        
        with open(filepath, 'w') as f:
            f.write("# Auto-generated .env file\n")
            f.write(f"# Generated at: {datetime.utcnow().isoformat()}\n")
            f.write("#\n\n")
            
            for name in secret_names:
                if name in self.secrets:
                    value = self.secrets[name]
                    f.write(f"{name}={value}\n")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about managed secrets
        
        Returns:
            Dictionary with statistics
        """
        total_secrets = len(self.secrets)
        secrets_by_type = {}
        total_rotations = 0
        
        for meta in self.metadata.values():
            secret_type = meta.secret_type.value
            secrets_by_type[secret_type] = secrets_by_type.get(secret_type, 0) + 1
            total_rotations += meta.rotation_count
        
        needs_rotation = len(self.check_rotation_needed())
        
        return {
            'total_secrets': total_secrets,
            'secrets_by_type': secrets_by_type,
            'total_rotations': total_rotations,
            'needs_rotation': needs_rotation,
            'total_history_records': len(self.history)
        }
    
    def validate_secret_strength(self, value: str, secret_type: SecretType) -> Dict[str, Any]:
        """
        Validate the strength of a secret
        
        Args:
            value: Secret value
            secret_type: Type of secret
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'issues': [],
            'score': 100
        }
        
        # Check length
        min_lengths = {
            SecretType.API_KEY: 16,
            SecretType.PASSWORD: 12,
            SecretType.TOKEN: 16,
            SecretType.DATABASE_PASSWORD: 16,
            SecretType.ENCRYPTION_KEY: 32,
            SecretType.SIGNING_KEY: 32,
        }
        
        min_length = min_lengths.get(secret_type, 12)
        if len(value) < min_length:
            results['valid'] = False
            results['issues'].append(f"Length too short (minimum: {min_length})")
            results['score'] -= 30
        
        # Check for common patterns (for passwords)
        if secret_type == SecretType.PASSWORD:
            if not any(c.isupper() for c in value):
                results['issues'].append("No uppercase letters")
                results['score'] -= 10
            if not any(c.islower() for c in value):
                results['issues'].append("No lowercase letters")
                results['score'] -= 10
            if not any(c.isdigit() for c in value):
                results['issues'].append("No digits")
                results['score'] -= 10
        
        # Check entropy
        unique_chars = len(set(value))
        if unique_chars < len(value) * 0.5:
            results['issues'].append("Low character diversity")
            results['score'] -= 20
        
        results['score'] = max(0, results['score'])
        
        return results
