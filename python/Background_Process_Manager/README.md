# dramatiq Emulator - Task Queue Framework for Python

This module emulates the **dramatiq** library, which is a fast and reliable distributed task processing library for Python. It provides a simple API for defining background tasks and processing them asynchronously.

## What is dramatiq?

dramatiq is a background task processing library for Python 3.6+. It is designed to be:
- Simple and easy to use
- Fast and reliable
- Built for modern Python
- Production-ready with features like retries, rate limiting, and more

## Features

This emulator implements core dramatiq functionality:

### Actor System
- **Actor Decorator**: Define tasks as actors using simple decorators
- **Synchronous Execution**: Call actors directly for testing
- **Asynchronous Execution**: Send messages to execute actors in the background
- **Custom Options**: Configure queue names, retries, timeouts

### Message Broker
- **In-Memory Broker**: Simulates Redis/RabbitMQ broker
- **Queue Management**: Support for multiple queues
- **Delayed Messages**: Schedule tasks for future execution
- **Message Persistence**: Messages stored until processed

### Worker System
- **Background Processing**: Workers process messages from queues
- **Multi-Queue Support**: Workers can listen to multiple queues
- **Automatic Retry**: Failed tasks can be retried

### Result Storage
- **Result Backend**: Store and retrieve task results
- **TTL Support**: Results expire after configurable time
- **Blocking Retrieval**: Wait for results with timeout

### Advanced Features
- **Pipelines**: Chain multiple tasks together
- **Groups**: Execute multiple tasks in parallel
- **Custom Brokers**: Use your own broker implementation

## Usage Examples

### Basic Actor Definition

```python
from Background_Process_Manager import actor

@actor
def send_email(to, subject, body):
    """Send an email (simulated)."""
    print(f"Sending email to {to}: {subject}")
    return f"Email sent to {to}"

# Execute synchronously (for testing)
result = send_email("user@example.com", "Hello", "Welcome!")
print(result)  # Email sent to user@example.com

# Execute asynchronously
message = send_email.send("user@example.com", "Hello", "Welcome!")
print(f"Message ID: {message.message_id}")
```

### Actor with Custom Options

```python
from Background_Process_Manager import actor

@actor(queue_name='emails', max_retries=5, time_limit=30000)
def send_notification(user_id, notification_type):
    """Send a notification with custom configuration."""
    print(f"Sending {notification_type} notification to user {user_id}")
    return f"Notification sent"

# Send to the 'emails' queue
message = send_notification.send(123, "welcome")
```

### Working with Workers

```python
from Background_Process_Manager import actor, get_broker, Worker
import time

@actor
def process_data(data_id):
    print(f"Processing data {data_id}")
    return f"Processed {data_id}"

# Get the broker
broker = get_broker()

# Create and start a worker
worker = Worker(broker, queues=['default'])
worker.start()

# Send some tasks
process_data.send(1)
process_data.send(2)
process_data.send(3)

# Let the worker process tasks
time.sleep(1)

# Stop the worker
worker.stop()
```

### Storing and Retrieving Results

```python
from Background_Process_Manager import actor, get_broker, Worker, ResultBackend, Results
import time

# Set up result backend
broker = get_broker()
backend = ResultBackend()
broker.set_result_backend(backend)

@actor
def calculate(x, y):
    return x * y + x + y

# Start worker
worker = Worker(broker, queues=['default'])
worker.start()

# Send task
message = calculate.send(10, 5)

# Wait for processing
time.sleep(0.5)

# Get result
results = Results(backend)
result = results.get(message.message_id)
print(f"Result: {result}")  # Result: 65

worker.stop()
```

### Delayed Tasks

```python
from Background_Process_Manager import actor

@actor
def scheduled_task(task_name):
    print(f"Executing scheduled task: {task_name}")
    return "Done"

# Schedule task to run after 5000ms (5 seconds)
message = scheduled_task.send_with_options(
    args=("Daily Report",),
    delay=5000
)

print("Task scheduled for later execution")
```

### Pipelines - Chaining Tasks

```python
from Background_Process_Manager import actor, Pipeline

@actor
def download_file(url):
    print(f"Downloading {url}")
    return f"file_{url}.dat"

@actor
def process_file(filename):
    print(f"Processing {filename}")
    return f"processed_{filename}"

@actor
def upload_result(processed_file):
    print(f"Uploading {processed_file}")
    return "uploaded"

# Create a pipeline
pipeline = Pipeline()
pipeline | download_file.send("http://example.com/data") | \
           process_file.send("file_example.dat") | \
           upload_result.send("processed_file.dat")

# Execute the pipeline
pipeline.run()
```

### Groups - Parallel Execution

```python
from Background_Process_Manager import actor, group, get_broker, Worker
import time

@actor
def resize_image(image_id, size):
    print(f"Resizing image {image_id} to {size}")
    return f"resized_{image_id}_{size}"

# Start worker
broker = get_broker()
worker = Worker(broker, queues=['default'])
worker.start()

# Create a group of parallel tasks
g = group(
    resize_image.send(1, "small"),
    resize_image.send(1, "medium"),
    resize_image.send(1, "large")
)

# Run all tasks in parallel
messages = g.run()
print(f"Started {len(messages)} parallel tasks")

time.sleep(1)
worker.stop()
```

### Complete Example: Image Processing Service

```python
from Background_Process_Manager import actor, get_broker, Worker, ResultBackend, Results
import time

# Set up infrastructure
broker = get_broker()
backend = ResultBackend()
broker.set_result_backend(backend)

@actor(queue_name='downloads')
def download_image(url):
    """Simulate downloading an image."""
    print(f"Downloading image from {url}")
    time.sleep(0.1)
    return {"filename": "image.jpg", "size": 1024}

@actor(queue_name='processing')
def resize_image(image_data, width, height):
    """Simulate resizing an image."""
    print(f"Resizing {image_data['filename']} to {width}x{height}")
    time.sleep(0.1)
    return {
        "filename": f"resized_{width}x{height}_{image_data['filename']}",
        "size": width * height
    }

@actor(queue_name='uploads')
def upload_to_s3(image_data):
    """Simulate uploading to S3."""
    print(f"Uploading {image_data['filename']} to S3")
    time.sleep(0.1)
    return f"s3://bucket/{image_data['filename']}"

# Start workers for different queues
download_worker = Worker(broker, queues=['downloads'])
processing_worker = Worker(broker, queues=['processing'])
upload_worker = Worker(broker, queues=['uploads'])

download_worker.start()
processing_worker.start()
upload_worker.start()

# Process an image
msg1 = download_image.send("http://example.com/photo.jpg")
time.sleep(0.2)

# Get downloaded image data
results_helper = Results(backend)
downloaded = results_helper.get(msg1.message_id)

if downloaded:
    # Resize the image
    msg2 = resize_image.send(downloaded, 800, 600)
    time.sleep(0.2)
    
    # Get resized image
    resized = results_helper.get(msg2.message_id)
    
    if resized:
        # Upload to S3
        msg3 = upload_to_s3.send(resized)
        time.sleep(0.2)
        
        # Get upload result
        upload_url = results_helper.get(msg3.message_id)
        print(f"Image uploaded to: {upload_url}")

# Clean up
download_worker.stop()
processing_worker.stop()
upload_worker.stop()
```

### Error Handling

```python
from Background_Process_Manager import actor, ActorNotFound

@actor
def risky_task(value):
    if value < 0:
        raise ValueError("Value must be positive")
    return value * 2

# This will work
result = risky_task(5)
print(result)  # 10

# This will raise an error when processed
message = risky_task.send(-5)
# Worker will log the error and potentially retry
```

## Testing

Run the comprehensive test suite:

```bash
python test_Background_Process_Manager.py
```

Tests cover:
- Broker message enqueueing and dequeueing
- Actor definition and execution
- Message creation and serialization
- Worker processing
- Result storage and retrieval
- Delayed message execution
- Pipelines and groups
- Error handling
- Complete integration scenarios

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for dramatiq in development and testing:

```python
# Instead of:
# import dramatiq

# Use:
import Background_Process_Manager as dramatiq

# The rest of your code remains unchanged
@dramatiq.actor
def my_task(x, y):
    return x + y
```

## Use Cases

Perfect for:
- **Local Development**: Develop task queues without Redis/RabbitMQ
- **Testing**: Test async task logic without external dependencies
- **CI/CD**: Run task tests in pipelines without broker setup
- **Learning**: Understand task queue patterns
- **Prototyping**: Quickly prototype background job systems
- **Education**: Teach async task processing concepts

## Limitations

This is an emulator for development and testing purposes:
- In-memory only (no persistence)
- Single-process workers (no distributed processing)
- Simplified retry logic
- No rate limiting implementation
- No middleware system
- Limited to basic broker features

## Supported Features

### Core Features
- ✅ Actor decorator
- ✅ Synchronous execution
- ✅ Asynchronous message sending
- ✅ Message broker
- ✅ Worker processing
- ✅ Result backend
- ✅ Delayed messages
- ✅ Multiple queues
- ✅ Pipelines
- ✅ Groups

### Configuration Options
- ✅ queue_name
- ✅ max_retries
- ✅ min_backoff
- ✅ max_backoff
- ✅ time_limit
- ✅ priority

### Advanced Features
- ✅ Custom actors
- ✅ Message options
- ✅ Result storage
- ✅ Worker management

## Real-World Task Queue Concepts

This emulator teaches the following concepts:

1. **Asynchronous Processing**: Offload work to background
2. **Message Brokers**: Queue-based task distribution
3. **Worker Pools**: Parallel task processing
4. **Retry Logic**: Handling transient failures
5. **Result Backends**: Storing task outputs
6. **Task Chaining**: Building workflows
7. **Parallel Execution**: Processing multiple tasks simultaneously

## Compatibility

Emulates core features of:
- dramatiq 1.x API patterns
- Actor-based task definitions
- Common task queue patterns

## License

Part of the Emu-Soft project. See main repository LICENSE.
