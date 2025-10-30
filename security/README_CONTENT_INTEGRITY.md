# Content Integrity Verification System

## Overview

The Content Integrity Verification System provides hash-based checksums and blockchain-style audit trails for critical content. This ensures tamper detection and cryptographic proof of content integrity.

## Emulates

This implementation is inspired by:
- **Blockchain technology**: Linked blocks with cryptographic hashes
- **Git version control**: Content-addressable storage and integrity verification
- **Certificate Transparency**: Append-only audit logs
- **Digital signatures**: Cryptographic proof of authenticity

## Key Features

### 1. Hash-Based Checksums
- **SHA-256 hashing** by default (also supports SHA-512, SHA3-256)
- Content hash generation for any data type (strings, dicts, bytes)
- Metadata inclusion in hash for enhanced security
- Deterministic hashing ensures consistency

### 2. Blockchain-Style Verification Chain
- **Genesis blocks** for new content
- **Linked blocks** with previous block hash references
- **Cryptographic signatures** for each block
- **Immutable chain** once blocks are added
- **Chain validation** to detect tampering

### 3. Tamper Detection System
- **Real-time verification** of content integrity
- **Hash mismatch detection** between stored and current content
- **Chain integrity validation** to detect broken links
- **Signature verification** for each block

### 4. Content Signature Verification
- Each block has a unique signature
- Signatures calculated from block data
- Verification ensures no tampering with block contents

### 5. Audit Trail with Cryptographic Proof
- Complete history of all content changes
- Timestamps for every action
- User tracking for accountability
- Action types: CREATE, UPDATE, DELETE, VERIFY, RESTORE

### 6. Integration with Version Control
- Works alongside existing versioning system
- Provides cryptographic proof for version history
- Export/import chains for backup and migration
- Content history tracking with integrity verification

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  ContentIntegrityVerifier                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Genesis Block          Block 1              Block 2            │
│  ┌──────────┐          ┌──────────┐         ┌──────────┐       │
│  │ Content  │  ┌──────▶│ Content  │  ┌─────▶│ Content  │       │
│  │ Hash     │  │       │ Hash     │  │      │ Hash     │       │
│  │          │  │       │          │  │      │          │       │
│  │ Prev:0000│  │       │ Prev:ABC │  │      │ Prev:XYZ │       │
│  │          │  │       │          │  │      │          │       │
│  │ Sig: ABC │──┘       │ Sig: XYZ │──┘      │ Sig: 123 │       │
│  └──────────┘          └──────────┘         └──────────┘       │
│      ▲                      ▲                     ▲             │
│      │                      │                     │             │
│   CREATE                 UPDATE               UPDATE            │
└─────────────────────────────────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from mycms.security.content_integrity import (
    ContentIntegrityVerifier,
    ContentIntegrityAction,
    get_content_integrity_verifier,
    verify_content_integrity,
)

# Get verifier instance
verifier = get_content_integrity_verifier()

# Create content with integrity tracking
content = "This is my important content"
content_hash = verifier.generate_content_hash(content)

genesis_block = verifier.create_genesis_block(
    content_id="article-123",
    content_type="article",
    content_hash=content_hash,
    user_id="user-456",
    metadata={"title": "Important Article"}
)

# Update content
updated_content = "This is my updated content"
new_hash = verifier.generate_content_hash(updated_content)

update_block = verifier.add_block(
    content_id="article-123",
    content_type="article",
    content_hash=new_hash,
    action=ContentIntegrityAction.UPDATE,
    user_id="user-789"
)

# Verify integrity
result = verifier.verify_chain("article", "article-123")
print(f"Chain valid: {result.is_valid}")
print(f"Chain length: {result.chain_length}")

# Detect tampering
is_tampered, message = verifier.detect_tampering(
    "article-123", "article", updated_content
)
print(f"Content tampered: {is_tampered}")
```

### Convenience Functions

```python
# Quick verification
is_valid, message = verify_content_integrity(
    content_id="article-123",
    content_type="article",
    current_content=updated_content
)
```

### Getting Audit Trail

```python
# Get human-readable audit trail
audit_trail = verifier.get_audit_trail("article", "article-123")

for entry in audit_trail:
    print(f"Action: {entry['action']}")
    print(f"User: {entry['user_id']}")
    print(f"Timestamp: {entry['timestamp']}")
    print(f"Hash: {entry['content_hash']}")
```

### Export/Import Chains

```python
# Export chain for backup
chain_json = verifier.export_chain("article", "article-123")

# Import chain (e.g., after migration)
success = verifier.import_chain(chain_json)
```

### Integration with Content Manager

```python
from examples.content_integrity_demo import IntegrityAwareContentManager

manager = IntegrityAwareContentManager()

# Create content
result = manager.create_content(
    content_id="post-001",
    content_type="post",
    content_data={
        "title": "My Post",
        "body": "Post content"
    },
    user_id="user-123"
)

# Update content
result = manager.update_content(
    content_id="post-001",
    content_type="post",
    content_data={
        "title": "My Updated Post",
        "body": "Updated content"
    },
    user_id="user-123"
)

# Verify content
verification = manager.verify_content("post-001", "post")
print(f"Valid: {verification['is_valid']}")
```

## Data Structures

### ContentHash
Represents a hash of content with metadata.

```python
@dataclass
class ContentHash:
    content_id: str
    content_type: str
    hash_value: str
    algorithm: str
    timestamp: datetime
    metadata: Dict[str, Any]
```

### IntegrityBlock
Represents a block in the verification chain (similar to blockchain block).

```python
@dataclass
class IntegrityBlock:
    block_id: str
    content_id: str
    content_type: str
    content_hash: str
    previous_hash: str  # Links to previous block
    timestamp: datetime
    action: ContentIntegrityAction
    user_id: Optional[str]
    metadata: Dict[str, Any]
    signature: Optional[str]  # Block signature
```

### VerificationResult
Result of integrity verification.

```python
@dataclass
class VerificationResult:
    is_valid: bool
    content_id: str
    content_type: str
    verification_timestamp: datetime
    chain_length: int
    issues: List[str]
    details: Dict[str, Any]
```

## API Reference

### ContentIntegrityVerifier

#### `__init__(hash_algorithm: str = "sha256")`
Initialize the verifier with specified hash algorithm.

#### `generate_content_hash(content, metadata=None) -> str`
Generate hash for content with optional metadata.

#### `create_genesis_block(...) -> IntegrityBlock`
Create the first block (genesis block) for content.

#### `add_block(...) -> IntegrityBlock`
Add a new block to the integrity chain.

#### `verify_chain(content_type, content_id) -> VerificationResult`
Verify integrity of the entire chain.

#### `detect_tampering(content_id, content_type, current_content) -> Tuple[bool, Optional[str]]`
Detect if content has been tampered with.

#### `get_chain(content_type, content_id) -> List[IntegrityBlock]`
Get the integrity chain for content.

#### `get_audit_trail(content_type, content_id) -> List[Dict]`
Get human-readable audit trail.

#### `export_chain(content_type, content_id) -> str`
Export chain as JSON string.

#### `import_chain(chain_json: str) -> bool`
Import chain from JSON string.

#### `get_content_history(content_type, content_id) -> List[Dict]`
Get history of content changes.

## Security Considerations

### Strengths
1. **Cryptographic integrity**: SHA-256 hashing provides strong collision resistance
2. **Chain linkage**: Tampering with any block breaks the chain
3. **Immutability**: Once added, blocks cannot be modified without detection
4. **Audit trail**: Complete history with cryptographic proof
5. **Tamper detection**: Real-time verification of content integrity

### Limitations
1. **In-memory storage**: Current implementation stores chains in memory
2. **No persistence**: Chains are lost on restart (use export/import for persistence)
3. **No distributed consensus**: Single-node verification (not a true blockchain)
4. **No key management**: User IDs are used instead of cryptographic keys

### Production Recommendations
1. **Persistent storage**: Integrate with database for chain persistence
2. **Regular backups**: Export chains regularly
3. **Access control**: Restrict who can create/modify chains
4. **Monitoring**: Alert on verification failures
5. **Key management**: Implement proper cryptographic key management for signatures

## Testing

The implementation includes comprehensive tests covering:
- Hash generation (29 tests total)
- Genesis block creation
- Block addition and chain building
- Chain verification
- Tampering detection
- Export/import functionality
- Content history tracking
- Multiple content chains
- Error handling

Run tests:
```bash
pytest tests/test_content_integrity.py -v
```

## Files

- `content_integrity.py` - Main implementation (600+ lines)
- `test_content_integrity.py` - Test suite (29 tests)
- `content_integrity_demo.py` - Integration example
- `README_CONTENT_INTEGRITY.md` - This documentation

## Implementation Date

October 2025

## Related Systems

- Content versioning (`mycms/content/versioning.py`)
- Audit logging (`mycms/security/audit.py`)
- Enhanced audit logging (`mycms/security/enhanced_audit.py`)

## Future Enhancements

1. **Database persistence**: Store chains in database
2. **Async support**: Make all operations async-compatible
3. **Distributed verification**: Multi-node consensus
4. **Digital signatures**: Use actual cryptographic signatures
5. **Performance optimization**: Caching and indexing
6. **Merkle trees**: For efficient batch verification
7. **Time-stamping service**: External timestamp authority
8. **Smart contracts**: Blockchain integration for public verification
