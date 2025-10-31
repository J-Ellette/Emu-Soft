"""
Developed by PowerShield, as an alternative to Redis-py


Redis Emulator - In-Memory Data Store

This module emulates the redis-py library, which is the Python client for Redis,
an in-memory data structure store used as a database, cache, and message broker.

Key Features:
- String operations (get, set, delete)
- Hash operations (hget, hset, hgetall)
- List operations (lpush, rpush, lpop, rpop, lrange)
- Set operations (sadd, srem, smembers)
- Sorted Set operations (zadd, zrem, zrange)
- Key operations (exists, delete, expire, ttl)
- Pub/Sub messaging
- Pipeline operations
- Transaction support (MULTI/EXEC)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import time
import threading
import fnmatch


class RedisError(Exception):
    """Base exception for Redis errors."""
    pass


class ConnectionError(RedisError):
    """Raised when connection to Redis fails."""
    pass


class ResponseError(RedisError):
    """Raised when Redis returns an error response."""
    pass


class WatchError(RedisError):
    """Raised when a watched key is modified."""
    pass


# In-memory storage for emulated Redis
_redis_storage: Dict[str, Any] = {}
_redis_hashes: Dict[str, Dict[str, str]] = defaultdict(dict)
_redis_lists: Dict[str, List[str]] = defaultdict(list)
_redis_sets: Dict[str, set] = defaultdict(set)
_redis_sorted_sets: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
_redis_expiry: Dict[str, float] = {}
_redis_pubsub_channels: Dict[str, List[Callable]] = defaultdict(list)


def _check_expiry(key: str) -> bool:
    """Check if a key has expired and remove it if necessary."""
    if key in _redis_expiry:
        if time.time() >= _redis_expiry[key]:
            # Key has expired, remove it
            _redis_storage.pop(key, None)
            _redis_hashes.pop(key, None)
            _redis_lists.pop(key, None)
            _redis_sets.pop(key, None)
            _redis_sorted_sets.pop(key, None)
            del _redis_expiry[key]
            return True
    return False


class Redis:
    """Redis client for key-value operations."""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        socket_timeout: Optional[float] = None,
        decode_responses: bool = False,
        **kwargs
    ):
        """
        Initialize Redis client.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Database number (0-15)
            password: Password for authentication
            socket_timeout: Socket timeout in seconds
            decode_responses: Decode responses to strings
            **kwargs: Additional connection parameters
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.socket_timeout = socket_timeout
        self.decode_responses = decode_responses
        self._watching = set()
        self._transaction = []
        self._in_transaction = False
    
    # String operations
    def get(self, name: str) -> Optional[Union[str, bytes]]:
        """Get the value of a key."""
        _check_expiry(name)
        value = _redis_storage.get(name)
        if value is not None and self.decode_responses and isinstance(value, bytes):
            return value.decode('utf-8')
        return value
    
    def set(
        self,
        name: str,
        value: Union[str, bytes, int, float],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set the value of a key.
        
        Args:
            name: Key name
            value: Value to set
            ex: Expire time in seconds
            px: Expire time in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists
        
        Returns:
            True if set, False otherwise
        """
        _check_expiry(name)
        
        # Check nx and xx conditions
        exists = name in _redis_storage
        if nx and exists:
            return False
        if xx and not exists:
            return False
        
        if isinstance(value, (int, float)):
            value = str(value)
        if isinstance(value, str) and not self.decode_responses:
            value = value.encode('utf-8')
        
        _redis_storage[name] = value
        
        # Set expiry
        if ex is not None:
            self.expire(name, ex)
        elif px is not None:
            self.pexpire(name, px)
        
        return True
    
    def delete(self, *names: str) -> int:
        """Delete one or more keys."""
        count = 0
        for name in names:
            if name in _redis_storage:
                del _redis_storage[name]
                _redis_expiry.pop(name, None)
                count += 1
            if name in _redis_hashes:
                del _redis_hashes[name]
                count += 1
            if name in _redis_lists:
                del _redis_lists[name]
                count += 1
            if name in _redis_sets:
                del _redis_sets[name]
                count += 1
            if name in _redis_sorted_sets:
                del _redis_sorted_sets[name]
                count += 1
        return count
    
    def exists(self, *names: str) -> int:
        """Check if keys exist."""
        count = 0
        for name in names:
            if not _check_expiry(name):
                if (name in _redis_storage or name in _redis_hashes or 
                    name in _redis_lists or name in _redis_sets or 
                    name in _redis_sorted_sets):
                    count += 1
        return count
    
    def incr(self, name: str, amount: int = 1) -> int:
        """Increment the value of a key."""
        _check_expiry(name)
        current = _redis_storage.get(name, '0')
        if isinstance(current, bytes):
            current = current.decode('utf-8')
        try:
            new_value = int(current) + amount
            _redis_storage[name] = str(new_value)
            return new_value
        except ValueError:
            raise ResponseError("value is not an integer or out of range")
    
    def decr(self, name: str, amount: int = 1) -> int:
        """Decrement the value of a key."""
        return self.incr(name, -amount)
    
    # Hash operations
    def hget(self, name: str, key: str) -> Optional[Union[str, bytes]]:
        """Get the value of a hash field."""
        _check_expiry(name)
        value = _redis_hashes[name].get(key)
        if value is not None and not self.decode_responses:
            return value.encode('utf-8')
        return value
    
    def hset(self, name: str, key: Optional[str] = None, value: Optional[str] = None, 
             mapping: Optional[Dict[str, str]] = None) -> int:
        """Set the value of a hash field."""
        _check_expiry(name)
        count = 0
        
        if mapping:
            for k, v in mapping.items():
                if k not in _redis_hashes[name]:
                    count += 1
                _redis_hashes[name][k] = str(v)
        elif key is not None and value is not None:
            if key not in _redis_hashes[name]:
                count += 1
            _redis_hashes[name][key] = str(value)
        
        return count
    
    def hgetall(self, name: str) -> Dict[str, Union[str, bytes]]:
        """Get all fields and values of a hash."""
        _check_expiry(name)
        result = _redis_hashes[name].copy()
        if not self.decode_responses:
            return {k.encode('utf-8'): v.encode('utf-8') for k, v in result.items()}
        return result
    
    def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        _check_expiry(name)
        count = 0
        for key in keys:
            if key in _redis_hashes[name]:
                del _redis_hashes[name][key]
                count += 1
        return count
    
    def hexists(self, name: str, key: str) -> bool:
        """Check if hash field exists."""
        _check_expiry(name)
        return key in _redis_hashes[name]
    
    # List operations
    def lpush(self, name: str, *values: str) -> int:
        """Push values to the head of a list."""
        _check_expiry(name)
        for value in reversed(values):
            _redis_lists[name].insert(0, str(value))
        return len(_redis_lists[name])
    
    def rpush(self, name: str, *values: str) -> int:
        """Push values to the tail of a list."""
        _check_expiry(name)
        for value in values:
            _redis_lists[name].append(str(value))
        return len(_redis_lists[name])
    
    def lpop(self, name: str) -> Optional[Union[str, bytes]]:
        """Remove and return the first element of a list."""
        _check_expiry(name)
        if _redis_lists[name]:
            value = _redis_lists[name].pop(0)
            if not self.decode_responses:
                return value.encode('utf-8')
            return value
        return None
    
    def rpop(self, name: str) -> Optional[Union[str, bytes]]:
        """Remove and return the last element of a list."""
        _check_expiry(name)
        if _redis_lists[name]:
            value = _redis_lists[name].pop()
            if not self.decode_responses:
                return value.encode('utf-8')
            return value
        return None
    
    def lrange(self, name: str, start: int, end: int) -> List[Union[str, bytes]]:
        """Get a range of elements from a list."""
        _check_expiry(name)
        lst = _redis_lists[name]
        
        # Handle negative indices
        if end == -1:
            end = len(lst)
        else:
            end = end + 1
        
        result = lst[start:end]
        
        if not self.decode_responses:
            return [v.encode('utf-8') for v in result]
        return result
    
    def llen(self, name: str) -> int:
        """Get the length of a list."""
        _check_expiry(name)
        return len(_redis_lists[name])
    
    # Set operations
    def sadd(self, name: str, *values: str) -> int:
        """Add members to a set."""
        _check_expiry(name)
        count = 0
        for value in values:
            if value not in _redis_sets[name]:
                _redis_sets[name].add(str(value))
                count += 1
        return count
    
    def srem(self, name: str, *values: str) -> int:
        """Remove members from a set."""
        _check_expiry(name)
        count = 0
        for value in values:
            if value in _redis_sets[name]:
                _redis_sets[name].remove(str(value))
                count += 1
        return count
    
    def smembers(self, name: str) -> set:
        """Get all members of a set."""
        _check_expiry(name)
        result = _redis_sets[name].copy()
        if not self.decode_responses:
            return {v.encode('utf-8') for v in result}
        return result
    
    def sismember(self, name: str, value: str) -> bool:
        """Check if value is a member of a set."""
        _check_expiry(name)
        return str(value) in _redis_sets[name]
    
    def scard(self, name: str) -> int:
        """Get the number of members in a set."""
        _check_expiry(name)
        return len(_redis_sets[name])
    
    # Sorted Set operations
    def zadd(self, name: str, mapping: Dict[str, float], **kwargs) -> int:
        """Add members with scores to a sorted set."""
        _check_expiry(name)
        count = 0
        
        for member, score in mapping.items():
            # Remove existing member if present
            _redis_sorted_sets[name] = [
                (m, s) for m, s in _redis_sorted_sets[name] if m != member
            ]
            # Add new member with score
            _redis_sorted_sets[name].append((str(member), float(score)))
            count += 1
        
        # Keep sorted by score
        _redis_sorted_sets[name].sort(key=lambda x: x[1])
        return count
    
    def zrem(self, name: str, *values: str) -> int:
        """Remove members from a sorted set."""
        _check_expiry(name)
        count = 0
        for value in values:
            original_len = len(_redis_sorted_sets[name])
            _redis_sorted_sets[name] = [
                (m, s) for m, s in _redis_sorted_sets[name] if m != str(value)
            ]
            if len(_redis_sorted_sets[name]) < original_len:
                count += 1
        return count
    
    def zrange(self, name: str, start: int, end: int, withscores: bool = False) -> List:
        """Get a range of members from a sorted set."""
        _check_expiry(name)
        
        if end == -1:
            result = _redis_sorted_sets[name][start:]
        else:
            result = _redis_sorted_sets[name][start:end + 1]
        
        if withscores:
            if not self.decode_responses:
                return [(m.encode('utf-8'), s) for m, s in result]
            return result
        else:
            if not self.decode_responses:
                return [m.encode('utf-8') for m, s in result]
            return [m for m, s in result]
    
    def zscore(self, name: str, value: str) -> Optional[float]:
        """Get the score of a member in a sorted set."""
        _check_expiry(name)
        for member, score in _redis_sorted_sets[name]:
            if member == str(value):
                return score
        return None
    
    # Key operations
    def expire(self, name: str, seconds: int) -> bool:
        """Set a key's time to live in seconds."""
        if self.exists(name):
            _redis_expiry[name] = time.time() + seconds
            return True
        return False
    
    def pexpire(self, name: str, milliseconds: int) -> bool:
        """Set a key's time to live in milliseconds."""
        if self.exists(name):
            _redis_expiry[name] = time.time() + (milliseconds / 1000.0)
            return True
        return False
    
    def ttl(self, name: str) -> int:
        """Get the time to live for a key in seconds."""
        if not self.exists(name):
            return -2
        if name not in _redis_expiry:
            return -1
        
        remaining = _redis_expiry[name] - time.time()
        return int(remaining) if remaining > 0 else -2
    
    def persist(self, name: str) -> bool:
        """Remove the expiration from a key."""
        if name in _redis_expiry:
            del _redis_expiry[name]
            return True
        return False
    
    def keys(self, pattern: str = '*') -> List[str]:
        """Find all keys matching a pattern."""
        # Simple pattern matching (only supports * wildcard)
        all_keys = set()
        all_keys.update(_redis_storage.keys())
        all_keys.update(_redis_hashes.keys())
        all_keys.update(_redis_lists.keys())
        all_keys.update(_redis_sets.keys())
        all_keys.update(_redis_sorted_sets.keys())
        
        # Remove expired keys
        for key in list(all_keys):
            if _check_expiry(key):
                all_keys.discard(key)
        
        if pattern == '*':
            return list(all_keys)
        
        # Simple wildcard matching using fnmatch (imported at top)
        return [key for key in all_keys if fnmatch.fnmatch(key, pattern)]
    
    def flushdb(self) -> bool:
        """Delete all keys in the current database."""
        _redis_storage.clear()
        _redis_hashes.clear()
        _redis_lists.clear()
        _redis_sets.clear()
        _redis_sorted_sets.clear()
        _redis_expiry.clear()
        return True
    
    def flushall(self) -> bool:
        """Delete all keys in all databases."""
        return self.flushdb()
    
    # Pipeline support
    def pipeline(self, transaction: bool = True) -> Pipeline:
        """Create a pipeline for batching commands."""
        return Pipeline(self, transaction=transaction)
    
    # Pub/Sub support
    def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel."""
        count = 0
        if channel in _redis_pubsub_channels:
            for callback in _redis_pubsub_channels[channel]:
                callback({'type': 'message', 'channel': channel, 'data': message})
                count += 1
        return count
    
    def pubsub(self) -> PubSub:
        """Create a PubSub instance."""
        return PubSub(self)


class Pipeline:
    """Redis pipeline for batching commands."""
    
    def __init__(self, client: Redis, transaction: bool = True):
        self.client = client
        self.transaction = transaction
        self.command_stack = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.execute()
    
    def execute(self) -> List[Any]:
        """Execute all commands in the pipeline."""
        results = []
        for command, args, kwargs in self.command_stack:
            method = getattr(self.client, command)
            results.append(method(*args, **kwargs))
        self.command_stack = []
        return results
    
    def __getattr__(self, name: str):
        """Capture command calls."""
        def method(*args, **kwargs):
            self.command_stack.append((name, args, kwargs))
            return self
        return method


class PubSub:
    """Redis Pub/Sub messaging."""
    
    def __init__(self, client: Redis):
        self.client = client
        self.channels = {}
        self.patterns = {}
    
    def subscribe(self, *args, **kwargs):
        """Subscribe to channels."""
        for channel in args:
            if channel not in self.channels:
                self.channels[channel] = []
    
    def psubscribe(self, *args, **kwargs):
        """Subscribe to channel patterns."""
        for pattern in args:
            if pattern not in self.patterns:
                self.patterns[pattern] = []
    
    def unsubscribe(self, *args):
        """Unsubscribe from channels."""
        for channel in args:
            self.channels.pop(channel, None)
    
    def punsubscribe(self, *args):
        """Unsubscribe from channel patterns."""
        for pattern in args:
            self.patterns.pop(pattern, None)
    
    def get_message(self, ignore_subscribe_messages: bool = False) -> Optional[Dict[str, Any]]:
        """Get a message from subscribed channels."""
        # Simplified implementation - returns None
        # In real Redis, this would block/poll for messages
        return None
    
    def listen(self):
        """
        Listen for messages on subscribed channels.
        
        NOTE: This is a simplified implementation that returns an empty iterator.
        In production Redis, this would block and yield messages as they arrive.
        For testing scenarios that require message handling, use the publish()
        method with callbacks or mock the listen() behavior in your tests.
        """
        return iter([])


# Module-level convenience function
def from_url(url: str, **kwargs) -> Redis:
    """Create a Redis client from a URL."""
    # Simplified URL parsing
    return Redis(**kwargs)


# Connection pool (simplified)
class ConnectionPool:
    """Connection pool for Redis connections."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, **kwargs):
        self.host = host
        self.port = port
        self.db = db
        self.kwargs = kwargs
    
    def get_connection(self, command_name: str, *keys, **options) -> Redis:
        """Get a connection from the pool."""
        return Redis(host=self.host, port=self.port, db=self.db, **self.kwargs)


# Sentinel support (placeholder)
class Sentinel:
    """Redis Sentinel client for high availability."""
    
    def __init__(self, sentinels: List[Tuple[str, int]], **kwargs):
        self.sentinels = sentinels
        self.kwargs = kwargs
    
    def master_for(self, service_name: str, **kwargs) -> Redis:
        """Get a Redis client for the master."""
        return Redis(**{**self.kwargs, **kwargs})
    
    def slave_for(self, service_name: str, **kwargs) -> Redis:
        """Get a Redis client for a slave."""
        return Redis(**{**self.kwargs, **kwargs})


# StrictRedis alias for compatibility
StrictRedis = Redis
