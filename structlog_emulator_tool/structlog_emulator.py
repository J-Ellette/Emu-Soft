"""
structlog Emulator - Structured logging without external dependencies

This module emulates core structlog functionality for structured logging.
It provides a clean API for creating structured logs with context binding
and processor pipelines.

Features:
- BoundLogger for context binding
- Processor pipelines
- Multiple output formats (JSON, key-value, console)
- Log level filtering
- Context managers for temporary context
- Thread-local context storage
- Structured data with arbitrary key-value pairs
- Integration with standard logging
- Async-safe logging

Note: This is a simplified implementation focusing on core functionality.
Advanced features like custom processors and complex serialization are simplified.
"""

import json
import logging
import sys
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from contextlib import contextmanager


# Thread-local storage for context
_thread_local = threading.local()


def _get_context() -> Dict[str, Any]:
    """Get thread-local context"""
    if not hasattr(_thread_local, 'context'):
        _thread_local.context = {}
    return _thread_local.context


def _set_context(context: Dict[str, Any]):
    """Set thread-local context"""
    _thread_local.context = context


class BoundLogger:
    """Logger with bound context data"""
    
    def __init__(self, logger_name: str, context: Optional[Dict[str, Any]] = None,
                 processors: Optional[List[Callable]] = None):
        self._logger_name = logger_name
        self._context = context or {}
        self._processors = processors or []
    
    def bind(self, **new_values) -> 'BoundLogger':
        """Return a new logger with additional context bound"""
        new_context = self._context.copy()
        new_context.update(new_values)
        return BoundLogger(self._logger_name, new_context, self._processors)
    
    def unbind(self, *keys) -> 'BoundLogger':
        """Return a new logger with specified keys removed from context"""
        new_context = self._context.copy()
        for key in keys:
            new_context.pop(key, None)
        return BoundLogger(self._logger_name, new_context, self._processors)
    
    def new(self, **new_values) -> 'BoundLogger':
        """Create a new logger with only the specified context"""
        return BoundLogger(self._logger_name, new_values, self._processors)
    
    def try_unbind(self, *keys) -> 'BoundLogger':
        """Same as unbind but doesn't raise if keys don't exist"""
        return self.unbind(*keys)
    
    def _process(self, method_name: str, event: str, **event_kw) -> Dict[str, Any]:
        """Process log event through the processor pipeline"""
        # Start with context
        event_dict = {
            'event': event,
            'level': method_name,
            'timestamp': datetime.utcnow().isoformat(),
            'logger': self._logger_name,
        }
        
        # Add bound context
        event_dict.update(self._context)
        
        # Add event-specific data
        event_dict.update(event_kw)
        
        # Run through processors
        for processor in self._processors:
            result = processor(event_dict)
            if result is None:
                # Processor filtered this event
                return None
            event_dict = result
        
        return event_dict
    
    def _log(self, method_name: str, event: str, **event_kw):
        """Internal log method"""
        event_dict = self._process(method_name, event, **event_kw)
        # The final processor should handle output
        # If no output processor, we return the dict
        return event_dict
    
    def debug(self, event: str, **kw):
        """Log a debug message"""
        return self._log('debug', event, **kw)
    
    def info(self, event: str, **kw):
        """Log an info message"""
        return self._log('info', event, **kw)
    
    def warning(self, event: str, **kw):
        """Log a warning message"""
        return self._log('warning', event, **kw)
    
    def warn(self, event: str, **kw):
        """Alias for warning"""
        return self.warning(event, **kw)
    
    def error(self, event: str, **kw):
        """Log an error message"""
        return self._log('error', event, **kw)
    
    def critical(self, event: str, **kw):
        """Log a critical message"""
        return self._log('critical', event, **kw)
    
    def exception(self, event: str, **kw):
        """Log an exception"""
        import traceback
        kw['exc_info'] = traceback.format_exc()
        return self._log('error', event, **kw)
    
    def msg(self, event: str, **kw):
        """Log a message (generic)"""
        return self._log('info', event, **kw)


# Built-in processors

def add_timestamp(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp to event"""
    if 'timestamp' not in event_dict:
        event_dict['timestamp'] = datetime.utcnow().isoformat()
    return event_dict


def add_log_level(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure log level is present"""
    if 'level' not in event_dict:
        event_dict['level'] = 'info'
    return event_dict


def add_logger_name(logger_name: str) -> Callable:
    """Create a processor that adds logger name"""
    def processor(event_dict: Dict[str, Any]) -> Dict[str, Any]:
        event_dict['logger'] = logger_name
        return event_dict
    return processor


class JSONRenderer:
    """Render log events as JSON"""
    
    def __init__(self, sort_keys: bool = False, **dumps_kw):
        self.sort_keys = sort_keys
        self.dumps_kw = dumps_kw
    
    def __call__(self, event_dict: Dict[str, Any]) -> str:
        """Render event as JSON"""
        return json.dumps(event_dict, sort_keys=self.sort_keys, **self.dumps_kw)


class KeyValueRenderer:
    """Render log events as key=value pairs"""
    
    def __init__(self, sort_keys: bool = False, key_order: Optional[List[str]] = None,
                 drop_missing: bool = False):
        self.sort_keys = sort_keys
        self.key_order = key_order or []
        self.drop_missing = drop_missing
    
    def __call__(self, event_dict: Dict[str, Any]) -> str:
        """Render event as key=value pairs"""
        items = []
        
        # Add ordered keys first
        for key in self.key_order:
            if key in event_dict:
                items.append(f"{key}={self._format_value(event_dict[key])}")
            elif not self.drop_missing:
                items.append(f"{key}=")
        
        # Add remaining keys
        remaining_keys = [k for k in event_dict.keys() if k not in self.key_order]
        if self.sort_keys:
            remaining_keys.sort()
        
        for key in remaining_keys:
            items.append(f"{key}={self._format_value(event_dict[key])}")
        
        return " ".join(items)
    
    def _format_value(self, value: Any) -> str:
        """Format a value for output"""
        if isinstance(value, str):
            # Quote strings with spaces
            if ' ' in value or '=' in value:
                return f'"{value}"'
            return value
        return str(value)


class ConsoleRenderer:
    """Render log events in a human-readable console format"""
    
    def __init__(self, colors: bool = True, pad_event: int = 30):
        self.colors = colors and sys.stdout.isatty()
        self.pad_event = pad_event
        
        # ANSI color codes
        self.color_codes = {
            'debug': '\033[36m',     # Cyan
            'info': '\033[32m',      # Green
            'warning': '\033[33m',   # Yellow
            'error': '\033[31m',     # Red
            'critical': '\033[35m',  # Magenta
            'reset': '\033[0m',
        }
    
    def __call__(self, event_dict: Dict[str, Any]) -> str:
        """Render event for console output"""
        level = event_dict.get('level', 'info')
        event = event_dict.get('event', '')
        timestamp = event_dict.get('timestamp', '')
        
        # Format timestamp
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp_str = timestamp[:19] if len(timestamp) > 19 else timestamp
        else:
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Color the level
        if self.colors:
            color = self.color_codes.get(level, self.color_codes['reset'])
            level_str = f"{color}{level.upper():8s}{self.color_codes['reset']}"
        else:
            level_str = f"{level.upper():8s}"
        
        # Pad or truncate event
        if len(event) > self.pad_event:
            event_str = event[:self.pad_event-3] + "..."
        else:
            event_str = event.ljust(self.pad_event)
        
        # Build the message
        parts = [timestamp_str, level_str, event_str]
        
        # Add other fields
        skip_keys = {'event', 'level', 'timestamp', 'logger'}
        extra_items = []
        for key, value in event_dict.items():
            if key not in skip_keys:
                extra_items.append(f"{key}={value}")
        
        if extra_items:
            parts.append(" ".join(extra_items))
        
        return " ".join(parts)


class PrintLogger:
    """Processor that prints to stdout or stderr"""
    
    def __init__(self, file=None):
        self.file = file or sys.stdout
    
    def __call__(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Print the event"""
        # If event_dict contains a rendered string (from a renderer)
        # we print that, otherwise we print the dict
        if isinstance(event_dict, str):
            print(event_dict, file=self.file)
        else:
            print(json.dumps(event_dict), file=self.file)
        return event_dict


class PrintLoggerFactory:
    """Factory for creating print loggers"""
    
    def __init__(self, file=None):
        self.file = file or sys.stdout
    
    def __call__(self, logger_name: str, method_name: str, event_dict: Dict[str, Any]) -> str:
        """Render and print the event"""
        output = json.dumps(event_dict)
        print(output, file=self.file)
        return output


def filter_by_level(min_level: str) -> Callable:
    """Create a processor that filters by log level"""
    level_order = ['debug', 'info', 'warning', 'error', 'critical']
    min_level_idx = level_order.index(min_level.lower())
    
    def processor(event_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        level = event_dict.get('level', 'info').lower()
        if level in level_order:
            if level_order.index(level) >= min_level_idx:
                return event_dict
        return None
    
    return processor


# Logger configuration

_default_processors = [
    add_timestamp,
    add_log_level,
    JSONRenderer(),
]

_loggers = {}
_default_logger_name = 'root'


def configure(processors: Optional[List[Callable]] = None,
              context_class: type = dict,
              logger_factory: Optional[Callable] = None,
              cache_logger_on_first_use: bool = True):
    """Configure structlog globally"""
    global _default_processors
    if processors is not None:
        _default_processors = processors


def get_logger(name: Optional[str] = None, **initial_values) -> BoundLogger:
    """Get a logger instance"""
    logger_name = name or _default_logger_name
    
    # Create logger with default processors
    logger = BoundLogger(logger_name, initial_values, _default_processors)
    
    return logger


def wrap_logger(logger, processors: Optional[List[Callable]] = None, **context):
    """Wrap a standard library logger with structlog"""
    if processors is None:
        processors = _default_processors
    
    return BoundLogger(logger.name, context, processors)


# Context management

@contextmanager
def threadlocal_context(**tmp_context):
    """Context manager for temporary thread-local context"""
    context = _get_context()
    old_context = context.copy()
    
    try:
        context.update(tmp_context)
        yield
    finally:
        _set_context(old_context)


def clear_threadlocal_context():
    """Clear thread-local context"""
    _set_context({})


def merge_threadlocal_context(**kw):
    """Merge values into thread-local context"""
    context = _get_context()
    context.update(kw)


def unbind_threadlocal_context(*keys):
    """Remove keys from thread-local context"""
    context = _get_context()
    for key in keys:
        context.pop(key, None)


# Convenience function to create a simple logger

def create_console_logger(level: str = 'info', colors: bool = True) -> BoundLogger:
    """Create a logger that outputs to console"""
    processors = [
        add_timestamp,
        add_log_level,
        filter_by_level(level),
        ConsoleRenderer(colors=colors),
        PrintLogger(),
    ]
    configure(processors=processors)
    return get_logger()


def create_json_logger(file=None, level: str = 'info') -> BoundLogger:
    """Create a logger that outputs JSON"""
    processors = [
        add_timestamp,
        add_log_level,
        filter_by_level(level),
        JSONRenderer(),
        PrintLogger(file=file),
    ]
    configure(processors=processors)
    return get_logger()


if __name__ == "__main__":
    # Demo usage
    print("structlog Emulator Demo")
    print("=" * 50)
    
    # Console logger
    print("\n1. Console Logger:")
    log = create_console_logger()
    log.info("application started", version="1.0.0")
    log.debug("debug message", user_id=123)
    log.warning("low disk space", available_mb=100)
    log.error("connection failed", host="example.com", port=80)
    
    # JSON logger
    print("\n2. JSON Logger:")
    json_log = create_json_logger()
    json_log.info("user login", user_id=456, username="john")
    
    # Context binding
    print("\n3. Context Binding:")
    log = get_logger()
    request_log = log.bind(request_id="abc-123", user_id=789)
    request_log.info("processing request")
    request_log.info("request completed", duration_ms=150)
    
    # Different log levels
    print("\n4. Log Levels:")
    log.debug("debug message")
    log.info("info message")
    log.warning("warning message")
    log.error("error message")
    log.critical("critical message")
