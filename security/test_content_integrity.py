"""Tests for content integrity verification system."""

import pytest
from datetime import datetime, timezone
from security.content_integrity import (
    ContentIntegrityVerifier,
    ContentIntegrityAction,
    IntegrityBlock,
    VerificationResult,
    get_content_integrity_verifier,
    verify_content_integrity,
)


def test_generate_content_hash():
    """Test content hash generation."""
    verifier = ContentIntegrityVerifier()

    # Test string content
    content = "Hello, World!"
    hash1 = verifier.generate_content_hash(content)
    assert hash1 is not None
    assert len(hash1) == 64  # SHA-256 produces 64 hex characters

    # Same content should produce same hash
    hash2 = verifier.generate_content_hash(content)
    assert hash1 == hash2

    # Different content should produce different hash
    hash3 = verifier.generate_content_hash("Different content")
    assert hash1 != hash3


def test_generate_content_hash_with_metadata():
    """Test hash generation with metadata."""
    verifier = ContentIntegrityVerifier()

    content = "Test content"
    metadata = {"author": "John", "version": "1.0"}

    hash1 = verifier.generate_content_hash(content, metadata)
    hash2 = verifier.generate_content_hash(content, metadata)
    assert hash1 == hash2

    # Different metadata should produce different hash
    hash3 = verifier.generate_content_hash(content, {"author": "Jane"})
    assert hash1 != hash3


def test_generate_content_hash_dict():
    """Test hash generation for dictionary content."""
    verifier = ContentIntegrityVerifier()

    content = {"title": "Test", "body": "Content"}
    hash1 = verifier.generate_content_hash(content)
    assert hash1 is not None

    # Same dict should produce same hash
    hash2 = verifier.generate_content_hash({"title": "Test", "body": "Content"})
    assert hash1 == hash2


def test_generate_content_hash_different_algorithms():
    """Test different hash algorithms."""
    verifier_sha256 = ContentIntegrityVerifier(hash_algorithm="sha256")
    verifier_sha512 = ContentIntegrityVerifier(hash_algorithm="sha512")

    content = "Test content"
    hash_256 = verifier_sha256.generate_content_hash(content)
    hash_512 = verifier_sha512.generate_content_hash(content)

    assert len(hash_256) == 64
    assert len(hash_512) == 128
    assert hash_256 != hash_512


def test_create_genesis_block():
    """Test creating genesis block."""
    verifier = ContentIntegrityVerifier()

    content_hash = verifier.generate_content_hash("Initial content")
    genesis = verifier.create_genesis_block(
        content_id="content-1",
        content_type="page",
        content_hash=content_hash,
        user_id="user-1",
        metadata={"title": "Test Page"},
    )

    assert genesis.content_id == "content-1"
    assert genesis.content_type == "page"
    assert genesis.content_hash == content_hash
    assert genesis.previous_hash == "0" * 64
    assert genesis.action == ContentIntegrityAction.CREATE
    assert genesis.user_id == "user-1"
    assert genesis.signature is not None


def test_create_genesis_block_duplicate_error():
    """Test that creating duplicate genesis block raises error."""
    verifier = ContentIntegrityVerifier()

    content_hash = verifier.generate_content_hash("Content")
    verifier.create_genesis_block(
        content_id="content-1", content_type="page", content_hash=content_hash
    )

    # Should raise error for duplicate
    with pytest.raises(ValueError, match="Chain already exists"):
        verifier.create_genesis_block(
            content_id="content-1", content_type="page", content_hash=content_hash
        )


def test_add_block():
    """Test adding blocks to chain."""
    verifier = ContentIntegrityVerifier()

    # Create genesis
    hash1 = verifier.generate_content_hash("Initial content")
    genesis = verifier.create_genesis_block(
        content_id="content-1", content_type="page", content_hash=hash1
    )

    # Add update block
    hash2 = verifier.generate_content_hash("Updated content")
    block2 = verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash2,
        action=ContentIntegrityAction.UPDATE,
        user_id="user-2",
    )

    assert block2.previous_hash == genesis.signature
    assert block2.content_hash == hash2
    assert block2.action == ContentIntegrityAction.UPDATE


def test_add_block_without_genesis():
    """Test that adding block without genesis raises error."""
    verifier = ContentIntegrityVerifier()

    with pytest.raises(ValueError, match="No chain exists"):
        verifier.add_block(
            content_id="nonexistent",
            content_type="page",
            content_hash="somehash",
            action=ContentIntegrityAction.UPDATE,
        )


def test_verify_chain_valid():
    """Test verification of valid chain."""
    verifier = ContentIntegrityVerifier()

    # Create chain with multiple blocks
    hash1 = verifier.generate_content_hash("Version 1")
    verifier.create_genesis_block(content_id="content-1", content_type="page", content_hash=hash1)

    hash2 = verifier.generate_content_hash("Version 2")
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash2,
        action=ContentIntegrityAction.UPDATE,
    )

    hash3 = verifier.generate_content_hash("Version 3")
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash3,
        action=ContentIntegrityAction.UPDATE,
    )

    # Verify chain
    result = verifier.verify_chain("page", "content-1")
    assert result.is_valid is True
    assert result.chain_length == 3
    assert len(result.issues) == 0


def test_verify_chain_no_chain():
    """Test verification when no chain exists."""
    verifier = ContentIntegrityVerifier()

    result = verifier.verify_chain("page", "nonexistent")
    assert result.is_valid is False
    assert "No integrity chain found" in result.issues[0]


def test_verify_chain_tampered_signature():
    """Test verification detects tampered signature."""
    verifier = ContentIntegrityVerifier()

    # Create chain
    hash1 = verifier.generate_content_hash("Content")
    verifier.create_genesis_block(content_id="content-1", content_type="page", content_hash=hash1)

    # Tamper with signature
    chain = verifier.get_chain("page", "content-1")
    chain[0].signature = "tampered_signature"

    # Verify should detect tampering
    result = verifier.verify_chain("page", "content-1")
    assert result.is_valid is False
    assert len(result.issues) > 0
    assert "invalid signature" in result.issues[0].lower()


def test_verify_chain_broken_link():
    """Test verification detects broken chain link."""
    verifier = ContentIntegrityVerifier()

    # Create chain with two blocks
    hash1 = verifier.generate_content_hash("Version 1")
    verifier.create_genesis_block(content_id="content-1", content_type="page", content_hash=hash1)

    hash2 = verifier.generate_content_hash("Version 2")
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash2,
        action=ContentIntegrityAction.UPDATE,
    )

    # Break the link
    chain = verifier.get_chain("page", "content-1")
    chain[1].previous_hash = "broken_link"

    # Verify should detect broken link
    result = verifier.verify_chain("page", "content-1")
    assert result.is_valid is False
    assert any("broken chain link" in issue.lower() for issue in result.issues)


def test_detect_tampering_valid_content():
    """Test tampering detection with valid content."""
    verifier = ContentIntegrityVerifier()

    content = "Original content"
    content_hash = verifier.generate_content_hash(content)
    verifier.create_genesis_block(
        content_id="content-1", content_type="page", content_hash=content_hash
    )

    # Check with same content
    is_tampered, message = verifier.detect_tampering("content-1", "page", content)
    assert is_tampered is False
    assert message is None


def test_detect_tampering_content_mismatch():
    """Test tampering detection with content mismatch."""
    verifier = ContentIntegrityVerifier()

    content = "Original content"
    content_hash = verifier.generate_content_hash(content)
    verifier.create_genesis_block(
        content_id="content-1", content_type="page", content_hash=content_hash
    )

    # Check with different content
    is_tampered, message = verifier.detect_tampering("content-1", "page", "Tampered content")
    assert is_tampered is True
    assert message is not None
    assert "hash mismatch" in message.lower()


def test_detect_tampering_no_chain():
    """Test tampering detection when no chain exists."""
    verifier = ContentIntegrityVerifier()

    is_tampered, message = verifier.detect_tampering("nonexistent", "page", "Some content")
    assert is_tampered is True
    assert "No integrity chain" in message


def test_get_chain():
    """Test getting integrity chain."""
    verifier = ContentIntegrityVerifier()

    # Create chain
    hash1 = verifier.generate_content_hash("V1")
    verifier.create_genesis_block(content_id="content-1", content_type="page", content_hash=hash1)

    hash2 = verifier.generate_content_hash("V2")
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash2,
        action=ContentIntegrityAction.UPDATE,
    )

    # Get chain
    chain = verifier.get_chain("page", "content-1")
    assert len(chain) == 2
    assert chain[0].action == ContentIntegrityAction.CREATE
    assert chain[1].action == ContentIntegrityAction.UPDATE


def test_get_audit_trail():
    """Test getting audit trail."""
    verifier = ContentIntegrityVerifier()

    # Create chain
    hash1 = verifier.generate_content_hash("Content")
    verifier.create_genesis_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash1,
        user_id="user-1",
        metadata={"title": "Test"},
    )

    hash2 = verifier.generate_content_hash("Updated")
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash2,
        action=ContentIntegrityAction.UPDATE,
        user_id="user-2",
    )

    # Get audit trail
    trail = verifier.get_audit_trail("page", "content-1")
    assert len(trail) == 2
    assert trail[0]["action"] == "create"
    assert trail[0]["user_id"] == "user-1"
    assert trail[1]["action"] == "update"
    assert trail[1]["user_id"] == "user-2"


def test_export_import_chain():
    """Test exporting and importing chain."""
    verifier1 = ContentIntegrityVerifier()

    # Create chain
    hash1 = verifier1.generate_content_hash("Content")
    verifier1.create_genesis_block(content_id="content-1", content_type="page", content_hash=hash1)

    hash2 = verifier1.generate_content_hash("Updated")
    verifier1.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash2,
        action=ContentIntegrityAction.UPDATE,
    )

    # Export chain
    chain_json = verifier1.export_chain("page", "content-1")
    assert chain_json is not None

    # Import into new verifier
    verifier2 = ContentIntegrityVerifier()
    success = verifier2.import_chain(chain_json)
    assert success is True

    # Verify imported chain
    chain1 = verifier1.get_chain("page", "content-1")
    chain2 = verifier2.get_chain("page", "content-1")
    assert len(chain1) == len(chain2)
    assert chain1[0].block_id == chain2[0].block_id


def test_import_chain_invalid_json():
    """Test importing invalid JSON."""
    verifier = ContentIntegrityVerifier()

    success = verifier.import_chain("invalid json")
    assert success is False


def test_get_content_history():
    """Test getting content history."""
    verifier = ContentIntegrityVerifier()

    # Create chain with multiple updates
    hash1 = verifier.generate_content_hash("V1")
    verifier.create_genesis_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash1,
        user_id="user-1",
    )

    hash2 = verifier.generate_content_hash("V2")
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash2,
        action=ContentIntegrityAction.UPDATE,
        user_id="user-2",
    )

    hash3 = verifier.generate_content_hash("V3")
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash3,
        action=ContentIntegrityAction.UPDATE,
        user_id="user-1",
    )

    # Get history
    history = verifier.get_content_history("page", "content-1")
    assert len(history) == 3
    assert history[0]["action"] == "create"
    assert history[1]["action"] == "update"
    assert history[2]["action"] == "update"
    assert all("timestamp" in entry for entry in history)
    assert all("content_hash" in entry for entry in history)


def test_block_calculate_hash():
    """Test block hash calculation."""
    block = IntegrityBlock(
        block_id="block-1",
        content_id="content-1",
        content_type="page",
        content_hash="abc123",
        previous_hash="prev123",
        timestamp=datetime.now(timezone.utc),
        action=ContentIntegrityAction.CREATE,
        user_id="user-1",
    )

    hash1 = block.calculate_block_hash()
    assert hash1 is not None
    assert len(hash1) == 64

    # Same block should produce same hash
    hash2 = block.calculate_block_hash()
    assert hash1 == hash2


def test_block_to_dict():
    """Test block conversion to dictionary."""
    timestamp = datetime.now(timezone.utc)
    block = IntegrityBlock(
        block_id="block-1",
        content_id="content-1",
        content_type="page",
        content_hash="abc123",
        previous_hash="prev123",
        timestamp=timestamp,
        action=ContentIntegrityAction.CREATE,
        user_id="user-1",
        metadata={"key": "value"},
        signature="sig123",
    )

    block_dict = block.to_dict()
    assert block_dict["block_id"] == "block-1"
    assert block_dict["content_id"] == "content-1"
    assert block_dict["action"] == "create"
    assert block_dict["signature"] == "sig123"
    assert block_dict["metadata"] == {"key": "value"}


def test_verification_result_to_dict():
    """Test verification result conversion to dictionary."""
    timestamp = datetime.now(timezone.utc)
    result = VerificationResult(
        is_valid=True,
        content_id="content-1",
        content_type="page",
        verification_timestamp=timestamp,
        chain_length=5,
        issues=[],
        details={"key": "value"},
    )

    result_dict = result.to_dict()
    assert result_dict["is_valid"] is True
    assert result_dict["content_id"] == "content-1"
    assert result_dict["chain_length"] == 5
    assert result_dict["issues"] == []


def test_get_content_integrity_verifier_singleton():
    """Test that global verifier is singleton."""
    verifier1 = get_content_integrity_verifier()
    verifier2 = get_content_integrity_verifier()
    assert verifier1 is verifier2


def test_verify_content_integrity_convenience():
    """Test convenience function for verification."""
    verifier = get_content_integrity_verifier()

    content = "Test content"
    content_hash = verifier.generate_content_hash(content)
    verifier.create_genesis_block(
        content_id="test-1", content_type="page", content_hash=content_hash
    )

    # Valid content
    is_valid, message = verify_content_integrity("test-1", "page", content)
    assert is_valid is True

    # Invalid content
    is_valid, message = verify_content_integrity("test-1", "page", "Different")
    assert is_valid is False
    assert message is not None


def test_chain_with_delete_action():
    """Test chain with delete action."""
    verifier = ContentIntegrityVerifier()

    hash1 = verifier.generate_content_hash("Content")
    verifier.create_genesis_block(content_id="content-1", content_type="page", content_hash=hash1)

    # Add delete block
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash="",
        action=ContentIntegrityAction.DELETE,
        user_id="user-1",
    )

    chain = verifier.get_chain("page", "content-1")
    assert chain[-1].action == ContentIntegrityAction.DELETE


def test_chain_with_restore_action():
    """Test chain with restore action."""
    verifier = ContentIntegrityVerifier()

    hash1 = verifier.generate_content_hash("Content")
    verifier.create_genesis_block(content_id="content-1", content_type="page", content_hash=hash1)

    # Delete
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash="",
        action=ContentIntegrityAction.DELETE,
    )

    # Restore
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash1,
        action=ContentIntegrityAction.RESTORE,
    )

    chain = verifier.get_chain("page", "content-1")
    assert chain[-1].action == ContentIntegrityAction.RESTORE
    assert len(chain) == 3


def test_multiple_content_chains():
    """Test managing multiple content chains."""
    verifier = ContentIntegrityVerifier()

    # Create multiple chains
    for i in range(3):
        content_hash = verifier.generate_content_hash(f"Content {i}")
        verifier.create_genesis_block(
            content_id=f"content-{i}", content_type="page", content_hash=content_hash
        )

    # Verify all chains exist
    for i in range(3):
        chain = verifier.get_chain("page", f"content-{i}")
        assert len(chain) == 1

    # Verify they are independent
    assert len(verifier.chains) == 3


def test_verification_result_details():
    """Test verification result includes detailed information."""
    verifier = ContentIntegrityVerifier()

    hash1 = verifier.generate_content_hash("V1")
    verifier.create_genesis_block(
        content_id="content-1", content_type="page", content_hash=hash1, user_id="user-1"
    )

    hash2 = verifier.generate_content_hash("V2")
    verifier.add_block(
        content_id="content-1",
        content_type="page",
        content_hash=hash2,
        action=ContentIntegrityAction.UPDATE,
        user_id="user-2",
    )

    result = verifier.verify_chain("page", "content-1")
    assert "first_block_timestamp" in result.details
    assert "last_block_timestamp" in result.details
    assert "actions" in result.details
    assert "users" in result.details
    assert set(result.details["users"]) == {"user-1", "user-2"}
