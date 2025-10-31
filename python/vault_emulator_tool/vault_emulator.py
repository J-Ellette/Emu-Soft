#!/usr/bin/env python3
"""
Vault Emulator - Secrets Management

This module emulates core HashiCorp Vault functionality including:
- Secret storage and retrieval (KV secrets engine)
- Dynamic secrets generation
- Secret versioning
- Encryption as a service (transit engine)
- Token-based authentication
- Policy-based access control
- Audit logging
"""

import json
import time
import hashlib
import hmac
import secrets
import base64
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading


class SecretEngineType(Enum):
    """Types of secret engines"""
    KV_V1 = "kv"
    KV_V2 = "kv-v2"
    TRANSIT = "transit"
    DATABASE = "database"
    PKI = "pki"
    AWS = "aws"


class PolicyEffect(Enum):
    """Policy effects"""
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class SecretVersion:
    """Versioned secret data"""
    version: int
    data: Dict[str, Any]
    created_time: str
    deletion_time: Optional[str] = None
    destroyed: bool = False


@dataclass
class Secret:
    """Secret storage with versioning"""
    path: str
    versions: Dict[int, SecretVersion] = field(default_factory=dict)
    current_version: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Token:
    """Vault token"""
    id: str
    policies: List[str]
    ttl: int  # seconds
    created_at: float
    renewable: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return time.time() > (self.created_at + self.ttl)
    
    def renew(self, increment: int = 0):
        """Renew token TTL"""
        if not self.renewable:
            raise Exception("Token is not renewable")
        if increment > 0:
            self.ttl = increment
        self.created_at = time.time()


@dataclass
class Policy:
    """Access control policy"""
    name: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    
    def allows(self, path: str, capability: str) -> bool:
        """Check if policy allows capability on path"""
        for rule in self.rules:
            rule_path = rule.get("path", "")
            capabilities = rule.get("capabilities", [])
            
            # Simple prefix matching
            if path.startswith(rule_path) or rule_path == "*":
                if capability in capabilities or "*" in capabilities:
                    return True
        
        return False


@dataclass
class AuditEntry:
    """Audit log entry"""
    timestamp: str
    type: str  # request or response
    operation: str
    path: str
    token: str
    client_ip: str
    success: bool
    error: Optional[str] = None


class VaultEmulator:
    """Main Vault emulator class"""
    
    def __init__(self):
        self.secrets: Dict[str, Secret] = {}
        self.tokens: Dict[str, Token] = {}
        self.policies: Dict[str, Policy] = {}
        self.audit_log: List[AuditEntry] = []
        self.encryption_keys: Dict[str, bytes] = {}
        self.root_token = self._generate_token_id()
        self.initialized = False
        self.sealed = True
        self.unseal_keys: List[str] = []
        self.unseal_threshold = 3
        self.unseal_progress = 0
        self._lock = threading.Lock()
        
        # Create root token
        root = Token(
            id=self.root_token,
            policies=["root"],
            ttl=0,  # No expiry
            created_at=time.time(),
            renewable=False
        )
        self.tokens[self.root_token] = root
        
        # Create root policy
        root_policy = Policy(name="root")
        root_policy.rules.append({
            "path": "*",
            "capabilities": ["*"]
        })
        self.policies["root"] = root_policy
    
    def _generate_token_id(self) -> str:
        """Generate random token ID"""
        return "hvs." + secrets.token_urlsafe(24)
    
    def _log_audit(self, operation: str, path: str, token: str, 
                   success: bool, error: Optional[str] = None):
        """Log audit entry"""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            type="request",
            operation=operation,
            path=path,
            token=token[:10] + "...",  # Redact token
            client_ip="127.0.0.1",
            success=success,
            error=error
        )
        self.audit_log.append(entry)
    
    def _check_token(self, token_id: str) -> Optional[Token]:
        """Validate and return token"""
        token = self.tokens.get(token_id)
        if not token:
            return None
        
        if token.is_expired():
            del self.tokens[token_id]
            return None
        
        return token
    
    def _check_permission(self, token: Token, path: str, capability: str) -> bool:
        """Check if token has permission"""
        for policy_name in token.policies:
            policy = self.policies.get(policy_name)
            if policy and policy.allows(path, capability):
                return True
        return False
    
    def initialize(self, secret_shares: int = 5, secret_threshold: int = 3) -> Dict[str, Any]:
        """Initialize Vault (Shamir secret sharing)"""
        if self.initialized:
            raise Exception("Vault is already initialized")
        
        # Generate unseal keys (simplified - not real Shamir)
        self.unseal_keys = [secrets.token_hex(16) for _ in range(secret_shares)]
        self.unseal_threshold = secret_threshold
        self.initialized = True
        
        return {
            "keys": self.unseal_keys,
            "keys_base64": [base64.b64encode(k.encode()).decode() for k in self.unseal_keys],
            "root_token": self.root_token
        }
    
    def seal(self):
        """Seal Vault"""
        self.sealed = True
        self.unseal_progress = 0
    
    def unseal(self, key: str) -> Dict[str, Any]:
        """Unseal Vault with key"""
        if not self.initialized:
            raise Exception("Vault is not initialized")
        
        if not self.sealed:
            return {"sealed": False, "progress": 0, "threshold": self.unseal_threshold}
        
        if key in self.unseal_keys:
            self.unseal_progress += 1
            
            if self.unseal_progress >= self.unseal_threshold:
                self.sealed = False
                self.unseal_progress = 0
                return {"sealed": False, "progress": 0, "threshold": self.unseal_threshold}
        
        return {
            "sealed": True,
            "progress": self.unseal_progress,
            "threshold": self.unseal_threshold
        }
    
    def status(self) -> Dict[str, Any]:
        """Get Vault status"""
        return {
            "initialized": self.initialized,
            "sealed": self.sealed,
            "unseal_progress": self.unseal_progress,
            "unseal_threshold": self.unseal_threshold
        }
    
    # KV Secrets Engine
    
    def write_secret(self, token_id: str, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write secret (KV v2)"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            self._log_audit("write", path, token_id, False, "invalid token")
            raise Exception("Invalid or expired token")
        
        if not self._check_permission(token, path, "create"):
            self._log_audit("write", path, token_id, False, "permission denied")
            raise Exception("Permission denied")
        
        with self._lock:
            if path not in self.secrets:
                self.secrets[path] = Secret(path=path)
            
            secret = self.secrets[path]
            secret.current_version += 1
            
            version = SecretVersion(
                version=secret.current_version,
                data=data.copy(),
                created_time=datetime.utcnow().isoformat()
            )
            
            secret.versions[secret.current_version] = version
        
        self._log_audit("write", path, token_id, True)
        
        return {
            "data": {
                "version": secret.current_version,
                "created_time": version.created_time
            }
        }
    
    def read_secret(self, token_id: str, path: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Read secret (KV v2)"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            self._log_audit("read", path, token_id, False, "invalid token")
            raise Exception("Invalid or expired token")
        
        if not self._check_permission(token, path, "read"):
            self._log_audit("read", path, token_id, False, "permission denied")
            raise Exception("Permission denied")
        
        secret = self.secrets.get(path)
        if not secret:
            self._log_audit("read", path, token_id, False, "not found")
            raise Exception("Secret not found")
        
        if version is None:
            version = secret.current_version
        
        secret_version = secret.versions.get(version)
        if not secret_version or secret_version.destroyed:
            self._log_audit("read", path, token_id, False, "version not found")
            raise Exception("Secret version not found or destroyed")
        
        self._log_audit("read", path, token_id, True)
        
        return {
            "data": {
                "data": secret_version.data.copy(),
                "metadata": {
                    "version": version,
                    "created_time": secret_version.created_time,
                    "destroyed": secret_version.destroyed
                }
            }
        }
    
    def delete_secret(self, token_id: str, path: str) -> Dict[str, Any]:
        """Delete secret (soft delete)"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        if not self._check_permission(token, path, "delete"):
            raise Exception("Permission denied")
        
        if path in self.secrets:
            # Soft delete - mark latest version as deleted
            secret = self.secrets[path]
            latest = secret.versions.get(secret.current_version)
            if latest:
                latest.deletion_time = datetime.utcnow().isoformat()
        
        self._log_audit("delete", path, token_id, True)
        return {}
    
    def list_secrets(self, token_id: str, path: str) -> Dict[str, Any]:
        """List secrets at path"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        if not self._check_permission(token, path, "list"):
            raise Exception("Permission denied")
        
        # List all secrets under path
        keys = []
        for secret_path in self.secrets.keys():
            if secret_path.startswith(path):
                relative = secret_path[len(path):].lstrip("/")
                if relative and "/" not in relative:
                    keys.append(relative)
        
        return {"data": {"keys": sorted(set(keys))}}
    
    # Transit Engine (Encryption as a Service)
    
    def create_encryption_key(self, token_id: str, name: str) -> Dict[str, Any]:
        """Create encryption key in transit engine"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        if name in self.encryption_keys:
            raise Exception("Key already exists")
        
        # Generate 256-bit encryption key
        self.encryption_keys[name] = secrets.token_bytes(32)
        
        return {}
    
    def encrypt(self, token_id: str, key_name: str, plaintext: str) -> Dict[str, Any]:
        """Encrypt data using transit key"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        key = self.encryption_keys.get(key_name)
        if not key:
            raise Exception("Encryption key not found")
        
        # Simple encryption (not cryptographically secure - just for emulation)
        plaintext_bytes = plaintext.encode('utf-8')
        nonce = secrets.token_bytes(12)
        
        # XOR with key material (simplified)
        ciphertext = bytes(b ^ key[i % len(key)] for i, b in enumerate(plaintext_bytes))
        
        # Encode result
        result = base64.b64encode(nonce + ciphertext).decode('utf-8')
        
        return {
            "data": {
                "ciphertext": f"vault:v1:{result}"
            }
        }
    
    def decrypt(self, token_id: str, key_name: str, ciphertext: str) -> Dict[str, Any]:
        """Decrypt data using transit key"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        key = self.encryption_keys.get(key_name)
        if not key:
            raise Exception("Encryption key not found")
        
        # Parse ciphertext
        if not ciphertext.startswith("vault:v1:"):
            raise Exception("Invalid ciphertext format")
        
        encoded = ciphertext[9:]  # Remove "vault:v1:" prefix
        data = base64.b64decode(encoded)
        
        # Extract nonce and ciphertext
        nonce = data[:12]
        encrypted = data[12:]
        
        # XOR decrypt (matching encryption)
        plaintext_bytes = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
        plaintext = plaintext_bytes.decode('utf-8')
        
        return {
            "data": {
                "plaintext": base64.b64encode(plaintext.encode()).decode('utf-8')
            }
        }
    
    # Token Management
    
    def create_token(self, token_id: str, policies: List[str] = None, 
                     ttl: int = 3600, renewable: bool = True) -> Dict[str, Any]:
        """Create new token"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        if policies is None:
            policies = ["default"]
        
        new_token_id = self._generate_token_id()
        new_token = Token(
            id=new_token_id,
            policies=policies,
            ttl=ttl,
            created_at=time.time(),
            renewable=renewable
        )
        
        self.tokens[new_token_id] = new_token
        
        return {
            "auth": {
                "client_token": new_token_id,
                "policies": policies,
                "renewable": renewable,
                "lease_duration": ttl
            }
        }
    
    def renew_token(self, token_id: str, increment: int = 0) -> Dict[str, Any]:
        """Renew token lease"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        token.renew(increment)
        
        return {
            "auth": {
                "client_token": token_id,
                "renewable": token.renewable,
                "lease_duration": token.ttl
            }
        }
    
    def revoke_token(self, token_id: str, revoke_token_id: str) -> Dict[str, Any]:
        """Revoke token"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        if revoke_token_id in self.tokens:
            del self.tokens[revoke_token_id]
        
        return {}
    
    # Policy Management
    
    def write_policy(self, token_id: str, name: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Write policy"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        policy = Policy(name=name, rules=rules)
        self.policies[name] = policy
        
        return {}
    
    def read_policy(self, token_id: str, name: str) -> Dict[str, Any]:
        """Read policy"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        policy = self.policies.get(name)
        if not policy:
            raise Exception("Policy not found")
        
        return {
            "data": {
                "name": name,
                "rules": policy.rules
            }
        }
    
    def list_policies(self, token_id: str) -> Dict[str, Any]:
        """List all policies"""
        if self.sealed:
            raise Exception("Vault is sealed")
        
        token = self._check_token(token_id)
        if not token:
            raise Exception("Invalid or expired token")
        
        return {
            "data": {
                "policies": list(self.policies.keys())
            }
        }
    
    # Audit
    
    def get_audit_log(self, token_id: str, limit: int = 100) -> List[AuditEntry]:
        """Get audit log entries"""
        token = self._check_token(token_id)
        if not token or "root" not in token.policies:
            raise Exception("Permission denied")
        
        return self.audit_log[-limit:]


if __name__ == "__main__":
    # Example usage
    vault = VaultEmulator()
    
    # Initialize
    init_result = vault.initialize(secret_shares=5, secret_threshold=3)
    print(f"Root token: {init_result['root_token']}")
    print(f"Unseal keys: {init_result['keys'][:2]}...")
    
    # Unseal
    for key in init_result['keys'][:3]:
        result = vault.unseal(key)
        print(f"Unseal progress: {result}")
    
    # Use root token
    root_token = init_result['root_token']
    
    # Write secret
    vault.write_secret(root_token, "secret/myapp/config", {
        "username": "admin",
        "password": "secret123"
    })
    print("Secret written")
    
    # Read secret
    secret = vault.read_secret(root_token, "secret/myapp/config")
    print(f"Secret data: {secret['data']['data']}")
    
    # Create encryption key
    vault.create_encryption_key(root_token, "mykey")
    
    # Encrypt
    encrypted = vault.encrypt(root_token, "mykey", "Hello World")
    print(f"Encrypted: {encrypted['data']['ciphertext']}")
    
    # Decrypt
    decrypted = vault.decrypt(root_token, "mykey", encrypted['data']['ciphertext'])
    plaintext = base64.b64decode(decrypted['data']['plaintext']).decode('utf-8')
    print(f"Decrypted: {plaintext}")
