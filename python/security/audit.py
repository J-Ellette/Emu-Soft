"""
Developed by PowerShield, as an alternative to Django Security
"""

"""Audit logging system for tracking security-relevant events."""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import json
import threading
from functools import wraps


class AuditAction(Enum):
    """Types of actions that can be audited."""

    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # Authorization
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_ASSIGN = "role_assign"
    ROLE_REMOVE = "role_remove"

    # Content Management
    CONTENT_CREATE = "content_create"
    CONTENT_UPDATE = "content_update"
    CONTENT_DELETE = "content_delete"
    CONTENT_PUBLISH = "content_publish"
    CONTENT_UNPUBLISH = "content_unpublish"

    # User Management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"

    # System
    CONFIG_CHANGE = "config_change"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"

    # Security
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCESS_DENIED = "access_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Compliance
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    CONSENT_GRANT = "consent_grant"
    CONSENT_REVOKE = "consent_revoke"


@dataclass
class AuditLog:
    """Represents a single audit log entry."""

    action: AuditAction
    user_id: Optional[str]
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    severity: str = "info"  # info, warning, error, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "action": self.action.value,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "success": self.success,
            "severity": self.severity,
        }

    def to_json(self) -> str:
        """Convert audit log to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Audit logger for tracking security-relevant events."""

    def __init__(self, max_logs: int = 10000) -> None:
        """Initialize audit logger.

        Args:
            max_logs: Maximum number of logs to keep in memory
        """
        self._logs: List[AuditLog] = []
        self._max_logs = max_logs
        self._lock = threading.RLock()

    def log(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        severity: str = "info",
    ) -> AuditLog:
        """Log an audit event.

        Args:
            action: Type of action being audited
            user_id: ID of the user performing the action
            ip_address: IP address of the request
            user_agent: User agent string
            resource_type: Type of resource being accessed
            resource_id: ID of the resource
            details: Additional details about the action
            success: Whether the action was successful
            severity: Severity level (info, warning, error, critical)

        Returns:
            Created AuditLog instance
        """
        log_entry = AuditLog(
            action=action,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            success=success,
            severity=severity,
        )

        with self._lock:
            self._logs.append(log_entry)
            # Keep only the most recent logs
            if len(self._logs) > self._max_logs:
                self._logs = self._logs[-self._max_logs :]

        return log_entry

    def get_logs(
        self,
        action: Optional[AuditAction] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        success: Optional[bool] = None,
        severity: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[AuditLog]:
        """Query audit logs with filters.

        Args:
            action: Filter by action type
            user_id: Filter by user ID
            resource_type: Filter by resource type
            success: Filter by success status
            severity: Filter by severity level
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            limit: Maximum number of logs to return

        Returns:
            List of matching audit logs
        """
        with self._lock:
            logs = list(self._logs)

        # Apply filters
        if action:
            logs = [log for log in logs if log.action == action]
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        if resource_type:
            logs = [log for log in logs if log.resource_type == resource_type]
        if success is not None:
            logs = [log for log in logs if log.success == success]
        if severity:
            logs = [log for log in logs if log.severity == severity]
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]

        # Apply limit
        if limit:
            logs = logs[-limit:]

        return logs

    def get_failed_logins(self, user_id: Optional[str] = None, minutes: int = 60) -> List[AuditLog]:
        """Get failed login attempts.

        Args:
            user_id: Optional user ID to filter by
            minutes: Number of minutes to look back

        Returns:
            List of failed login attempts
        """
        start_time = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=minutes)

        return self.get_logs(
            action=AuditAction.LOGIN_FAILURE,
            user_id=user_id,
            success=False,
            start_time=start_time,
        )

    def get_suspicious_activity(
        self, user_id: Optional[str] = None, hours: int = 24
    ) -> List[AuditLog]:
        """Get suspicious activity logs.

        Args:
            user_id: Optional user ID to filter by
            hours: Number of hours to look back

        Returns:
            List of suspicious activity logs
        """
        start_time = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=hours)

        return self.get_logs(
            action=AuditAction.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            start_time=start_time,
        )

    def export_logs(self, format: str = "json", **filters: Any) -> str:
        """Export audit logs.

        Args:
            format: Export format (json)
            **filters: Filters to apply to logs

        Returns:
            Exported logs as string
        """
        logs = self.get_logs(**filters)

        if format == "json":
            return json.dumps([log.to_dict() for log in logs], indent=2)

        raise ValueError(f"Unsupported export format: {format}")

    def clear_logs(self) -> None:
        """Clear all audit logs."""
        with self._lock:
            self._logs.clear()


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance.

    Returns:
        Global AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_log(
    action: AuditAction,
    resource_type: Optional[str] = None,
    severity: str = "info",
) -> Callable:
    """Decorator to automatically audit function calls.

    Args:
        action: Type of action being audited
        resource_type: Type of resource being accessed
        severity: Severity level

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_audit_logger()
            user_id = kwargs.get("user_id")
            resource_id = kwargs.get("resource_id") or kwargs.get("id")

            try:
                result = await func(*args, **kwargs)
                logger.log(
                    action=action,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None,
                    success=True,
                    severity=severity,
                )
                return result
            except Exception as e:
                logger.log(
                    action=action,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None,
                    details={"error": str(e)},
                    success=False,
                    severity="error",
                )
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_audit_logger()
            user_id = kwargs.get("user_id")
            resource_id = kwargs.get("resource_id") or kwargs.get("id")

            try:
                result = func(*args, **kwargs)
                logger.log(
                    action=action,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None,
                    success=True,
                    severity=severity,
                )
                return result
            except Exception as e:
                logger.log(
                    action=action,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None,
                    details={"error": str(e)},
                    success=False,
                    severity="error",
                )
                raise

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
