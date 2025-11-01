# PerProVis - Performance Profiling Visualizer

A pure Python performance profiling and visualization tool without external dependencies.

## What This Tool Does

**Purpose:** PerProVis profiles application performance, tracks function execution times, identifies bottlenecks, and visualizes performance data through various formats.

## Features

- **Function-Level Profiling** - Track execution time and call counts
- **Decorator Support** - Easy `@profile` decorator for functions
- **Context Manager** - Profile code blocks with `with profile_block()`
- **Call Stack Tracking** - Track nested function calls
- **Statistical Analysis** - Mean, median, percentiles, standard deviation
- **Hotspot Detection** - Identify slowest functions automatically
- **Flame Graph Generation** - Text-based flame graphs
- **Timeline Visualization** - Visualize execution timeline
- **Multiple Export Formats** - JSON, CSV, and text reports
- **Thread-safe** - Works with multi-threaded applications
- **Zero Dependencies** - Uses only Python standard library

## Core Components

- **PerformanceProfiler**: Main profiler class
- **FunctionCall**: Represents a single function execution
- **FunctionStats**: Aggregated statistics for a function
- **profile()**: Decorator for profiling functions
- **profile_block()**: Context manager for profiling code blocks

## Usage

### Basic Function Profiling

```python
from PerProVis import profile, get_profiler

@profile
def slow_function():
    total = 0
    for i in range(1000000):
        total += i
    return total

@profile
def fast_function():
    return sum(range(100))

# Run functions
result1 = slow_function()
result2 = fast_function()

# Get profiling report
profiler = get_profiler()
profiler.print_report()
```

### Profiling Code Blocks

```python
from PerProVis import profile_block, get_profiler

def process_data():
    with profile_block("data_loading"):
        # Simulate data loading
        data = list(range(100000))
    
    with profile_block("data_processing"):
        # Simulate processing
        processed = [x * 2 for x in data]
    
    with profile_block("data_saving"):
        # Simulate saving
        result = sum(processed)
    
    return result

# Run function
result = process_data()

# Print report
profiler = get_profiler()
profiler.print_report()
```

### Custom Profiler Instance

```python
from PerProVis import create_profiler

# Create a dedicated profiler
profiler = create_profiler()

@profiler.profile_function
def my_function():
    return sum(range(10000))

# Run and analyze
my_function()
my_function()
my_function()

stats = profiler.get_function_stats("my_function")
print(f"Called {stats.call_count} times")
print(f"Average time: {stats.get_avg_time()*1000:.2f}ms")
print(f"Total time: {stats.total_time:.4f}s")
```

### Finding Performance Hotspots

```python
from PerProVis import profile, get_profiler

@profile
def expensive_operation():
    result = 0
    for i in range(1000000):
        result += i ** 2
    return result

@profile
def cheap_operation():
    return sum(range(100))

# Run multiple times
for _ in range(10):
    expensive_operation()
    cheap_operation()

# Find hotspots
profiler = get_profiler()
hotspots = profiler.get_hotspots(limit=5)

print("Performance Hotspots:")
for name, total_time, call_count in hotspots:
    print(f"  {name}: {total_time:.4f}s ({call_count} calls)")
```

### Statistical Analysis

```python
from PerProVis import profile, get_profiler
import random
import time

@profile
def variable_function():
    # Simulate variable execution time
    time.sleep(random.uniform(0.001, 0.01))

# Run multiple times
for _ in range(50):
    variable_function()

# Get statistics
profiler = get_profiler()
stats = profiler.get_function_stats("variable_function")

print(f"Statistics for variable_function:")
print(f"  Call count: {stats.call_count}")
print(f"  Average: {stats.get_avg_time()*1000:.2f}ms")
print(f"  Median: {stats.get_median_time()*1000:.2f}ms")
print(f"  Min: {stats.min_time*1000:.2f}ms")
print(f"  Max: {stats.max_time*1000:.2f}ms")
print(f"  P95: {stats.get_percentile(95)*1000:.2f}ms")
print(f"  P99: {stats.get_percentile(99)*1000:.2f}ms")
print(f"  Std Dev: {stats.get_std_dev()*1000:.2f}ms")
```

### Flame Graph Visualization

```python
from PerProVis import profile, get_profiler

@profile
def task_a():
    sum(range(100000))

@profile
def task_b():
    sum(range(500000))

@profile
def task_c():
    sum(range(1000000))

# Run tasks multiple times
for _ in range(10):
    task_a()
    task_b()
    task_c()

# Generate flame graph
profiler = get_profiler()
flame_graph = profiler.generate_flame_graph_text(width=80)
print(flame_graph)
```

Output example:
```
Performance Flame Graph (Horizontal)
task_c                    ████████████████████████████████  55.2% (10 calls)
task_b                    ████████████████  27.6% (10 calls)
task_a                    █████  9.2% (10 calls)
```

### Timeline Visualization

```python
from PerProVis import profile, get_profiler
import time

@profile
def step_1():
    time.sleep(0.01)

@profile
def step_2():
    time.sleep(0.02)

@profile
def step_3():
    time.sleep(0.015)

# Execute steps
step_1()
step_2()
step_3()

# Generate timeline
profiler = get_profiler()
timeline = profiler.generate_timeline_text(limit=50)
print(timeline)
```

### Profiling Nested Function Calls

```python
from PerProVis import profile, get_profiler

@profile
def level_3():
    return sum(range(10000))

@profile
def level_2():
    result = 0
    for _ in range(3):
        result += level_3()
    return result

@profile
def level_1():
    result = 0
    for _ in range(2):
        result += level_2()
    return result

# Run nested calls
level_1()

# View call tree
profiler = get_profiler()
call_tree = profiler.get_call_tree()
print("Call Tree:", call_tree)

# Get all calls with stack information
all_calls = profiler.get_all_calls()
for call in all_calls[:5]:
    print(f"{call.name}: depth={len(call.call_stack)}, duration={call.duration*1000:.2f}ms")
```

### Export to JSON

```python
from PerProVis import profile, get_profiler

@profile
def my_function():
    return sum(range(100000))

# Run multiple times
for _ in range(10):
    my_function()

# Export to JSON
profiler = get_profiler()
profiler.export_to_json("performance_report.json")
print("Report exported to performance_report.json")
```

### Export to CSV

```python
from PerProVis import profile, get_profiler

@profile
def function_a():
    return sum(range(10000))

@profile
def function_b():
    return sum(range(50000))

# Run functions
for _ in range(20):
    function_a()
    function_b()

# Export to CSV
profiler = get_profiler()
profiler.export_to_csv("performance_stats.csv")
print("Statistics exported to performance_stats.csv")
```

### Getting Summary Statistics

```python
from PerProVis import profile, get_profiler

@profile
def task():
    sum(range(50000))

# Run tasks
for _ in range(100):
    task()

# Get summary
profiler = get_profiler()
summary = profiler.get_summary()

print("Profiling Summary:")
print(f"  Total functions profiled: {summary['total_functions']}")
print(f"  Total function calls: {summary['total_calls']}")
print(f"  Total execution time: {summary['total_time']:.4f}s")
print(f"  Average call time: {summary['avg_call_time']*1000:.2f}ms")
print(f"  Median call time: {summary['median_call_time']*1000:.2f}ms")
print(f"  P95 call time: {summary['p95_call_time']*1000:.2f}ms")
```

### Finding Slowest Individual Calls

```python
from PerProVis import profile, get_profiler
import random
import time

@profile
def sometimes_slow():
    # Occasionally take longer
    delay = random.uniform(0.001, 0.05)
    time.sleep(delay)

# Run multiple times
for _ in range(20):
    sometimes_slow()

# Find slowest calls
profiler = get_profiler()
slowest = profiler.get_slowest_calls(limit=5)

print("Slowest Individual Calls:")
for name, duration in slowest:
    print(f"  {name}: {duration*1000:.2f}ms")
```

### Profiling with Metadata

```python
from PerProVis import profile_block, get_profiler

def process_user_request(user_id, action):
    with profile_block("process_request", user_id=user_id, action=action):
        # Simulate processing
        result = sum(range(100000))
        return result

# Process requests
process_user_request(user_id=123, action="create")
process_user_request(user_id=456, action="update")

# Access call metadata
profiler = get_profiler()
calls = profiler.get_all_calls()
for call in calls:
    if call.metadata:
        print(f"Call: {call.name}, Metadata: {call.metadata}")
```

### Enable/Disable Profiling

```python
from PerProVis import create_profiler

profiler = create_profiler(enabled=True)

@profiler.profile_function
def my_function():
    return sum(range(100000))

# Profile this call
my_function()

# Disable profiling
profiler.disable()

# This call won't be profiled
my_function()

# Re-enable profiling
profiler.enable()

# Profile this call
my_function()

stats = profiler.get_function_stats("my_function")
print(f"Total calls recorded: {stats.call_count}")  # Should be 2
```

### Clear Profiling Data

```python
from PerProVis import profile, get_profiler

@profile
def my_function():
    return sum(range(100000))

# First batch
for _ in range(10):
    my_function()

profiler = get_profiler()
print(f"Calls before clear: {profiler.get_function_stats('my_function').call_count}")

# Clear data
profiler.clear()

# Second batch
for _ in range(5):
    my_function()

print(f"Calls after clear: {profiler.get_function_stats('my_function').call_count}")
```

### Multi-threaded Profiling

```python
from PerProVis import profile, get_profiler
import threading

@profile
def worker_task(worker_id):
    result = 0
    for i in range(100000):
        result += i
    return result

# Create threads
threads = []
for i in range(5):
    t = threading.Thread(target=worker_task, args=(i,))
    threads.append(t)
    t.start()

# Wait for completion
for t in threads:
    t.join()

# Analyze results
profiler = get_profiler()
stats = profiler.get_function_stats("worker_task")
print(f"Worker task called {stats.call_count} times across threads")

# View per-thread data
all_calls = profiler.get_all_calls()
thread_ids = set(call.thread_id for call in all_calls)
print(f"Total threads: {len(thread_ids)}")
```

## Testing

Run the test suite:

```bash
python test_PerProVis.py
```

## Implementation Notes

- **Thread-safe**: All operations protected by locks
- **Low overhead**: Minimal performance impact when disabled
- **High precision**: Uses `time.perf_counter()` for accurate timing
- **Memory efficient**: Stores only essential profiling data
- **No dependencies**: Pure Python standard library implementation

## API Reference

### PerformanceProfiler

**Constructor:**
- `PerformanceProfiler(enabled=True)` - Create profiler instance

**Methods:**
- `enable()` - Enable profiling
- `disable()` - Disable profiling
- `clear()` - Clear all profiling data
- `profile_function(func, name)` - Decorator for profiling
- `profile_block(name, **metadata)` - Context manager for profiling
- `get_function_stats(name)` - Get stats for a function
- `get_all_function_stats()` - Get stats for all functions
- `get_all_calls()` - Get all recorded calls
- `get_hotspots(limit)` - Get performance hotspots
- `get_slowest_calls(limit)` - Get slowest individual calls
- `get_call_tree()` - Build call tree
- `generate_flame_graph_text(width)` - Generate text flame graph
- `generate_timeline_text(limit)` - Generate timeline visualization
- `get_summary()` - Get summary statistics
- `export_to_json(filename)` - Export to JSON
- `export_to_csv(filename)` - Export to CSV
- `print_report(top_n)` - Print formatted report

### FunctionStats

**Attributes:**
- `name` - Function name
- `call_count` - Number of calls
- `total_time` - Total execution time
- `min_time` - Minimum execution time
- `max_time` - Maximum execution time
- `durations` - List of all durations

**Methods:**
- `get_avg_time()` - Get average time
- `get_median_time()` - Get median time
- `get_percentile(percentile)` - Get percentile time
- `get_std_dev()` - Get standard deviation

### FunctionCall

**Attributes:**
- `name` - Function name
- `start_time` - Start timestamp
- `end_time` - End timestamp
- `duration` - Execution duration
- `call_stack` - Call stack at time of call
- `thread_id` - Thread ID
- `metadata` - Additional metadata

### Global Functions

- `get_profiler()` - Get global profiler instance
- `profile(func, name)` - Global profiling decorator
- `profile_block(name, **metadata)` - Global profiling context manager
- `create_profiler(enabled)` - Create new profiler instance

## Use Cases

### Web Application Performance

```python
@profile
def handle_request(request):
    with profile_block("authentication"):
        user = authenticate(request)
    
    with profile_block("database_query"):
        data = fetch_user_data(user.id)
    
    with profile_block("template_rendering"):
        response = render_template(data)
    
    return response
```

### Algorithm Optimization

```python
@profile
def algorithm_v1(data):
    # Original implementation
    pass

@profile
def algorithm_v2(data):
    # Optimized implementation
    pass

# Compare performance
for _ in range(100):
    algorithm_v1(test_data)
    algorithm_v2(test_data)

profiler.print_report()
```

### Continuous Profiling

```python
profiler = create_profiler()

# Profile production code
@profiler.profile_function
def critical_path():
    # Business logic
    pass

# Periodically export metrics
import schedule
schedule.every(1).hours.do(lambda: profiler.export_to_json("hourly_profile.json"))
```

## Differences from Full Profilers

- **No C-level profiling**: Python functions only
- **Manual instrumentation**: Requires decorators/context managers
- **Text-only visualization**: No graphical flame graphs
- **Basic memory tracking**: Simplified memory measurements
- **No line-level profiling**: Function-level only

## Tips

1. **Use context managers** for profiling specific code blocks
2. **Clear data periodically** to avoid memory buildup in long-running apps
3. **Disable in production** if overhead is a concern
4. **Export regularly** for historical analysis
5. **Focus on hotspots** rather than trying to optimize everything
