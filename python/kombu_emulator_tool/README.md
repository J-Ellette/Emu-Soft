# Kombu Emulator - Messaging Library for Python

A Python messaging library emulator that replicates the core functionality of Kombu without requiring external message brokers like RabbitMQ or Redis.

## What is Kombu?

Kombu is a messaging library for Python that provides a simple, uniform API for interacting with various message brokers (RabbitMQ, Redis, Amazon SQS, etc.). It's the messaging backbone used by Celery for distributed task processing.

## Features

This emulator provides the following Kombu features:

### Core Functionality
- **Message Queues**: Create and manage message queues
- **Exchanges**: Support for direct, topic, and fanout exchanges
- **Message Routing**: Route messages based on routing keys and exchange types
- **Producers and Consumers**: High-level APIs for publishing and consuming messages
- **Message Acknowledgment**: Acknowledge or reject messages
- **Connection Management**: Thread-safe connection and channel management
- **No External Dependencies**: In-memory implementation without message brokers

### Exchange Types

1. **Direct Exchange**: Routes messages to queues based on exact routing key match
2. **Topic Exchange**: Routes messages based on pattern matching
3. **Fanout Exchange**: Broadcasts messages to all bound queues
4. **Headers Exchange**: Routes based on message headers (basic support)

## Installation

No external dependencies required! Just copy the `kombu_emulator.py` file to your project.

## Usage

### Basic Producer-Consumer Pattern

```python
from kombu_emulator import Connection, Producer, Consumer, Queue

# Create connection and channel
conn = Connection()
conn.connect()
channel = conn.channel()

# Declare a queue
queue = channel.queue_declare('my_queue')

# Producer - Send messages
producer = Producer(channel, routing_key='my_queue')
producer.publish({'message': 'Hello, World!'})

# Consumer - Receive messages
def callback(message):
    print(f"Received: {message.body}")
    message.ack()

consumer = Consumer(channel, queues=[queue], callbacks=[callback])
consumer.consume()
```

### Using Exchanges for Routing

```python
from kombu_emulator import Connection, Exchange, Queue, Producer

conn = Connection()
conn.connect()
channel = conn.channel()

# Declare exchange and queues
exchange = channel.exchange_declare('logs', type='direct')
queue = channel.queue_declare('error_logs')

# Bind queue to exchange with routing key
channel.queue_bind('error_logs', 'logs', routing_key='error')

# Publish to exchange
producer = Producer(channel, exchange=exchange)
producer.publish({'level': 'error', 'message': 'Something went wrong'}, 
                 routing_key='error')

# Consume messages
message = channel.basic_get('error_logs', no_ack=True)
if message:
    print(f"Error log: {message.body}")
```

### Fanout Exchange (Broadcast)

```python
from kombu_emulator import Connection, Exchange, Queue, Producer

conn = Connection()
conn.connect()
channel = conn.channel()

# Create fanout exchange
exchange = channel.exchange_declare('notifications', type='fanout')

# Create multiple queues
email_queue = channel.queue_declare('email_notifications')
sms_queue = channel.queue_declare('sms_notifications')

# Bind all queues to exchange
channel.queue_bind('email_notifications', 'notifications')
channel.queue_bind('sms_notifications', 'notifications')

# Broadcast message to all queues
producer = Producer(channel, exchange=exchange)
producer.publish({'event': 'user_signup', 'user_id': 123})

# All bound queues receive the message
email_msg = channel.basic_get('email_notifications', no_ack=True)
sms_msg = channel.basic_get('sms_notifications', no_ack=True)
```

### Message Acknowledgment

```python
from kombu_emulator import Connection, Producer

conn = Connection()
conn.connect()
channel = conn.channel()

# Declare queue
channel.queue_declare('tasks')

# Publish message
producer = Producer(channel, routing_key='tasks')
producer.publish({'task': 'process_data', 'data_id': 456})

# Get message without auto-ack
message = channel.basic_get('tasks', no_ack=False)

if message:
    try:
        # Process message
        process_task(message.body)
        
        # Acknowledge successful processing
        message.ack()
    except Exception as e:
        # Reject and requeue on failure
        message.reject(requeue=True)
```

### Context Manager for Connections

```python
from kombu_emulator import Connection, Producer

with Connection() as conn:
    channel = conn.channel()
    queue = channel.queue_declare('temp_queue')
    
    producer = Producer(channel, routing_key='temp_queue')
    producer.publish('Temporary message')
    
# Connection automatically closed
```

### Consumer with Callback

```python
from kombu_emulator import Connection, Queue, Consumer
import time

conn = Connection()
conn.connect()
channel = conn.channel()

queue = channel.queue_declare('work_queue')

# Define callback
def process_message(message):
    print(f"Processing: {message.body}")
    # Do work here
    message.ack()

# Start consuming
consumer = Consumer(
    channel, 
    queues=[queue], 
    callbacks=[process_message],
    no_ack=False
)
consumer.consume()

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    conn.disconnect()
```

### Message Properties and Headers

```python
from kombu_emulator import Connection, Message, Producer

conn = Connection()
conn.connect()
channel = conn.channel()

channel.queue_declare('priority_queue')

# Send message with headers and properties
message = Message(
    body={'data': 'important'},
    headers={'priority': 'high', 'source': 'api'},
    properties={'timestamp': '2024-01-01T00:00:00Z'}
)

channel.basic_publish(message, routing_key='priority_queue')

# Receive and inspect
received = channel.basic_get('priority_queue', no_ack=True)
print(f"Priority: {received.headers['priority']}")
print(f"Timestamp: {received.properties['timestamp']}")
```

### Multiple Producers and Consumers

```python
from kombu_emulator import Connection, Producer, Consumer, Queue
import threading

conn = Connection()
conn.connect()
channel = conn.channel()

queue = channel.queue_declare('shared_queue')

# Multiple producers
def producer_task(producer_id):
    producer = Producer(channel, routing_key='shared_queue')
    for i in range(5):
        producer.publish(f'Message from producer {producer_id}: {i}')

# Start producers in threads
threads = []
for i in range(3):
    t = threading.Thread(target=producer_task, args=(i,))
    t.start()
    threads.append(t)

# Wait for producers
for t in threads:
    t.join()

# Consumer processes all messages
messages_received = []
def callback(msg):
    messages_received.append(msg.body)
    msg.ack()

consumer = Consumer(channel, queues=[queue], callbacks=[callback])
consumer.consume()

# Wait for processing
time.sleep(2)
print(f"Received {len(messages_received)} messages")
```

## API Reference

### Connection

- `Connection(hostname, port, userid, password, virtual_host, transport)`: Create a connection
- `connect()`: Establish connection
- `disconnect()`: Close connection
- `channel()`: Create a new channel
- `release()`: Release resources

### Channel

- `exchange_declare(exchange, type, durable, auto_delete)`: Declare an exchange
- `queue_declare(queue, durable, exclusive, auto_delete)`: Declare a queue
- `queue_bind(queue, exchange, routing_key)`: Bind queue to exchange
- `basic_publish(message, exchange, routing_key)`: Publish a message
- `basic_get(queue, no_ack)`: Get a single message
- `basic_consume(queue, callback, no_ack, consumer_tag)`: Start consuming
- `basic_ack(delivery_tag)`: Acknowledge a message
- `basic_reject(delivery_tag, requeue)`: Reject a message
- `close()`: Close the channel

### Exchange

- `Exchange(name, type, durable, auto_delete, channel)`: Create an exchange
- `bind_to(queue_name, routing_key)`: Bind a queue
- `get_bound_queues(routing_key)`: Get queues for routing key

### Queue

- `Queue(name, exchange, routing_key, durable, exclusive, auto_delete, channel)`: Create a queue
- `put(message)`: Add a message
- `get(block, timeout)`: Get a message
- `qsize()`: Get queue size
- `empty()`: Check if empty

### Message

- `Message(body, content_type, content_encoding, headers, properties, delivery_info)`: Create a message
- `ack()`: Acknowledge the message
- `reject(requeue)`: Reject the message
- `requeue()`: Requeue the message

### Producer

- `Producer(channel, exchange, routing_key, serializer)`: Create a producer
- `publish(body, routing_key, exchange, **kwargs)`: Publish a message

### Consumer

- `Consumer(channel, queues, callbacks, no_ack)`: Create a consumer
- `consume(no_ack)`: Start consuming messages
- `register_callback(callback)`: Add a callback function

## Architecture

### Components

1. **Connection**: Manages the connection to the message broker (simulated)
2. **Channel**: Communication channel for operations
3. **Exchange**: Routes messages to queues based on routing rules
4. **Queue**: Stores messages for consumption
5. **Producer**: High-level API for publishing messages
6. **Consumer**: High-level API for consuming messages
7. **Message**: Represents a message with body, headers, and properties

### Message Flow

```
Producer → Exchange → [Routing Logic] → Queue(s) → Consumer
```

### Differences from Kombu

This emulator provides core Kombu functionality but differs in some ways:

**What's Included:**
- ✅ Connection and channel management
- ✅ Exchange types (direct, topic, fanout)
- ✅ Queue operations
- ✅ Message routing
- ✅ Producer and Consumer APIs
- ✅ Message acknowledgment
- ✅ Message properties and headers

**What's Not Included:**
- ❌ Actual broker connections (RabbitMQ, Redis, etc.)
- ❌ Message persistence across restarts
- ❌ Distributed messaging
- ❌ Advanced topic routing patterns
- ❌ Dead letter queues
- ❌ Message TTL
- ❌ Priority queues
- ❌ Complex consumer prefetch

For production systems requiring persistence, distribution, or advanced features, use actual Kombu with a message broker.

## Use Cases

This emulator is ideal for:

1. **Development and Testing**: Test messaging logic without a broker
2. **Educational Purposes**: Learn messaging patterns
3. **Single Application Messaging**: Inter-component communication
4. **Prototyping**: Quick messaging implementation
5. **Embedded Systems**: Messaging without external services

## Testing

Run the test suite:

```bash
python test_kombu_emulator.py
```

The test suite includes:
- Connection management
- Exchange and queue operations
- Message routing (direct, fanout)
- Producer and consumer functionality
- Message acknowledgment and rejection
- Multiple message handling
- Message properties and headers

## Performance

The emulator is designed for efficiency:

- **In-Memory Queues**: Fast message storage and retrieval
- **Thread-Safe**: Safe for concurrent producers and consumers
- **Low Overhead**: Direct function calls, no network latency
- **Scalable**: Handles multiple queues and consumers efficiently

For high-throughput production systems, consider using actual Kombu with a dedicated message broker like RabbitMQ.

## License

This is an emulator created for educational and development purposes. It implements the Kombu API without using the original Kombu code. For production use with message brokers, please use the official Kombu library.

## See Also

- [Kombu Documentation](https://kombu.readthedocs.io/)
- [RabbitMQ](https://www.rabbitmq.com/) - Popular AMQP message broker
- [Celery](https://docs.celeryproject.org/) - Distributed task queue using Kombu
- `infrastructure/tasks.py` - Celery emulator in this repository
- `rq_emulator_tool/` - RQ (Redis Queue) emulator
