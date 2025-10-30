"""Real-time template collaboration infrastructure.

This module provides collaborative editing capabilities for templates,
including change tracking, conflict resolution, and real-time sync.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib
from dataclasses import dataclass, field, asdict


@dataclass
class TemplateChange:
    """Represents a change to a template."""

    user_id: str
    timestamp: datetime
    operation: str  # 'insert', 'delete', 'replace'
    position: int
    content: str
    old_content: Optional[str] = None
    change_id: str = field(
        default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert change to dictionary.

        Returns:
            Dictionary representation
        """
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class TemplateVersion:
    """Represents a version of a template."""

    version_id: str
    content: str
    author_id: str
    timestamp: datetime
    changes: List[TemplateChange] = field(default_factory=list)
    parent_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "version_id": self.version_id,
            "content": self.content,
            "author_id": self.author_id,
            "timestamp": self.timestamp.isoformat(),
            "changes": [c.to_dict() for c in self.changes],
            "parent_version": self.parent_version,
        }


class CollaborationSession:
    """Manages a collaborative editing session for a template."""

    def __init__(self, template_id: str, initial_content: str = "") -> None:
        """Initialize a collaboration session.

        Args:
            template_id: Unique identifier for the template
            initial_content: Initial template content
        """
        self.template_id = template_id
        self.content = initial_content
        self.active_users: Dict[str, datetime] = {}
        self.changes: List[TemplateChange] = []
        self.versions: List[TemplateVersion] = []
        self.locks: Dict[int, str] = {}  # position -> user_id
        self._create_initial_version()

    def _create_initial_version(self) -> None:
        """Create the initial version."""
        version = TemplateVersion(
            version_id="v0",
            content=self.content,
            author_id="system",
            timestamp=datetime.now(),
        )
        self.versions.append(version)

    def join_user(self, user_id: str) -> None:
        """Add a user to the session.

        Args:
            user_id: User identifier
        """
        self.active_users[user_id] = datetime.now()

    def leave_user(self, user_id: str) -> None:
        """Remove a user from the session.

        Args:
            user_id: User identifier
        """
        if user_id in self.active_users:
            del self.active_users[user_id]
        # Release any locks held by this user
        self.locks = {pos: uid for pos, uid in self.locks.items() if uid != user_id}

    def apply_change(self, change: TemplateChange) -> Tuple[bool, Optional[str]]:
        """Apply a change to the template.

        Args:
            change: TemplateChange to apply

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if change.operation == "insert":
                self.content = (
                    self.content[: change.position]
                    + change.content
                    + self.content[change.position :]
                )
            elif change.operation == "delete":
                end_pos = change.position + len(change.old_content or "")
                self.content = self.content[: change.position] + self.content[end_pos:]
            elif change.operation == "replace":
                end_pos = change.position + len(change.old_content or "")
                self.content = (
                    self.content[: change.position] + change.content + self.content[end_pos:]
                )
            else:
                return False, f"Unknown operation: {change.operation}"

            self.changes.append(change)
            return True, None

        except Exception as e:
            return False, str(e)

    def create_version(self, author_id: str) -> TemplateVersion:
        """Create a new version snapshot.

        Args:
            author_id: User creating the version

        Returns:
            New TemplateVersion
        """
        version_id = f"v{len(self.versions)}"
        parent_id = self.versions[-1].version_id if self.versions else None

        version = TemplateVersion(
            version_id=version_id,
            content=self.content,
            author_id=author_id,
            timestamp=datetime.now(),
            changes=self.changes.copy(),
            parent_version=parent_id,
        )
        self.versions.append(version)
        return version

    def get_version(self, version_id: str) -> Optional[TemplateVersion]:
        """Get a specific version.

        Args:
            version_id: Version identifier

        Returns:
            TemplateVersion or None if not found
        """
        for version in self.versions:
            if version.version_id == version_id:
                return version
        return None

    def revert_to_version(self, version_id: str) -> Tuple[bool, Optional[str]]:
        """Revert to a previous version.

        Args:
            version_id: Version to revert to

        Returns:
            Tuple of (success, error_message)
        """
        version = self.get_version(version_id)
        if version is None:
            return False, f"Version {version_id} not found"

        self.content = version.content
        return True, None

    def lock_region(self, user_id: str, start: int, end: int) -> bool:
        """Lock a region for editing by a user.

        Args:
            user_id: User requesting the lock
            start: Start position
            end: End position

        Returns:
            True if lock was acquired, False otherwise
        """
        # Check if any position in range is already locked by another user
        for pos in range(start, end):
            if pos in self.locks and self.locks[pos] != user_id:
                return False

        # Lock all positions in range
        for pos in range(start, end):
            self.locks[pos] = user_id

        return True

    def unlock_region(self, user_id: str, start: int, end: int) -> None:
        """Unlock a region.

        Args:
            user_id: User unlocking the region
            start: Start position
            end: End position
        """
        for pos in range(start, end):
            if pos in self.locks and self.locks[pos] == user_id:
                del self.locks[pos]

    def get_active_users(self) -> List[str]:
        """Get list of active users.

        Returns:
            List of user IDs
        """
        return list(self.active_users.keys())

    def get_changes_since(self, timestamp: datetime) -> List[TemplateChange]:
        """Get changes since a specific timestamp.

        Args:
            timestamp: Timestamp to filter from

        Returns:
            List of changes
        """
        return [c for c in self.changes if c.timestamp > timestamp]

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "template_id": self.template_id,
            "content": self.content,
            "active_users": [
                {"user_id": uid, "last_active": ts.isoformat()}
                for uid, ts in self.active_users.items()
            ],
            "changes": [c.to_dict() for c in self.changes],
            "versions": [v.to_dict() for v in self.versions],
        }


class CollaborationManager:
    """Manages multiple collaboration sessions."""

    def __init__(self) -> None:
        """Initialize the collaboration manager."""
        self.sessions: Dict[str, CollaborationSession] = {}

    def create_session(self, template_id: str, initial_content: str = "") -> CollaborationSession:
        """Create a new collaboration session.

        Args:
            template_id: Template identifier
            initial_content: Initial template content

        Returns:
            New CollaborationSession
        """
        session = CollaborationSession(template_id, initial_content)
        self.sessions[template_id] = session
        return session

    def get_session(self, template_id: str) -> Optional[CollaborationSession]:
        """Get an existing session.

        Args:
            template_id: Template identifier

        Returns:
            CollaborationSession or None if not found
        """
        return self.sessions.get(template_id)

    def end_session(self, template_id: str) -> bool:
        """End a collaboration session.

        Args:
            template_id: Template identifier

        Returns:
            True if session was ended, False if not found
        """
        if template_id in self.sessions:
            del self.sessions[template_id]
            return True
        return False

    def list_sessions(self) -> List[str]:
        """List all active session IDs.

        Returns:
            List of template IDs
        """
        return list(self.sessions.keys())


# Global collaboration manager
_global_manager = CollaborationManager()


def get_global_collaboration_manager() -> CollaborationManager:
    """Get the global collaboration manager.

    Returns:
        Global CollaborationManager instance
    """
    return _global_manager
