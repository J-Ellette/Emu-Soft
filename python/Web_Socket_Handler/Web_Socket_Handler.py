"""
channels Emulator - WebSocket and Async Support for Django-style Frameworks

This module emulates the Django Channels library, which extends Django to handle
WebSockets, chat protocols, IoT protocols, and other async protocols. It provides
a layer for handling real-time communication in web applications.

Key Features:
- Consumer classes for handling WebSocket connections
- Channel layers for message passing
- Routing system for mapping connections to consumers
- Support for synchronous and asynchronous consumers
- Group broadcasting


Developed by PowerShield
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable, Union
from collections import defaultdict, deque
import asyncio
import json
import uuid
import time
import concurrent.futures


class ChannelsError(Exception):
    """Base exception for channels errors."""
    pass


class InvalidChannelName(ChannelsError):
    """Raised when channel name is invalid."""
    pass


class MessageTooLarge(ChannelsError):
    """Raised when message is too large."""
    pass


# Consumer base classes
class BaseConsumer:
    """Base consumer class."""
    
    def __init__(self, scope: Dict[str, Any]):
        self.scope = scope
        self.channel_layer = None
        self.channel_name = None
    
    async def __call__(self, receive: Callable, send: Callable):
        """Handle the connection."""
        raise NotImplementedError("Subclasses must implement __call__")


class WebsocketConsumer(BaseConsumer):
    """Synchronous WebSocket consumer."""
    
    def connect(self):
        """Called when WebSocket is handshaking."""
        self.accept()
    
    def disconnect(self, close_code: int):
        """Called when WebSocket closes."""
        pass
    
    def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None):
        """Called when data is received."""
        pass
    
    def accept(self, subprotocol: Optional[str] = None):
        """Accept the WebSocket connection."""
        if hasattr(self, '_send_queue'):
            self._send_queue.append({
                'type': 'websocket.accept',
                'subprotocol': subprotocol
            })
    
    def send(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None, close: bool = False):
        """Send data to the WebSocket."""
        if hasattr(self, '_send_queue'):
            if close:
                self._send_queue.append({'type': 'websocket.close', 'code': 1000})
            elif text_data:
                self._send_queue.append({'type': 'websocket.send', 'text': text_data})
            elif bytes_data:
                self._send_queue.append({'type': 'websocket.send', 'bytes': bytes_data})
    
    def close(self, code: int = 1000):
        """Close the WebSocket connection."""
        if hasattr(self, '_send_queue'):
            self._send_queue.append({'type': 'websocket.close', 'code': code})
    
    async def __call__(self, receive: Callable, send: Callable):
        """Handle the WebSocket connection."""
        # Use deque for O(1) popleft() instead of O(n) list.pop(0)
        self._send_queue = deque()
        self._receive = receive
        
        async def flush_send_queue():
            """Send all queued messages."""
            while self._send_queue:
                message = self._send_queue.popleft()
                await send(message)
        
        # Wait for connection
        message = await receive()
        
        if message['type'] == 'websocket.connect':
            self.connect()
            await flush_send_queue()
            
            # Handle messages
            while True:
                message = await receive()
                
                if message['type'] == 'websocket.receive':
                    text_data = message.get('text')
                    bytes_data = message.get('bytes')
                    self.receive(text_data=text_data, bytes_data=bytes_data)
                    await flush_send_queue()
                
                elif message['type'] == 'websocket.disconnect':
                    self.disconnect(message.get('code', 1000))
                    await flush_send_queue()
                    break


class AsyncWebsocketConsumer(BaseConsumer):
    """Asynchronous WebSocket consumer."""
    
    async def connect(self):
        """Called when WebSocket is handshaking."""
        await self.accept()
    
    async def disconnect(self, close_code: int):
        """Called when WebSocket closes."""
        pass
    
    async def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None):
        """Called when data is received."""
        pass
    
    async def accept(self, subprotocol: Optional[str] = None):
        """Accept the WebSocket connection."""
        if hasattr(self, '_send'):
            await self._send({
                'type': 'websocket.accept',
                'subprotocol': subprotocol
            })
    
    async def send(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None, close: bool = False):
        """Send data to the WebSocket."""
        if hasattr(self, '_send'):
            if close:
                await self._send({'type': 'websocket.close', 'code': 1000})
            elif text_data:
                await self._send({'type': 'websocket.send', 'text': text_data})
            elif bytes_data:
                await self._send({'type': 'websocket.send', 'bytes': bytes_data})
    
    async def close(self, code: int = 1000):
        """Close the WebSocket connection."""
        if hasattr(self, '_send'):
            await self._send({'type': 'websocket.close', 'code': code})
    
    async def __call__(self, receive: Callable, send: Callable):
        """Handle the WebSocket connection."""
        self._send = send
        self._receive = receive
        
        # Wait for connection
        message = await receive()
        
        if message['type'] == 'websocket.connect':
            await self.connect()
            
            # Handle messages
            while True:
                message = await receive()
                
                if message['type'] == 'websocket.receive':
                    text_data = message.get('text')
                    bytes_data = message.get('bytes')
                    await self.receive(text_data=text_data, bytes_data=bytes_data)
                
                elif message['type'] == 'websocket.disconnect':
                    await self.disconnect(message.get('code', 1000))
                    break


class JsonWebsocketConsumer(WebsocketConsumer):
    """WebSocket consumer that automatically encodes/decodes JSON."""
    
    def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None):
        """Called when data is received."""
        if text_data:
            data = json.loads(text_data)
            self.receive_json(data)
    
    def receive_json(self, content: Dict[str, Any]):
        """Called when JSON data is received."""
        pass
    
    def send_json(self, content: Dict[str, Any]):
        """Send JSON data."""
        self.send(text_data=json.dumps(content))


class AsyncJsonWebsocketConsumer(AsyncWebsocketConsumer):
    """Async WebSocket consumer that automatically encodes/decodes JSON."""
    
    async def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None):
        """Called when data is received."""
        if text_data:
            data = json.loads(text_data)
            await self.receive_json(data)
    
    async def receive_json(self, content: Dict[str, Any]):
        """Called when JSON data is received."""
        pass
    
    async def send_json(self, content: Dict[str, Any]):
        """Send JSON data."""
        await self.send(text_data=json.dumps(content))


# Channel Layer
class InMemoryChannelLayer:
    """In-memory channel layer for message passing."""
    
    def __init__(self, expiry: int = 60):
        self.expiry = expiry
        self._channels: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._groups: Dict[str, List[str]] = defaultdict(list)  # group -> [channels]
    
    async def send(self, channel: str, message: Dict[str, Any]):
        """Send a message to a channel."""
        message['__timestamp__'] = time.time()
        self._channels[channel].append(message)
        
        # Clean up old messages
        self._cleanup_channel(channel)
    
    async def receive(self, channel: str) -> Optional[Dict[str, Any]]:
        """Receive a message from a channel."""
        self._cleanup_channel(channel)
        
        if self._channels[channel]:
            message = self._channels[channel].pop(0)
            message.pop('__timestamp__', None)
            return message
        
        return None
    
    async def new_channel(self, prefix: str = 'specific') -> str:
        """Create a new channel name."""
        return f"{prefix}.{uuid.uuid4().hex}"
    
    async def group_add(self, group: str, channel: str):
        """Add a channel to a group."""
        if channel not in self._groups[group]:
            self._groups[group].append(channel)
    
    async def group_discard(self, group: str, channel: str):
        """Remove a channel from a group."""
        if channel in self._groups[group]:
            self._groups[group].remove(channel)
    
    async def group_send(self, group: str, message: Dict[str, Any]):
        """Send a message to all channels in a group."""
        for channel in self._groups[group]:
            await self.send(channel, message.copy())
    
    def _cleanup_channel(self, channel: str):
        """Remove expired messages from a channel."""
        current_time = time.time()
        self._channels[channel] = [
            msg for msg in self._channels[channel]
            if current_time - msg.get('__timestamp__', 0) < self.expiry
        ]


# Routing
class URLRouter:
    """Routes connections based on URL patterns."""
    
    def __init__(self, routes: List[tuple]):
        self.routes = routes
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        """Route the connection to the appropriate consumer."""
        path = scope.get('path', '')
        
        for pattern, consumer in self.routes:
            if self._match_pattern(pattern, path):
                consumer_instance = consumer(scope)
                await consumer_instance(receive, send)
                return
        
        # No matching route
        await send({'type': 'websocket.close', 'code': 4004})
    
    def _match_pattern(self, pattern: str, path: str) -> bool:
        """Check if pattern matches path (simplified)."""
        # Simple matching - just check if pattern equals path
        return pattern == path or pattern.rstrip('/') == path.rstrip('/')


class ProtocolTypeRouter:
    """Routes connections based on protocol type."""
    
    def __init__(self, application: Dict[str, Any]):
        self.application = application
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        """Route based on protocol type."""
        protocol_type = scope.get('type', 'http')
        
        if protocol_type in self.application:
            await self.application[protocol_type](scope, receive, send)
        else:
            await send({'type': f'{protocol_type}.close'})


# Database sync to async
def database_sync_to_async(func: Callable) -> Callable:
    """Decorator to run sync database queries in async context."""
    async def wrapper(*args, **kwargs):
        # In a real implementation, this would run in a thread pool
        # For emulation, we just call the function directly
        return func(*args, **kwargs)
    return wrapper


# Async to sync
def async_to_sync(func: Callable) -> Callable:
    """Decorator to run async functions in sync context."""
    def wrapper(*args, **kwargs):
        # In a real implementation, this would create an event loop
        # For emulation, we try to use existing loop or run new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a new loop in a thread using ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, func(*args, **kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(func(*args, **kwargs))
        except RuntimeError:
            return asyncio.run(func(*args, **kwargs))
    return wrapper


# Utility functions
def get_channel_layer(alias: str = 'default') -> InMemoryChannelLayer:
    """Get a channel layer by alias."""
    # In emulation, always return a new in-memory layer
    return InMemoryChannelLayer()


# Export all public APIs
__all__ = [
    'BaseConsumer',
    'WebsocketConsumer',
    'AsyncWebsocketConsumer',
    'JsonWebsocketConsumer',
    'AsyncJsonWebsocketConsumer',
    'InMemoryChannelLayer',
    'URLRouter',
    'ProtocolTypeRouter',
    'database_sync_to_async',
    'async_to_sync',
    'get_channel_layer',
    'ChannelsError',
    'InvalidChannelName',
    'MessageTooLarge',
]
