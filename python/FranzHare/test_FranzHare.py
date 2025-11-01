"""
Tests for FranzHare Kafka/RabbitMQ Testing Harness
"""

import unittest
from FranzHare import FranzHare, BrokerType, MessageStatus, Message


class TestFranzHare(unittest.TestCase):
    """Test FranzHare testing harness"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.harness = FranzHare(broker_type=BrokerType.KAFKA)
    
    def test_create_topic(self):
        """Test creating a topic"""
        self.harness.create_topic('test_topic')
        self.assertIn('test_topic', self.harness.topics)
    
    def test_produce_message(self):
        """Test producing a message"""
        msg_id = self.harness.produce('test_topic', 'test_value', key='test_key')
        
        self.assertIsNotNone(msg_id)
        messages = self.harness.get_topic_messages('test_topic')
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].value, 'test_value')
        self.assertEqual(messages[0].key, 'test_key')
    
    def test_produce_batch(self):
        """Test producing batch messages"""
        messages = [('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')]
        msg_ids = self.harness.produce_batch('test_topic', messages)
        
        self.assertEqual(len(msg_ids), 3)
        self.assertEqual(self.harness.get_topic_count('test_topic'), 3)
    
    def test_consume_messages(self):
        """Test consuming messages"""
        self.harness.produce('test_topic', 'message1')
        self.harness.produce('test_topic', 'message2')
        
        consumed = self.harness.consume('test_topic', max_messages=2)
        
        self.assertEqual(len(consumed), 2)
        self.assertEqual(consumed[0].value, 'message1')
        self.assertEqual(consumed[1].value, 'message2')
    
    def test_consumer_group_offset(self):
        """Test consumer group offset management"""
        # Produce messages
        for i in range(5):
            self.harness.produce('test_topic', f'message{i}')
        
        # Consume with group
        consumed1 = self.harness.consume('test_topic', group_id='group1', max_messages=3)
        self.assertEqual(len(consumed1), 3)
        
        # Consume again - should get remaining messages
        consumed2 = self.harness.consume('test_topic', group_id='group1', max_messages=3)
        self.assertEqual(len(consumed2), 2)
        
        # Consume again - should get nothing
        consumed3 = self.harness.consume('test_topic', group_id='group1', max_messages=3)
        self.assertEqual(len(consumed3), 0)
    
    def test_subscribe_callback(self):
        """Test subscribing with callback"""
        received_messages = []
        
        def callback(message):
            received_messages.append(message)
        
        self.harness.subscribe('test_topic', callback)
        self.harness.produce('test_topic', 'test_message')
        
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0].value, 'test_message')
    
    def test_acknowledge_message(self):
        """Test acknowledging messages"""
        msg_id = self.harness.produce('test_topic', 'test_value')
        
        result = self.harness.acknowledge(msg_id)
        self.assertTrue(result)
        
        # Find message and check status
        msg = next(m for m in self.harness.message_history if m.id == msg_id)
        self.assertEqual(msg.status, MessageStatus.ACKNOWLEDGED)
    
    def test_nack_with_requeue(self):
        """Test negative acknowledge with requeue"""
        msg_id = self.harness.produce('test_topic', 'test_value')
        initial_count = self.harness.get_topic_count('test_topic')
        
        self.harness.nack(msg_id, requeue=True)
        
        # Message should be requeued
        self.assertEqual(self.harness.get_topic_count('test_topic'), initial_count + 1)
    
    def test_dead_letter_queue(self):
        """Test dead letter queue behavior"""
        msg_id = self.harness.produce('test_topic', 'test_value')
        
        # NACK multiple times to exceed retry limit
        for _ in range(3):
            self.harness.nack(msg_id, requeue=True)
        
        dlq_messages = self.harness.get_dead_letter_messages()
        self.assertGreater(len(dlq_messages), 0)
    
    def test_clear_topic(self):
        """Test clearing a topic"""
        self.harness.produce('test_topic', 'message1')
        self.harness.produce('test_topic', 'message2')
        
        self.harness.clear_topic('test_topic')
        
        self.assertEqual(self.harness.get_topic_count('test_topic'), 0)
    
    def test_reset_consumer_group(self):
        """Test resetting consumer group offset"""
        for i in range(5):
            self.harness.produce('test_topic', f'message{i}')
        
        # Consume all messages
        self.harness.consume('test_topic', group_id='group1', max_messages=5)
        
        # Reset offset
        self.harness.reset_consumer_group('group1', 'test_topic')
        
        # Should be able to consume again
        consumed = self.harness.consume('test_topic', group_id='group1', max_messages=5)
        self.assertEqual(len(consumed), 5)
    
    def test_throughput(self):
        """Test throughput testing"""
        result = self.harness.test_throughput('perf_topic', num_messages=100, message_size=50)
        
        self.assertTrue(result.passed)
        self.assertEqual(result.messages_sent, 100)
        self.assertEqual(result.messages_received, 100)
        self.assertIn('throughput_msg_per_sec', result.details)
    
    def test_consumer_group_test(self):
        """Test consumer group testing"""
        result = self.harness.test_consumer_group('test_topic', 'group1', num_messages=10)
        
        self.assertTrue(result.passed)
        self.assertEqual(result.messages_sent, 10)
    
    def test_ordering(self):
        """Test message ordering"""
        result = self.harness.test_ordering('test_topic', num_messages=10)
        
        self.assertTrue(result.passed)
        self.assertEqual(len(result.errors), 0)
    
    def test_statistics(self):
        """Test getting statistics"""
        self.harness.produce('topic1', 'message1')
        self.harness.produce('topic2', 'message2')
        
        stats = self.harness.get_statistics()
        
        self.assertEqual(stats['broker_type'], 'kafka')
        self.assertEqual(stats['total_topics'], 2)
        self.assertEqual(stats['total_messages'], 2)


if __name__ == '__main__':
    unittest.main()
