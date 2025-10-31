# Sidekiq Emulator - Background Jobs

A lightweight emulation of **Sidekiq**, the popular background job processing framework for Ruby that uses threads to handle many jobs at the same time in the same process.

## Features

This emulator implements core Sidekiq functionality:

### Worker Framework
- **Worker Module**: Include in job classes
- **perform Method**: Define job logic
- **perform_async**: Enqueue jobs asynchronously
- **perform_in**: Schedule jobs for future execution
- **perform_at**: Schedule jobs at specific time
- **sidekiq_options**: Configure worker behavior

### Job Queues
- **Multiple Queues**: Support different job queues
- **Queue Priority**: Process different queues
- **Queue Management**: Clear, inspect queues
- **Queue Statistics**: Monitor queue sizes
- **FIFO Processing**: First-in, first-out job processing

### Scheduling
- **Delayed Jobs**: Schedule jobs for future execution
- **Scheduled Set**: Manage scheduled jobs
- **Automatic Processing**: Process due jobs automatically
- **Time-based Execution**: Execute at specific times

### Retry Mechanism
- **Automatic Retries**: Retry failed jobs
- **Exponential Backoff**: Increasing delay between retries
- **Retry Limits**: Maximum retry attempts
- **Retry Tracking**: Monitor retry attempts
- **Error Handling**: Capture and log errors

### Dead Jobs
- **Dead Set**: Store jobs that exceeded retry limit
- **Error Information**: Store error details
- **Dead Job Inspection**: Review failed jobs
- **Size Limits**: Prevent unbounded growth

### Processing
- **Multi-threaded**: Process multiple jobs concurrently
- **Processor Pool**: Configurable concurrency
- **Manager**: Coordinate job processors
- **Statistics**: Track processed and failed jobs

### Statistics & Monitoring
- **Job Counts**: Track processed and failed jobs
- **Success Rate**: Calculate job success percentage
- **Queue Sizes**: Monitor queue depths
- **Retry Monitoring**: Track retry queue size

## What It Emulates

This tool emulates [Sidekiq](https://sidekiq.org/), the most popular background job processing framework in the Ruby ecosystem, used by companies like GitHub, Shopify, and Airbnb.

### Core Components Implemented

1. **Workers**
   - Worker module and DSL
   - Job enqueuing
   - Job scheduling
   - Configuration options

2. **Queues**
   - Multiple named queues
   - Queue operations
   - Queue monitoring

3. **Scheduler**
   - Delayed job execution
   - Scheduled job processing
   - Time-based triggers

4. **Retry**
   - Automatic retry logic
   - Exponential backoff
   - Dead job handling

5. **Manager**
   - Worker coordination
   - Concurrent processing
   - Statistics tracking

## Usage

### Define a Worker

```ruby
require_relative 'sidekiq_emulator'

class EmailWorker
  include Sidekiq::Worker
  
  # Configure worker options
  sidekiq_options queue: 'mailers', retry: 5
  
  def perform(user_email, subject, body)
    # Send email
    puts "Sending email to #{user_email}"
    # Email sending logic here
  end
end
```

### Enqueue Jobs

```ruby
# Enqueue job for immediate processing
job_id = EmailWorker.perform_async(
  'user@example.com',
  'Welcome',
  'Welcome to our service!'
)

puts "Enqueued job: #{job_id}"
```

### Schedule Jobs

```ruby
# Schedule job for 1 hour from now
EmailWorker.perform_in(3600, 'user@example.com', 'Reminder', 'Don't forget!')

# Schedule job at specific time
future_time = Time.now + 86400  # 24 hours
EmailWorker.perform_at(future_time, 'user@example.com', 'Daily Digest', 'Your digest')
```

### Multiple Workers

```ruby
class ReportWorker
  include Sidekiq::Worker
  
  sidekiq_options queue: 'reports', retry: 3
  
  def perform(report_type, user_id)
    puts "Generating #{report_type} report for user #{user_id}"
    # Generate report
  end
end

class CleanupWorker
  include Sidekiq::Worker
  
  sidekiq_options queue: 'maintenance', retry: 2
  
  def perform(resource_type)
    puts "Cleaning up #{resource_type}"
    # Cleanup logic
  end
end

# Enqueue different jobs
ReportWorker.perform_async('monthly', 123)
CleanupWorker.perform_async('temp_files')
```

### Start Processing

```ruby
# Create manager with configuration
manager = Sidekiq::Manager.new(
  concurrency: 5,                              # Number of worker threads
  queues: ['critical', 'default', 'low']       # Queues to process
)

# Start processing jobs
manager.start

# Jobs will be processed in background threads

# When done, stop the manager
manager.stop
```

### Queue Operations

```ruby
# Check queue size
size = Sidekiq::Queue.size('mailers')
puts "Queue has #{size} jobs"

# Get all jobs in queue
jobs = Sidekiq::Queue.jobs('mailers')
jobs.each do |job|
  puts "Job #{job['jid']}: #{job['class']}"
end

# Clear a queue
Sidekiq::Queue.clear('mailers')

# Clear all queues
Sidekiq::Queue.clear
```

### Monitor Statistics

```ruby
# Get manager statistics
stats = manager.stats

puts "Queues: #{stats[:queues]}"
puts "Processors: #{stats[:processors]}"
puts "Queue Sizes: #{stats[:queue_sizes]}"
puts "Scheduled: #{stats[:scheduled]}"
puts "Retries: #{stats[:retries]}"
puts "Dead: #{stats[:dead]}"
puts "Processed: #{stats[:statistics][:processed]}"
puts "Failed: #{stats[:statistics][:failed]}"
puts "Success Rate: #{stats[:statistics][:success_rate]}%"
```

### Bulk Job Enqueuing

```ruby
# Enqueue multiple jobs at once
jobs = []
100.times do |i|
  jobs << {
    'class' => 'EmailWorker',
    'args' => ["user#{i}@example.com", 'Bulk', 'Message'],
    'jid' => SecureRandom.uuid,
    'queue' => 'mailers',
    'retry' => 3,
    'created_at' => Time.now.to_f,
    'enqueued_at' => Time.now.to_f
  }
end

Sidekiq::Client.push_bulk(jobs)
```

### Complete Example

```ruby
require_relative 'sidekiq_emulator'

# Define workers
class NotificationWorker
  include Sidekiq::Worker
  
  sidekiq_options queue: 'notifications', retry: 5
  
  def perform(user_id, message)
    puts "Sending notification to user #{user_id}: #{message}"
    # Notification logic
    sleep 0.1  # Simulate work
  end
end

class DataExportWorker
  include Sidekiq::Worker
  
  sidekiq_options queue: 'exports', retry: 3
  
  def perform(export_type, user_id)
    puts "Exporting #{export_type} data for user #{user_id}"
    # Export logic
    sleep 0.5  # Simulate work
  end
end

# Enqueue immediate jobs
10.times do |i|
  NotificationWorker.perform_async(i, "Message #{i}")
end

# Schedule future jobs
DataExportWorker.perform_in(60, 'csv', 123)  # 1 minute from now
DataExportWorker.perform_in(3600, 'pdf', 456)  # 1 hour from now

# Start processing
manager = Sidekiq::Manager.new(
  concurrency: 3,
  queues: ['notifications', 'exports']
)

manager.start

# Let it run
sleep 5

# Check statistics
stats = manager.stats
puts "\nStatistics:"
puts "Processed: #{stats[:statistics][:processed]}"
puts "Failed: #{stats[:statistics][:failed]}"
puts "Scheduled: #{stats[:scheduled]}"

# Stop when done
manager.stop
```

### Error Handling

```ruby
class RiskyWorker
  include Sidekiq::Worker
  
  sidekiq_options queue: 'default', retry: 3
  
  def perform(task_id)
    # This might fail
    result = risky_operation(task_id)
    
    # If it raises an exception, Sidekiq will:
    # 1. Catch the error
    # 2. Add job to retry queue with exponential backoff
    # 3. Retry up to 3 times (as configured)
    # 4. If all retries fail, move to dead set
  end
  
  private
  
  def risky_operation(task_id)
    # Operation that might fail
  end
end
```

## Testing

```bash
ruby test_sidekiq_emulator.rb
```

## Use Cases

1. **Email Sending**: Queue email delivery jobs
2. **Report Generation**: Generate reports asynchronously
3. **Data Processing**: Process large datasets in background
4. **API Calls**: Make external API calls without blocking
5. **Image Processing**: Resize and optimize images
6. **Database Cleanup**: Periodic maintenance tasks
7. **Notifications**: Send push notifications
8. **Data Exports**: Generate and deliver data exports
9. **Webhook Delivery**: Retry webhook callbacks
10. **Batch Operations**: Process items in batches

## Key Differences from Real Sidekiq

1. **No Redis**: Doesn't use Redis for job storage
2. **In-Memory**: All jobs stored in memory
3. **Single Process**: No multi-process support
4. **No Persistence**: Jobs lost on restart
5. **Simplified Retry**: Basic exponential backoff only
6. **No Middleware**: Middleware chain not implemented
7. **No Web UI**: No dashboard/monitoring UI
8. **Limited Options**: Fewer configuration options
9. **No Batches**: Batch API not implemented
10. **No Cron**: Periodic jobs (cron-style) not included

## Sidekiq Concepts

### Workers
Workers are classes that include the Sidekiq::Worker module and define a perform method. They represent units of work to be done asynchronously.

### Queues
Queues organize jobs by priority or category. You can have different queues for different types of work (emails, reports, cleanup, etc.).

### Jobs
Jobs are serialized representations of work to be done. They contain the worker class name, arguments, and metadata.

### Scheduling
Jobs can be executed immediately or scheduled for future execution. Sidekiq checks scheduled jobs and enqueues them when due.

### Retries
When jobs fail, Sidekiq automatically retries them with exponential backoff. After exhausting retries, jobs move to the dead set.

### Concurrency
Sidekiq uses threads to process multiple jobs simultaneously within a single process, making it very efficient.

## Advanced Features (Not Implemented)

- **Middleware**: Job processing pipeline
- **Batches**: Track groups of related jobs
- **Unique Jobs**: Prevent duplicate job enqueuing
- **Rate Limiting**: Throttle job processing
- **Periodic Jobs**: Cron-style recurring jobs
- **Job Priority**: Within-queue priority
- **Server Middleware**: Cross-cutting concerns
- **Client Middleware**: Job enqueuing hooks
- **Job Lifecycle Callbacks**: Before/after hooks
- **ActiveJob Integration**: Rails ActiveJob adapter

## License

Educational emulator for learning purposes.

## References

- [Sidekiq Documentation](https://github.com/mperham/sidekiq/wiki)
- [Sidekiq Best Practices](https://github.com/mperham/sidekiq/wiki/Best-Practices)
- [Sidekiq GitHub](https://github.com/mperham/sidekiq)
