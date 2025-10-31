# channels Emulator - WebSocket and Async Support for Django-style Frameworks

This module emulates the **Django Channels** library, which extends Django to handle WebSockets, chat protocols, IoT protocols, and other async protocols. It provides a layer for handling real-time communication in web applications.

## What is Django Channels?

Django Channels is a project that extends Django to handle asynchronous protocols like WebSockets, MQTT, and others. It allows Django to handle:
- WebSocket connections for real-time features
- Long-running connections
- Background tasks
- Protocol routing

## Features

This emulator implements core Channels functionality:

### Consumer Classes
- **WebsocketConsumer**: Synchronous WebSocket handling
- **AsyncWebsocketConsumer**: Asynchronous WebSocket handling
- **JsonWebsocketConsumer**: Automatic JSON encoding/decoding
- **AsyncJsonWebsocketConsumer**: Async JSON WebSocket handling

### Channel Layers
- **InMemoryChannelLayer**: Message passing between consumers
- **Group Broadcasting**: Send messages to groups of connections
- **Channel Management**: Create and manage channels

### Routing
- **URLRouter**: Route connections based on URL patterns
- **ProtocolTypeRouter**: Route based on protocol type (HTTP, WebSocket, etc.)

### Utilities
- **database_sync_to_async**: Run sync database queries in async context
- **async_to_sync**: Run async functions in sync context

## Usage Examples

### Basic WebSocket Consumer

```python
from Web_Socket_Handler import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        """Called when WebSocket connects."""
        print("Client connected")
        self.accept()
    
    def disconnect(self, close_code):
        """Called when WebSocket disconnects."""
        print(f"Client disconnected with code {close_code}")
    
    def receive(self, text_data=None, bytes_data=None):
        """Called when data is received."""
        print(f"Received: {text_data}")
        # Echo the message back
        self.send(text_data=f"Echo: {text_data}")
```

### Async WebSocket Consumer

```python
from Web_Socket_Handler import AsyncWebsocketConsumer

class AsyncChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Called when WebSocket connects."""
        print("Client connected")
        await self.accept()
    
    async def disconnect(self, close_code):
        """Called when WebSocket disconnects."""
        print(f"Client disconnected with code {close_code}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Called when data is received."""
        print(f"Received: {text_data}")
        # Echo the message back
        await self.send(text_data=f"Echo: {text_data}")
```

### JSON WebSocket Consumer

```python
from Web_Socket_Handler import JsonWebsocketConsumer

class JsonChatConsumer(JsonWebsocketConsumer):
    def connect(self):
        """Accept connection and send welcome message."""
        self.accept()
        self.send_json({
            'type': 'welcome',
            'message': 'Connected to chat!'
        })
    
    def receive_json(self, content):
        """Handle JSON messages."""
        message_type = content.get('type')
        
        if message_type == 'chat.message':
            # Broadcast to all clients (in real app)
            self.send_json({
                'type': 'chat.message',
                'user': content.get('user'),
                'text': content.get('text')
            })
    
    def disconnect(self, close_code):
        """Handle disconnection."""
        print(f"Client disconnected: {close_code}")
```

### Using Channel Layers for Broadcasting

```python
from Web_Socket_Handler import AsyncJsonWebsocketConsumer, get_channel_layer
import asyncio

class ChatRoomConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """Join a chat room."""
        self.room_name = 'general'
        self.room_group_name = f'chat_{self.room_name}'
        
        # Get channel layer
        self.channel_layer = get_channel_layer()
        
        # Create unique channel name
        self.channel_name = await self.channel_layer.new_channel('chat')
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send_json({
            'type': 'system',
            'message': f'Welcome to {self.room_name}!'
        })
    
    async def disconnect(self, close_code):
        """Leave chat room."""
        if hasattr(self, 'channel_layer'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive_json(self, content):
        """Receive message from WebSocket and broadcast to room."""
        message = content.get('message', '')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message
            }
        )
    
    async def chat_message(self, event):
        """Receive message from room group."""
        message = event['message']
        
        # Send message to WebSocket
        await self.send_json({
            'type': 'message',
            'message': message
        })
```

### URL Routing

```python
from Web_Socket_Handler import URLRouter, WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
    
    def receive(self, text_data=None):
        self.send(text_data=f"Chat: {text_data}")

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
    
    def receive(self, text_data=None):
        self.send(text_data=f"Notification: {text_data}")

# Define URL routes
websocket_urlpatterns = URLRouter([
    ('/ws/chat/', ChatConsumer),
    ('/ws/notifications/', NotificationConsumer),
])
```

### Protocol Type Routing

```python
from Web_Socket_Handler import ProtocolTypeRouter, URLRouter, AsyncWebsocketConsumer

class MyWebsocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

# Define application with protocol routing
application = ProtocolTypeRouter({
    'websocket': URLRouter([
        ('/ws/', MyWebsocketConsumer),
    ]),
    # Can add other protocols here
})
```

### Database Sync to Async

```python
from Web_Socket_Handler import AsyncWebsocketConsumer, database_sync_to_async

class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        # Get user from database (simulated)
        user = await self.get_user(123)
        
        await self.send_json({
            'type': 'user_info',
            'user': user
        })
    
    @database_sync_to_async
    def get_user(self, user_id):
        """Simulate database query."""
        # In real app, this would query Django ORM
        return {
            'id': user_id,
            'username': 'john_doe',
            'email': 'john@example.com'
        }
```

### Complete Chat Application Example

```python
from Web_Socket_Handler import (
    AsyncJsonWebsocketConsumer,
    get_channel_layer,
    URLRouter,
    ProtocolTypeRouter
)
import asyncio

class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Full-featured chat consumer."""
    
    async def connect(self):
        """Handle new connection."""
        # Get room name from URL
        self.room_name = self.scope.get('room', 'lobby')
        self.room_group_name = f'chat_{self.room_name}'
        
        # Setup channel layer
        self.channel_layer = get_channel_layer()
        self.channel_name = await self.channel_layer.new_channel('chat')
        
        # Join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user.join',
                'username': 'Anonymous'
            }
        )
    
    async def disconnect(self, close_code):
        """Handle disconnection."""
        # Leave room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user.leave',
                'username': 'Anonymous'
            }
        )
    
    async def receive_json(self, content):
        """Handle incoming messages."""
        message_type = content.get('type')
        
        if message_type == 'chat_message':
            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat.message',
                    'username': content.get('username', 'Anonymous'),
                    'message': content.get('message', '')
                }
            )
    
    async def chat_message(self, event):
        """Send chat message to WebSocket."""
        await self.send_json({
            'type': 'message',
            'username': event['username'],
            'message': event['message']
        })
    
    async def user_join(self, event):
        """Send user join notification."""
        await self.send_json({
            'type': 'user_joined',
            'username': event['username']
        })
    
    async def user_leave(self, event):
        """Send user leave notification."""
        await self.send_json({
            'type': 'user_left',
            'username': event['username']
        })

# Setup routing
application = ProtocolTypeRouter({
    'websocket': URLRouter([
        ('/ws/chat/', ChatConsumer),
    ])
})
```

## Testing

Run the comprehensive test suite:

```bash
python test_Web_Socket_Handler.py
```

Tests cover:
- Channel layer message passing
- Group broadcasting
- WebSocket consumer lifecycle
- JSON encoding/decoding
- URL routing
- Protocol routing
- Async/sync utilities
- Error handling

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for Django Channels in development and testing:

```python
# Instead of:
# from channels.generic.websocket import WebsocketConsumer

# Use:
from Web_Socket_Handler import WebsocketConsumer

# The rest of your code remains unchanged
class MyConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
```

## Use Cases

Perfect for:
- **Local Development**: Build WebSocket features without Redis
- **Testing**: Test real-time features without external dependencies
- **Learning**: Understand WebSocket and async patterns
- **Prototyping**: Quickly prototype real-time applications
- **CI/CD**: Run WebSocket tests in pipelines
- **Education**: Teach real-time web development

## Limitations

This is an emulator for development and testing purposes:
- In-memory only (no persistence)
- Single-process (no distributed messaging)
- Simplified routing (basic pattern matching)
- No ASGI server integration
- No Redis/RabbitMQ backend support
- Limited to basic WebSocket features

## Supported Features

### Consumer Types
- ✅ WebsocketConsumer
- ✅ AsyncWebsocketConsumer
- ✅ JsonWebsocketConsumer
- ✅ AsyncJsonWebsocketConsumer

### Channel Layer Features
- ✅ Message sending
- ✅ Message receiving
- ✅ Group management
- ✅ Group broadcasting
- ✅ Channel creation

### Routing
- ✅ URLRouter
- ✅ ProtocolTypeRouter
- ✅ Basic URL pattern matching

### Utilities
- ✅ database_sync_to_async
- ✅ async_to_sync
- ✅ get_channel_layer

## Real-World WebSocket Concepts

This emulator teaches the following concepts:

1. **WebSocket Lifecycle**: Connect, receive, send, disconnect
2. **Async Programming**: Using async/await with WebSockets
3. **Channel Layers**: Message passing between consumers
4. **Group Broadcasting**: Sending to multiple connections
5. **Routing**: Directing connections to consumers
6. **JSON Communication**: Structured data over WebSockets

## Compatibility

Emulates core features of:
- Django Channels 3.x API patterns
- WebSocket consumer interfaces
- Common channel layer operations

## License

Part of the Emu-Soft project. See main repository LICENSE.
