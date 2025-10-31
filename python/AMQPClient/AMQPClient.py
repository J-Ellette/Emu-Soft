"""
Developed by PowerShield, as an alternative to pika


Pika Emulator - RabbitMQ Client Library

This module emulates the pika library functionality for RabbitMQ messaging.
Provides AMQP 0-9-1 protocol concepts without requiring RabbitMQ server.

Key Features:
- Connection and channel management
- Queue, exchange, and binding operations
- Message publishing and consuming
- Message acknowledgment
- Quality of Service (QoS) settings
- Connection parameters and credentials
- Multiple exchange types (direct, topic, fanout, headers)
- Durable queues and persistent messages
"""

import json
import queue as queue_module
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse


# Connection Parameters and Credentials
@dataclass
class PlainCredentials:
    """Plain username/password credentials for authentication."""
    
    username: str
    password: str
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


class ConnectionParameters:
    """Connection parameters for RabbitMQ connection."""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5672,
        virtual_host: str = '/',
        credentials: Optional[PlainCredentials] = None,
        heartbeat: int = 0,
        blocked_connection_timeout: Optional[int] = None,
        socket_timeout: Optional[float] = None,
        connection_attempts: int = 1,
        retry_delay: float = 2.0,
    ):
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.credentials = credentials or PlainCredentials('guest', 'guest')
        self.heartbeat = heartbeat
        self.blocked_connection_timeout = blocked_connection_timeout
        self.socket_timeout = socket_timeout
        self.connection_attempts = connection_attempts
        self.retry_delay = retry_delay


class URLParameters(ConnectionParameters):
    """Parse connection parameters from AMQP URL."""
    
    def __init__(self, url: str):
        parsed = urlparse(url)
        
        # Parse credentials
        username = parsed.username or 'guest'
        password = parsed.password or 'guest'
        credentials = PlainCredentials(username, password)
        
        # Parse host and port
        host = parsed.hostname or 'localhost'
        port = parsed.port or 5672
        
        # Parse virtual host (remove leading /)
        virtual_host = parsed.path[1:] if parsed.path else '/'
        
        # Parse query parameters
        query_params = parse_qs(parsed.query)
        heartbeat = int(query_params.get('heartbeat', [0])[0])
        
        super().__init__(
            host=host,
            port=port,
            virtual_host=virtual_host,
            credentials=credentials,
            heartbeat=heartbeat,
        )


# Exceptions
class AMQPError(Exception):
    """Base exception for AMQP errors."""
    pass


class AMQPConnectionError(AMQPError):
    """Connection-related errors."""
    pass


class AMQPChannelError(AMQPError):
    """Channel-related errors."""
    pass


class ChannelClosedByBroker(AMQPChannelError):
    """Channel was closed by broker."""
    
    def __init__(self, reply_code: int, reply_text: str):
        self.reply_code = reply_code
        self.reply_text = reply_text
        super().__init__(f"{reply_code}: {reply_text}")


class UnroutableError(AMQPError):
    """Message was returned as unroutable."""
    pass


# Properties
class BasicProperties:
    """Message properties for AMQP basic class."""
    
    def __init__(
        self,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        delivery_mode: Optional[int] = None,  # 1 = non-persistent, 2 = persistent
        priority: Optional[int] = None,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        expiration: Optional[str] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[int] = None,
        type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ):
        self.content_type = content_type
        self.content_encoding = content_encoding
        self.headers = headers or {}
        self.delivery_mode = delivery_mode
        self.priority = priority
        self.correlation_id = correlation_id
        self.reply_to = reply_to
        self.expiration = expiration
        self.message_id = message_id
        self.timestamp = timestamp or int(time.time())
        self.type = type
        self.user_id = user_id
        self.app_id = app_id


# Message delivery
@dataclass
class Deliver:
    """Delivery information for consumed messages."""
    
    delivery_tag: int
    exchange: str
    routing_key: str
    redelivered: bool = False


# Internal message structure
@dataclass
class Message:
    """Internal message representation."""
    
    exchange: str
    routing_key: str
    body: bytes
    properties: BasicProperties
    delivery_tag: int
    redelivered: bool = False


# Channel
class Channel:
    """AMQP Channel for operations."""
    
    def __init__(self, connection: 'BlockingConnection', channel_number: int):
        self._connection = connection
        self._channel_number = channel_number
        self._closed = False
        self._consumers: Dict[str, Tuple[Callable, bool, bool, Dict]] = {}  # tag -> (callback, no_ack, exclusive, arguments)
        self._delivery_tag_counter = 0
        self._prefetch_count = 0
        self._unacked_messages: Dict[int, Message] = {}
        
    def _check_open(self):
        """Verify channel is still open."""
        if self._closed:
            raise AMQPChannelError("Channel is closed")
        if self._connection._closed:
            raise AMQPConnectionError("Connection is closed")
    
    def exchange_declare(
        self,
        exchange: str,
        exchange_type: str = 'direct',
        passive: bool = False,
        durable: bool = False,
        auto_delete: bool = False,
        internal: bool = False,
        arguments: Optional[Dict] = None,
    ):
        """Declare an exchange."""
        self._check_open()
        
        if passive:
            # Just verify exchange exists
            if exchange not in self._connection._exchanges:
                raise ChannelClosedByBroker(404, f"NOT_FOUND - no exchange '{exchange}'")
        else:
            self._connection._exchanges[exchange] = {
                'type': exchange_type,
                'durable': durable,
                'auto_delete': auto_delete,
                'internal': internal,
                'arguments': arguments or {},
            }
    
    def queue_declare(
        self,
        queue: str = '',
        passive: bool = False,
        durable: bool = False,
        exclusive: bool = False,
        auto_delete: bool = False,
        arguments: Optional[Dict] = None,
    ):
        """Declare a queue."""
        self._check_open()
        
        # Auto-generate queue name if empty
        if not queue:
            queue = f"amq.gen-{id(self)}-{len(self._connection._queues)}"
        
        if passive:
            # Just verify queue exists
            if queue not in self._connection._queues:
                raise ChannelClosedByBroker(404, f"NOT_FOUND - no queue '{queue}'")
        else:
            if queue not in self._connection._queues:
                self._connection._queues[queue] = {
                    'messages': queue_module.Queue(),
                    'durable': durable,
                    'exclusive': exclusive,
                    'auto_delete': auto_delete,
                    'arguments': arguments or {},
                }
        
        # Return method frame with queue name, message count, and consumer count
        class Method:
            def __init__(self, queue_name):
                self.queue = queue_name
                self.message_count = 0
                self.consumer_count = 0
        
        return Method(queue)
    
    def queue_bind(
        self,
        queue: str,
        exchange: str,
        routing_key: str = '',
        arguments: Optional[Dict] = None,
    ):
        """Bind a queue to an exchange."""
        self._check_open()
        
        if exchange not in self._connection._exchanges:
            raise ChannelClosedByBroker(404, f"NOT_FOUND - no exchange '{exchange}'")
        if queue not in self._connection._queues:
            raise ChannelClosedByBroker(404, f"NOT_FOUND - no queue '{queue}'")
        
        binding_key = (exchange, routing_key)
        if binding_key not in self._connection._bindings:
            self._connection._bindings[binding_key] = []
        
        if queue not in self._connection._bindings[binding_key]:
            self._connection._bindings[binding_key].append(queue)
    
    def queue_unbind(
        self,
        queue: str,
        exchange: str,
        routing_key: str = '',
        arguments: Optional[Dict] = None,
    ):
        """Unbind a queue from an exchange."""
        self._check_open()
        
        binding_key = (exchange, routing_key)
        if binding_key in self._connection._bindings:
            if queue in self._connection._bindings[binding_key]:
                self._connection._bindings[binding_key].remove(queue)
    
    def queue_purge(self, queue: str):
        """Remove all messages from a queue."""
        self._check_open()
        
        if queue not in self._connection._queues:
            raise ChannelClosedByBroker(404, f"NOT_FOUND - no queue '{queue}'")
        
        q = self._connection._queues[queue]['messages']
        count = 0
        while not q.empty():
            try:
                q.get_nowait()
                count += 1
            except queue_module.Empty:
                break
        
        class Method:
            def __init__(self, msg_count):
                self.message_count = msg_count
        
        return Method(count)
    
    def queue_delete(self, queue: str, if_unused: bool = False, if_empty: bool = False):
        """Delete a queue."""
        self._check_open()
        
        if queue not in self._connection._queues:
            raise ChannelClosedByBroker(404, f"NOT_FOUND - no queue '{queue}'")
        
        q_info = self._connection._queues[queue]
        
        if if_unused and queue in [tag for tags in self._consumers.values() for tag in [tags]]:
            raise ChannelClosedByBroker(406, f"PRECONDITION_FAILED - queue '{queue}' in use")
        
        if if_empty and not q_info['messages'].empty():
            raise ChannelClosedByBroker(406, f"PRECONDITION_FAILED - queue '{queue}' not empty")
        
        del self._connection._queues[queue]
    
    def basic_publish(
        self,
        exchange: str,
        routing_key: str,
        body: bytes,
        properties: Optional[BasicProperties] = None,
        mandatory: bool = False,
    ):
        """Publish a message."""
        self._check_open()
        
        if exchange and exchange not in self._connection._exchanges:
            raise ChannelClosedByBroker(404, f"NOT_FOUND - no exchange '{exchange}'")
        
        properties = properties or BasicProperties()
        
        # Route message to queues
        routed_queues = self._route_message(exchange, routing_key)
        
        if mandatory and not routed_queues:
            raise UnroutableError(f"Message to exchange '{exchange}' with routing key '{routing_key}' is unroutable")
        
        # Deliver to all matched queues
        for queue_name in routed_queues:
            if queue_name in self._connection._queues:
                self._delivery_tag_counter += 1
                msg = Message(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=body,
                    properties=properties,
                    delivery_tag=self._delivery_tag_counter,
                )
                self._connection._queues[queue_name]['messages'].put(msg)
    
    def _route_message(self, exchange: str, routing_key: str) -> List[str]:
        """Route message based on exchange type and routing key."""
        if not exchange:
            # Default exchange - direct routing to queue name
            return [routing_key] if routing_key in self._connection._queues else []
        
        exchange_info = self._connection._exchanges.get(exchange, {})
        exchange_type = exchange_info.get('type', 'direct')
        
        matched_queues = []
        
        if exchange_type == 'direct':
            # Direct: exact routing key match
            binding_key = (exchange, routing_key)
            matched_queues = self._connection._bindings.get(binding_key, [])
        
        elif exchange_type == 'fanout':
            # Fanout: ignore routing key, deliver to all bound queues
            for (exch, _), queues in self._connection._bindings.items():
                if exch == exchange:
                    matched_queues.extend(queues)
        
        elif exchange_type == 'topic':
            # Topic: pattern matching with * and #
            for (exch, pattern), queues in self._connection._bindings.items():
                if exch == exchange and self._match_topic(routing_key, pattern):
                    matched_queues.extend(queues)
        
        elif exchange_type == 'headers':
            # Headers: match based on message headers (simplified)
            # For this emulator, we'll treat it like fanout
            for (exch, _), queues in self._connection._bindings.items():
                if exch == exchange:
                    matched_queues.extend(queues)
        
        return list(set(matched_queues))  # Remove duplicates
    
    def _match_topic(self, routing_key: str, pattern: str) -> bool:
        """Match routing key against topic pattern."""
        routing_parts = routing_key.split('.')
        pattern_parts = pattern.split('.')
        
        r_idx = 0
        p_idx = 0
        
        while r_idx < len(routing_parts) and p_idx < len(pattern_parts):
            if pattern_parts[p_idx] == '#':
                # # matches zero or more words
                if p_idx == len(pattern_parts) - 1:
                    return True  # # at end matches everything remaining
                # Try to match next pattern part
                p_idx += 1
                while r_idx < len(routing_parts):
                    if pattern_parts[p_idx] == routing_parts[r_idx] or pattern_parts[p_idx] == '*':
                        break
                    r_idx += 1
            elif pattern_parts[p_idx] == '*' or pattern_parts[p_idx] == routing_parts[r_idx]:
                # * matches exactly one word, or exact match
                r_idx += 1
                p_idx += 1
            else:
                return False
        
        # Both should be exhausted for a match
        return r_idx == len(routing_parts) and p_idx == len(pattern_parts)
    
    def basic_consume(
        self,
        queue: str,
        on_message_callback: Callable,
        auto_ack: bool = False,
        exclusive: bool = False,
        consumer_tag: Optional[str] = None,
        arguments: Optional[Dict] = None,
    ):
        """Start a consumer."""
        self._check_open()
        
        if queue not in self._connection._queues:
            raise ChannelClosedByBroker(404, f"NOT_FOUND - no queue '{queue}'")
        
        # Generate consumer tag if not provided
        if not consumer_tag:
            consumer_tag = f"ctag-{len(self._consumers)}"
        
        self._consumers[consumer_tag] = (on_message_callback, auto_ack, exclusive, arguments or {})
        
        return consumer_tag
    
    def basic_cancel(self, consumer_tag: str):
        """Cancel a consumer."""
        self._check_open()
        
        if consumer_tag in self._consumers:
            del self._consumers[consumer_tag]
    
    def basic_get(self, queue: str, auto_ack: bool = False):
        """Get a single message from a queue."""
        self._check_open()
        
        if queue not in self._connection._queues:
            raise ChannelClosedByBroker(404, f"NOT_FOUND - no queue '{queue}'")
        
        q = self._connection._queues[queue]['messages']
        
        try:
            msg = q.get_nowait()
            
            if not auto_ack:
                self._unacked_messages[msg.delivery_tag] = msg
            
            # Return (method, properties, body) tuple
            method = Deliver(
                delivery_tag=msg.delivery_tag,
                exchange=msg.exchange,
                routing_key=msg.routing_key,
                redelivered=msg.redelivered,
            )
            
            return (method, msg.properties, msg.body)
        
        except queue_module.Empty:
            return (None, None, None)
    
    def basic_ack(self, delivery_tag: int, multiple: bool = False):
        """Acknowledge message(s)."""
        self._check_open()
        
        if multiple:
            # Ack all messages up to and including delivery_tag
            tags_to_ack = [tag for tag in self._unacked_messages.keys() if tag <= delivery_tag]
            for tag in tags_to_ack:
                del self._unacked_messages[tag]
        else:
            if delivery_tag in self._unacked_messages:
                del self._unacked_messages[delivery_tag]
    
    def basic_nack(self, delivery_tag: int, multiple: bool = False, requeue: bool = True):
        """Negative acknowledge message(s)."""
        self._check_open()
        
        if multiple:
            tags_to_nack = [tag for tag in self._unacked_messages.keys() if tag <= delivery_tag]
        else:
            tags_to_nack = [delivery_tag] if delivery_tag in self._unacked_messages else []
        
        for tag in tags_to_nack:
            if tag in self._unacked_messages:
                msg = self._unacked_messages[tag]
                del self._unacked_messages[tag]
                
                if requeue:
                    # Find the queue this message came from and requeue it
                    for queue_name, q_info in self._connection._queues.items():
                        # Simple requeue - mark as redelivered
                        msg.redelivered = True
                        q_info['messages'].put(msg)
                        break
    
    def basic_reject(self, delivery_tag: int, requeue: bool = True):
        """Reject a single message."""
        self.basic_nack(delivery_tag, multiple=False, requeue=requeue)
    
    def basic_qos(self, prefetch_size: int = 0, prefetch_count: int = 0, global_qos: bool = False):
        """Set quality of service (QoS) limits."""
        self._check_open()
        self._prefetch_count = prefetch_count
    
    def _consume_messages(self):
        """Internal method to consume messages (called by connection)."""
        for consumer_tag, (callback, auto_ack, exclusive, arguments) in list(self._consumers.items()):
            # Find queues for this consumer
            for queue_name in self._connection._queues:
                q = self._connection._queues[queue_name]['messages']
                
                # Check prefetch limit
                if self._prefetch_count > 0 and len(self._unacked_messages) >= self._prefetch_count:
                    continue
                
                try:
                    msg = q.get_nowait()
                    
                    if not auto_ack:
                        self._unacked_messages[msg.delivery_tag] = msg
                    
                    # Create method frame
                    method = Deliver(
                        delivery_tag=msg.delivery_tag,
                        exchange=msg.exchange,
                        routing_key=msg.routing_key,
                        redelivered=msg.redelivered,
                    )
                    
                    # Call consumer callback
                    callback(self, method, msg.properties, msg.body)
                
                except queue_module.Empty:
                    continue
    
    def close(self, reply_code: int = 0, reply_text: str = "Normal shutdown"):
        """Close the channel."""
        if not self._closed:
            self._closed = True
            self._consumers.clear()


# Connection
class BlockingConnection:
    """Blocking connection to RabbitMQ."""
    
    def __init__(self, parameters: ConnectionParameters):
        self._parameters = parameters
        self._closed = False
        self._channels: Dict[int, Channel] = {}
        self._channel_counter = 0
        
        # Internal storage
        self._exchanges: Dict[str, Dict] = {
            'amq.direct': {'type': 'direct', 'durable': True, 'auto_delete': False, 'internal': False, 'arguments': {}},
            'amq.fanout': {'type': 'fanout', 'durable': True, 'auto_delete': False, 'internal': False, 'arguments': {}},
            'amq.topic': {'type': 'topic', 'durable': True, 'auto_delete': False, 'internal': False, 'arguments': {}},
            'amq.headers': {'type': 'headers', 'durable': True, 'auto_delete': False, 'internal': False, 'arguments': {}},
        }
        self._queues: Dict[str, Dict] = {}
        self._bindings: Dict[Tuple[str, str], List[str]] = {}  # (exchange, routing_key) -> [queues]
    
    def channel(self, channel_number: Optional[int] = None) -> Channel:
        """Open a new channel."""
        if self._closed:
            raise AMQPConnectionError("Connection is closed")
        
        if channel_number is None:
            self._channel_counter += 1
            channel_number = self._channel_counter
        
        ch = Channel(self, channel_number)
        self._channels[channel_number] = ch
        return ch
    
    def close(self):
        """Close the connection."""
        if not self._closed:
            # Close all channels
            for channel in list(self._channels.values()):
                channel.close()
            self._channels.clear()
            self._closed = True
    
    def is_open(self) -> bool:
        """Check if connection is open."""
        return not self._closed
    
    def is_closed(self) -> bool:
        """Check if connection is closed."""
        return self._closed
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# Adapter classes for async compatibility (SelectConnection)
class SelectConnection:
    """Async-style connection (simplified for emulator)."""
    
    def __init__(self, parameters: ConnectionParameters, on_open_callback: Optional[Callable] = None):
        self._connection = BlockingConnection(parameters)
        self._on_open_callback = on_open_callback
        
        if on_open_callback:
            on_open_callback(self._connection)
    
    def channel(self, on_open_callback: Optional[Callable] = None) -> Channel:
        """Open a channel with callback."""
        ch = self._connection.channel()
        if on_open_callback:
            on_open_callback(ch)
        return ch
    
    def ioloop(self):
        """Get event loop (stub for compatibility)."""
        class IOLoop:
            def start(self):
                pass
            def stop(self):
                pass
        return IOLoop()


# Module-level helper functions
def get_connection_url_parameters(url: str) -> URLParameters:
    """Helper to create URLParameters from URL string."""
    return URLParameters(url)


# Expose common classes at module level
__all__ = [
    'BlockingConnection',
    'SelectConnection',
    'ConnectionParameters',
    'URLParameters',
    'PlainCredentials',
    'Channel',
    'BasicProperties',
    'Deliver',
    'AMQPError',
    'AMQPConnectionError',
    'AMQPChannelError',
    'ChannelClosedByBroker',
    'UnroutableError',
]
