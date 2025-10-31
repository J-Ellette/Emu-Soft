"""
dramatiq Emulator - Task Queue Framework for Python

This module emulates the dramatiq library, which is a fast and reliable distributed
task processing library for Python. It provides a simple API for defining background
tasks and processing them asynchronously.

Key Features:
- Actor-based task definitions
- Message brokers (in-memory for emulation)
- Task scheduling and delayed execution
- Retry mechanisms
- Middleware support
- Result backends


Developed by PowerShield
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta
from collections import deque
from functools import wraps
import time
import threading
import queue
import uuid


class DramatiqError(Exception):
    """Base exception for dramatiq errors."""
    pass


class ConnectionError(DramatiqError):
    """Raised when there's a connection error with the broker."""
    pass


class RateLimitExceeded(DramatiqError):
    """Raised when rate limit is exceeded."""
    pass


class ActorNotFound(DramatiqError):
    """Raised when an actor is not found."""
    pass


# Message class
class Message:
    """Represents a task message."""
    
    def __init__(
        self,
        queue_name: str,
        actor_name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None
    ):
        self.queue_name = queue_name
        self.actor_name = actor_name
        self.args = args
        self.kwargs = kwargs or {}
        self.options = options or {}
        self.message_id = message_id or str(uuid.uuid4())
        self.message_timestamp = int(time.time() * 1000)
    
    def asdict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'queue_name': self.queue_name,
            'actor_name': self.actor_name,
            'args': self.args,
            'kwargs': self.kwargs,
            'options': self.options,
            'message_id': self.message_id,
            'message_timestamp': self.message_timestamp
        }


# Actor class
class Actor:
    """Represents an actor (task)."""
    
    def __init__(
        self,
        fn: Callable,
        actor_name: Optional[str] = None,
        queue_name: str = 'default',
        priority: int = 0,
        max_retries: int = 20,
        min_backoff: int = 15000,
        max_backoff: int = 86400000,
        time_limit: Optional[int] = None,
        broker: Optional['Broker'] = None
    ):
        self.fn = fn
        self.actor_name = actor_name or fn.__name__
        self.queue_name = queue_name
        self.priority = priority
        self.max_retries = max_retries
        self.min_backoff = min_backoff
        self.max_backoff = max_backoff
        self.time_limit = time_limit
        self.broker = broker
        self.options = {
            'max_retries': max_retries,
            'min_backoff': min_backoff,
            'max_backoff': max_backoff,
            'time_limit': time_limit
        }
    
    def __call__(self, *args, **kwargs) -> Any:
        """Execute the actor function directly."""
        return self.fn(*args, **kwargs)
    
    def send(self, *args, **kwargs) -> Message:
        """Send a message to execute this actor asynchronously."""
        message = Message(
            queue_name=self.queue_name,
            actor_name=self.actor_name,
            args=args,
            kwargs=kwargs,
            options=self.options
        )
        
        if self.broker:
            self.broker.enqueue(message)
        
        return message
    
    def send_with_options(
        self,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        delay: Optional[int] = None,
        **options
    ) -> Message:
        """Send a message with additional options."""
        message_options = self.options.copy()
        message_options.update(options)
        
        if delay:
            message_options['eta'] = int(time.time() * 1000) + delay
        
        message = Message(
            queue_name=self.queue_name,
            actor_name=self.actor_name,
            args=args,
            kwargs=kwargs or {},
            options=message_options
        )
        
        if self.broker:
            self.broker.enqueue(message, delay=delay)
        
        return message


# Result backend
class ResultBackend:
    """Stores task results."""
    
    def __init__(self):
        self._results: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def store(self, message_id: str, result: Any, ttl: int = 600000):
        """Store a result."""
        with self._lock:
            self._results[message_id] = {
                'result': result,
                'stored_at': time.time(),
                'ttl': ttl
            }
    
    def get(self, message_id: str) -> Optional[Any]:
        """Get a result."""
        with self._lock:
            result_data = self._results.get(message_id)
            if not result_data:
                return None
            
            # Check if expired
            if time.time() - result_data['stored_at'] > result_data['ttl'] / 1000:
                del self._results[message_id]
                return None
            
            return result_data['result']
    
    def delete(self, message_id: str):
        """Delete a result."""
        with self._lock:
            self._results.pop(message_id, None)


# Broker class
class Broker:
    """Message broker for handling task distribution."""
    
    def __init__(self):
        self._queues: Dict[str, deque] = {}
        self._delayed_messages: List[tuple] = []  # (eta, message)
        self._actors: Dict[str, Actor] = {}
        self._result_backend: Optional[ResultBackend] = None
        # Use RLock (Reentrant Lock) to prevent deadlocks when methods like 
        # enqueue() call declare_queue() while already holding the lock.
        # This allows the same thread to acquire the lock multiple times.
        self._lock = threading.RLock()
    
    def declare_queue(self, queue_name: str):
        """Declare a queue."""
        with self._lock:
            if queue_name not in self._queues:
                self._queues[queue_name] = deque()
    
    def enqueue(self, message: Message, delay: Optional[int] = None):
        """Enqueue a message."""
        with self._lock:
            self.declare_queue(message.queue_name)
            
            if delay:
                eta = int(time.time() * 1000) + delay
                self._delayed_messages.append((eta, message))
            else:
                self._queues[message.queue_name].append(message)
    
    def dequeue(self, queue_name: str, timeout: Optional[int] = None) -> Optional[Message]:
        """Dequeue a message."""
        with self._lock:
            # Check delayed messages
            current_time = int(time.time() * 1000)
            ready_messages = []
            remaining_delayed = []
            
            for eta, msg in self._delayed_messages:
                if eta <= current_time:
                    ready_messages.append(msg)
                else:
                    remaining_delayed.append((eta, msg))
            
            self._delayed_messages = remaining_delayed
            
            # Add ready messages to queue
            for msg in ready_messages:
                if msg.queue_name == queue_name:
                    self._queues[queue_name].append(msg)
            
            # Dequeue from queue
            if queue_name in self._queues and self._queues[queue_name]:
                return self._queues[queue_name].popleft()
        
        return None
    
    def declare_actor(self, actor: Actor):
        """Register an actor with the broker."""
        with self._lock:
            self._actors[actor.actor_name] = actor
            actor.broker = self
    
    def get_actor(self, actor_name: str) -> Optional[Actor]:
        """Get an actor by name."""
        with self._lock:
            return self._actors.get(actor_name)
    
    def set_result_backend(self, backend: ResultBackend):
        """Set the result backend."""
        self._result_backend = backend
    
    def get_result_backend(self) -> Optional[ResultBackend]:
        """Get the result backend."""
        return self._result_backend


# Worker class
class Worker:
    """Worker that processes messages from queues."""
    
    def __init__(self, broker: Broker, queues: Optional[List[str]] = None):
        self.broker = broker
        self.queues = queues or ['default']
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the worker."""
        self._running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self):
        """Stop the worker."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
    
    def _run(self):
        """Worker run loop."""
        while self._running:
            processed = False
            
            for queue_name in self.queues:
                message = self.broker.dequeue(queue_name)
                
                if message:
                    self._process_message(message)
                    processed = True
            
            if not processed:
                time.sleep(0.1)  # Sleep briefly if no messages
    
    def _process_message(self, message: Message):
        """Process a single message."""
        try:
            actor = self.broker.get_actor(message.actor_name)
            
            if not actor:
                raise ActorNotFound(f"Actor '{message.actor_name}' not found")
            
            # Execute the actor
            result = actor(*message.args, **message.kwargs)
            
            # Store result if backend is available
            result_backend = self.broker.get_result_backend()
            if result_backend:
                result_backend.store(message.message_id, result)
        
        except Exception as e:
            # In a real implementation, this would handle retries
            print(f"Error processing message {message.message_id}: {e}")


# Global broker instance
_default_broker: Optional[Broker] = None


def get_broker() -> Broker:
    """Get the default broker."""
    global _default_broker
    if _default_broker is None:
        _default_broker = Broker()
    return _default_broker


def set_broker(broker: Broker):
    """Set the default broker."""
    global _default_broker
    _default_broker = broker


# Decorator for defining actors
def actor(
    fn: Optional[Callable] = None,
    *,
    actor_name: Optional[str] = None,
    queue_name: str = 'default',
    priority: int = 0,
    max_retries: int = 20,
    min_backoff: int = 15000,
    max_backoff: int = 86400000,
    time_limit: Optional[int] = None,
    broker: Optional[Broker] = None
) -> Union[Callable, Actor]:
    """Decorator to define an actor."""
    
    def decorator(func: Callable) -> Actor:
        actor_obj = Actor(
            fn=func,
            actor_name=actor_name,
            queue_name=queue_name,
            priority=priority,
            max_retries=max_retries,
            min_backoff=min_backoff,
            max_backoff=max_backoff,
            time_limit=time_limit,
            broker=broker or get_broker()
        )
        
        # Register with broker
        actor_obj.broker.declare_actor(actor_obj)
        
        return actor_obj
    
    if fn is None:
        # Called with arguments: @actor(queue_name='custom')
        return decorator
    else:
        # Called without arguments: @actor
        return decorator(fn)


# Pipeline support
class Pipeline:
    """Pipeline for chaining actors."""
    
    def __init__(self):
        self.messages: List[Message] = []
    
    def __or__(self, other: Union[Message, 'Pipeline']) -> 'Pipeline':
        """Chain messages using | operator."""
        if isinstance(other, Message):
            self.messages.append(other)
        elif isinstance(other, Pipeline):
            self.messages.extend(other.messages)
        return self
    
    def run(self):
        """Execute the pipeline."""
        for message in self.messages:
            broker = get_broker()
            broker.enqueue(message)


# Group support
class group:
    """Execute multiple actors in parallel."""
    
    def __init__(self, *messages: Message):
        self.messages = list(messages)
    
    def run(self) -> List[Message]:
        """Execute all messages in the group."""
        broker = get_broker()
        for message in self.messages:
            broker.enqueue(message)
        return self.messages


# Results support
class Results:
    """Helper for retrieving task results."""
    
    def __init__(self, backend: ResultBackend):
        self.backend = backend
    
    def get(self, message_id: str, block: bool = False, timeout: Optional[int] = None) -> Any:
        """Get a result by message ID."""
        if not block:
            return self.backend.get(message_id)
        
        # Blocking wait
        start_time = time.time()
        while True:
            result = self.backend.get(message_id)
            if result is not None:
                return result
            
            if timeout and (time.time() - start_time) > timeout / 1000:
                raise TimeoutError(f"Timeout waiting for result {message_id}")
            
            time.sleep(0.1)


# Export all public APIs
__all__ = [
    'actor',
    'Actor',
    'Message',
    'Broker',
    'Worker',
    'Pipeline',
    'group',
    'ResultBackend',
    'Results',
    'get_broker',
    'set_broker',
    'DramatiqError',
    'ConnectionError',
    'RateLimitExceeded',
    'ActorNotFound',
]
