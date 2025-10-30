# py-spy Emulator

A pure Python implementation of a sampling profiler inspired by py-spy.

## What This Emulates

**Emulates:** py-spy (Sampling profiler for Python programs)
**Original:** https://github.com/benfred/py-spy

## Features

- Statistical sampling profiler with minimal overhead
- Stack trace collection at regular intervals
- Function timing statistics (total and self time)
- Flame graph data generation
- Top-like live profiling view
- Context manager and decorator interfaces
- No external dependencies

## Core Components

- **py_spy_emulator.py**: Main implementation
  - `StackFrame`: Represents a single stack frame
  - `ProfileData`: Container for profiling data with statistics
  - `SamplingProfiler`: Main profiler using threading-based sampling
  - `ProfilerContext`: Context manager for easy profiling
  - `TopView`: Live 'top'-like profiling display
  - `profile()`: Decorator for profiling functions
  - `record()`: Record profiling data for a function
  - `dump()`: Dump current stack trace
  - `top()`: Display live profiling view

## Usage

### Context Manager

```python
from py_spy_emulator import ProfilerContext

with ProfilerContext(sample_rate=100) as profiler:
    # Code to profile
    my_function()
    
profiler.print_stats(top_n=20)
```

### Decorator

```python
from py_spy_emulator import profile

@profile(sample_rate=100)
def my_function():
    # Code to profile
    pass

my_function()  # Automatically profiled and results printed
```

### Manual Control

```python
from py_spy_emulator import SamplingProfiler

profiler = SamplingProfiler(sample_rate=100)
profiler.start()

# Run code to profile
my_function()

profile_data = profiler.stop()

# Get statistics
stats = profile_data.get_function_stats()
for func_name, data in stats.items():
    print(f"{func_name}: {data['total_time']:.3f}s ({data['total_percent']:.1f}%)")
```

### Record and Save Flame Graph

```python
from py_spy_emulator import record

def target_function():
    # Code to profile
    pass

profile_data = record(target_function, sample_rate=100, 
                     output_file="flamegraph.txt")
```

### Live Top View

```python
from py_spy_emulator import top

# Display live profiling view for 10 seconds
profile_data = top(duration=10.0, sample_rate=10)
```

### Dump Stack Trace

```python
from py_spy_emulator import dump

# Get current stack trace
stack = dump()
for frame in stack:
    print(frame)
```

## Testing

Run the test suite:

```bash
python test_py_spy_emulator.py
```

## Implementation Notes

- Uses threading for sampling (separate sampler thread)
- Collects stack traces using `sys._current_frames()`
- Statistical sampling with configurable sample rate (Hz)
- Tracks both total time (including callees) and self time
- Generates flame graph compatible data format
- Minimal performance overhead compared to deterministic profilers

## Profiling Metrics

- **Total Time**: Time spent in function including callees
- **Self Time**: Time spent in function excluding callees
- **Samples**: Number of times function appeared in samples
- **Percentage**: Proportion of total execution time

## Sample Rate

The sample rate (in Hz) determines how often the profiler collects stack traces:
- **Low rate (10-50 Hz)**: Lower overhead, less precise
- **Medium rate (100 Hz)**: Good balance (default)
- **High rate (200+ Hz)**: More precise, higher overhead

## Differences from py-spy

- py-spy is written in Rust for minimal overhead
- py-spy can attach to running processes
- py-spy has native integration with various Python implementations
- This emulator is pure Python and profiles only the current process
- This emulator uses threading while py-spy uses process inspection

## Why This Was Created

This emulator was created as part of the Emu-Soft project to provide statistical profiling capabilities without external dependencies. It enables performance analysis and optimization in self-contained environments, suitable for understanding program behavior and identifying performance bottlenecks.

## Example Output

```
Profiling Results (2.15s, 215 samples)
====================================================================================================
Function                                           Total%    Self%   Total(s)    Self(s)
----------------------------------------------------------------------------------------------------
fibonacci (test.py)                                 95.3%    45.2%      2.048      0.972
test_function (test.py)                            100.0%     4.7%      2.150      0.101
<module> (test.py)                                 100.0%     0.0%      2.150      0.000
```
