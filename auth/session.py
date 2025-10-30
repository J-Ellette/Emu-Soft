"""Session management for user authentication."""

import secrets
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class Session:
    """Represents a user session."""

    def __init__(
        self,
        session_id: str,
        user_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Initialize a session.

        Args:
            session_id: Unique session identifier
            user_id: ID of authenticated user (None if not authenticated)
            data: Session data dictionary
            expires_at: Session expiration time
        """
        self.session_id = session_id
        self.user_id = user_id
        self.data = data or {}
        self.expires_at = expires_at or datetime.utcnow() + timedelta(days=7)

    def is_expired(self) -> bool:
        """Check if session is expired.

        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at

    def set(self, key: str, value: Any) -> None:
        """Set a session value.

        Args:
            key: Session key
            value: Value to store
        """
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a session value.

        Args:
            key: Session key
            default: Default value if key not found

        Returns:
            Session value or default
        """
        return self.data.get(key, default)

    def delete(self, key: str) -> None:
        """Delete a session value.

        Args:
            key: Session key to delete
        """
        self.data.pop(key, None)

    def clear(self) -> None:
        """Clear all session data."""
        self.data.clear()


class SessionManager:
    """Manages user sessions."""

    def __init__(self, session_timeout: int = 7 * 24 * 60 * 60) -> None:
        """Initialize session manager.

        Args:
            session_timeout: Session timeout in seconds (default: 7 days)
        """
        self.session_timeout = session_timeout
        self._sessions: Dict[str, Session] = {}

    def create_session(self, user_id: Optional[int] = None) -> Session:
        """Create a new session.

        Args:
            user_id: Optional user ID for authenticated session

        Returns:
            New Session instance
        """
        session_id = self._generate_session_id()
        expires_at = datetime.utcnow() + timedelta(seconds=self.session_timeout)
        session = Session(session_id, user_id, {}, expires_at)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session instance or None if not found or expired
        """
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            self.delete_session(session_id)
            return None
        return session

    def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: Session ID to delete
        """
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> None:
        """Remove all expired sessions."""
        expired = [sid for sid, session in self._sessions.items() if session.is_expired()]
        for sid in expired:
            self.delete_session(sid)

    def _generate_session_id(self) -> str:
        """Generate a secure random session ID.

        Returns:
            Random session ID string
        """
        return secrets.token_urlsafe(32)


class DatabaseSessionManager(SessionManager):
    """Session manager that stores sessions in database."""

    async def create_session(self, user_id: Optional[int] = None) -> Session:
        """Create a new session and store in database.

        Args:
            user_id: Optional user ID for authenticated session

        Returns:
            New Session instance
        """
        from database.connection import db
        from database.query import QueryBuilder

        session_id = self._generate_session_id()
        expires_at = datetime.utcnow() + timedelta(seconds=self.session_timeout)

        qb = QueryBuilder("sessions")
        qb.insert(
            {
                "session_id": session_id,
                "user_id": user_id,
                "data": json.dumps({}),
                "expires_at": expires_at.isoformat(),
            }
        )
        query, params = qb.build()
        await db.execute(query, *params)

        return Session(session_id, user_id, {}, expires_at)

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session from database.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session instance or None if not found or expired
        """
        from database.connection import db
        from database.query import QueryBuilder

        qb = QueryBuilder("sessions")
        qb.where("session_id", "=", session_id)
        query, params = qb.build()

        row = await db.fetch_one(query, *params)
        if not row:
            return None

        expires_at = datetime.fromisoformat(row["expires_at"])
        session = Session(
            session_id=row["session_id"],
            user_id=row["user_id"],
            data=json.loads(row["data"]),
            expires_at=expires_at,
        )

        if session.is_expired():
            await self.delete_session(session_id)
            return None

        return session

    async def delete_session(self, session_id: str) -> None:
        """Delete a session from database.

        Args:
            session_id: Session ID to delete
        """
        from database.connection import db
        from database.query import QueryBuilder

        qb = QueryBuilder("sessions")
        qb.delete().where("session_id", "=", session_id)
        query, params = qb.build()
        await db.execute(query, *params)

    async def save_session(self, session: Session) -> None:
        """Save session data to database.

        Args:
            session: Session to save
        """
        from database.connection import db
        from database.query import QueryBuilder

        qb = QueryBuilder("sessions")
        qb.update(
            {
                "user_id": session.user_id,
                "data": json.dumps(session.data),
                "expires_at": session.expires_at.isoformat(),
            }
        ).where("session_id", "=", session.session_id)
        query, params = qb.build()
        await db.execute(query, *params)

    async def cleanup_expired(self) -> None:
        """Remove all expired sessions from database."""
        from database.connection import db
        from database.query import QueryBuilder

        qb = QueryBuilder("sessions")
        qb.delete().where("expires_at", "<", datetime.utcnow().isoformat())
        query, params = qb.build()
        await db.execute(query, *params)
