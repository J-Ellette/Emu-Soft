"""Enhanced audit logging with persistent storage and detailed tracking.

Extends the base audit system with database persistence, advanced querying,
and detailed login attempt tracking.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import json

from security.audit import AuditAction, AuditLogger


@dataclass
class LoginAttempt:
    """Detailed login attempt record."""

    username: str
    success: bool
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    failure_reason: Optional[str] = None
    user_id: Optional[int] = None
    location: Optional[str] = None
    device_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "username": self.username,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "failure_reason": self.failure_reason,
            "user_id": self.user_id,
            "location": self.location,
            "device_type": self.device_type,
        }


@dataclass
class SystemChange:
    """Detailed system change record."""

    change_type: str  # config, user, content, permission, etc.
    action: str  # create, update, delete
    user_id: Optional[int]
    timestamp: datetime
    target_type: str
    target_id: Optional[str] = None
    changes: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    rollback_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_type": self.change_type,
            "action": self.action,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "target_type": self.target_type,
            "target_id": self.target_id,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "rollback_data": self.rollback_data,
        }


class EnhancedAuditLogger(AuditLogger):
    """Enhanced audit logger with persistent storage and detailed tracking."""

    def __init__(self, max_logs: int = 10000) -> None:
        """Initialize enhanced audit logger.

        Args:
            max_logs: Maximum number of logs to keep in memory
        """
        super().__init__(max_logs)
        self._login_attempts: List[LoginAttempt] = []
        self._system_changes: List[SystemChange] = []
        self._max_login_attempts = max_logs
        self._max_system_changes = max_logs

    def log_login_attempt(
        self,
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
        user_id: Optional[int] = None,
        location: Optional[str] = None,
    ) -> LoginAttempt:
        """Log a detailed login attempt.

        Args:
            username: Username attempting login
            success: Whether login was successful
            ip_address: IP address of request
            user_agent: User agent string
            failure_reason: Reason for failure if applicable
            user_id: User ID if successful
            location: Geographic location if available

        Returns:
            LoginAttempt record
        """
        # Parse user agent for device type
        device_type = self._parse_device_type(user_agent)

        attempt = LoginAttempt(
            username=username,
            success=success,
            timestamp=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=failure_reason,
            user_id=user_id,
            location=location,
            device_type=device_type,
        )

        self._login_attempts.append(attempt)
        if len(self._login_attempts) > self._max_login_attempts:
            self._login_attempts = self._login_attempts[-self._max_login_attempts :]

        # Also log to base audit system
        action = AuditAction.LOGIN_SUCCESS if success else AuditAction.LOGIN_FAILURE
        self.log(
            action=action,
            user_id=str(user_id) if user_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "username": username,
                "failure_reason": failure_reason,
                "location": location,
                "device_type": device_type,
            },
            success=success,
            severity="info" if success else "warning",
        )

        return attempt

    def log_system_change(
        self,
        change_type: str,
        action: str,
        target_type: str,
        user_id: Optional[int] = None,
        target_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        rollback_data: Optional[Dict[str, Any]] = None,
    ) -> SystemChange:
        """Log a detailed system change.

        Args:
            change_type: Type of change (config, user, content, etc.)
            action: Action performed (create, update, delete)
            target_type: Type of target resource
            user_id: User ID performing change
            target_id: ID of target resource
            changes: Dictionary of changes made
            ip_address: IP address of request
            rollback_data: Data needed to rollback change

        Returns:
            SystemChange record
        """
        change = SystemChange(
            change_type=change_type,
            action=action,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            target_type=target_type,
            target_id=target_id,
            changes=changes or {},
            ip_address=ip_address,
            rollback_data=rollback_data,
        )

        self._system_changes.append(change)
        if len(self._system_changes) > self._max_system_changes:
            self._system_changes = self._system_changes[-self._max_system_changes :]

        # Also log to base audit system
        audit_action = self._map_to_audit_action(change_type, action)
        self.log(
            action=audit_action,
            user_id=str(user_id) if user_id else None,
            ip_address=ip_address,
            resource_type=target_type,
            resource_id=target_id,
            details={
                "change_type": change_type,
                "changes": changes,
                "has_rollback_data": rollback_data is not None,
            },
            success=True,
            severity="info",
        )

        return change

    def get_login_attempts(
        self,
        username: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[LoginAttempt]:
        """Query login attempts with filters.

        Args:
            username: Filter by username
            success: Filter by success status
            start_time: Filter after this time
            end_time: Filter before this time
            ip_address: Filter by IP address
            limit: Maximum number of results

        Returns:
            List of matching login attempts
        """
        attempts = list(self._login_attempts)

        if username:
            attempts = [a for a in attempts if a.username == username]
        if success is not None:
            attempts = [a for a in attempts if a.success == success]
        if start_time:
            attempts = [a for a in attempts if a.timestamp >= start_time]
        if end_time:
            attempts = [a for a in attempts if a.timestamp <= end_time]
        if ip_address:
            attempts = [a for a in attempts if a.ip_address == ip_address]

        if limit:
            attempts = attempts[-limit:]

        return attempts

    def get_system_changes(
        self,
        change_type: Optional[str] = None,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[SystemChange]:
        """Query system changes with filters.

        Args:
            change_type: Filter by change type
            action: Filter by action
            target_type: Filter by target type
            user_id: Filter by user ID
            start_time: Filter after this time
            end_time: Filter before this time
            limit: Maximum number of results

        Returns:
            List of matching system changes
        """
        changes = list(self._system_changes)

        if change_type:
            changes = [c for c in changes if c.change_type == change_type]
        if action:
            changes = [c for c in changes if c.action == action]
        if target_type:
            changes = [c for c in changes if c.target_type == target_type]
        if user_id:
            changes = [c for c in changes if c.user_id == user_id]
        if start_time:
            changes = [c for c in changes if c.timestamp >= start_time]
        if end_time:
            changes = [c for c in changes if c.timestamp <= end_time]

        if limit:
            changes = changes[-limit:]

        return changes

    def get_failed_login_stats(
        self, username: Optional[str] = None, hours: int = 24
    ) -> Dict[str, Any]:
        """Get statistics on failed login attempts.

        Args:
            username: Optional username to filter by
            hours: Number of hours to look back

        Returns:
            Dictionary with statistics
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        failed_attempts = self.get_login_attempts(
            username=username, success=False, start_time=start_time
        )

        # Count by IP address
        ip_counts: Dict[str, int] = {}
        for attempt in failed_attempts:
            if attempt.ip_address:
                ip_counts[attempt.ip_address] = ip_counts.get(attempt.ip_address, 0) + 1

        # Count by username
        username_counts: Dict[str, int] = {}
        for attempt in failed_attempts:
            username_counts[attempt.username] = username_counts.get(attempt.username, 0) + 1

        return {
            "total_failed": len(failed_attempts),
            "unique_ips": len(ip_counts),
            "unique_usernames": len(username_counts),
            "top_ips": sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_usernames": sorted(username_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "time_range_hours": hours,
        }

    def detect_brute_force(self, username: str, threshold: int = 5, minutes: int = 15) -> bool:
        """Detect potential brute force attack.

        Args:
            username: Username to check
            threshold: Number of failed attempts to trigger detection
            minutes: Time window in minutes

        Returns:
            True if potential brute force detected
        """
        start_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        failed_attempts = self.get_login_attempts(
            username=username, success=False, start_time=start_time
        )

        return len(failed_attempts) >= threshold

    def export_login_attempts(self, format: str = "json", **filters: Any) -> str:
        """Export login attempts.

        Args:
            format: Export format (json)
            **filters: Filters to apply

        Returns:
            Exported data as string
        """
        attempts = self.get_login_attempts(**filters)

        if format == "json":
            return json.dumps([a.to_dict() for a in attempts], indent=2)

        raise ValueError(f"Unsupported export format: {format}")

    def export_system_changes(self, format: str = "json", **filters: Any) -> str:
        """Export system changes.

        Args:
            format: Export format (json)
            **filters: Filters to apply

        Returns:
            Exported data as string
        """
        changes = self.get_system_changes(**filters)

        if format == "json":
            return json.dumps([c.to_dict() for c in changes], indent=2)

        raise ValueError(f"Unsupported export format: {format}")

    def _parse_device_type(self, user_agent: Optional[str]) -> Optional[str]:
        """Parse device type from user agent.

        Args:
            user_agent: User agent string

        Returns:
            Device type or None
        """
        if not user_agent:
            return None

        user_agent_lower = user_agent.lower()

        # Check for bots first
        if "bot" in user_agent_lower or "crawler" in user_agent_lower:
            return "bot"
        # Check for tablets
        elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
            return "tablet"
        # Check for mobile devices
        elif (
            "mobile" in user_agent_lower
            or "android" in user_agent_lower
            or "iphone" in user_agent_lower
            or "ipod" in user_agent_lower
        ):
            return "mobile"
        else:
            return "desktop"

    def _map_to_audit_action(self, change_type: str, action: str) -> AuditAction:
        """Map change type and action to AuditAction enum.

        Args:
            change_type: Type of change
            action: Action performed

        Returns:
            AuditAction enum value
        """
        mapping = {
            ("user", "create"): AuditAction.USER_CREATE,
            ("user", "update"): AuditAction.USER_UPDATE,
            ("user", "delete"): AuditAction.USER_DELETE,
            ("content", "create"): AuditAction.CONTENT_CREATE,
            ("content", "update"): AuditAction.CONTENT_UPDATE,
            ("content", "delete"): AuditAction.CONTENT_DELETE,
            ("config", "update"): AuditAction.CONFIG_CHANGE,
        }

        key = (change_type, action)
        return mapping.get(key, AuditAction.CONFIG_CHANGE)


# Global enhanced audit logger instance
_enhanced_audit_logger: Optional[EnhancedAuditLogger] = None


def get_enhanced_audit_logger() -> EnhancedAuditLogger:
    """Get the global enhanced audit logger instance.

    Returns:
        Global EnhancedAuditLogger instance
    """
    global _enhanced_audit_logger
    if _enhanced_audit_logger is None:
        _enhanced_audit_logger = EnhancedAuditLogger()
    return _enhanced_audit_logger
