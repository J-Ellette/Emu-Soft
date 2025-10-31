"""
Tests for dramatiq emulator

Comprehensive test suite for task queue framework emulator functionality.


Developed by PowerShield
"""

import unittest
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from Background_Process_Manager import (
    actor, Actor, Message, Broker, Worker, Pipeline, group,
    ResultBackend, Results, get_broker, set_broker,
    DramatiqError, ConnectionError, RateLimitExceeded, ActorNotFound
)


class TestBroker(unittest.TestCase):
    """Test Broker functionality."""
    
    def setUp(self):
        """Create a fresh broker for each test."""
        self.broker = Broker()
    
    def test_broker_creation(self):
        """Test creating a broker."""
        broker = Broker()
        self.assertIsNotNone(broker)
    
    def test_declare_queue(self):
        """Test declaring a queue."""
        self.broker.declare_queue('test-queue')
        self.assertIn('test-queue', self.broker._queues)
    
    def test_enqueue_message(self):
        """Test enqueueing a message."""
        message = Message(
            queue_name='default',
            actor_name='test_actor',
            args=(1, 2),
            kwargs={'key': 'value'}
        )
        
        self.broker.enqueue(message)
        
        dequeued = self.broker.dequeue('default')
        self.assertIsNotNone(dequeued)
        self.assertEqual(dequeued.actor_name, 'test_actor')
    
    def test_delayed_message(self):
        """Test delayed message enqueueing."""
        message = Message(
            queue_name='default',
            actor_name='test_actor',
            args=()
        )
        
        # Enqueue with 100ms delay
        self.broker.enqueue(message, delay=100)
        
        # Should not be available immediately
        dequeued = self.broker.dequeue('default')
        self.assertIsNone(dequeued)
        
        # Wait for delay
        time.sleep(0.15)
        
        # Should be available now
        dequeued = self.broker.dequeue('default')
        self.assertIsNotNone(dequeued)


class TestActor(unittest.TestCase):
    """Test Actor functionality."""
    
    def setUp(self):
        """Create a fresh broker for each test."""
        self.broker = Broker()
        set_broker(self.broker)
    
    def test_actor_creation_decorator(self):
        """Test creating an actor with decorator."""
        @actor
        def test_task(x, y):
            return x + y
        
        self.assertIsInstance(test_task, Actor)
        self.assertEqual(test_task.actor_name, 'test_task')
    
    def test_actor_direct_call(self):
        """Test calling an actor directly."""
        @actor
        def add_numbers(x, y):
            return x + y
        
        result = add_numbers(5, 3)
        self.assertEqual(result, 8)
    
    def test_actor_send(self):
        """Test sending an actor message."""
        @actor
        def multiply(x, y):
            return x * y
        
        message = multiply.send(4, 5)
        
        self.assertIsInstance(message, Message)
        self.assertEqual(message.actor_name, 'multiply')
        self.assertEqual(message.args, (4, 5))
    
    def test_actor_with_options(self):
        """Test creating actor with options."""
        @actor(queue_name='custom-queue', max_retries=10)
        def custom_task():
            return "done"
        
        self.assertEqual(custom_task.queue_name, 'custom-queue')
        self.assertEqual(custom_task.max_retries, 10)
    
    def test_actor_send_with_options(self):
        """Test sending actor message with options."""
        @actor
        def delayed_task():
            return "completed"
        
        message = delayed_task.send_with_options(delay=1000)
        
        self.assertIsInstance(message, Message)
        self.assertIn('eta', message.options)


class TestMessage(unittest.TestCase):
    """Test Message functionality."""
    
    def test_message_creation(self):
        """Test creating a message."""
        message = Message(
            queue_name='default',
            actor_name='test_actor',
            args=(1, 2, 3),
            kwargs={'key': 'value'}
        )
        
        self.assertEqual(message.queue_name, 'default')
        self.assertEqual(message.actor_name, 'test_actor')
        self.assertEqual(message.args, (1, 2, 3))
        self.assertEqual(message.kwargs, {'key': 'value'})
        self.assertIsNotNone(message.message_id)
    
    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        message = Message(
            queue_name='default',
            actor_name='test_actor',
            args=(1,)
        )
        
        msg_dict = message.asdict()
        
        self.assertIn('queue_name', msg_dict)
        self.assertIn('actor_name', msg_dict)
        self.assertIn('message_id', msg_dict)


class TestWorker(unittest.TestCase):
    """Test Worker functionality."""
    
    def setUp(self):
        """Create a fresh broker for each test."""
        self.broker = Broker()
        set_broker(self.broker)
        self.results = []
    
    def test_worker_creation(self):
        """Test creating a worker."""
        worker = Worker(self.broker, queues=['default'])
        
        self.assertEqual(worker.broker, self.broker)
        self.assertEqual(worker.queues, ['default'])
    
    def test_worker_processes_messages(self):
        """Test that worker processes messages."""
        results = []
        
        @actor
        def collect_result(value):
            results.append(value)
            return value
        
        # Create and start worker
        worker = Worker(self.broker, queues=['default'])
        worker.start()
        
        # Send messages
        collect_result.send(1)
        collect_result.send(2)
        collect_result.send(3)
        
        # Wait for processing
        time.sleep(0.3)
        
        # Stop worker
        worker.stop()
        
        # Verify results
        self.assertEqual(sorted(results), [1, 2, 3])


class TestResultBackend(unittest.TestCase):
    """Test ResultBackend functionality."""
    
    def setUp(self):
        """Create a fresh result backend."""
        self.backend = ResultBackend()
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving results."""
        self.backend.store('msg-123', 'result-value')
        
        result = self.backend.get('msg-123')
        self.assertEqual(result, 'result-value')
    
    def test_get_nonexistent(self):
        """Test getting non-existent result."""
        result = self.backend.get('nonexistent')
        self.assertIsNone(result)
    
    def test_delete_result(self):
        """Test deleting a result."""
        self.backend.store('msg-456', 'value')
        self.backend.delete('msg-456')
        
        result = self.backend.get('msg-456')
        self.assertIsNone(result)


class TestResults(unittest.TestCase):
    """Test Results functionality."""
    
    def setUp(self):
        """Create a fresh result backend."""
        self.backend = ResultBackend()
        self.results = Results(self.backend)
    
    def test_get_result(self):
        """Test getting a result."""
        self.backend.store('msg-789', 'test-result')
        
        result = self.results.get('msg-789')
        self.assertEqual(result, 'test-result')
    
    def test_get_nonexistent_result(self):
        """Test getting non-existent result."""
        result = self.results.get('nonexistent')
        self.assertIsNone(result)


class TestPipeline(unittest.TestCase):
    """Test Pipeline functionality."""
    
    def setUp(self):
        """Create a fresh broker."""
        self.broker = Broker()
        set_broker(self.broker)
    
    def test_pipeline_creation(self):
        """Test creating a pipeline."""
        @actor
        def step1(x):
            return x + 1
        
        @actor
        def step2(x):
            return x * 2
        
        pipeline = Pipeline()
        pipeline | step1.send(5) | step2.send(10)
        
        self.assertEqual(len(pipeline.messages), 2)
    
    def test_pipeline_run(self):
        """Test running a pipeline."""
        @actor
        def task1():
            return "task1"
        
        @actor
        def task2():
            return "task2"
        
        pipeline = Pipeline()
        pipeline | task1.send() | task2.send()
        pipeline.run()
        
        # Verify messages were enqueued
        msg1 = self.broker.dequeue('default')
        msg2 = self.broker.dequeue('default')
        
        self.assertIsNotNone(msg1)
        self.assertIsNotNone(msg2)


class TestGroup(unittest.TestCase):
    """Test group functionality."""
    
    def setUp(self):
        """Create a fresh broker."""
        self.broker = Broker()
        set_broker(self.broker)
    
    def test_group_creation(self):
        """Test creating a group."""
        @actor
        def parallel_task(x):
            return x * 2
        
        g = group(
            parallel_task.send(1),
            parallel_task.send(2),
            parallel_task.send(3)
        )
        
        self.assertEqual(len(g.messages), 3)
    
    def test_group_run(self):
        """Test running a group."""
        @actor
        def batch_task(x):
            return x + 10
        
        g = group(
            batch_task.send(1),
            batch_task.send(2)
        )
        
        messages = g.run()
        
        self.assertEqual(len(messages), 2)
        
        # Verify messages were enqueued
        msg1 = self.broker.dequeue('default')
        msg2 = self.broker.dequeue('default')
        
        self.assertIsNotNone(msg1)
        self.assertIsNotNone(msg2)


class TestCompleteExample(unittest.TestCase):
    """Test a complete example with workers and results."""
    
    def test_task_processing_with_results(self):
        """Test complete task processing with result storage."""
        broker = Broker()
        backend = ResultBackend()
        broker.set_result_backend(backend)
        set_broker(broker)
        
        @actor
        def compute(x, y):
            return x * y + x + y
        
        # Start worker
        worker = Worker(broker, queues=['default'])
        worker.start()
        
        # Send task
        message = compute.send(5, 3)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Stop worker
        worker.stop()
        
        # Get result
        results = Results(backend)
        result = results.get(message.message_id)
        
        # 5 * 3 + 5 + 3 = 23
        self.assertEqual(result, 23)


class TestErrorHandling(unittest.TestCase):
    """Test error handling."""
    
    def test_dramatiq_error(self):
        """Test DramatiqError exception."""
        with self.assertRaises(DramatiqError):
            raise DramatiqError("Test error")
    
    def test_actor_not_found(self):
        """Test ActorNotFound exception."""
        with self.assertRaises(ActorNotFound):
            raise ActorNotFound("Actor not found")


if __name__ == '__main__':
    unittest.main()
