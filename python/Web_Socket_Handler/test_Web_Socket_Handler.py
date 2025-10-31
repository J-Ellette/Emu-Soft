"""
Tests for channels emulator

Comprehensive test suite for WebSocket and async support emulator functionality.


Developed by PowerShield
"""

import unittest
import sys
import os
import asyncio
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from Web_Socket_Handler import (
    BaseConsumer, WebsocketConsumer, AsyncWebsocketConsumer,
    JsonWebsocketConsumer, AsyncJsonWebsocketConsumer,
    InMemoryChannelLayer, URLRouter, ProtocolTypeRouter,
    database_sync_to_async, async_to_sync, get_channel_layer,
    ChannelsError, InvalidChannelName, MessageTooLarge
)


class TestInMemoryChannelLayer(unittest.TestCase):
    """Test InMemoryChannelLayer functionality."""
    
    def setUp(self):
        """Create a channel layer for testing."""
        self.channel_layer = InMemoryChannelLayer()
    
    def test_send_and_receive(self):
        """Test sending and receiving messages."""
        async def test():
            await self.channel_layer.send('test-channel', {'type': 'test.message', 'data': 'hello'})
            message = await self.channel_layer.receive('test-channel')
            self.assertEqual(message['type'], 'test.message')
            self.assertEqual(message['data'], 'hello')
        
        asyncio.run(test())
    
    def test_receive_empty_channel(self):
        """Test receiving from empty channel."""
        async def test():
            message = await self.channel_layer.receive('empty-channel')
            self.assertIsNone(message)
        
        asyncio.run(test())
    
    def test_new_channel(self):
        """Test creating a new channel name."""
        async def test():
            channel1 = await self.channel_layer.new_channel('test')
            channel2 = await self.channel_layer.new_channel('test')
            
            self.assertTrue(channel1.startswith('test.'))
            self.assertTrue(channel2.startswith('test.'))
            self.assertNotEqual(channel1, channel2)
        
        asyncio.run(test())
    
    def test_group_add_and_send(self):
        """Test adding channels to groups and broadcasting."""
        async def test():
            channel1 = await self.channel_layer.new_channel()
            channel2 = await self.channel_layer.new_channel()
            
            await self.channel_layer.group_add('test-group', channel1)
            await self.channel_layer.group_add('test-group', channel2)
            
            await self.channel_layer.group_send('test-group', {'type': 'broadcast', 'message': 'hello all'})
            
            msg1 = await self.channel_layer.receive(channel1)
            msg2 = await self.channel_layer.receive(channel2)
            
            self.assertEqual(msg1['type'], 'broadcast')
            self.assertEqual(msg2['message'], 'hello all')
        
        asyncio.run(test())
    
    def test_group_discard(self):
        """Test removing channels from groups."""
        async def test():
            channel = await self.channel_layer.new_channel()
            
            await self.channel_layer.group_add('test-group', channel)
            await self.channel_layer.group_discard('test-group', channel)
            
            await self.channel_layer.group_send('test-group', {'type': 'test'})
            
            msg = await self.channel_layer.receive(channel)
            self.assertIsNone(msg)
        
        asyncio.run(test())


class TestWebsocketConsumer(unittest.TestCase):
    """Test WebsocketConsumer functionality."""
    
    def test_consumer_creation(self):
        """Test creating a WebSocket consumer."""
        class TestConsumer(WebsocketConsumer):
            def connect(self):
                self.accept()
        
        scope = {'type': 'websocket', 'path': '/test/'}
        consumer = TestConsumer(scope)
        
        self.assertEqual(consumer.scope, scope)
    
    def test_consumer_connect(self):
        """Test consumer connection handling."""
        messages_sent = []
        
        class TestConsumer(WebsocketConsumer):
            def connect(self):
                self.accept()
        
        async def test():
            scope = {'type': 'websocket', 'path': '/test/'}
            consumer = TestConsumer(scope)
            
            async def send(message):
                messages_sent.append(message)
            
            messages = [
                {'type': 'websocket.connect'},
                {'type': 'websocket.disconnect', 'code': 1000}
            ]
            message_iter = iter(messages)
            
            async def receive():
                return next(message_iter)
            
            await consumer(receive, send)
            
            # Check that accept was called
            self.assertEqual(len(messages_sent), 1)
            self.assertEqual(messages_sent[0]['type'], 'websocket.accept')
        
        asyncio.run(test())
    
    def test_consumer_send_text(self):
        """Test sending text data."""
        messages_sent = []
        
        class TestConsumer(WebsocketConsumer):
            def connect(self):
                self.accept()
                self.send(text_data='Hello, World!')
        
        async def test():
            scope = {'type': 'websocket', 'path': '/test/'}
            consumer = TestConsumer(scope)
            
            async def send(message):
                messages_sent.append(message)
            
            messages = [
                {'type': 'websocket.connect'},
                {'type': 'websocket.disconnect', 'code': 1000}
            ]
            message_iter = iter(messages)
            
            async def receive():
                return next(message_iter)
            
            await consumer(receive, send)
            
            # Check that accept and send were called
            self.assertEqual(len(messages_sent), 2)
            self.assertEqual(messages_sent[1]['type'], 'websocket.send')
            self.assertEqual(messages_sent[1]['text'], 'Hello, World!')
        
        asyncio.run(test())


class TestAsyncWebsocketConsumer(unittest.TestCase):
    """Test AsyncWebsocketConsumer functionality."""
    
    def test_async_consumer_creation(self):
        """Test creating an async WebSocket consumer."""
        class TestConsumer(AsyncWebsocketConsumer):
            async def connect(self):
                await self.accept()
        
        scope = {'type': 'websocket', 'path': '/test/'}
        consumer = TestConsumer(scope)
        
        self.assertEqual(consumer.scope, scope)
    
    def test_async_consumer_connect(self):
        """Test async consumer connection handling."""
        messages_sent = []
        
        class TestConsumer(AsyncWebsocketConsumer):
            async def connect(self):
                await self.accept()
        
        async def test():
            scope = {'type': 'websocket', 'path': '/test/'}
            consumer = TestConsumer(scope)
            
            async def send(message):
                messages_sent.append(message)
            
            messages = [
                {'type': 'websocket.connect'},
                {'type': 'websocket.disconnect', 'code': 1000}
            ]
            message_iter = iter(messages)
            
            async def receive():
                return next(message_iter)
            
            await consumer(receive, send)
            
            self.assertEqual(len(messages_sent), 1)
            self.assertEqual(messages_sent[0]['type'], 'websocket.accept')
        
        asyncio.run(test())


class TestJsonWebsocketConsumer(unittest.TestCase):
    """Test JsonWebsocketConsumer functionality."""
    
    def test_json_consumer_receive(self):
        """Test receiving JSON data."""
        received_data = []
        
        class TestConsumer(JsonWebsocketConsumer):
            def connect(self):
                self.accept()
            
            def receive_json(self, content):
                received_data.append(content)
        
        async def test():
            scope = {'type': 'websocket', 'path': '/test/'}
            consumer = TestConsumer(scope)
            
            messages = [
                {'type': 'websocket.connect'},
                {'type': 'websocket.receive', 'text': json.dumps({'message': 'hello'})},
                {'type': 'websocket.disconnect', 'code': 1000}
            ]
            message_iter = iter(messages)
            
            async def receive():
                return next(message_iter)
            
            async def send(message):
                pass
            
            await consumer(receive, send)
            
            self.assertEqual(len(received_data), 1)
            self.assertEqual(received_data[0]['message'], 'hello')
        
        asyncio.run(test())
    
    def test_json_consumer_send(self):
        """Test sending JSON data."""
        messages_sent = []
        
        class TestConsumer(JsonWebsocketConsumer):
            def connect(self):
                self.accept()
                self.send_json({'status': 'connected'})
        
        async def test():
            scope = {'type': 'websocket', 'path': '/test/'}
            consumer = TestConsumer(scope)
            
            async def send(message):
                messages_sent.append(message)
            
            messages = [
                {'type': 'websocket.connect'},
                {'type': 'websocket.disconnect', 'code': 1000}
            ]
            message_iter = iter(messages)
            
            async def receive():
                return next(message_iter)
            
            await consumer(receive, send)
            
            self.assertEqual(len(messages_sent), 2)
            text_message = messages_sent[1]
            self.assertEqual(text_message['type'], 'websocket.send')
            data = json.loads(text_message['text'])
            self.assertEqual(data['status'], 'connected')
        
        asyncio.run(test())


class TestURLRouter(unittest.TestCase):
    """Test URLRouter functionality."""
    
    def test_url_routing(self):
        """Test routing based on URL path."""
        routed_to = []
        
        class Consumer1(AsyncWebsocketConsumer):
            async def connect(self):
                routed_to.append('consumer1')
                await self.accept()
        
        class Consumer2(AsyncWebsocketConsumer):
            async def connect(self):
                routed_to.append('consumer2')
                await self.accept()
        
        async def test():
            router = URLRouter([
                ('/path1/', Consumer1),
                ('/path2/', Consumer2),
            ])
            
            # Test routing to path1
            scope = {'type': 'websocket', 'path': '/path1/'}
            
            messages = [
                {'type': 'websocket.connect'},
                {'type': 'websocket.disconnect', 'code': 1000}
            ]
            message_iter = iter(messages)
            
            async def receive():
                return next(message_iter)
            
            async def send(message):
                pass
            
            await router(scope, receive, send)
            
            self.assertIn('consumer1', routed_to)
        
        asyncio.run(test())


class TestProtocolTypeRouter(unittest.TestCase):
    """Test ProtocolTypeRouter functionality."""
    
    def test_protocol_routing(self):
        """Test routing based on protocol type."""
        routed_protocols = []
        
        async def websocket_handler(scope, receive, send):
            routed_protocols.append('websocket')
        
        async def http_handler(scope, receive, send):
            routed_protocols.append('http')
        
        async def test():
            router = ProtocolTypeRouter({
                'websocket': websocket_handler,
                'http': http_handler,
            })
            
            # Test WebSocket routing
            scope = {'type': 'websocket'}
            await router(scope, None, None)
            
            # Test HTTP routing
            scope = {'type': 'http'}
            await router(scope, None, None)
            
            self.assertIn('websocket', routed_protocols)
            self.assertIn('http', routed_protocols)
        
        asyncio.run(test())


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_database_sync_to_async(self):
        """Test database_sync_to_async decorator."""
        @database_sync_to_async
        def get_user(user_id):
            return {'id': user_id, 'name': 'Test User'}
        
        async def test():
            user = await get_user(123)
            self.assertEqual(user['id'], 123)
        
        asyncio.run(test())
    
    def test_async_to_sync(self):
        """Test async_to_sync decorator."""
        @async_to_sync
        async def async_function(x, y):
            await asyncio.sleep(0.01)
            return x + y
        
        result = async_function(5, 3)
        self.assertEqual(result, 8)
    
    def test_get_channel_layer(self):
        """Test getting a channel layer."""
        layer = get_channel_layer()
        self.assertIsInstance(layer, InMemoryChannelLayer)


class TestErrorHandling(unittest.TestCase):
    """Test error handling."""
    
    def test_channels_error(self):
        """Test ChannelsError exception."""
        with self.assertRaises(ChannelsError):
            raise ChannelsError("Test error")
    
    def test_invalid_channel_name(self):
        """Test InvalidChannelName exception."""
        with self.assertRaises(InvalidChannelName):
            raise InvalidChannelName("Invalid channel name")


if __name__ == '__main__':
    unittest.main()
