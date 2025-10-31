"""
Tests for Pika Emulator

Comprehensive test suite for RabbitMQ client functionality.
"""

import unittest
import time
from pika_emulator import (
    BlockingConnection,
    ConnectionParameters,
    URLParameters,
    PlainCredentials,
    BasicProperties,
    AMQPChannelError,
    ChannelClosedByBroker,
    UnroutableError,
)


class TestConnectionParameters(unittest.TestCase):
    """Test connection parameter classes."""
    
    def test_connection_parameters_defaults(self):
        """Test default connection parameters."""
        params = ConnectionParameters()
        self.assertEqual(params.host, 'localhost')
        self.assertEqual(params.port, 5672)
        self.assertEqual(params.virtual_host, '/')
        self.assertIsNotNone(params.credentials)
        self.assertEqual(params.credentials.username, 'guest')
        self.assertEqual(params.credentials.password, 'guest')
    
    def test_connection_parameters_custom(self):
        """Test custom connection parameters."""
        creds = PlainCredentials('myuser', 'mypass')
        params = ConnectionParameters(
            host='rabbitmq.example.com',
            port=5673,
            virtual_host='/myvhost',
            credentials=creds,
            heartbeat=60,
        )
        self.assertEqual(params.host, 'rabbitmq.example.com')
        self.assertEqual(params.port, 5673)
        self.assertEqual(params.virtual_host, '/myvhost')
        self.assertEqual(params.credentials.username, 'myuser')
        self.assertEqual(params.heartbeat, 60)
    
    def test_url_parameters(self):
        """Test URL parameter parsing."""
        params = URLParameters('amqp://user:pass@rabbit.local:5673/vhost?heartbeat=30')
        self.assertEqual(params.host, 'rabbit.local')
        self.assertEqual(params.port, 5673)
        self.assertEqual(params.virtual_host, 'vhost')
        self.assertEqual(params.credentials.username, 'user')
        self.assertEqual(params.credentials.password, 'pass')
        self.assertEqual(params.heartbeat, 30)
    
    def test_url_parameters_defaults(self):
        """Test URL parameters with defaults."""
        params = URLParameters('amqp://localhost')
        self.assertEqual(params.host, 'localhost')
        self.assertEqual(params.port, 5672)
        self.assertEqual(params.virtual_host, '/')
        self.assertEqual(params.credentials.username, 'guest')


class TestConnection(unittest.TestCase):
    """Test connection operations."""
    
    def test_connection_creation(self):
        """Test creating a connection."""
        params = ConnectionParameters()
        conn = BlockingConnection(params)
        self.assertTrue(conn.is_open())
        self.assertFalse(conn.is_closed())
        conn.close()
        self.assertTrue(conn.is_closed())
    
    def test_connection_context_manager(self):
        """Test connection as context manager."""
        params = ConnectionParameters()
        with BlockingConnection(params) as conn:
            self.assertTrue(conn.is_open())
        self.assertTrue(conn.is_closed())
    
    def test_channel_creation(self):
        """Test creating channels."""
        params = ConnectionParameters()
        with BlockingConnection(params) as conn:
            ch1 = conn.channel()
            ch2 = conn.channel()
            self.assertIsNotNone(ch1)
            self.assertIsNotNone(ch2)
            self.assertNotEqual(ch1._channel_number, ch2._channel_number)


class TestExchangeOperations(unittest.TestCase):
    """Test exchange operations."""
    
    def setUp(self):
        """Set up test connection and channel."""
        self.conn = BlockingConnection(ConnectionParameters())
        self.ch = self.conn.channel()
    
    def tearDown(self):
        """Clean up connection."""
        self.conn.close()
    
    def test_exchange_declare(self):
        """Test declaring an exchange."""
        self.ch.exchange_declare('test_exchange', exchange_type='direct', durable=True)
        self.assertIn('test_exchange', self.conn._exchanges)
        self.assertEqual(self.conn._exchanges['test_exchange']['type'], 'direct')
        self.assertTrue(self.conn._exchanges['test_exchange']['durable'])
    
    def test_exchange_declare_fanout(self):
        """Test declaring fanout exchange."""
        self.ch.exchange_declare('fanout_exchange', exchange_type='fanout')
        self.assertEqual(self.conn._exchanges['fanout_exchange']['type'], 'fanout')
    
    def test_exchange_declare_topic(self):
        """Test declaring topic exchange."""
        self.ch.exchange_declare('topic_exchange', exchange_type='topic')
        self.assertEqual(self.conn._exchanges['topic_exchange']['type'], 'topic')
    
    def test_exchange_passive_exists(self):
        """Test passive declare of existing exchange."""
        self.ch.exchange_declare('test_exchange', exchange_type='direct')
        # Should not raise
        self.ch.exchange_declare('test_exchange', passive=True)
    
    def test_exchange_passive_not_exists(self):
        """Test passive declare of non-existing exchange."""
        with self.assertRaises(ChannelClosedByBroker):
            self.ch.exchange_declare('nonexistent', passive=True)


class TestQueueOperations(unittest.TestCase):
    """Test queue operations."""
    
    def setUp(self):
        """Set up test connection and channel."""
        self.conn = BlockingConnection(ConnectionParameters())
        self.ch = self.conn.channel()
    
    def tearDown(self):
        """Clean up connection."""
        self.conn.close()
    
    def test_queue_declare(self):
        """Test declaring a queue."""
        result = self.ch.queue_declare('test_queue', durable=True)
        self.assertEqual(result.queue, 'test_queue')
        self.assertIn('test_queue', self.conn._queues)
        self.assertTrue(self.conn._queues['test_queue']['durable'])
    
    def test_queue_declare_auto_name(self):
        """Test declaring queue with auto-generated name."""
        result = self.ch.queue_declare('')
        self.assertIsNotNone(result.queue)
        self.assertTrue(result.queue.startswith('amq.gen-'))
    
    def test_queue_declare_passive(self):
        """Test passive queue declare."""
        self.ch.queue_declare('test_queue')
        # Should not raise
        self.ch.queue_declare('test_queue', passive=True)
    
    def test_queue_declare_passive_not_exists(self):
        """Test passive declare of non-existing queue."""
        with self.assertRaises(ChannelClosedByBroker):
            self.ch.queue_declare('nonexistent', passive=True)
    
    def test_queue_purge(self):
        """Test purging a queue."""
        self.ch.queue_declare('test_queue')
        
        # Add some messages
        for i in range(5):
            self.ch.basic_publish('', 'test_queue', f'Message {i}'.encode())
        
        result = self.ch.queue_purge('test_queue')
        self.assertEqual(result.message_count, 5)
        
        # Queue should be empty
        method, props, body = self.ch.basic_get('test_queue')
        self.assertIsNone(method)
    
    def test_queue_delete(self):
        """Test deleting a queue."""
        self.ch.queue_declare('test_queue')
        self.ch.queue_delete('test_queue')
        self.assertNotIn('test_queue', self.conn._queues)


class TestQueueBinding(unittest.TestCase):
    """Test queue binding operations."""
    
    def setUp(self):
        """Set up test connection and channel."""
        self.conn = BlockingConnection(ConnectionParameters())
        self.ch = self.conn.channel()
    
    def tearDown(self):
        """Clean up connection."""
        self.conn.close()
    
    def test_queue_bind(self):
        """Test binding queue to exchange."""
        self.ch.exchange_declare('test_exchange', exchange_type='direct')
        self.ch.queue_declare('test_queue')
        self.ch.queue_bind('test_queue', 'test_exchange', routing_key='test_key')
        
        binding_key = ('test_exchange', 'test_key')
        self.assertIn(binding_key, self.conn._bindings)
        self.assertIn('test_queue', self.conn._bindings[binding_key])
    
    def test_queue_unbind(self):
        """Test unbinding queue from exchange."""
        self.ch.exchange_declare('test_exchange', exchange_type='direct')
        self.ch.queue_declare('test_queue')
        self.ch.queue_bind('test_queue', 'test_exchange', routing_key='test_key')
        self.ch.queue_unbind('test_queue', 'test_exchange', routing_key='test_key')
        
        binding_key = ('test_exchange', 'test_key')
        self.assertNotIn('test_queue', self.conn._bindings.get(binding_key, []))


class TestBasicPublish(unittest.TestCase):
    """Test message publishing."""
    
    def setUp(self):
        """Set up test connection and channel."""
        self.conn = BlockingConnection(ConnectionParameters())
        self.ch = self.conn.channel()
    
    def tearDown(self):
        """Clean up connection."""
        self.conn.close()
    
    def test_publish_to_default_exchange(self):
        """Test publishing to default exchange (direct to queue)."""
        self.ch.queue_declare('test_queue')
        self.ch.basic_publish('', 'test_queue', b'Test message')
        
        method, props, body = self.ch.basic_get('test_queue')
        self.assertIsNotNone(method)
        self.assertEqual(body, b'Test message')
    
    def test_publish_with_properties(self):
        """Test publishing with message properties."""
        self.ch.queue_declare('test_queue')
        
        properties = BasicProperties(
            content_type='application/json',
            delivery_mode=2,  # persistent
            correlation_id='abc123',
            reply_to='reply_queue',
        )
        
        self.ch.basic_publish('', 'test_queue', b'{"key": "value"}', properties=properties)
        
        method, props, body = self.ch.basic_get('test_queue')
        self.assertEqual(props.content_type, 'application/json')
        self.assertEqual(props.delivery_mode, 2)
        self.assertEqual(props.correlation_id, 'abc123')
    
    def test_publish_direct_exchange(self):
        """Test publishing to direct exchange."""
        self.ch.exchange_declare('direct_ex', exchange_type='direct')
        self.ch.queue_declare('queue1')
        self.ch.queue_bind('queue1', 'direct_ex', routing_key='key1')
        
        self.ch.basic_publish('direct_ex', 'key1', b'Message 1')
        
        method, props, body = self.ch.basic_get('queue1')
        self.assertEqual(body, b'Message 1')
    
    def test_publish_fanout_exchange(self):
        """Test publishing to fanout exchange."""
        self.ch.exchange_declare('fanout_ex', exchange_type='fanout')
        self.ch.queue_declare('queue1')
        self.ch.queue_declare('queue2')
        self.ch.queue_bind('queue1', 'fanout_ex', routing_key='')
        self.ch.queue_bind('queue2', 'fanout_ex', routing_key='')
        
        self.ch.basic_publish('fanout_ex', '', b'Broadcast message')
        
        # Both queues should receive the message
        method1, props1, body1 = self.ch.basic_get('queue1')
        method2, props2, body2 = self.ch.basic_get('queue2')
        
        self.assertEqual(body1, b'Broadcast message')
        self.assertEqual(body2, b'Broadcast message')
    
    def test_publish_topic_exchange(self):
        """Test publishing to topic exchange."""
        self.ch.exchange_declare('topic_ex', exchange_type='topic')
        self.ch.queue_declare('queue1')
        self.ch.queue_declare('queue2')
        self.ch.queue_bind('queue1', 'topic_ex', routing_key='stock.*.nyse')
        self.ch.queue_bind('queue2', 'topic_ex', routing_key='stock.#')
        
        # Publish with routing key that matches both patterns
        self.ch.basic_publish('topic_ex', 'stock.usd.nyse', b'Stock message 1')
        
        method1, props1, body1 = self.ch.basic_get('queue1')
        method2, props2, body2 = self.ch.basic_get('queue2')
        
        self.assertEqual(body1, b'Stock message 1')
        self.assertEqual(body2, b'Stock message 1')
    
    def test_publish_mandatory_unroutable(self):
        """Test mandatory flag with unroutable message."""
        self.ch.exchange_declare('test_ex', exchange_type='direct')
        
        with self.assertRaises(UnroutableError):
            self.ch.basic_publish('test_ex', 'nonexistent_key', b'Message', mandatory=True)


class TestBasicGet(unittest.TestCase):
    """Test basic.get operations."""
    
    def setUp(self):
        """Set up test connection and channel."""
        self.conn = BlockingConnection(ConnectionParameters())
        self.ch = self.conn.channel()
    
    def tearDown(self):
        """Clean up connection."""
        self.conn.close()
    
    def test_basic_get_message(self):
        """Test getting a message."""
        self.ch.queue_declare('test_queue')
        self.ch.basic_publish('', 'test_queue', b'Test message')
        
        method, props, body = self.ch.basic_get('test_queue')
        self.assertIsNotNone(method)
        self.assertEqual(body, b'Test message')
        self.assertEqual(method.routing_key, 'test_queue')
    
    def test_basic_get_empty_queue(self):
        """Test getting from empty queue."""
        self.ch.queue_declare('test_queue')
        
        method, props, body = self.ch.basic_get('test_queue')
        self.assertIsNone(method)
        self.assertIsNone(props)
        self.assertIsNone(body)
    
    def test_basic_get_auto_ack(self):
        """Test basic.get with auto_ack."""
        self.ch.queue_declare('test_queue')
        self.ch.basic_publish('', 'test_queue', b'Test message')
        
        method, props, body = self.ch.basic_get('test_queue', auto_ack=True)
        self.assertIsNotNone(method)
        # Message should be auto-acknowledged
        self.assertNotIn(method.delivery_tag, self.ch._unacked_messages)


class TestAcknowledgment(unittest.TestCase):
    """Test message acknowledgment."""
    
    def setUp(self):
        """Set up test connection and channel."""
        self.conn = BlockingConnection(ConnectionParameters())
        self.ch = self.conn.channel()
    
    def tearDown(self):
        """Clean up connection."""
        self.conn.close()
    
    def test_basic_ack(self):
        """Test acknowledging a message."""
        self.ch.queue_declare('test_queue')
        self.ch.basic_publish('', 'test_queue', b'Test message')
        
        method, props, body = self.ch.basic_get('test_queue', auto_ack=False)
        delivery_tag = method.delivery_tag
        
        self.assertIn(delivery_tag, self.ch._unacked_messages)
        
        self.ch.basic_ack(delivery_tag)
        self.assertNotIn(delivery_tag, self.ch._unacked_messages)
    
    def test_basic_ack_multiple(self):
        """Test acknowledging multiple messages."""
        self.ch.queue_declare('test_queue')
        
        # Publish and get multiple messages
        delivery_tags = []
        for i in range(3):
            self.ch.basic_publish('', 'test_queue', f'Message {i}'.encode())
            method, props, body = self.ch.basic_get('test_queue', auto_ack=False)
            delivery_tags.append(method.delivery_tag)
        
        # Ack all up to last tag
        self.ch.basic_ack(delivery_tags[-1], multiple=True)
        
        # All should be acked
        for tag in delivery_tags:
            self.assertNotIn(tag, self.ch._unacked_messages)
    
    def test_basic_nack_requeue(self):
        """Test nack with requeue."""
        self.ch.queue_declare('test_queue')
        self.ch.basic_publish('', 'test_queue', b'Test message')
        
        method, props, body = self.ch.basic_get('test_queue', auto_ack=False)
        delivery_tag = method.delivery_tag
        
        self.ch.basic_nack(delivery_tag, requeue=True)
        
        # Message should be requeued
        method2, props2, body2 = self.ch.basic_get('test_queue')
        self.assertIsNotNone(method2)
        self.assertTrue(method2.redelivered)
    
    def test_basic_reject(self):
        """Test rejecting a message."""
        self.ch.queue_declare('test_queue')
        self.ch.basic_publish('', 'test_queue', b'Test message')
        
        method, props, body = self.ch.basic_get('test_queue', auto_ack=False)
        delivery_tag = method.delivery_tag
        
        self.ch.basic_reject(delivery_tag, requeue=False)
        
        # Message should be rejected and not requeued
        self.assertNotIn(delivery_tag, self.ch._unacked_messages)


class TestQoS(unittest.TestCase):
    """Test QoS operations."""
    
    def setUp(self):
        """Set up test connection and channel."""
        self.conn = BlockingConnection(ConnectionParameters())
        self.ch = self.conn.channel()
    
    def tearDown(self):
        """Clean up connection."""
        self.conn.close()
    
    def test_basic_qos(self):
        """Test setting QoS prefetch count."""
        self.ch.basic_qos(prefetch_count=10)
        self.assertEqual(self.ch._prefetch_count, 10)


class TestTopicRouting(unittest.TestCase):
    """Test topic exchange routing patterns."""
    
    def setUp(self):
        """Set up test connection and channel."""
        self.conn = BlockingConnection(ConnectionParameters())
        self.ch = self.conn.channel()
        self.ch.exchange_declare('topic_ex', exchange_type='topic')
    
    def tearDown(self):
        """Clean up connection."""
        self.conn.close()
    
    def test_topic_single_wildcard(self):
        """Test topic routing with * wildcard."""
        self.ch.queue_declare('queue1')
        self.ch.queue_bind('queue1', 'topic_ex', routing_key='user.*.created')
        
        # Should match
        self.ch.basic_publish('topic_ex', 'user.admin.created', b'Message 1')
        method, _, body = self.ch.basic_get('queue1')
        self.assertEqual(body, b'Message 1')
        
        # Should not match
        self.ch.basic_publish('topic_ex', 'user.admin.guest.created', b'Message 2')
        method, _, body = self.ch.basic_get('queue1')
        self.assertIsNone(method)
    
    def test_topic_hash_wildcard(self):
        """Test topic routing with # wildcard."""
        self.ch.queue_declare('queue1')
        self.ch.queue_bind('queue1', 'topic_ex', routing_key='log.#')
        
        # All should match
        self.ch.basic_publish('topic_ex', 'log.info', b'Message 1')
        self.ch.basic_publish('topic_ex', 'log.error.critical', b'Message 2')
        self.ch.basic_publish('topic_ex', 'log.debug.app.startup', b'Message 3')
        
        for i in range(3):
            method, _, body = self.ch.basic_get('queue1')
            self.assertIsNotNone(method)


class TestChannelClose(unittest.TestCase):
    """Test channel closing."""
    
    def setUp(self):
        """Set up test connection."""
        self.conn = BlockingConnection(ConnectionParameters())
    
    def tearDown(self):
        """Clean up connection."""
        self.conn.close()
    
    def test_channel_close(self):
        """Test closing a channel."""
        ch = self.conn.channel()
        self.assertFalse(ch._closed)
        
        ch.close()
        self.assertTrue(ch._closed)
    
    def test_operations_on_closed_channel(self):
        """Test operations on closed channel raise error."""
        ch = self.conn.channel()
        ch.close()
        
        with self.assertRaises(AMQPChannelError):
            ch.queue_declare('test_queue')


if __name__ == '__main__':
    unittest.main()
