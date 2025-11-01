"""
FranzHare - Kafka/RabbitMQ Testing Harness

A comprehensive testing harness for Kafka and RabbitMQ message brokers,
providing utilities for testing message producers, consumers, and queue behavior.
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict
import queue


class BrokerType(Enum):
    """Type of message broker"""
    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"


class MessageStatus(Enum):
    """Status of a message"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class Message:
    """Represents a message in the queue"""
    id: str
    topic: str
    key: Optional[str]
    value: Any
    headers: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: MessageStatus = MessageStatus.PENDING
    retry_count: int = 0
    partition: Optional[int] = None


@dataclass
class ConsumerGroup:
    """Represents a consumer group"""
    group_id: str
    topics: List[str]
    offset: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    members: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Result of a test"""
    test_name: str
    passed: bool
    duration_ms: float
    messages_sent: int
    messages_received: int
    errors: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class FranzHare:
    """
    Kafka/RabbitMQ Testing Harness
    
    Provides utilities for testing message broker behavior without
    requiring actual Kafka or RabbitMQ instances.
    """
    
    def __init__(self, broker_type: BrokerType = BrokerType.KAFKA):
        """
        Initialize FranzHare testing harness
        
        Args:
            broker_type: Type of broker to emulate
        """
        self.broker_type = broker_type
        self.topics: Dict[str, List[Message]] = defaultdict(list)
        self.queues: Dict[str, queue.Queue] = {}
        self.consumer_groups: Dict[str, ConsumerGroup] = {}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.dead_letter_queue: List[Message] = []
        self.message_history: List[Message] = []
        self.produce_delay_ms: int = 0
        self.consume_delay_ms: int = 0
        self.failure_rate: float = 0.0
    
    def create_topic(self, topic_name: str, partitions: int = 1) -> None:
        """
        Create a topic
        
        Args:
            topic_name: Name of the topic
            partitions: Number of partitions (Kafka)
        """
        if topic_name not in self.topics:
            self.topics[topic_name] = []
        
        if self.broker_type == BrokerType.KAFKA:
            # Initialize partitions
            for i in range(partitions):
                pass  # Topic partitions are handled in message routing
    
    def create_queue(self, queue_name: str, max_size: Optional[int] = None) -> None:
        """
        Create a queue (RabbitMQ)
        
        Args:
            queue_name: Name of the queue
            max_size: Maximum queue size
        """
        if queue_name not in self.queues:
            maxsize = max_size or 0
            self.queues[queue_name] = queue.Queue(maxsize=maxsize)
    
    def produce(
        self,
        topic: str,
        value: Any,
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        partition: Optional[int] = None
    ) -> str:
        """
        Produce a message to a topic
        
        Args:
            topic: Topic or queue name
            value: Message value
            key: Message key (Kafka)
            headers: Message headers
            partition: Target partition (Kafka)
            
        Returns:
            Message ID
        """
        # Simulate production delay
        if self.produce_delay_ms > 0:
            time.sleep(self.produce_delay_ms / 1000.0)
        
        message_id = str(uuid.uuid4())
        
        message = Message(
            id=message_id,
            topic=topic,
            key=key,
            value=value,
            headers=headers or {},
            partition=partition
        )
        
        # Add to topic
        if topic not in self.topics:
            self.create_topic(topic)
        
        self.topics[topic].append(message)
        self.message_history.append(message)
        
        # Notify subscribers
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    callback(message)
                except Exception as e:
                    message.status = MessageStatus.FAILED
                    self.dead_letter_queue.append(message)
        
        return message_id
    
    def produce_batch(
        self,
        topic: str,
        messages: List[Tuple[Optional[str], Any]]
    ) -> List[str]:
        """
        Produce a batch of messages
        
        Args:
            topic: Topic name
            messages: List of (key, value) tuples
            
        Returns:
            List of message IDs
        """
        message_ids = []
        for key, value in messages:
            msg_id = self.produce(topic, value, key=key)
            message_ids.append(msg_id)
        
        return message_ids
    
    def consume(
        self,
        topic: str,
        group_id: Optional[str] = None,
        max_messages: int = 1,
        timeout_ms: int = 1000
    ) -> List[Message]:
        """
        Consume messages from a topic
        
        Args:
            topic: Topic name
            group_id: Consumer group ID
            max_messages: Maximum messages to consume
            timeout_ms: Timeout in milliseconds
            
        Returns:
            List of consumed messages
        """
        # Simulate consumption delay
        if self.consume_delay_ms > 0:
            time.sleep(self.consume_delay_ms / 1000.0)
        
        if topic not in self.topics:
            return []
        
        # Get consumer group offset
        offset = 0
        if group_id:
            if group_id not in self.consumer_groups:
                self.consumer_groups[group_id] = ConsumerGroup(
                    group_id=group_id,
                    topics=[topic]
                )
            offset = self.consumer_groups[group_id].offset.get(topic, 0)
        
        # Get messages from offset
        messages = self.topics[topic][offset:offset + max_messages]
        
        # Update offset for consumer group
        if group_id and messages:
            self.consumer_groups[group_id].offset[topic] = offset + len(messages)
        
        # Mark messages as delivered
        for msg in messages:
            msg.status = MessageStatus.DELIVERED
        
        return messages
    
    def subscribe(self, topic: str, callback: Callable[[Message], None]) -> None:
        """
        Subscribe to a topic with a callback
        
        Args:
            topic: Topic name
            callback: Callback function to process messages
        """
        self.subscribers[topic].append(callback)
    
    def acknowledge(self, message_id: str) -> bool:
        """
        Acknowledge a message
        
        Args:
            message_id: Message ID
            
        Returns:
            True if acknowledged
        """
        for msg in self.message_history:
            if msg.id == message_id:
                msg.status = MessageStatus.ACKNOWLEDGED
                return True
        return False
    
    def nack(self, message_id: str, requeue: bool = True) -> bool:
        """
        Negative acknowledge a message
        
        Args:
            message_id: Message ID
            requeue: Whether to requeue the message
            
        Returns:
            True if processed
        """
        for msg in self.message_history:
            if msg.id == message_id:
                msg.status = MessageStatus.FAILED
                msg.retry_count += 1
                
                if requeue and msg.retry_count < 3:
                    # Requeue message
                    self.topics[msg.topic].append(msg)
                else:
                    # Move to dead letter queue
                    self.dead_letter_queue.append(msg)
                
                return True
        return False
    
    def get_topic_messages(self, topic: str) -> List[Message]:
        """Get all messages in a topic"""
        return self.topics.get(topic, [])
    
    def get_topic_count(self, topic: str) -> int:
        """Get message count in a topic"""
        return len(self.topics.get(topic, []))
    
    def get_dead_letter_messages(self) -> List[Message]:
        """Get all messages in dead letter queue"""
        return self.dead_letter_queue
    
    def clear_topic(self, topic: str) -> None:
        """Clear all messages from a topic"""
        if topic in self.topics:
            self.topics[topic].clear()
    
    def clear_all(self) -> None:
        """Clear all topics and messages"""
        self.topics.clear()
        self.dead_letter_queue.clear()
        self.message_history.clear()
        self.consumer_groups.clear()
    
    def set_produce_delay(self, delay_ms: int) -> None:
        """Set production delay in milliseconds"""
        self.produce_delay_ms = delay_ms
    
    def set_consume_delay(self, delay_ms: int) -> None:
        """Set consumption delay in milliseconds"""
        self.consume_delay_ms = delay_ms
    
    def set_failure_rate(self, rate: float) -> None:
        """
        Set failure rate for message processing
        
        Args:
            rate: Failure rate between 0.0 and 1.0
        """
        self.failure_rate = max(0.0, min(1.0, rate))
    
    def get_consumer_group(self, group_id: str) -> Optional[ConsumerGroup]:
        """Get consumer group information"""
        return self.consumer_groups.get(group_id)
    
    def reset_consumer_group(self, group_id: str, topic: Optional[str] = None) -> None:
        """
        Reset consumer group offset
        
        Args:
            group_id: Consumer group ID
            topic: Specific topic to reset (all if None)
        """
        if group_id in self.consumer_groups:
            if topic:
                self.consumer_groups[group_id].offset[topic] = 0
            else:
                self.consumer_groups[group_id].offset.clear()
    
    def test_throughput(
        self,
        topic: str,
        num_messages: int,
        message_size: int = 100
    ) -> TestResult:
        """
        Test message throughput
        
        Args:
            topic: Topic name
            num_messages: Number of messages to send
            message_size: Size of each message in bytes
            
        Returns:
            TestResult object
        """
        start_time = time.time()
        
        # Generate test messages
        test_value = 'x' * message_size
        
        # Produce messages
        for i in range(num_messages):
            self.produce(topic, test_value, key=str(i))
        
        # Consume messages
        consumed = []
        while len(consumed) < num_messages:
            batch = self.consume(topic, max_messages=100)
            consumed.extend(batch)
            if not batch:
                break
        
        duration_ms = (time.time() - start_time) * 1000
        
        return TestResult(
            test_name='throughput_test',
            passed=len(consumed) == num_messages,
            duration_ms=duration_ms,
            messages_sent=num_messages,
            messages_received=len(consumed),
            details={
                'throughput_msg_per_sec': num_messages / (duration_ms / 1000) if duration_ms > 0 else 0,
                'message_size_bytes': message_size
            }
        )
    
    def test_consumer_group(
        self,
        topic: str,
        group_id: str,
        num_messages: int
    ) -> TestResult:
        """
        Test consumer group behavior
        
        Args:
            topic: Topic name
            group_id: Consumer group ID
            num_messages: Number of messages to test
            
        Returns:
            TestResult object
        """
        start_time = time.time()
        errors = []
        
        # Produce messages
        for i in range(num_messages):
            self.produce(topic, f"message_{i}", key=str(i))
        
        # Consume with consumer group
        consumed = self.consume(topic, group_id=group_id, max_messages=num_messages)
        
        # Try to consume again - should get no messages
        consumed_again = self.consume(topic, group_id=group_id, max_messages=10)
        
        if consumed_again:
            errors.append(f"Consumer group consumed {len(consumed_again)} duplicate messages")
        
        # Reset and consume again
        self.reset_consumer_group(group_id, topic)
        consumed_after_reset = self.consume(topic, group_id=group_id, max_messages=num_messages)
        
        if len(consumed_after_reset) != num_messages:
            errors.append(f"After reset, consumed {len(consumed_after_reset)} instead of {num_messages}")
        
        duration_ms = (time.time() - start_time) * 1000
        
        return TestResult(
            test_name='consumer_group_test',
            passed=len(errors) == 0,
            duration_ms=duration_ms,
            messages_sent=num_messages,
            messages_received=len(consumed),
            errors=errors,
            details={
                'duplicate_messages': len(consumed_again),
                'messages_after_reset': len(consumed_after_reset)
            }
        )
    
    def test_dead_letter_queue(
        self,
        topic: str,
        num_messages: int
    ) -> TestResult:
        """
        Test dead letter queue behavior
        
        Args:
            topic: Topic name
            num_messages: Number of messages to test
            
        Returns:
            TestResult object
        """
        start_time = time.time()
        
        # Produce messages
        message_ids = []
        for i in range(num_messages):
            msg_id = self.produce(topic, f"message_{i}")
            message_ids.append(msg_id)
        
        # NACK all messages multiple times to trigger DLQ
        for msg_id in message_ids:
            for _ in range(3):
                self.nack(msg_id, requeue=True)
        
        dlq_count = len(self.dead_letter_queue)
        
        duration_ms = (time.time() - start_time) * 1000
        
        return TestResult(
            test_name='dead_letter_queue_test',
            passed=dlq_count == num_messages,
            duration_ms=duration_ms,
            messages_sent=num_messages,
            messages_received=dlq_count,
            details={
                'dlq_messages': dlq_count,
                'expected': num_messages
            }
        )
    
    def test_ordering(
        self,
        topic: str,
        num_messages: int,
        partition: Optional[int] = None
    ) -> TestResult:
        """
        Test message ordering
        
        Args:
            topic: Topic name
            num_messages: Number of messages to test
            partition: Specific partition (Kafka)
            
        Returns:
            TestResult object
        """
        start_time = time.time()
        
        # Produce messages with sequence numbers
        for i in range(num_messages):
            self.produce(topic, {'seq': i}, key=str(i), partition=partition)
        
        # Consume all messages
        consumed = self.consume(topic, max_messages=num_messages)
        
        # Check ordering
        errors = []
        for i, msg in enumerate(consumed):
            if msg.value.get('seq') != i:
                errors.append(f"Out of order at position {i}: expected {i}, got {msg.value.get('seq')}")
        
        duration_ms = (time.time() - start_time) * 1000
        
        return TestResult(
            test_name='ordering_test',
            passed=len(errors) == 0,
            duration_ms=duration_ms,
            messages_sent=num_messages,
            messages_received=len(consumed),
            errors=errors
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get broker statistics"""
        total_messages = sum(len(msgs) for msgs in self.topics.values())
        
        status_counts = defaultdict(int)
        for msg in self.message_history:
            status_counts[msg.status.value] += 1
        
        return {
            'broker_type': self.broker_type.value,
            'total_topics': len(self.topics),
            'total_messages': len(self.message_history),
            'messages_in_topics': total_messages,
            'dead_letter_messages': len(self.dead_letter_queue),
            'consumer_groups': len(self.consumer_groups),
            'message_status': dict(status_counts)
        }
