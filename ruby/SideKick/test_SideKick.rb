require_relative 'SideKick'

puts "=== Sidekiq Emulator Tests ===\n\n"

# Test 1: Basic job enqueuing
puts "Test 1: Basic Job Enqueuing"
puts "----------------------------"

job_id = EmailWorker.perform_async('user@example.com', 'Welcome', 'Welcome to our service!')
puts "✓ Enqueued job with ID: #{job_id}"
puts "✓ Queue size: #{Sidekiq::Queue.size('mailers')}"
puts

# Test 2: Multiple jobs
puts "Test 2: Multiple Jobs"
puts "----------------------"

5.times do |i|
  EmailWorker.perform_async("user#{i}@example.com", "Test #{i}", "Message #{i}")
end

puts "✓ Enqueued 5 jobs"
puts "✓ Queue size: #{Sidekiq::Queue.size('mailers')}"
puts

# Test 3: Scheduled jobs
puts "Test 3: Scheduled Jobs"
puts "----------------------"

# Schedule job for 2 seconds from now
EmailWorker.perform_in(2, 'delayed@example.com', 'Delayed', 'This is delayed')
puts "✓ Scheduled job for 2 seconds from now"
puts "✓ Scheduled set size: #{Sidekiq::ScheduledSet.size}"

# Schedule job at specific time
future_time = Time.now + 5
ReportWorker.perform_at(future_time, 'monthly', 123)
puts "✓ Scheduled job for specific time"
puts "✓ Scheduled set size: #{Sidekiq::ScheduledSet.size}"
puts

# Test 4: Different queues
puts "Test 4: Different Queues"
puts "------------------------"

EmailWorker.perform_async('test@example.com', 'Test', 'Body')
ReportWorker.perform_async('daily', 456)
CleanupWorker.perform_async('temp_files')

puts "✓ Enqueued jobs to different queues:"
puts "  - mailers: #{Sidekiq::Queue.size('mailers')}"
puts "  - reports: #{Sidekiq::Queue.size('reports')}"
puts "  - default: #{Sidekiq::Queue.size('default')}"
puts

# Test 5: Process jobs with manager
puts "Test 5: Processing Jobs"
puts "-----------------------"

# Create manager with multiple queues
manager = Sidekiq::Manager.new(
  concurrency: 3,
  queues: ['mailers', 'reports', 'default']
)

# Start processing
manager.start
puts "✓ Started Sidekiq manager"

# Let it process for a bit
sleep 2

# Check stats
stats = manager.stats
puts "\nQueue Statistics:"
puts "  Processed: #{stats[:statistics][:processed]}"
puts "  Failed: #{stats[:statistics][:failed]}"
puts "  Success Rate: #{stats[:statistics][:success_rate]}%"
puts

# Test 6: Process scheduled jobs
puts "Test 6: Processing Scheduled Jobs"
puts "----------------------------------"

# Wait for scheduled jobs to become due
puts "Waiting for scheduled jobs to become due..."
sleep 3

# Process due scheduled jobs
processed = Sidekiq::ScheduledSet.process_due_jobs
puts "✓ Processed #{processed} scheduled jobs"
puts "✓ Remaining scheduled: #{Sidekiq::ScheduledSet.size}"

# Let manager process them
sleep 1
puts

# Test 7: Retry failed jobs
puts "Test 7: Retry Mechanism"
puts "-----------------------"

class FailingWorker
  include Sidekiq::Worker
  
  sidekiq_options queue: 'default', retry: 3
  
  @@attempts = 0
  
  def perform(job_id)
    @@attempts += 1
    puts "  Attempt #{@@attempts} for job #{job_id}"
    
    # Fail first 2 attempts, succeed on 3rd
    if @@attempts < 3
      raise StandardError, "Simulated failure"
    end
    
    puts "  Job succeeded!"
  end
end

FailingWorker.perform_async('test-retry-job')
puts "✓ Enqueued failing job"

# Process the job (will fail and retry)
sleep 2
puts "✓ Retry set size: #{Sidekiq::RetrySet.size}"
puts

# Test 8: Final statistics
puts "Test 8: Final Statistics"
puts "------------------------"

sleep 2  # Let remaining jobs process

final_stats = manager.stats
puts "Final Queue Sizes:"
final_stats[:queue_sizes].each do |queue, size|
  puts "  #{queue}: #{size}"
end

puts "\nFinal Statistics:"
puts "  Total Processed: #{final_stats[:statistics][:processed]}"
puts "  Total Failed: #{final_stats[:statistics][:failed]}"
puts "  Success Rate: #{final_stats[:statistics][:success_rate]}%"
puts "  Scheduled: #{final_stats[:scheduled]}"
puts "  Retries: #{final_stats[:retries]}"
puts "  Dead: #{final_stats[:dead]}"
puts

# Stop the manager
manager.stop
puts "✓ Stopped Sidekiq manager"
puts

# Test 9: Bulk operations
puts "Test 9: Bulk Operations"
puts "-----------------------"

jobs = []
10.times do |i|
  jobs << {
    'class' => 'CleanupWorker',
    'args' => ["resource_#{i}"],
    'jid' => SecureRandom.uuid,
    'queue' => 'default',
    'retry' => 3,
    'created_at' => Time.now.to_f,
    'enqueued_at' => Time.now.to_f
  }
end

Sidekiq::Client.push_bulk(jobs)
puts "✓ Enqueued 10 jobs in bulk"
puts "✓ Queue size: #{Sidekiq::Queue.size('default')}"
puts

# Clean up
Sidekiq::Queue.clear
Sidekiq::ScheduledSet.clear
Sidekiq::RetrySet.clear
Sidekiq::DeadSet.clear
Sidekiq::Statistics.reset

puts "\n=== All Tests Completed ==="
