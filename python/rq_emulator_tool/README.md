# RQ (Redis Queue) Emulator

A lightweight Python job queue emulator that replicates the core functionality of RQ (Redis Queue) without requiring Redis or any external dependencies.

## What is RQ?

RQ (Redis Queue) is a simple Python library for queueing jobs and processing them in the background with workers. It's backed by Redis and designed to have a low barrier to entry. It's much simpler than Celery but still very powerful for most use cases.

## Features

This emulator provides the following RQ features:

### Core Functionality
- **Job enqueueing**: Queue jobs for background processing
- **Worker execution**: Background workers process jobs from queues
- **Multiple queues**: Support for multiple named queues with priority
- **Job status tracking**: Track job states (queued, started, finished, failed)
- **Result retrieval**: Get job results with optional timeout
- **Job scheduling**: Schedule jobs to run at specific times or after delays
- **Failure handling**: Capture and report job failures with exception info
- **Job metadata**: Store and retrieve custom metadata for jobs

### API Compatibility
- `Job` class with status tracking and result retrieval
- `Queue` class for job management
- `Worker` class for job processing
- Burst mode for processing all jobs and exiting
- Multiple queue support for priority-based processing

## Installation

No external dependencies required! Just copy the `rq_emulator.py` file to your project.

## Usage

### Basic Usage

```python
from rq_emulator import Queue, Worker

# Define a job function
def add_numbers(x, y):
    return x + y

# Create a queue
queue = Queue('default')

# Enqueue a job
job = queue.enqueue(add_numbers, 5, 10)

# Create and start a worker
worker = Worker([queue])
worker.start(burst=True)  # Process all jobs and exit

# Get the result
result = job.get_result(timeout=5)
print(f"Result: {result}")  # Output: Result: 15
```

### Multiple Queues with Priority

```python
from rq_emulator import Queue, Worker

high_priority = Queue('high')
low_priority = Queue('low')

# Enqueue jobs to different queues
urgent_job = high_priority.enqueue(process_payment, order_id=123)
background_job = low_priority.enqueue(send_newsletter)

# Worker processes high priority queue first
worker = Worker([high_priority, low_priority])
worker.work(burst=True)
```

### Job Status Tracking

```python
from rq_emulator import Queue, Worker, JobStatus

queue = Queue('tasks')
job = queue.enqueue(long_running_task)

# Check job status
if job.is_queued():
    print("Job is waiting to be processed")

worker = Worker([queue])
worker.start()

# Poll for completion
while not job.is_finished() and not job.is_failed():
    time.sleep(1)

if job.is_finished():
    print(f"Job completed with result: {job.result}")
elif job.is_failed():
    print(f"Job failed: {job.exc_info}")

worker.stop()
```

### Scheduled Jobs

```python
from datetime import datetime, timedelta
from rq_emulator import Queue

queue = Queue('scheduled')

# Schedule a job to run in 5 minutes
job = queue.enqueue_in(timedelta(minutes=5), send_reminder, user_id=456)

# Schedule a job to run at a specific time
job = queue.enqueue_at(datetime(2024, 12, 31, 23, 59), send_new_year_message)
```

### Error Handling

```python
from rq_emulator import Queue, Worker

def risky_operation():
    raise ValueError("Something went wrong!")

queue = Queue('default')
job = queue.enqueue(risky_operation)

worker = Worker([queue])
worker.start(burst=True)
worker.stop()

if job.is_failed():
    print(f"Job failed: {job.exc_info}")
```

### Job Metadata and Tracking

```python
from rq_emulator import Queue

queue = Queue('default')
job = queue.enqueue(
    process_data,
    data_id=123,
    description="Process user data",
    timeout=300,  # 5 minutes
    result_ttl=3600  # Keep result for 1 hour
)

# Access job information
print(f"Job ID: {job.id}")
print(f"Description: {job.description}")
print(f"Created at: {job.created_at}")

# Convert to dictionary for storage/logging
job_dict = job.to_dict()
print(job_dict)
```

### Long-Running Workers

```python
from rq_emulator import Queue, Worker
import signal

queue = Queue('default')
worker = Worker([queue])

# Graceful shutdown handler
def shutdown_handler(signum, frame):
    print("Shutting down worker...")
    worker.stop()

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# Start worker (runs indefinitely until stopped)
print("Worker started. Press Ctrl+C to stop.")
worker.work()
```

## Architecture

### Components

1. **Job**: Represents a unit of work to be executed
   - Tracks status, result, and execution metadata
   - Supports timeout and result TTL configuration
   - Provides status checking methods

2. **Queue**: Manages jobs and provides enqueueing functionality
   - Named queues for organization
   - Thread-safe job storage
   - Support for job scheduling

3. **Worker**: Processes jobs from one or more queues
   - Multi-queue support with priority
   - Burst mode for finite execution
   - Background thread execution
   - Graceful shutdown

### Differences from RQ

This emulator provides the core RQ functionality but differs in some ways:

**What's Included:**
- ✅ Job enqueueing and execution
- ✅ Multiple queues and workers
- ✅ Job status tracking
- ✅ Result retrieval
- ✅ Failure handling
- ✅ Basic scheduling

**What's Not Included:**
- ❌ Redis backend (uses in-memory storage)
- ❌ Job persistence across restarts
- ❌ Distributed workers across machines
- ❌ Advanced retry mechanisms
- ❌ Job dependencies
- ❌ Connection management
- ❌ RQ Dashboard

For simple background job processing in a single application, this emulator provides sufficient functionality. For distributed systems or persistence requirements, consider using actual RQ with Redis.

## Testing

Run the test suite:

```bash
python test_rq_emulator.py
```

The test suite includes:
- Job creation and enqueueing
- Worker execution
- Multiple queues
- Job status transitions
- Error handling
- Scheduled jobs
- Concurrent job processing

## Use Cases

This emulator is ideal for:

1. **Development and Testing**: Test job queue logic without Redis
2. **Simple Background Tasks**: Process jobs in a single application
3. **Educational Purposes**: Understand how job queues work
4. **Embedded Systems**: Background processing without external services
5. **Prototyping**: Quick job queue implementation before scaling

## API Reference

### Job Class

- `Job(func, args, kwargs, result_ttl, timeout, job_id, description)`: Create a job
- `get_status()`: Get current status string
- `is_queued()`: Check if job is queued
- `is_started()`: Check if job has started
- `is_finished()`: Check if job is finished
- `is_failed()`: Check if job failed
- `get_result(timeout)`: Get job result (blocking)
- `to_dict()`: Convert job to dictionary

### Queue Class

- `Queue(name, is_async)`: Create a queue
- `enqueue(func, *args, **kwargs)`: Enqueue a job
- `enqueue_at(datetime, func, *args, **kwargs)`: Schedule job at specific time
- `enqueue_in(timedelta, func, *args, **kwargs)`: Schedule job after delay
- `fetch_job(job_id)`: Fetch job by ID
- `get_jobs()`: Get all jobs
- `get_job_ids()`: Get all job IDs
- `count()`: Get number of queued jobs
- `empty()`: Check if queue is empty

### Worker Class

- `Worker(queues, name)`: Create a worker
- `work(burst)`: Start processing jobs (blocking)
- `start(burst)`: Start worker in background thread
- `stop()`: Stop worker gracefully

## Performance

The emulator uses Python's threading and queue modules for efficient job processing:

- **Job Enqueueing**: O(1) - constant time
- **Job Retrieval**: O(1) - hash map lookup
- **Worker Processing**: Efficient multi-threaded execution
- **Memory Usage**: Minimal overhead per job

For high-throughput production systems, consider using actual RQ with Redis.

## License

This is an emulator created for educational and development purposes. It implements the RQ API without using the original RQ code. For production use with Redis, please use the official RQ library.

## See Also

- [RQ Documentation](https://python-rq.org/)
- [Celery](https://docs.celeryproject.org/) - More feature-rich alternative
- `infrastructure/tasks.py` - Celery emulator in this repository
