# Pika Emulator - RabbitMQ Client Library

This module emulates the **pika** library, which is the most popular Python client for RabbitMQ. It provides AMQP 0-9-1 protocol functionality without requiring an actual RabbitMQ server.

## What is Pika?

Pika is a pure-Python implementation of the AMQP 0-9-1 protocol that works with RabbitMQ. It's used for:
- Message queue communication
- Distributed task processing
- Microservice communication
- Event-driven architectures
- Pub/sub messaging patterns

## Features

This emulator implements:

### Connection Management
- `BlockingConnection` - Synchronous connection
- `SelectConnection` - Async-style connection
- `ConnectionParameters` - Connection configuration
- `URLParameters` - Parse connection from AMQP URL
- `PlainCredentials` - Authentication credentials

### Channel Operations
- Exchange declaration (direct, fanout, topic, headers)
- Queue declaration with auto-naming support
- Queue binding and unbinding
- Queue purging and deletion
- Passive declarations for checking existence

### Message Publishing
- Publish to exchanges with routing keys
- Default exchange (direct-to-queue) support
- Message properties (content_type, delivery_mode, etc.)
- Mandatory flag for unroutable message detection
- Persistent and transient messages

### Message Consuming
- `basic_get` - Pull single message
- `basic_consume` - Push-based consumption
- Auto-acknowledgment mode
- Manual acknowledgment with `basic_ack`
- Negative acknowledgment with `basic_nack`
- Message rejection with `basic_reject`

### Quality of Service (QoS)
- Prefetch count limits
- Prefetch size limits
- Global vs. channel-specific QoS

### Routing Patterns
- **Direct**: Exact routing key match
- **Fanout**: Broadcast to all bound queues
- **Topic**: Pattern matching with `*` and `#` wildcards
- **Headers**: Header-based routing

### Advanced Features
- Message redelivery on nack/reject
- Redelivered flag tracking
- Multiple message acknowledgment
- Connection context managers
- Channel closing and error handling

## Usage Examples

### Basic Publisher

```python
from pika_emulator import BlockingConnection, ConnectionParameters, BasicProperties

# Create connection
params = ConnectionParameters(host='localhost')
connection = BlockingConnection(params)
channel = connection.channel()

# Declare queue
channel.queue_declare(queue='hello')

# Publish message
channel.basic_publish(
    exchange='',
    routing_key='hello',
    body=b'Hello World!'
)

connection.close()
```

### Basic Consumer

```python
from pika_emulator import BlockingConnection, ConnectionParameters

connection = BlockingConnection(ConnectionParameters())
channel = connection.channel()

channel.queue_declare(queue='hello')

# Get a single message
method, properties, body = channel.basic_get('hello', auto_ack=True)
if method:
    print(f"Received: {body.decode()}")
else:
    print("No messages in queue")

connection.close()
```

### Work Queue with Acknowledgments

```python
# Producer
connection = BlockingConnection(ConnectionParameters())
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)

message = b'A task that takes time...'
properties = BasicProperties(delivery_mode=2)  # Persistent

channel.basic_publish(
    exchange='',
    routing_key='task_queue',
    body=message,
    properties=properties
)

connection.close()

# Consumer
connection = BlockingConnection(ConnectionParameters())
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)
channel.basic_qos(prefetch_count=1)  # Fair dispatch

method, properties, body = channel.basic_get('task_queue', auto_ack=False)
if method:
    print(f"Processing: {body.decode()}")
    # Do work...
    channel.basic_ack(method.delivery_tag)

connection.close()
```

### Publish/Subscribe (Fanout Exchange)

```python
# Publisher
connection = BlockingConnection(ConnectionParameters())
channel = connection.channel()

channel.exchange_declare(exchange='logs', exchange_type='fanout')
channel.basic_publish(exchange='logs', routing_key='', body=b'Log message')

connection.close()

# Subscriber
connection = BlockingConnection(ConnectionParameters())
channel = connection.channel()

channel.exchange_declare(exchange='logs', exchange_type='fanout')

# Create exclusive queue with auto-generated name
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.queue

channel.queue_bind(exchange='logs', queue=queue_name)

method, properties, body = channel.basic_get(queue_name, auto_ack=True)
if method:
    print(f"Received: {body.decode()}")

connection.close()
```

### Topic Exchange (Pattern Routing)

```python
# Publisher
connection = BlockingConnection(ConnectionParameters())
channel = connection.channel()

channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

# Publish with different routing keys
channel.basic_publish(exchange='topic_logs', routing_key='kern.critical', body=b'Critical kernel error')
channel.basic_publish(exchange='topic_logs', routing_key='kern.info', body=b'Kernel info')
channel.basic_publish(exchange='topic_logs', routing_key='app.error', body=b'Application error')

connection.close()

# Consumer for all kernel messages
connection = BlockingConnection(ConnectionParameters())
channel = connection.channel()

channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.queue

# Bind with pattern
channel.queue_bind(exchange='topic_logs', queue=queue_name, routing_key='kern.*')

# Will receive messages with routing keys: kern.critical, kern.info
# Will NOT receive: app.error
```

### URL Connection

```python
from pika_emulator import BlockingConnection, URLParameters

# Connect using AMQP URL
params = URLParameters('amqp://user:pass@localhost:5672/vhost?heartbeat=30')
connection = BlockingConnection(params)
channel = connection.channel()

# Use channel...

connection.close()
```

### Context Manager

```python
from pika_emulator import BlockingConnection, ConnectionParameters

with BlockingConnection(ConnectionParameters()) as connection:
    channel = connection.channel()
    channel.queue_declare(queue='hello')
    channel.basic_publish(exchange='', routing_key='hello', body=b'Hello!')
    # Connection automatically closed
```

## Topic Exchange Pattern Matching

Topic exchanges use routing keys with words separated by dots and special wildcards:

- `*` (star) - Matches exactly one word
- `#` (hash) - Matches zero or more words

Examples:
- Pattern: `kern.*` matches `kern.critical`, `kern.info` but not `kern.critical.error`
- Pattern: `*.critical` matches `kern.critical`, `app.critical`
- Pattern: `kern.#` matches `kern`, `kern.critical`, `kern.critical.error`
- Pattern: `#.critical` matches `critical`, `kern.critical`, `app.system.critical`

## Differences from Real Pika

This emulator focuses on core functionality and has some simplifications:

1. **No network layer**: All operations are in-memory
2. **No broker**: State managed internally
3. **Simplified async**: `SelectConnection` is a thin wrapper
4. **Headers exchange**: Simplified to work like fanout
5. **No transactions**: Not implemented
6. **No confirms**: Publisher confirms not implemented
7. **No SSL/TLS**: Connection security not needed (in-memory)

## Testing

Run the comprehensive test suite:

```bash
python test_pika_emulator.py
```

Tests cover:
- Connection parameters and URL parsing
- Exchange and queue operations
- Message publishing and routing
- Message consumption and acknowledgment
- QoS settings
- Topic pattern matching
- Error handling

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for pika in development and testing:

```python
# Instead of:
# import pika

# Use:
import pika_emulator as pika

# Rest of your code remains the same
```

## Use Cases

Perfect for:
- **Development**: Test message-driven applications without RabbitMQ
- **CI/CD**: Run tests without external dependencies
- **Education**: Learn RabbitMQ concepts and patterns
- **Prototyping**: Quick experimentation with messaging patterns
- **Testing**: Unit test message producers and consumers in isolation

## Compatibility

Emulates core features of:
- pika 1.x API
- AMQP 0-9-1 protocol concepts
- RabbitMQ exchange types and routing

## License

Part of the Emu-Soft project. See main repository LICENSE.
