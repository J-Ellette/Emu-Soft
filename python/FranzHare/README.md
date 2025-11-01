# FranzHare - Kafka/RabbitMQ Testing Harness

A comprehensive testing harness for Kafka and RabbitMQ message brokers, providing utilities for testing message producers, consumers, and queue behavior without requiring actual broker instances.

## Features

- **Multi-Broker Support**: Emulate both Kafka and RabbitMQ
- **Message Production**: Produce single messages or batches
- **Message Consumption**: Consume with consumer groups and offsets
- **Subscription Model**: Subscribe to topics with callbacks
- **Dead Letter Queue**: Automatic DLQ handling for failed messages
- **Consumer Groups**: Full consumer group offset management
- **Testing Utilities**: Built-in throughput, ordering, and DLQ tests
- **Message Acknowledgment**: ACK/NACK with requeue support
- **Statistics**: Comprehensive broker and message statistics

## Usage

### Basic Setup

```python
from FranzHare import FranzHare, BrokerType

# Initialize harness
harness = FranzHare(broker_type=BrokerType.KAFKA)

# Create topic
harness.create_topic('events')
```

### Producing Messages

```python
# Produce single message
msg_id = harness.produce('events', {'user_id': 123, 'action': 'login'}, key='user123')

# Produce batch
messages = [
    ('key1', {'data': 'value1'}),
    ('key2', {'data': 'value2'}),
    ('key3', {'data': 'value3'})
]
msg_ids = harness.produce_batch('events', messages)
```

### Consuming Messages

```python
# Consume messages
messages = harness.consume('events', max_messages=10)

for msg in messages:
    print(f"Key: {msg.key}, Value: {msg.value}")
    harness.acknowledge(msg.id)
```

### Consumer Groups

```python
# Consume with consumer group
messages = harness.consume('events', group_id='consumer-group-1', max_messages=10)

# Offset is automatically tracked
messages2 = harness.consume('events', group_id='consumer-group-1', max_messages=10)
# Gets next batch

# Reset consumer group offset
harness.reset_consumer_group('consumer-group-1', 'events')
```

### Subscribe with Callbacks

```python
def process_message(message):
    print(f"Processing: {message.value}")
    # Process message
    
harness.subscribe('events', process_message)

# Messages produced will trigger callback
harness.produce('events', {'data': 'test'})
```

### Dead Letter Queue

```python
# NACK message with requeue
msg_id = harness.produce('events', {'data': 'test'})
harness.nack(msg_id, requeue=True)

# After multiple retries, message goes to DLQ
dlq_messages = harness.get_dead_letter_messages()
```

### Testing Utilities

```python
# Test throughput
result = harness.test_throughput('perf-topic', num_messages=1000, message_size=100)
print(f"Throughput: {result.details['throughput_msg_per_sec']} msg/sec")

# Test consumer group behavior
result = harness.test_consumer_group('events', 'test-group', num_messages=100)
print(f"Test passed: {result.passed}")

# Test message ordering
result = harness.test_ordering('events', num_messages=100)
print(f"Messages in order: {result.passed}")

# Test DLQ behavior
result = harness.test_dead_letter_queue('events', num_messages=10)
print(f"DLQ messages: {result.details['dlq_messages']}")
```

### Statistics

```python
stats = harness.get_statistics()
print(f"Total topics: {stats['total_topics']}")
print(f"Total messages: {stats['total_messages']}")
print(f"DLQ messages: {stats['dead_letter_messages']}")
print(f"Consumer groups: {stats['consumer_groups']}")
```

## API Reference

### FranzHare Class

**Methods:**
- `create_topic(topic_name, partitions)` - Create topic
- `produce(topic, value, key, headers, partition)` - Produce message
- `produce_batch(topic, messages)` - Produce batch
- `consume(topic, group_id, max_messages, timeout_ms)` - Consume messages
- `subscribe(topic, callback)` - Subscribe with callback
- `acknowledge(message_id)` - Acknowledge message
- `nack(message_id, requeue)` - Negative acknowledge
- `get_topic_messages(topic)` - Get all topic messages
- `get_dead_letter_messages()` - Get DLQ messages
- `reset_consumer_group(group_id, topic)` - Reset offset
- `test_throughput(topic, num_messages, message_size)` - Test throughput
- `test_consumer_group(topic, group_id, num_messages)` - Test consumer groups
- `test_ordering(topic, num_messages, partition)` - Test ordering
- `test_dead_letter_queue(topic, num_messages)` - Test DLQ
- `get_statistics()` - Get statistics

## Use Cases

- **Unit Testing**: Test message producers and consumers
- **Integration Testing**: Test message flow without brokers
- **Performance Testing**: Measure throughput and latency
- **Error Handling**: Test error scenarios and DLQ
- **Consumer Groups**: Test consumer group behavior
- **Order Testing**: Verify message ordering

## Testing

```bash
python test_FranzHare.py
```

## Dependencies

- Python 3.7+
- No external dependencies

## License

Part of the Emu-Soft project - see main repository LICENSE.
