"""
Developed by PowerShield, as an alternative to Kombu
"""

"""
Tests for Kombu emulator.
"""

import time
import json
from MessageBroker import (
    Connection, Channel, Exchange, Queue, Message,
    Producer, Consumer, ExchangeType
)


# Test storage for received messages
received_messages = []


def test_connection():
    """Test creating and managing connections."""
    conn = Connection(hostname="localhost", port=5672)
    conn.connect()
    assert conn._connected
    conn.disconnect()
    assert not conn._connected
    print("✓ Connection test passed")


def test_connection_context_manager():
    """Test connection as context manager."""
    with Connection() as conn:
        assert conn._connected
    assert not conn._connected
    print("✓ Connection context manager test passed")


def test_channel_creation():
    """Test creating channels."""
    conn = Connection()
    conn.connect()

    channel = conn.channel()
    assert channel is not None
    assert channel.connection == conn

    conn.disconnect()
    print("✓ Channel creation test passed")


def test_exchange_declaration():
    """Test declaring exchanges."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    exchange = channel.exchange_declare("test_exchange", type="direct")
    assert exchange.name == "test_exchange"
    assert exchange.type == "direct"

    conn.disconnect()
    print("✓ Exchange declaration test passed")


def test_queue_declaration():
    """Test declaring queues."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    queue = channel.queue_declare("test_queue")
    assert queue.name == "test_queue"
    assert queue.durable

    # Auto-generated name
    queue2 = channel.queue_declare()
    assert queue2.name.startswith("queue-")

    conn.disconnect()
    print("✓ Queue declaration test passed")


def test_queue_binding():
    """Test binding queues to exchanges."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    exchange = channel.exchange_declare("test_exchange", type="direct")
    queue = channel.queue_declare("test_queue")

    channel.queue_bind("test_queue", "test_exchange", routing_key="test.key")

    # Verify binding
    bound_queues = exchange.get_bound_queues("test.key")
    assert "test_queue" in bound_queues

    conn.disconnect()
    print("✓ Queue binding test passed")


def test_basic_publish_and_get():
    """Test basic message publishing and retrieval."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    # Declare queue
    queue = channel.queue_declare("test_queue")

    # Publish message directly to queue (default exchange)
    message = Message(body="Hello, World!")
    channel.basic_publish(message, routing_key="test_queue")

    # Get message
    received = channel.basic_get("test_queue", no_ack=True)
    assert received is not None
    assert received.body == "Hello, World!"

    conn.disconnect()
    print("✓ Basic publish and get test passed")


def test_producer():
    """Test using Producer to publish messages."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    # Declare queue
    queue = channel.queue_declare("producer_queue")

    # Create producer
    producer = Producer(channel, routing_key="producer_queue")

    # Publish message
    producer.publish({"message": "Hello from producer"})

    # Get message
    received = channel.basic_get("producer_queue", no_ack=True)
    assert received is not None

    # Deserialize
    body = json.loads(received.body)
    assert body["message"] == "Hello from producer"

    conn.disconnect()
    print("✓ Producer test passed")


def test_consumer():
    """Test using Consumer to receive messages."""
    global received_messages
    received_messages = []

    conn = Connection()
    conn.connect()
    channel = conn.channel()

    # Declare queue
    queue = channel.queue_declare("consumer_queue")

    # Callback function
    def callback(message):
        received_messages.append(message.body)

    # Create consumer
    consumer = Consumer(channel, queues=[queue], callbacks=[callback], no_ack=True)
    consumer.consume()

    # Publish messages
    producer = Producer(channel, routing_key="consumer_queue")
    producer.publish("Message 1")
    producer.publish("Message 2")
    producer.publish("Message 3")

    # Wait for consumption
    time.sleep(0.5)

    # Check received messages
    assert len(received_messages) >= 3

    conn.disconnect()
    print("✓ Consumer test passed")


def test_exchange_routing():
    """Test message routing through exchanges."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    # Declare exchange and queues
    exchange = channel.exchange_declare("routing_exchange", type="direct")
    queue1 = channel.queue_declare("queue1")
    queue2 = channel.queue_declare("queue2")

    # Bind queues with different routing keys
    channel.queue_bind("queue1", "routing_exchange", routing_key="key1")
    channel.queue_bind("queue2", "routing_exchange", routing_key="key2")

    # Publish to different routing keys
    producer = Producer(channel, exchange=exchange)
    producer.publish("Message for queue1", routing_key="key1")
    producer.publish("Message for queue2", routing_key="key2")

    # Retrieve messages
    msg1 = channel.basic_get("queue1", no_ack=True)
    msg2 = channel.basic_get("queue2", no_ack=True)

    assert msg1 is not None
    assert msg2 is not None

    # Parse JSON
    body1 = json.loads(msg1.body)
    body2 = json.loads(msg2.body)

    assert body1 == "Message for queue1"
    assert body2 == "Message for queue2"

    conn.disconnect()
    print("✓ Exchange routing test passed")


def test_fanout_exchange():
    """Test fanout exchange (broadcasts to all bound queues)."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    # Declare fanout exchange and queues
    exchange = channel.exchange_declare("fanout_exchange", type="fanout")
    queue1 = channel.queue_declare("fanout_queue1")
    queue2 = channel.queue_declare("fanout_queue2")

    # Bind queues (routing key doesn't matter for fanout)
    channel.queue_bind("fanout_queue1", "fanout_exchange", routing_key="")
    channel.queue_bind("fanout_queue2", "fanout_exchange", routing_key="")

    # Publish message
    producer = Producer(channel, exchange=exchange)
    producer.publish("Broadcast message")

    # Both queues should receive the message
    msg1 = channel.basic_get("fanout_queue1", no_ack=True)
    msg2 = channel.basic_get("fanout_queue2", no_ack=True)

    assert msg1 is not None
    assert msg2 is not None

    conn.disconnect()
    print("✓ Fanout exchange test passed")


def test_message_acknowledgment():
    """Test message acknowledgment."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    queue = channel.queue_declare("ack_queue")

    # Publish message
    message = Message(body="Test ack")
    channel.basic_publish(message, routing_key="ack_queue")

    # Get message without auto-ack
    received = channel.basic_get("ack_queue", no_ack=False)
    assert received is not None
    assert received.delivery_tag is not None

    # Acknowledge message
    received.ack()

    conn.disconnect()
    print("✓ Message acknowledgment test passed")


def test_message_rejection():
    """Test message rejection."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    queue = channel.queue_declare("reject_queue")

    # Publish message
    message = Message(body="Test reject")
    channel.basic_publish(message, routing_key="reject_queue")

    # Get and reject message
    received = channel.basic_get("reject_queue", no_ack=False)
    assert received is not None

    received.reject(requeue=False)

    conn.disconnect()
    print("✓ Message rejection test passed")


def test_multiple_messages():
    """Test handling multiple messages."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    queue = channel.queue_declare("multi_queue")
    producer = Producer(channel, routing_key="multi_queue")

    # Publish multiple messages
    for i in range(10):
        producer.publish(f"Message {i}")

    # Retrieve all messages
    messages = []
    for i in range(10):
        msg = channel.basic_get("multi_queue", no_ack=True)
        if msg:
            messages.append(json.loads(msg.body))

    assert len(messages) == 10
    assert messages[0] == "Message 0"
    assert messages[9] == "Message 9"

    conn.disconnect()
    print("✓ Multiple messages test passed")


def test_message_properties():
    """Test message properties and headers."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    queue = channel.queue_declare("props_queue")

    # Create message with properties
    message = Message(
        body="Test",
        headers={"priority": "high", "source": "test"},
        properties={"timestamp": "2024-01-01"},
    )

    channel.basic_publish(message, routing_key="props_queue")

    # Retrieve message
    received = channel.basic_get("props_queue", no_ack=True)
    assert received is not None
    assert received.headers["priority"] == "high"
    assert received.properties["timestamp"] == "2024-01-01"

    conn.disconnect()
    print("✓ Message properties test passed")


def test_queue_operations():
    """Test queue size and empty checks."""
    conn = Connection()
    conn.connect()
    channel = conn.channel()

    queue = channel.queue_declare("ops_queue")

    # Initially empty
    assert queue.empty()
    assert queue.qsize() == 0

    # Add messages
    producer = Producer(channel, routing_key="ops_queue")
    producer.publish("Message 1")
    producer.publish("Message 2")

    time.sleep(0.1)  # Allow messages to be queued

    # Check size
    assert queue.qsize() == 2
    assert not queue.empty()

    conn.disconnect()
    print("✓ Queue operations test passed")


if __name__ == "__main__":
    print("Running Kombu Emulator Tests...\n")

    test_connection()
    test_connection_context_manager()
    test_channel_creation()
    test_exchange_declaration()
    test_queue_declaration()
    test_queue_binding()
    test_basic_publish_and_get()
    test_producer()
    test_consumer()
    test_exchange_routing()
    test_fanout_exchange()
    test_message_acknowledgment()
    test_message_rejection()
    test_multiple_messages()
    test_message_properties()
    test_queue_operations()

    print("\n✅ All Kombu Emulator tests passed!")
