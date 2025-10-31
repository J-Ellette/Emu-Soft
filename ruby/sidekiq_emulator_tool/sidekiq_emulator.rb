require 'json'
require 'thread'
require 'securerandom'
require 'time'

module Sidekiq
  # Worker module - include in worker classes
  module Worker
    def self.included(base)
      base.extend(ClassMethods)
    end
    
    module ClassMethods
      attr_accessor :queue_name, :retry_count, :retry_on_errors
      
      def perform_async(*args)
        job_id = SecureRandom.uuid
        job = {
          'class' => self.name,
          'args' => args,
          'jid' => job_id,
          'queue' => @queue_name || 'default',
          'retry' => @retry_count || 3,
          'created_at' => Time.now.to_f,
          'enqueued_at' => Time.now.to_f
        }
        
        Sidekiq::Queue.push(job)
        job_id
      end
      
      def perform_in(interval, *args)
        job_id = SecureRandom.uuid
        scheduled_at = Time.now + interval
        
        job = {
          'class' => self.name,
          'args' => args,
          'jid' => job_id,
          'queue' => @queue_name || 'default',
          'retry' => @retry_count || 3,
          'created_at' => Time.now.to_f,
          'scheduled_at' => scheduled_at.to_f
        }
        
        Sidekiq::ScheduledSet.add(job)
        job_id
      end
      
      def perform_at(timestamp, *args)
        interval = timestamp - Time.now
        perform_in(interval, *args)
      end
      
      def sidekiq_options(options = {})
        @queue_name = options[:queue] if options[:queue]
        @retry_count = options[:retry] if options.key?(:retry)
        @retry_on_errors = options[:retry_on] if options[:retry_on]
      end
    end
    
    def perform(*args)
      raise NotImplementedError, "Worker must implement perform method"
    end
  end
  
  # Job queue management
  class Queue
    @@queues = {}
    @@mutex = Mutex.new
    
    def self.push(job)
      @@mutex.synchronize do
        queue_name = job['queue']
        @@queues[queue_name] ||= []
        @@queues[queue_name] << job
      end
    end
    
    def self.pop(queue_name = 'default')
      @@mutex.synchronize do
        queue = @@queues[queue_name]
        return nil unless queue && !queue.empty?
        queue.shift
      end
    end
    
    def self.all_queues
      @@mutex.synchronize do
        @@queues.keys
      end
    end
    
    def self.size(queue_name = 'default')
      @@mutex.synchronize do
        queue = @@queues[queue_name]
        queue ? queue.size : 0
      end
    end
    
    def self.clear(queue_name = nil)
      @@mutex.synchronize do
        if queue_name
          @@queues[queue_name] = []
        else
          @@queues.clear
        end
      end
    end
    
    def self.jobs(queue_name = 'default')
      @@mutex.synchronize do
        @@queues[queue_name]&.dup || []
      end
    end
  end
  
  # Scheduled jobs set
  class ScheduledSet
    @@scheduled = []
    @@mutex = Mutex.new
    
    def self.add(job)
      @@mutex.synchronize do
        @@scheduled << job
        @@scheduled.sort_by! { |j| j['scheduled_at'] }
      end
    end
    
    def self.process_due_jobs
      @@mutex.synchronize do
        now = Time.now.to_f
        due_jobs = []
        
        @@scheduled.delete_if do |job|
          if job['scheduled_at'] <= now
            due_jobs << job
            true
          else
            false
          end
        end
        
        due_jobs.each do |job|
          Sidekiq::Queue.push(job)
        end
        
        due_jobs.size
      end
    end
    
    def self.size
      @@mutex.synchronize do
        @@scheduled.size
      end
    end
    
    def self.clear
      @@mutex.synchronize do
        @@scheduled.clear
      end
    end
    
    def self.jobs
      @@mutex.synchronize do
        @@scheduled.dup
      end
    end
  end
  
  # Retry set for failed jobs
  class RetrySet
    @@retries = []
    @@mutex = Mutex.new
    
    # Exponential backoff constants
    RETRY_EXPONENT = 4  # Exponential growth factor
    RETRY_BASE_DELAY = 15  # Base delay in seconds
    
    def self.add(job, error)
      @@mutex.synchronize do
        job['retry_count'] ||= 0
        job['retry_count'] += 1
        job['error_message'] = error.message
        job['error_class'] = error.class.name
        job['failed_at'] = Time.now.to_f
        
        max_retries = job['retry'] || 3
        
        if job['retry_count'] < max_retries
          # Calculate exponential backoff: (retry_count^4) + 15
          retry_delay = (job['retry_count'] ** RETRY_EXPONENT) + RETRY_BASE_DELAY
          job['scheduled_at'] = Time.now.to_f + retry_delay
          @@retries << job
          @@retries.sort_by! { |j| j['scheduled_at'] }
          true
        else
          # Move to dead set
          DeadSet.add(job, error)
          false
        end
      end
    end
    
    def self.process_due_retries
      @@mutex.synchronize do
        now = Time.now.to_f
        due_retries = []
        
        @@retries.delete_if do |job|
          if job['scheduled_at'] <= now
            due_retries << job
            true
          else
            false
          end
        end
        
        due_retries.each do |job|
          Sidekiq::Queue.push(job)
        end
        
        due_retries.size
      end
    end
    
    def self.size
      @@mutex.synchronize do
        @@retries.size
      end
    end
    
    def self.clear
      @@mutex.synchronize do
        @@retries.clear
      end
    end
    
    def self.jobs
      @@mutex.synchronize do
        @@retries.dup
      end
    end
  end
  
  # Dead set for jobs that exceeded retry limit
  class DeadSet
    @@dead = []
    @@mutex = Mutex.new
    @@max_size = 10000
    
    def self.add(job, error)
      @@mutex.synchronize do
        job['dead_at'] = Time.now.to_f
        job['error_message'] = error.message
        job['error_class'] = error.class.name
        
        @@dead.unshift(job)
        @@dead = @@dead.first(@@max_size) if @@dead.size > @@max_size
      end
    end
    
    def self.size
      @@mutex.synchronize do
        @@dead.size
      end
    end
    
    def self.clear
      @@mutex.synchronize do
        @@dead.clear
      end
    end
    
    def self.jobs
      @@mutex.synchronize do
        @@dead.dup
      end
    end
  end
  
  # Worker processor
  class Processor
    attr_reader :queue_name, :thread
    
    def initialize(queue_name = 'default')
      @queue_name = queue_name
      @running = false
      @thread = nil
    end
    
    def start
      @running = true
      @thread = Thread.new do
        while @running
          process_one_job
          sleep 0.1
        end
      end
    end
    
    def stop
      @running = false
      @thread&.join
    end
    
    def process_one_job
      job = Sidekiq::Queue.pop(@queue_name)
      return unless job
      
      begin
        worker_class = Object.const_get(job['class'])
        worker = worker_class.new
        worker.perform(*job['args'])
        
        # Job succeeded
        Statistics.increment_processed
        
      rescue StandardError => e
        # Job failed
        Statistics.increment_failed
        
        # Try to retry
        unless Sidekiq::RetrySet.add(job, e)
          puts "Job #{job['jid']} moved to dead set: #{e.message}"
        end
      end
    end
  end
  
  # Statistics tracking
  class Statistics
    @@processed = 0
    @@failed = 0
    @@mutex = Mutex.new
    
    def self.increment_processed
      @@mutex.synchronize do
        @@processed += 1
      end
    end
    
    def self.increment_failed
      @@mutex.synchronize do
        @@failed += 1
      end
    end
    
    def self.processed
      @@mutex.synchronize { @@processed }
    end
    
    def self.failed
      @@mutex.synchronize { @@failed }
    end
    
    def self.reset
      @@mutex.synchronize do
        @@processed = 0
        @@failed = 0
      end
    end
    
    def self.summary
      {
        processed: processed,
        failed: failed,
        success_rate: processed > 0 ? ((processed - failed).to_f / processed * 100).round(2) : 0
      }
    end
  end
  
  # Sidekiq manager - coordinates processors
  class Manager
    attr_reader :processors
    
    def initialize(concurrency: 5, queues: ['default'])
      @concurrency = concurrency
      @queues = queues
      @processors = []
      @scheduler_thread = nil
      @running = false
    end
    
    def start
      @running = true
      
      # Start processors for each queue - ensure at least one processor per queue
      @queues.each do |queue|
        processors_per_queue = [@concurrency / @queues.size, 1].max
        processors_per_queue.times do
          processor = Processor.new(queue)
          processor.start
          @processors << processor
        end
      end
      
      # Start scheduler thread
      @scheduler_thread = Thread.new do
        while @running
          Sidekiq::ScheduledSet.process_due_jobs
          Sidekiq::RetrySet.process_due_retries
          sleep 1
        end
      end
      
      puts "Sidekiq started with #{@processors.size} processors"
    end
    
    def stop
      @running = false
      
      # Stop all processors
      @processors.each(&:stop)
      @processors.clear
      
      # Stop scheduler
      @scheduler_thread&.join
      
      puts "Sidekiq stopped"
    end
    
    def stats
      {
        queues: @queues,
        processors: @processors.size,
        queue_sizes: @queues.map { |q| [q, Sidekiq::Queue.size(q)] }.to_h,
        scheduled: Sidekiq::ScheduledSet.size,
        retries: Sidekiq::RetrySet.size,
        dead: Sidekiq::DeadSet.size,
        statistics: Sidekiq::Statistics.summary
      }
    end
  end
  
  # Client API
  class Client
    def self.push(job)
      Sidekiq::Queue.push(job)
    end
    
    def self.push_bulk(jobs)
      jobs.each { |job| push(job) }
    end
  end
end

# Example workers
class EmailWorker
  include Sidekiq::Worker
  
  sidekiq_options queue: 'mailers', retry: 5
  
  def perform(user_email, subject, body)
    puts "Sending email to #{user_email}"
    puts "Subject: #{subject}"
    puts "Body: #{body}"
    # Simulate email sending
    sleep 0.1
    puts "Email sent successfully!"
  end
end

class ReportWorker
  include Sidekiq::Worker
  
  sidekiq_options queue: 'reports', retry: 3
  
  def perform(report_type, user_id)
    puts "Generating #{report_type} report for user #{user_id}"
    # Simulate report generation
    sleep 0.5
    puts "Report generated!"
  end
end

class CleanupWorker
  include Sidekiq::Worker
  
  sidekiq_options queue: 'default', retry: 2
  
  def perform(resource_type)
    puts "Cleaning up old #{resource_type}"
    sleep 0.2
    puts "Cleanup completed!"
  end
end
