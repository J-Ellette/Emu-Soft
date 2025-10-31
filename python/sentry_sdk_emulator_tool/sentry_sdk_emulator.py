"""
Sentry SDK Emulator - Error tracking and performance monitoring without external dependencies

This module emulates core Sentry SDK functionality for error tracking and monitoring.
It provides a clean API for capturing exceptions, messages, and breadcrumbs.

Features:
- Exception capture with stack traces
- Message logging with levels (debug, info, warning, error, fatal)
- Breadcrumb tracking for context
- Event filtering and sampling
- User context binding
- Tags and extra data
- Release tracking
- Environment configuration
- Before-send hooks
- Scope management
- Transaction/span tracking for performance monitoring

Note: This is a simplified implementation focusing on core functionality.
Advanced features like real-time error reporting to Sentry servers are not included.
"""

import sys
import traceback
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum


class Level(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class Breadcrumb:
    """Breadcrumb for tracking user actions and events"""
    message: str
    level: str = "info"
    category: str = "default"
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    type: str = "default"


@dataclass
class User:
    """User context"""
    id: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    segment: Optional[str] = None


@dataclass
class Event:
    """Event data structure"""
    event_id: str
    timestamp: float
    level: str
    message: Optional[str] = None
    exception: Optional[Dict[str, Any]] = None
    user: Optional[Dict[str, Any]] = None
    tags: Dict[str, str] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    breadcrumbs: List[Dict[str, Any]] = field(default_factory=list)
    release: Optional[str] = None
    environment: Optional[str] = None
    server_name: Optional[str] = None
    transaction: Optional[str] = None


@dataclass
class Transaction:
    """Performance monitoring transaction"""
    name: str
    op: str
    transaction_id: str
    start_timestamp: float
    status: str = "ok"
    tags: Dict[str, str] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    spans: List['Span'] = field(default_factory=list)


@dataclass
class Span:
    """Performance monitoring span"""
    span_id: str
    parent_span_id: Optional[str]
    op: str
    description: str
    start_timestamp: float
    end_timestamp: Optional[float] = None
    status: str = "ok"
    tags: Dict[str, str] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)


# Thread-local storage for scope
_thread_local = threading.local()


def _generate_event_id() -> str:
    """Generate a unique event ID"""
    import uuid
    return str(uuid.uuid4()).replace('-', '')


class Scope:
    """Scope for managing context data"""
    
    def __init__(self):
        self.user: Optional[User] = None
        self.tags: Dict[str, str] = {}
        self.extra: Dict[str, Any] = {}
        self.breadcrumbs: List[Breadcrumb] = []
        self.level: Optional[str] = None
        self.fingerprint: Optional[List[str]] = None
        self.transaction: Optional[str] = None
        self._max_breadcrumbs = 100
    
    def set_user(self, user: Optional[Union[User, Dict[str, Any]]]):
        """Set user context"""
        if user is None:
            self.user = None
        elif isinstance(user, dict):
            self.user = User(**user)
        else:
            self.user = user
    
    def set_tag(self, key: str, value: str):
        """Set a tag"""
        self.tags[key] = value
    
    def set_tags(self, tags: Dict[str, str]):
        """Set multiple tags"""
        self.tags.update(tags)
    
    def set_extra(self, key: str, value: Any):
        """Set extra data"""
        self.extra[key] = value
    
    def set_extras(self, extras: Dict[str, Any]):
        """Set multiple extra data"""
        self.extra.update(extras)
    
    def set_context(self, key: str, value: Dict[str, Any]):
        """Set context data"""
        self.extra[key] = value
    
    def set_level(self, level: Union[Level, str]):
        """Set the level"""
        if isinstance(level, Level):
            self.level = level.value
        else:
            self.level = level
    
    def set_transaction(self, transaction: str):
        """Set transaction name"""
        self.transaction = transaction
    
    def add_breadcrumb(self, crumb: Union[Breadcrumb, Dict[str, Any]]):
        """Add a breadcrumb"""
        if isinstance(crumb, dict):
            crumb = Breadcrumb(**crumb)
        
        self.breadcrumbs.append(crumb)
        
        # Keep only the most recent breadcrumbs
        if len(self.breadcrumbs) > self._max_breadcrumbs:
            self.breadcrumbs = self.breadcrumbs[-self._max_breadcrumbs:]
    
    def clear(self):
        """Clear all scope data"""
        self.user = None
        self.tags = {}
        self.extra = {}
        self.breadcrumbs = []
        self.level = None
        self.fingerprint = None
        self.transaction = None
    
    def clear_breadcrumbs(self):
        """Clear all breadcrumbs"""
        self.breadcrumbs = []


class Hub:
    """Hub for managing scopes and clients"""
    
    def __init__(self, client: Optional['Client'] = None):
        self.client = client
        self._stack = [Scope()]
    
    @property
    def scope(self) -> Scope:
        """Get the current scope"""
        return self._stack[-1]
    
    def push_scope(self) -> Scope:
        """Push a new scope onto the stack"""
        new_scope = Scope()
        # Copy data from parent scope
        if len(self._stack) > 0:
            parent = self._stack[-1]
            new_scope.user = parent.user
            new_scope.tags = parent.tags.copy()
            new_scope.extra = parent.extra.copy()
            new_scope.breadcrumbs = parent.breadcrumbs.copy()
            new_scope.level = parent.level
            new_scope.transaction = parent.transaction
        self._stack.append(new_scope)
        return new_scope
    
    def pop_scope(self):
        """Pop the current scope from the stack"""
        if len(self._stack) > 1:
            self._stack.pop()
    
    def capture_event(self, event: Event) -> str:
        """Capture an event"""
        if self.client:
            return self.client.capture_event(event)
        return event.event_id
    
    def capture_exception(self, error: Optional[Exception] = None) -> str:
        """Capture an exception"""
        if self.client:
            return self.client.capture_exception(error, self.scope)
        return _generate_event_id()
    
    def capture_message(self, message: str, level: Union[Level, str] = Level.INFO) -> str:
        """Capture a message"""
        if self.client:
            return self.client.capture_message(message, level, self.scope)
        return _generate_event_id()


def _get_hub() -> Hub:
    """Get the current hub"""
    if not hasattr(_thread_local, 'hub'):
        _thread_local.hub = Hub()
    return _thread_local.hub


class Client:
    """Sentry client for capturing and processing events"""
    
    def __init__(
        self,
        dsn: Optional[str] = None,
        release: Optional[str] = None,
        environment: Optional[str] = None,
        sample_rate: float = 1.0,
        max_breadcrumbs: int = 100,
        before_send: Optional[Callable[[Event, Dict[str, Any]], Optional[Event]]] = None,
        before_breadcrumb: Optional[Callable[[Breadcrumb, Dict[str, Any]], Optional[Breadcrumb]]] = None,
    ):
        self.dsn = dsn
        self.release = release
        self.environment = environment
        self.sample_rate = sample_rate
        self.max_breadcrumbs = max_breadcrumbs
        self.before_send = before_send
        self.before_breadcrumb = before_breadcrumb
        self.events: List[Event] = []
        self._enabled = True
    
    def capture_event(self, event: Event, scope: Optional[Scope] = None) -> str:
        """Capture an event"""
        if not self._enabled:
            return event.event_id
        
        # Apply sampling
        import random
        if random.random() > self.sample_rate:
            return event.event_id
        
        # Apply scope data
        if scope:
            if scope.user:
                event.user = {
                    'id': scope.user.id,
                    'email': scope.user.email,
                    'username': scope.user.username,
                    'ip_address': scope.user.ip_address,
                }
            event.tags.update(scope.tags)
            event.extra.update(scope.extra)
            event.breadcrumbs = [
                {
                    'message': bc.message,
                    'level': bc.level,
                    'category': bc.category,
                    'timestamp': bc.timestamp,
                    'data': bc.data,
                    'type': bc.type,
                }
                for bc in scope.breadcrumbs
            ]
            if scope.level:
                event.level = scope.level
            if scope.transaction:
                event.transaction = scope.transaction
        
        # Apply before_send hook
        if self.before_send:
            hint = {}
            event = self.before_send(event, hint)
            if event is None:
                return _generate_event_id()
        
        # Store event (in a real implementation, this would send to Sentry)
        self.events.append(event)
        
        return event.event_id
    
    def capture_exception(
        self,
        error: Optional[Exception] = None,
        scope: Optional[Scope] = None,
    ) -> str:
        """Capture an exception"""
        if not self._enabled:
            return _generate_event_id()
        
        # Get exception info
        if error is None:
            exc_info = sys.exc_info()
            error = exc_info[1]
        else:
            exc_info = (type(error), error, error.__traceback__)
        
        if error is None:
            return _generate_event_id()
        
        # Format exception
        exception_data = {
            'type': type(error).__name__,
            'value': str(error),
            'module': type(error).__module__,
            'stacktrace': {
                'frames': self._format_stacktrace(exc_info[2])
            }
        }
        
        # Create event
        event = Event(
            event_id=_generate_event_id(),
            timestamp=time.time(),
            level=Level.ERROR.value,
            exception=exception_data,
            release=self.release,
            environment=self.environment,
        )
        
        return self.capture_event(event, scope)
    
    def capture_message(
        self,
        message: str,
        level: Union[Level, str] = Level.INFO,
        scope: Optional[Scope] = None,
    ) -> str:
        """Capture a message"""
        if not self._enabled:
            return _generate_event_id()
        
        if isinstance(level, Level):
            level = level.value
        
        event = Event(
            event_id=_generate_event_id(),
            timestamp=time.time(),
            level=level,
            message=message,
            release=self.release,
            environment=self.environment,
        )
        
        return self.capture_event(event, scope)
    
    def _format_stacktrace(self, tb) -> List[Dict[str, Any]]:
        """Format a traceback into frames"""
        frames = []
        for frame_summary in traceback.extract_tb(tb):
            frames.append({
                'filename': frame_summary.filename,
                'function': frame_summary.name,
                'lineno': frame_summary.lineno,
                'context_line': frame_summary.line,
            })
        return frames
    
    def flush(self, timeout: Optional[float] = None) -> bool:
        """Flush pending events (no-op in this implementation)"""
        return True
    
    def close(self, timeout: Optional[float] = None) -> bool:
        """Close the client"""
        self._enabled = False
        return self.flush(timeout)


# Global client instance
_client: Optional[Client] = None


def init(
    dsn: Optional[str] = None,
    release: Optional[str] = None,
    environment: Optional[str] = None,
    sample_rate: float = 1.0,
    max_breadcrumbs: int = 100,
    before_send: Optional[Callable[[Event, Dict[str, Any]], Optional[Event]]] = None,
    **options
) -> Client:
    """Initialize the Sentry SDK"""
    global _client
    
    _client = Client(
        dsn=dsn,
        release=release,
        environment=environment,
        sample_rate=sample_rate,
        max_breadcrumbs=max_breadcrumbs,
        before_send=before_send,
    )
    
    hub = _get_hub()
    hub.client = _client
    
    return _client


def capture_exception(error: Optional[Exception] = None) -> str:
    """Capture an exception"""
    hub = _get_hub()
    return hub.capture_exception(error)


def capture_message(message: str, level: Union[Level, str] = Level.INFO) -> str:
    """Capture a message"""
    hub = _get_hub()
    return hub.capture_message(message, level)


def add_breadcrumb(
    message: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """Add a breadcrumb"""
    hub = _get_hub()
    
    crumb = Breadcrumb(
        message=message or "",
        category=category or "default",
        level=level or "info",
        data=data or {},
        **kwargs
    )
    
    if _client and _client.before_breadcrumb:
        hint = {}
        crumb = _client.before_breadcrumb(crumb, hint)
        if crumb is None:
            return
    
    hub.scope.add_breadcrumb(crumb)


def set_user(user: Optional[Union[User, Dict[str, Any]]]) -> None:
    """Set user context"""
    hub = _get_hub()
    hub.scope.set_user(user)


def set_tag(key: str, value: str) -> None:
    """Set a tag"""
    hub = _get_hub()
    hub.scope.set_tag(key, value)


def set_tags(tags: Dict[str, str]) -> None:
    """Set multiple tags"""
    hub = _get_hub()
    hub.scope.set_tags(tags)


def set_extra(key: str, value: Any) -> None:
    """Set extra data"""
    hub = _get_hub()
    hub.scope.set_extra(key, value)


def set_extras(extras: Dict[str, Any]) -> None:
    """Set multiple extra data"""
    hub = _get_hub()
    hub.scope.set_extras(extras)


def set_context(key: str, value: Dict[str, Any]) -> None:
    """Set context data"""
    hub = _get_hub()
    hub.scope.set_context(key, value)


def set_level(level: Union[Level, str]) -> None:
    """Set the level"""
    hub = _get_hub()
    hub.scope.set_level(level)


def set_transaction(transaction: str) -> None:
    """Set transaction name"""
    hub = _get_hub()
    hub.scope.set_transaction(transaction)


@contextmanager
def push_scope():
    """Context manager for pushing a new scope"""
    hub = _get_hub()
    hub.push_scope()
    try:
        yield hub.scope
    finally:
        hub.pop_scope()


@contextmanager
def configure_scope():
    """Context manager for configuring the current scope"""
    hub = _get_hub()
    yield hub.scope


def flush(timeout: Optional[float] = None) -> bool:
    """Flush pending events"""
    if _client:
        return _client.flush(timeout)
    return True


def close(timeout: Optional[float] = None) -> bool:
    """Close the SDK"""
    if _client:
        return _client.close(timeout)
    return True


def start_transaction(
    name: str,
    op: Optional[str] = None,
    **kwargs
) -> Transaction:
    """Start a transaction for performance monitoring"""
    transaction = Transaction(
        name=name,
        op=op or "default",
        transaction_id=_generate_event_id(),
        start_timestamp=time.time(),
    )
    return transaction


def get_client() -> Optional[Client]:
    """Get the current client"""
    return _client


def get_events() -> List[Event]:
    """Get all captured events (for testing)"""
    if _client:
        return _client.events
    return []


def clear_events() -> None:
    """Clear all captured events (for testing)"""
    if _client:
        _client.events = []
    # Also clear the scope
    hub = _get_hub()
    hub.scope.clear()


if __name__ == "__main__":
    # Example usage
    init(
        dsn="https://example@sentry.io/123456",
        release="1.0.0",
        environment="production",
    )
    
    # Set user context
    set_user({
        "id": "12345",
        "email": "user@example.com",
        "username": "john_doe"
    })
    
    # Add tags
    set_tag("server", "web-1")
    set_tag("region", "us-west")
    
    # Add breadcrumbs
    add_breadcrumb(message="User logged in", category="auth")
    add_breadcrumb(message="Navigated to dashboard", category="navigation")
    
    # Capture a message
    capture_message("Application started", level=Level.INFO)
    
    # Capture an exception
    try:
        result = 1 / 0
    except Exception as e:
        capture_exception(e)
    
    # Use scopes
    with push_scope() as scope:
        scope.set_tag("request_id", "abc123")
        scope.set_extra("user_data", {"premium": True})
        capture_message("Request processed")
    
    # Print captured events
    print(f"\nCaptured {len(get_events())} events:")
    for event in get_events():
        print(f"- {event.level}: {event.message or event.exception}")
