"""
Developed by PowerShield, as an alternative to Django Security
"""

"""Integration example for Content Integrity Verification System.

This demonstrates how to integrate content integrity verification
with the existing content versioning system.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from security.content_integrity import (
    ContentIntegrityAction,
    get_content_integrity_verifier,
)


class IntegrityAwareContentManager:
    """Content manager that integrates integrity verification with versioning."""

    def __init__(self):
        """Initialize the content manager."""
        self.verifier = get_content_integrity_verifier()
        self.content_store: Dict[str, Dict[str, Any]] = {}

    def create_content(
        self,
        content_id: str,
        content_type: str,
        content_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create new content with integrity tracking.

        Args:
            content_id: Unique content identifier
            content_type: Type of content (page, post, etc.)
            content_data: Content data (title, body, etc.)
            user_id: User creating the content

        Returns:
            Dictionary with content and integrity information
        """
        # Generate content hash
        content_hash = self.verifier.generate_content_hash(
            content_data, metadata={"created_at": datetime.now(timezone.utc).isoformat()}
        )

        # Create genesis block
        genesis_block = self.verifier.create_genesis_block(
            content_id=content_id,
            content_type=content_type,
            content_hash=content_hash,
            user_id=user_id,
            metadata={
                "title": content_data.get("title", ""),
                "version": "1.0",
            },
        )

        # Store content
        self.content_store[content_id] = {
            "content_type": content_type,
            "data": content_data,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        return {
            "content_id": content_id,
            "content_hash": content_hash,
            "block_id": genesis_block.block_id,
            "signature": genesis_block.signature,
        }

    def update_content(
        self,
        content_id: str,
        content_type: str,
        content_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update content with integrity tracking.

        Args:
            content_id: Content identifier
            content_type: Type of content
            content_data: New content data
            user_id: User updating the content

        Returns:
            Dictionary with update and integrity information
        """
        if content_id not in self.content_store:
            raise ValueError(f"Content {content_id} not found")

        # Generate new content hash
        content_hash = self.verifier.generate_content_hash(
            content_data, metadata={"updated_at": datetime.now(timezone.utc).isoformat()}
        )

        # Add update block
        update_block = self.verifier.add_block(
            content_id=content_id,
            content_type=content_type,
            content_hash=content_hash,
            action=ContentIntegrityAction.UPDATE,
            user_id=user_id,
            metadata={
                "title": content_data.get("title", ""),
                "changed_fields": list(content_data.keys()),
            },
        )

        # Update stored content
        self.content_store[content_id]["data"] = content_data
        self.content_store[content_id]["updated_at"] = datetime.now(timezone.utc)

        return {
            "content_id": content_id,
            "content_hash": content_hash,
            "block_id": update_block.block_id,
            "signature": update_block.signature,
        }

    def verify_content(self, content_id: str, content_type: str) -> Dict[str, Any]:
        """Verify content integrity.

        Args:
            content_id: Content identifier
            content_type: Type of content

        Returns:
            Dictionary with verification results
        """
        if content_id not in self.content_store:
            return {
                "is_valid": False,
                "error": "Content not found",
            }

        # Get current content
        current_content = self.content_store[content_id]["data"]

        # Verify chain
        chain_verification = self.verifier.verify_chain(content_type, content_id)

        # Check for tampering
        is_tampered, tamper_message = self.verifier.detect_tampering(
            content_id, content_type, current_content
        )

        return {
            "is_valid": chain_verification.is_valid and not is_tampered,
            "chain_valid": chain_verification.is_valid,
            "content_valid": not is_tampered,
            "chain_length": chain_verification.chain_length,
            "issues": chain_verification.issues,
            "tamper_message": tamper_message,
        }

    def get_content_audit_trail(self, content_id: str, content_type: str) -> list:
        """Get audit trail for content.

        Args:
            content_id: Content identifier
            content_type: Type of content

        Returns:
            List of audit trail entries
        """
        return self.verifier.get_audit_trail(content_type, content_id)

    def get_content_history(self, content_id: str, content_type: str) -> list:
        """Get content change history.

        Args:
            content_id: Content identifier
            content_type: Type of content

        Returns:
            List of history entries
        """
        return self.verifier.get_content_history(content_type, content_id)


def main():
    """Demonstration of content integrity verification."""
    print("=" * 70)
    print("Content Integrity Verification System - Demo")
    print("=" * 70)

    # Initialize content manager
    manager = IntegrityAwareContentManager()

    # Create content
    print("\n1. Creating new content...")
    result = manager.create_content(
        content_id="article-001",
        content_type="article",
        content_data={
            "title": "Introduction to Blockchain",
            "body": "Blockchain is a distributed ledger technology...",
            "author": "John Doe",
        },
        user_id="user-123",
    )
    print(f"   Content created with hash: {result['content_hash'][:16]}...")
    print(f"   Block signature: {result['signature'][:16]}...")

    # Update content
    print("\n2. Updating content...")
    result = manager.update_content(
        content_id="article-001",
        content_type="article",
        content_data={
            "title": "Introduction to Blockchain Technology",
            "body": "Blockchain is a revolutionary distributed ledger technology...",
            "author": "John Doe",
        },
        user_id="user-456",
    )
    print(f"   Content updated with new hash: {result['content_hash'][:16]}...")
    print(f"   New block signature: {result['signature'][:16]}...")

    # Update again
    print("\n3. Updating content again...")
    result = manager.update_content(
        content_id="article-001",
        content_type="article",
        content_data={
            "title": "Introduction to Blockchain Technology",
            "body": "Blockchain is a revolutionary distributed ledger technology "
            "that enables secure, transparent, and decentralized transactions.",
            "author": "John Doe",
            "tags": ["blockchain", "technology"],
        },
        user_id="user-123",
    )
    print(f"   Content updated with new hash: {result['content_hash'][:16]}...")

    # Verify content
    print("\n4. Verifying content integrity...")
    verification = manager.verify_content("article-001", "article")
    print(f"   Content valid: {verification['is_valid']}")
    print(f"   Chain valid: {verification['chain_valid']}")
    print(f"   Chain length: {verification['chain_length']} blocks")

    # Get audit trail
    print("\n5. Audit trail:")
    audit_trail = manager.get_content_audit_trail("article-001", "article")
    for i, entry in enumerate(audit_trail, 1):
        print(f"   Block {i}:")
        print(f"     Action: {entry['action']}")
        print(f"     User: {entry['user_id']}")
        print(f"     Timestamp: {entry['timestamp']}")
        print(f"     Hash: {entry['content_hash'][:16]}...")

    # Get history
    print("\n6. Content change history:")
    history = manager.get_content_history("article-001", "article")
    for i, entry in enumerate(history, 1):
        print(f"   Change {i}:")
        print(f"     Action: {entry['action']}")
        print(f"     User: {entry['user_id']}")
        print(f"     Timestamp: {entry['timestamp']}")

    # Demonstrate tampering detection
    print("\n7. Demonstrating tampering detection...")
    print("   Simulating content tampering...")

    # Get verifier and tamper with stored hash
    verifier = get_content_integrity_verifier()
    chain = verifier.get_chain("article", "article-001")
    original_hash = chain[-1].content_hash
    chain[-1].content_hash = "tampered_hash_12345"

    verification = manager.verify_content("article-001", "article")
    print(f"   Content valid after tampering: {verification['is_valid']}")
    print(f"   Tampering detected: {verification['tamper_message']}")

    # Restore original hash
    chain[-1].content_hash = original_hash

    # Export chain
    print("\n8. Exporting integrity chain...")
    chain_export = verifier.export_chain("article", "article-001")
    print(f"   Chain exported ({len(chain_export)} characters)")
    print(f"   Preview: {chain_export[:100]}...")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
