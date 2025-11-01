#!/usr/bin/env ruby
# Developed by PowerShield, as an alternative to RSpec

# RSpec Testing Framework Emulator
# Emulates core RSpec testing functionality

module RSpec
  class << self
    attr_accessor :configuration, :world
    
    def configure
      @configuration ||= Configuration.new
      yield @configuration if block_given?
    end
    
    def describe(description, &block)
      @world ||= World.new
      example_group = ExampleGroup.new(description)
      example_group.instance_eval(&block)
      @world.add_example_group(example_group)
      example_group
    end
  end
  
  class Configuration
    attr_accessor :formatter, :color, :fail_fast
    
    def initialize
      @formatter = :documentation
      @color = true
      @fail_fast = false
    end
  end
  
  class World
    attr_reader :example_groups
    
    def initialize
      @example_groups = []
    end
    
    def add_example_group(group)
      @example_groups << group
    end
    
    def run
      runner = Runner.new(@example_groups)
      runner.run
    end
  end
  
  class ExampleGroup
    attr_reader :description, :examples, :before_hooks, :after_hooks, :let_definitions
    
    def initialize(description)
      @description = description
      @examples = []
      @before_hooks = []
      @after_hooks = []
      @let_definitions = {}
    end
    
    def it(description, &block)
      @examples << Example.new(description, block)
    end
    
    def specify(description, &block)
      it(description, &block)
    end
    
    def before(scope = :each, &block)
      @before_hooks << block
    end
    
    def after(scope = :each, &block)
      @after_hooks << block
    end
    
    def let(name, &block)
      @let_definitions[name] = block
    end
    
    def subject(&block)
      let(:subject, &block)
    end
    
    def context(description, &block)
      nested = ExampleGroup.new("#{@description} #{description}")
      nested.instance_eval(&block)
      @examples.concat(nested.examples)
    end
  end
  
  class Example
    attr_reader :description, :block, :result, :exception
    
    def initialize(description, block)
      @description = description
      @block = block
      @result = nil
      @exception = nil
    end
    
    def run(context)
      @result = :passed
      begin
        context.instance_eval(&@block)
      rescue ExpectationNotMetError => e
        @result = :failed
        @exception = e
      rescue => e
        @result = :error
        @exception = e
      end
      @result
    end
    
    def passed?
      @result == :passed
    end
    
    def failed?
      @result == :failed
    end
  end
  
  class Runner
    def initialize(example_groups)
      @example_groups = example_groups
      @passed = 0
      @failed = 0
      @errors = 0
    end
    
    def run
      puts "\n"
      
      @example_groups.each do |group|
        puts "#{group.description}"
        
        group.examples.each do |example|
          context = ExampleContext.new(group.let_definitions)
          
          # Run before hooks
          group.before_hooks.each { |hook| context.instance_eval(&hook) }
          
          # Run example
          result = example.run(context)
          
          # Run after hooks
          group.after_hooks.each { |hook| context.instance_eval(&hook) }
          
          # Display result
          case result
          when :passed
            puts "  ✓ #{example.description}"
            @passed += 1
          when :failed
            puts "  ✗ #{example.description}"
            puts "    Failure: #{example.exception.message}"
            @failed += 1
          when :error
            puts "  E #{example.description}"
            puts "    Error: #{example.exception.class}: #{example.exception.message}"
            @errors += 1
          end
        end
        puts
      end
      
      print_summary
    end
    
    def print_summary
      total = @passed + @failed + @errors
      puts "\nFinished in 0.001 seconds"
      puts "#{total} examples, #{@failed} failures, #{@errors} errors"
      puts
      
      if @failed == 0 && @errors == 0
        puts "All tests passed! ✓"
      else
        puts "Some tests failed."
      end
    end
  end
  
  class ExampleContext
    def initialize(let_definitions)
      @let_definitions = let_definitions
      @let_cache = {}
    end
    
    def method_missing(method, *args, &block)
      if @let_definitions.key?(method)
        @let_cache[method] ||= instance_eval(&@let_definitions[method])
      else
        super
      end
    end
    
    def respond_to_missing?(method, include_private = false)
      @let_definitions.key?(method) || super
    end
  end
  
  class ExpectationNotMetError < StandardError; end
  
  module Matchers
    class Matcher
      def initialize(expected)
        @expected = expected
      end
      
      def matches?(actual)
        raise NotImplementedError
      end
      
      def failure_message
        "expected #{@expected}, got #{@actual}"
      end
    end
    
    class EqualMatcher < Matcher
      def matches?(actual)
        @actual = actual
        @actual == @expected
      end
      
      def failure_message
        "expected: #{@expected.inspect}\n     got: #{@actual.inspect}"
      end
    end
    
    class BeNilMatcher < Matcher
      def initialize
        super(nil)
      end
      
      def matches?(actual)
        @actual = actual
        @actual.nil?
      end
      
      def failure_message
        "expected nil, got #{@actual.inspect}"
      end
    end
    
    class BeTruthyMatcher < Matcher
      def initialize
        super(true)
      end
      
      def matches?(actual)
        @actual = actual
        !!@actual
      end
      
      def failure_message
        "expected truthy value, got #{@actual.inspect}"
      end
    end
    
    class BeFalseyMatcher < Matcher
      def initialize
        super(false)
      end
      
      def matches?(actual)
        @actual = actual
        !@actual
      end
      
      def failure_message
        "expected falsey value, got #{@actual.inspect}"
      end
    end
    
    class IncludeMatcher < Matcher
      def matches?(actual)
        @actual = actual
        @actual.include?(@expected)
      end
      
      def failure_message
        "expected #{@actual.inspect} to include #{@expected.inspect}"
      end
    end
    
    class RaiseMatcher < Matcher
      def initialize(expected = StandardError)
        super(expected)
      end
      
      def matches?(block)
        begin
          block.call
          false
        rescue @expected
          true
        rescue => e
          @actual_exception = e
          false
        end
      end
      
      def failure_message
        if @actual_exception
          "expected #{@expected}, got #{@actual_exception.class}"
        else
          "expected #{@expected} to be raised, but nothing was raised"
        end
      end
    end
    
    class BeGreaterThanMatcher < Matcher
      def matches?(actual)
        @actual = actual
        @actual > @expected
      end
      
      def failure_message
        "expected #{@actual} to be greater than #{@expected}"
      end
    end
    
    class BeLessThanMatcher < Matcher
      def matches?(actual)
        @actual = actual
        @actual < @expected
      end
      
      def failure_message
        "expected #{@actual} to be less than #{@expected}"
      end
    end
  end
  
  class Expectation
    def initialize(actual)
      @actual = actual
    end
    
    def to(matcher)
      unless matcher.matches?(@actual)
        raise ExpectationNotMetError, matcher.failure_message
      end
    end
    
    def not_to(matcher)
      if matcher.matches?(@actual)
        raise ExpectationNotMetError, "expected not to match, but it did"
      end
    end
    
    alias to_not not_to
  end
end

# Top-level DSL methods
def describe(description, &block)
  RSpec.describe(description, &block)
end

def expect(actual)
  RSpec::Expectation.new(actual)
end

def eq(expected)
  RSpec::Matchers::EqualMatcher.new(expected)
end

def be_nil
  RSpec::Matchers::BeNilMatcher.new
end

def be_truthy
  RSpec::Matchers::BeTruthyMatcher.new
end

def be_falsey
  RSpec::Matchers::BeFalseyMatcher.new
end

def include(expected)
  RSpec::Matchers::IncludeMatcher.new(expected)
end

def raise_error(expected = StandardError)
  RSpec::Matchers::RaiseMatcher.new(expected)
end

def be_greater_than(expected)
  RSpec::Matchers::BeGreaterThanMatcher.new(expected)
end

def be_less_than(expected)
  RSpec::Matchers::BeLessThanMatcher.new(expected)
end

# Run specs
def run_specs
  RSpec.world.run
end
