"""Tests for DeadLetter"""
import unittest
from DeadLetter import DeadLetter, FailureReason

class TestDeadLetter(unittest.TestCase):
    def setUp(self):
        self.dlq = DeadLetter()
    
    def test_add_message(self):
        self.dlq.add_message('msg1', 'orders', {'order_id': 123}, FailureReason.TIMEOUT)
        msg = self.dlq.get_message('msg1')
        self.assertIsNotNone(msg)
        self.assertEqual(msg.failure_count, 1)
    
    def test_retry_increments_count(self):
        self.dlq.add_message('msg1', 'orders', {'data': 'test'}, FailureReason.TIMEOUT)
        self.dlq.add_message('msg1', 'orders', {'data': 'test'}, FailureReason.TIMEOUT)
        msg = self.dlq.get_message('msg1')
        self.assertEqual(msg.failure_count, 2)
    
    def test_list_messages(self):
        self.dlq.add_message('msg1', 'orders', {}, FailureReason.TIMEOUT)
        self.dlq.add_message('msg2', 'payments', {}, FailureReason.VALIDATION_ERROR)
        
        all_msgs = self.dlq.list_messages()
        self.assertEqual(len(all_msgs), 2)
        
        order_msgs = self.dlq.list_messages(queue='orders')
        self.assertEqual(len(order_msgs), 1)
    
    def test_failure_analysis(self):
        self.dlq.add_message('msg1', 'orders', {}, FailureReason.TIMEOUT)
        self.dlq.add_message('msg2', 'orders', {}, FailureReason.TIMEOUT)
        self.dlq.add_message('msg3', 'payments', {}, FailureReason.VALIDATION_ERROR)
        
        analysis = self.dlq.get_failure_analysis()
        self.assertEqual(analysis['total_messages'], 3)
        self.assertIn('timeout', analysis['failure_reasons'])
    
    def test_delete_message(self):
        self.dlq.add_message('msg1', 'orders', {}, FailureReason.TIMEOUT)
        self.assertTrue(self.dlq.delete_message('msg1'))
        self.assertIsNone(self.dlq.get_message('msg1'))

if __name__ == '__main__':
    unittest.main()
