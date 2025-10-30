# memory_profiler Emulator

A pure Python implementation of a memory profiler for Python programs.

## What This Emulates

**Emulates:** memory_profiler (Memory usage profiler for Python)
**Original:** https://github.com/pythonprofilers/memory_profiler

## Features

- Line-by-line memory usage tracking
- Memory increment tracking per line
- Memory usage over time monitoring
- Decorator-based profiling
- Process memory statistics
- Memory leak detection
- Built on Python's tracemalloc module

## Core Components

- **memory_profiler_emulator.py**: Main implementation
  - `MemorySnapshot`: Memory state at a specific point
  - `LineMemoryStats`: Memory statistics per line of code
  - `FunctionMemoryProfile`: Complete memory profile for a function
  - `MemoryProfiler`: Low-level memory profiling
  - `LineProfiler`: Line-by-line profiler with decorator support
  - `MemoryUsageMonitor`: Monitor memory over time
  - `profile()`: Decorator for profiling functions
  - `memory_usage()`: Get memory samples while running a function
  - `show_results()`: Profile and display results immediately

## Usage

### Basic Decorator Usage

```python
from memory_profiler_emulator import profile

@profile
def my_function():
    data1 = [0] * 1000000  # Allocate ~4MB
    data2 = [1] * 2000000  # Allocate ~8MB
    result = sum(data1) + sum(data2)
    del data1
    return result

my_function()
```

Output:
```
================================================================================
Function: my_function (test.py)
Memory increment: +8.123 MB
Peak memory: 12.456 MB
================================================================================
Line    Memory (MB) Increment (MB)  Occurrences Code
--------------------------------------------------------------------------------
10            4.123          +4.000            1 data1 = [0] * 1000000
11           12.345          +8.222            1 data2 = [1] * 2000000
12           12.346          +0.001            1 result = sum(data1) + sum(data2)
13            8.223          -4.123            1 del data1
```

### Manual Profiling

```python
from memory_profiler_emulator import LineProfiler

profiler = LineProfiler(backend='tracemalloc')

def my_function():
    data = [0] * 1000000
    return sum(data)

result = profiler.profile_function(my_function)
profiler.print_stats()
```

### Memory Usage Over Time

```python
from memory_profiler_emulator import MemoryUsageMonitor

monitor = MemoryUsageMonitor(interval=0.1)
monitor.start()

# Do some work
for i in range(10):
    monitor.sample()
    data = [0] * (i * 100000)
    del data

timeline = monitor.stop()

# Plot or analyze timeline
for elapsed, memory_mb in timeline:
    print(f"{elapsed:.2f}s: {memory_mb:.2f} MB")
```

### Memory Usage Function

```python
from memory_profiler_emulator import memory_usage

def target_function():
    data = [0] * 1000000
    return sum(data)

# Get memory samples while running
samples = memory_usage(target_function, interval=0.05)

print(f"Memory samples: {samples}")
print(f"Peak memory: {max(samples):.2f} MB")
```

### Show Results Immediately

```python
from memory_profiler_emulator import show_results

def my_function():
    data = [0] * 1000000
    return sum(data)

result = show_results(my_function)
# Results are printed automatically
```

## Testing

Run the test suite:

```bash
python test_memory_profiler_emulator.py
```

## Implementation Notes

- Uses Python's built-in `tracemalloc` module for memory tracking
- Line-by-line profiling uses `sys.settrace()` for execution tracking
- Minimal performance overhead compared to manual tracking
- Memory measurements in bytes, displayed in MB
- Tracks both total memory and memory increments

## Memory Metrics

- **Memory Usage**: Total memory at each line
- **Memory Increment**: Change in memory from previous line
- **Peak Memory**: Maximum memory used during execution
- **Occurrences**: Number of times each line was executed

## Use Cases

- **Memory Leak Detection**: Identify where memory is being allocated but not freed
- **Optimization**: Find memory-intensive operations
- **Memory Profiling**: Understand memory usage patterns
- **Performance Analysis**: Correlate memory usage with execution time
- **Capacity Planning**: Estimate memory requirements

## Differences from memory_profiler

- memory_profiler can track multiple processes
- memory_profiler has IPython integration
- memory_profiler supports subprocess tracking
- This emulator is pure Python with no external dependencies
- This emulator uses tracemalloc for accurate tracking

## Why This Was Created

This emulator was created as part of the Emu-Soft project to provide memory profiling capabilities without external dependencies. It enables memory analysis and optimization in self-contained environments, suitable for understanding memory usage patterns and identifying memory leaks.

## Example Output

```
================================================================================
Function: fibonacci (example.py)
Memory increment: +0.125 MB
Peak memory: 10.500 MB
================================================================================
Line    Memory (MB) Increment (MB)  Occurrences Code
--------------------------------------------------------------------------------
5            10.250          +0.000           21 if n <= 1:
6            10.250          +0.000            2 return n
7            10.375          +0.125           19 return fibonacci(n - 1) + fibonacci(n
```
