"""
Developed by PowerShield, as an alternative to Django Security
"""

"""Content Integrity Verification System.

This module provides hash-based checksums and blockchain-style audit trails for
critical content, ensuring tamper detection and cryptographic proof of integrity.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class ContentIntegrityAction(Enum):
    """Types of content integrity actions."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VERIFY = "verify"
    RESTORE = "restore"


@dataclass
class ContentHash:
    """Represents a hash of content with metadata."""

    content_id: str
    content_type: str
    hash_value: str
    algorithm: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class IntegrityBlock:
    """Represents a block in the integrity verification chain.

    Similar to blockchain, each block contains:
    - Content hash
    - Previous block hash (linking)
    - Timestamp
    - Action performed
    - User who performed action
    - Digital signature
    """

    block_id: str
    content_id: str
    content_type: str
    content_hash: str
    previous_hash: str
    timestamp: datetime
    action: ContentIntegrityAction
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None

    def calculate_block_hash(self) -> str:
        """Calculate hash of this block for chaining."""
        block_data = {
            "block_id": self.block_id,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "content_hash": self.content_hash,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }
        data_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "block_id": self.block_id,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "content_hash": self.content_hash,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "signature": self.signature,
        }


@dataclass
class VerificationResult:
    """Result of integrity verification."""

    is_valid: bool
    content_id: str
    content_type: str
    verification_timestamp: datetime
    chain_length: int
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "verification_timestamp": self.verification_timestamp.isoformat(),
            "chain_length": self.chain_length,
            "issues": self.issues,
            "details": self.details,
        }


class ContentIntegrityVerifier:
    """System for verifying content integrity using hash-based checksums
    and blockchain-style audit trails.
    """

    def __init__(self, hash_algorithm: str = "sha256") -> None:
        """Initialize the content integrity verifier.

        Args:
            hash_algorithm: Hash algorithm to use (sha256, sha512, etc.)
        """
        self.hash_algorithm = hash_algorithm
        self.chains: Dict[str, List[IntegrityBlock]] = {}
        self._genesis_blocks: Dict[str, IntegrityBlock] = {}

    def _get_chain_key(self, content_type: str, content_id: str) -> str:
        """Get unique key for content chain."""
        return f"{content_type}:{content_id}"

    def generate_content_hash(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate hash for content.

        Args:
            content: Content to hash (string, bytes, or dict)
            metadata: Optional metadata to include in hash

        Returns:
            Hexadecimal hash string
        """
        if isinstance(content, dict):
            content_str = json.dumps(content, sort_keys=True)
        elif isinstance(content, bytes):
            content_str = content.decode("utf-8", errors="ignore")
        else:
            content_str = str(content)

        if metadata:
            content_str += json.dumps(metadata, sort_keys=True)

        if self.hash_algorithm == "sha256":
            return hashlib.sha256(content_str.encode()).hexdigest()
        elif self.hash_algorithm == "sha512":
            return hashlib.sha512(content_str.encode()).hexdigest()
        elif self.hash_algorithm == "sha3_256":
            return hashlib.sha3_256(content_str.encode()).hexdigest()
        else:
            return hashlib.sha256(content_str.encode()).hexdigest()

    def create_genesis_block(
        self,
        content_id: str,
        content_type: str,
        content_hash: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IntegrityBlock:
        """Create the first block (genesis block) for content.

        Args:
            content_id: Unique content identifier
            content_type: Type of content (page, post, etc.)
            content_hash: Hash of the content
            user_id: User who created the content
            metadata: Additional metadata

        Returns:
            Genesis IntegrityBlock
        """
        chain_key = self._get_chain_key(content_type, content_id)

        if chain_key in self.chains:
            raise ValueError(f"Chain already exists for {chain_key}")

        genesis_block = IntegrityBlock(
            block_id=str(uuid.uuid4()),
            content_id=content_id,
            content_type=content_type,
            content_hash=content_hash,
            previous_hash="0" * 64,  # Genesis block has no previous
            timestamp=datetime.now(timezone.utc),
            action=ContentIntegrityAction.CREATE,
            user_id=user_id,
            metadata=metadata or {},
        )

        # Calculate and store signature
        genesis_block.signature = genesis_block.calculate_block_hash()

        # Initialize chain
        self.chains[chain_key] = [genesis_block]
        self._genesis_blocks[chain_key] = genesis_block

        return genesis_block

    def add_block(
        self,
        content_id: str,
        content_type: str,
        content_hash: str,
        action: ContentIntegrityAction,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IntegrityBlock:
        """Add a new block to the integrity chain.

        Args:
            content_id: Unique content identifier
            content_type: Type of content
            content_hash: Hash of the current content
            action: Action being performed
            user_id: User performing the action
            metadata: Additional metadata

        Returns:
            New IntegrityBlock

        Raises:
            ValueError: If no chain exists for this content
        """
        chain_key = self._get_chain_key(content_type, content_id)

        if chain_key not in self.chains:
            raise ValueError(f"No chain exists for {chain_key}. Create genesis block first.")

        # Get previous block
        previous_block = self.chains[chain_key][-1]

        # Create new block
        new_block = IntegrityBlock(
            block_id=str(uuid.uuid4()),
            content_id=content_id,
            content_type=content_type,
            content_hash=content_hash,
            previous_hash=previous_block.signature or previous_block.calculate_block_hash(),
            timestamp=datetime.now(timezone.utc),
            action=action,
            user_id=user_id,
            metadata=metadata or {},
        )

        # Calculate and store signature
        new_block.signature = new_block.calculate_block_hash()

        # Add to chain
        self.chains[chain_key].append(new_block)

        return new_block

    def verify_chain(
        self,
        content_type: str,
        content_id: str,
    ) -> VerificationResult:
        """Verify integrity of the entire chain for content.

        Args:
            content_type: Type of content
            content_id: Content identifier

        Returns:
            VerificationResult with validation status and details
        """
        chain_key = self._get_chain_key(content_type, content_id)

        if chain_key not in self.chains:
            return VerificationResult(
                is_valid=False,
                content_id=content_id,
                content_type=content_type,
                verification_timestamp=datetime.now(timezone.utc),
                chain_length=0,
                issues=["No integrity chain found for this content"],
            )

        chain = self.chains[chain_key]
        issues: List[str] = []
        details: Dict[str, Any] = {}

        # Verify genesis block
        if not chain:
            return VerificationResult(
                is_valid=False,
                content_id=content_id,
                content_type=content_type,
                verification_timestamp=datetime.now(timezone.utc),
                chain_length=0,
                issues=["Empty chain"],
            )

        genesis = chain[0]
        if genesis.previous_hash != "0" * 64:
            issues.append("Genesis block has invalid previous hash")

        # Verify each block's signature
        for i, block in enumerate(chain):
            expected_hash = block.calculate_block_hash()
            if block.signature != expected_hash:
                issues.append(
                    f"Block {i} (ID: {block.block_id}) has invalid signature. "
                    f"Expected: {expected_hash}, Got: {block.signature}"
                )

        # Verify chain linkage
        for i in range(1, len(chain)):
            previous_block = chain[i - 1]
            current_block = chain[i]

            expected_previous_hash = (
                previous_block.signature or previous_block.calculate_block_hash()
            )

            if current_block.previous_hash != expected_previous_hash:
                issues.append(
                    f"Block {i} (ID: {current_block.block_id}) has broken chain link. "
                    f"Expected previous_hash: {expected_previous_hash}, "
                    f"Got: {current_block.previous_hash}"
                )

        # Collect details
        details["first_block_timestamp"] = chain[0].timestamp.isoformat()
        details["last_block_timestamp"] = chain[-1].timestamp.isoformat()
        details["actions"] = [block.action.value for block in chain]
        details["users"] = list(set(block.user_id for block in chain if block.user_id))

        return VerificationResult(
            is_valid=len(issues) == 0,
            content_id=content_id,
            content_type=content_type,
            verification_timestamp=datetime.now(timezone.utc),
            chain_length=len(chain),
            issues=issues,
            details=details,
        )

    def detect_tampering(
        self,
        content_id: str,
        content_type: str,
        current_content: Any,
    ) -> Tuple[bool, Optional[str]]:
        """Detect if content has been tampered with.

        Args:
            content_id: Content identifier
            content_type: Type of content
            current_content: Current content to verify

        Returns:
            Tuple of (is_tampered, message)
        """
        chain_key = self._get_chain_key(content_type, content_id)

        if chain_key not in self.chains:
            return True, "No integrity chain exists for this content"

        # Get latest block
        latest_block = self.chains[chain_key][-1]

        # Calculate current content hash
        current_hash = self.generate_content_hash(current_content)

        # Compare with stored hash
        if current_hash != latest_block.content_hash:
            return (
                True,
                f"Content hash mismatch. Expected: {latest_block.content_hash}, "
                f"Got: {current_hash}",
            )

        # Verify chain integrity
        verification = self.verify_chain(content_type, content_id)
        if not verification.is_valid:
            return True, f"Chain integrity compromised: {', '.join(verification.issues)}"

        return False, None

    def get_chain(
        self,
        content_type: str,
        content_id: str,
    ) -> List[IntegrityBlock]:
        """Get the integrity chain for content.

        Args:
            content_type: Type of content
            content_id: Content identifier

        Returns:
            List of IntegrityBlock in chronological order
        """
        chain_key = self._get_chain_key(content_type, content_id)
        return self.chains.get(chain_key, [])

    def get_audit_trail(
        self,
        content_type: str,
        content_id: str,
    ) -> List[Dict[str, Any]]:
        """Get human-readable audit trail for content.

        Args:
            content_type: Type of content
            content_id: Content identifier

        Returns:
            List of audit trail entries
        """
        chain = self.get_chain(content_type, content_id)
        return [block.to_dict() for block in chain]

    def export_chain(
        self,
        content_type: str,
        content_id: str,
    ) -> str:
        """Export chain as JSON string.

        Args:
            content_type: Type of content
            content_id: Content identifier

        Returns:
            JSON string of the chain
        """
        chain = self.get_chain(content_type, content_id)
        chain_data = [block.to_dict() for block in chain]
        return json.dumps(chain_data, indent=2)

    def import_chain(
        self,
        chain_json: str,
    ) -> bool:
        """Import chain from JSON string.

        Args:
            chain_json: JSON string of the chain

        Returns:
            True if import successful, False otherwise
        """
        try:
            chain_data = json.loads(chain_json)

            if not chain_data:
                return False

            # Reconstruct blocks
            blocks = []
            for block_dict in chain_data:
                block = IntegrityBlock(
                    block_id=block_dict["block_id"],
                    content_id=block_dict["content_id"],
                    content_type=block_dict["content_type"],
                    content_hash=block_dict["content_hash"],
                    previous_hash=block_dict["previous_hash"],
                    timestamp=datetime.fromisoformat(block_dict["timestamp"]),
                    action=ContentIntegrityAction(block_dict["action"]),
                    user_id=block_dict.get("user_id"),
                    metadata=block_dict.get("metadata", {}),
                    signature=block_dict.get("signature"),
                )
                blocks.append(block)

            # Verify chain before importing
            first_block = blocks[0]
            chain_key = self._get_chain_key(first_block.content_type, first_block.content_id)

            # Store chain
            self.chains[chain_key] = blocks
            self._genesis_blocks[chain_key] = blocks[0]

            return True

        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def get_content_history(
        self,
        content_type: str,
        content_id: str,
    ) -> List[Dict[str, Any]]:
        """Get history of content changes with integrity information.

        Args:
            content_type: Type of content
            content_id: Content identifier

        Returns:
            List of history entries with timestamps, actions, and hashes
        """
        chain = self.get_chain(content_type, content_id)

        history = []
        for block in chain:
            history.append(
                {
                    "timestamp": block.timestamp.isoformat(),
                    "action": block.action.value,
                    "user_id": block.user_id,
                    "content_hash": block.content_hash,
                    "block_id": block.block_id,
                    "metadata": block.metadata,
                }
            )

        return history


# Global instance
_verifier_instance: Optional[ContentIntegrityVerifier] = None


def get_content_integrity_verifier() -> ContentIntegrityVerifier:
    """Get global content integrity verifier instance."""
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = ContentIntegrityVerifier()
    return _verifier_instance


def verify_content_integrity(
    content_id: str,
    content_type: str,
    current_content: Any,
) -> Tuple[bool, Optional[str]]:
    """Convenience function to verify content integrity.

    Args:
        content_id: Content identifier
        content_type: Type of content
        current_content: Current content to verify

    Returns:
        Tuple of (is_valid, message)
    """
    verifier = get_content_integrity_verifier()
    is_tampered, message = verifier.detect_tampering(content_id, content_type, current_content)
    return not is_tampered, message
