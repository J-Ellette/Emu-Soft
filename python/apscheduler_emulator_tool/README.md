# APScheduler (Advanced Python Scheduler) Emulator

A Python job scheduling library emulator that replicates the core functionality of APScheduler without requiring any external dependencies.

## What is APScheduler?

APScheduler (Advanced Python Scheduler) is a Python library that lets you schedule Python code to be executed later, either just once or periodically. You can add jobs dynamically and schedule them in three different ways: cron-style, interval-based, and date-based.

## Features

This emulator provides the following APScheduler features:

### Core Functionality
- **Multiple trigger types**: Date (one-time), Interval (periodic), and Cron (time-based)
- **Background execution**: Non-blocking scheduler runs in a separate thread
- **Job management**: Add, remove, pause, and resume jobs dynamically
- **Job tracking**: Track execution count, run times, and job state
- **Decorator support**: Schedule functions using decorators
- **Thread-safe**: Safe for use in multi-threaded applications

### Trigger Types

1. **Date Trigger**: Execute once at a specific date/time
2. **Interval Trigger**: Execute at fixed intervals (seconds, minutes, hours, days, weeks)
3. **Cron Trigger**: Execute at specific times (similar to cron)

## Installation

No external dependencies required! Just copy the `apscheduler_emulator.py` file to your project.

## Usage

### Basic Usage - Date Trigger (One-Time Execution)

```python
from apscheduler_emulator import BackgroundScheduler
from datetime import datetime, timedelta

scheduler = BackgroundScheduler()
scheduler.start()

# Schedule a job to run once in 10 seconds
run_time = datetime.now() + timedelta(seconds=10)
job = scheduler.add_job(
    send_email,
    trigger='date',
    run_date=run_time,
    args=['user@example.com', 'Welcome!']
)

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.shutdown()
```

### Interval Trigger (Periodic Execution)

```python
from apscheduler_emulator import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

# Run every 5 seconds
scheduler.add_job(
    check_system_health,
    trigger='interval',
    seconds=5
)

# Run every 2 minutes
scheduler.add_job(
    backup_database,
    trigger='interval',
    minutes=2
)

# Run every hour
scheduler.add_job(
    send_reports,
    trigger='interval',
    hours=1
)

# Run daily
scheduler.add_job(
    cleanup_logs,
    trigger='interval',
    days=1
)
```

### Cron Trigger (Time-Based Execution)

```python
from apscheduler_emulator import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

# Run at 3:00 AM every day
scheduler.add_job(
    daily_backup,
    trigger='cron',
    hour=3,
    minute=0
)

# Run every Monday at 9:00 AM
scheduler.add_job(
    weekly_report,
    trigger='cron',
    day_of_week='mon',
    hour=9,
    minute=0
)

# Run at the top of every hour
scheduler.add_job(
    hourly_sync,
    trigger='cron',
    minute=0
)
```

### Using Decorators

```python
from apscheduler_emulator import BackgroundScheduler, scheduled_job

scheduler = BackgroundScheduler()

@scheduled_job(scheduler, 'interval', seconds=30)
def monitor_servers():
    print("Checking server status...")

@scheduled_job(scheduler, 'cron', hour=0, minute=0)
def midnight_cleanup():
    print("Running midnight cleanup...")

scheduler.start()
```

### Job Management

```python
from apscheduler_emulator import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

# Add a job with custom ID
job = scheduler.add_job(
    process_queue,
    trigger='interval',
    seconds=10,
    id='queue_processor',
    name='Queue Processing Job'
)

# Get job by ID
job = scheduler.get_job('queue_processor')
print(f"Job: {job.name}, Run count: {job.run_count}")

# Pause job
scheduler.pause_job('queue_processor')

# Resume job
scheduler.resume_job('queue_processor')

# Remove job
scheduler.remove_job('queue_processor')

# Get all jobs
all_jobs = scheduler.get_jobs()
for job in all_jobs:
    print(f"{job.id}: {job.name} - {job.state.value}")
```

### Delayed Start for Intervals

```python
from datetime import datetime, timedelta
from apscheduler_emulator import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

# Start running in 1 hour, then every 30 minutes
start_time = datetime.now() + timedelta(hours=1)
scheduler.add_job(
    fetch_updates,
    trigger='interval',
    minutes=30,
    start_date=start_time
)
```

### Job with Arguments

```python
from apscheduler_emulator import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

# Positional arguments
scheduler.add_job(
    send_notification,
    trigger='interval',
    minutes=5,
    args=['admin@example.com', 'System status update']
)

# Keyword arguments
scheduler.add_job(
    log_metric,
    trigger='interval',
    seconds=30,
    kwargs={'metric': 'cpu_usage', 'threshold': 80}
)
```

### Tracking Job Execution

```python
from apscheduler_emulator import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

job = scheduler.add_job(
    periodic_task,
    trigger='interval',
    seconds=10,
    id='my_task'
)

# Later, check job status
job = scheduler.get_job('my_task')
print(f"Job has run {job.run_count} times")
print(f"Last run: {job.last_run_time}")
print(f"Next run: {job.next_run_time}")
print(f"State: {job.state.value}")
```

### Graceful Shutdown

```python
from apscheduler_emulator import BackgroundScheduler
import signal

scheduler = BackgroundScheduler()
scheduler.start()

# ... add jobs ...

def shutdown_handler(signum, frame):
    print("Shutting down scheduler...")
    scheduler.shutdown(wait=True)
    exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# Keep running
while True:
    time.sleep(1)
```

## API Reference

### BackgroundScheduler

- `BackgroundScheduler(timezone=None)`: Create a scheduler
- `start()`: Start the scheduler in background thread
- `shutdown(wait=True)`: Stop the scheduler
- `add_job(func, trigger, args, kwargs, id, name, **trigger_args)`: Add a job
- `remove_job(job_id)`: Remove a job
- `get_job(job_id)`: Get a job by ID
- `get_jobs()`: Get all jobs
- `pause_job(job_id)`: Pause a job
- `resume_job(job_id)`: Resume a job

### Job

- `id`: Unique job identifier
- `name`: Job name
- `state`: Current job state (PENDING, RUNNING, PAUSED, REMOVED)
- `next_run_time`: Next scheduled run time
- `last_run_time`: Last execution time
- `run_count`: Number of times job has executed
- `execute()`: Execute the job manually
- `pause()`: Pause the job
- `resume()`: Resume the job
- `remove()`: Mark job for removal

### Trigger Arguments

**Date Trigger:**
- `run_date`: datetime object or ISO format string

**Interval Trigger:**
- `weeks`: Number of weeks
- `days`: Number of days
- `hours`: Number of hours
- `minutes`: Number of minutes
- `seconds`: Number of seconds
- `start_date`: Optional start time (datetime)

**Cron Trigger:**
- `year`: 4-digit year
- `month`: Month (1-12)
- `day`: Day of month (1-31)
- `week`: ISO week (1-53)
- `day_of_week`: Day of week (0-6 or mon, tue, wed, etc.)
- `hour`: Hour (0-23)
- `minute`: Minute (0-59)
- `second`: Second (0-59)

## Architecture

### Components

1. **BackgroundScheduler**: Main scheduler class that manages jobs
   - Runs in a background thread
   - Uses a min-heap for efficient job scheduling
   - Thread-safe job management

2. **Job**: Represents a scheduled task
   - Tracks execution state and history
   - Supports different trigger types
   - Handles automatic rescheduling

3. **Triggers**: Determine when jobs should run
   - Date: One-time execution
   - Interval: Periodic execution
   - Cron: Time-based execution

### Differences from APScheduler

This emulator provides core APScheduler functionality but differs in some ways:

**What's Included:**
- ✅ Background scheduler
- ✅ Date, Interval, and Cron triggers
- ✅ Job management (add, remove, pause, resume)
- ✅ Job execution tracking
- ✅ Decorator support
- ✅ Thread-safe operations

**What's Not Included:**
- ❌ Blocking scheduler
- ❌ AsyncIO scheduler
- ❌ Job persistence (database storage)
- ❌ Multiple executors
- ❌ Complex cron expressions
- ❌ Job coalescing and misfires
- ❌ Event listeners
- ❌ Timezone support

For most scheduling needs, this emulator provides sufficient functionality. For advanced features like persistence or complex cron expressions, consider using the full APScheduler library.

## Use Cases

This emulator is ideal for:

1. **Periodic Tasks**: Running background jobs at regular intervals
2. **Scheduled Jobs**: One-time or recurring tasks at specific times
3. **Background Processing**: Non-blocking task execution
4. **System Maintenance**: Automated cleanup, backups, health checks
5. **Monitoring**: Periodic system monitoring and alerting
6. **Development/Testing**: Testing scheduled tasks without external dependencies

## Testing

Run the test suite:

```bash
python test_apscheduler_emulator.py
```

The test suite includes:
- Date trigger (one-time execution)
- Interval trigger (periodic execution)
- Cron trigger (time-based execution)
- Job management (add, remove, pause, resume)
- Multiple concurrent jobs
- Job state transitions
- Decorator-based scheduling
- Execution tracking

## Performance

The scheduler is efficient and lightweight:

- **Job Scheduling**: O(log n) insertion using min-heap
- **Job Execution**: Minimal overhead, direct function call
- **Memory Usage**: Small footprint per job
- **Thread Safety**: Lock-based synchronization

For high-frequency scheduling (sub-second intervals), consider the overhead of thread context switching.

## License

This is an emulator created for educational and development purposes. It implements the APScheduler API without using the original APScheduler code. For production use with advanced features, please use the official APScheduler library.

## See Also

- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Celery](https://docs.celeryproject.org/) - Distributed task queue
- `infrastructure/tasks.py` - Celery emulator in this repository
- `rq_emulator_tool/` - RQ (Redis Queue) emulator
