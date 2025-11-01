# PerProVis - Performance Profiling Visualizer

A pure Python implementation of an advanced performance profiling visualizer without external dependencies, going beyond basic Prometheus metrics.

## What This Provides

**Purpose:** Advanced performance profiling with flame graphs, hotspot detection, and memory leak analysis
**Use Case:** In-depth performance analysis and optimization of Python applications

## Features

- **CPU Profiling** with stack trace collection
- **Hotspot Detection** identifying performance bottlenecks
- **Flame Graph Generation** for visualization
- **Call Graph Analysis** showing function relationships
- **Memory Profiling** with leak detection
- **Time-Series Metrics** tracking performance over time
- **Profile Comparison** (diff between profiles)
- **Manual and Automatic** sampling modes
- **Thread-safe** concurrent profiling
- **Zero External Dependencies** - pure Python

## Core Components

- **PerProVis.py**: Main implementation
  - `PerProVis`: Main profiler class
  - `StackFrame`: Represents a single stack frame
  - `Sample`: Profiling sample with stack trace
  - `Hotspot`: Performance hotspot with metrics
  - `MemorySnapshot`: Memory usage snapshot
  - `FlameGraphNode`: Node in flame graph structure

## Usage

### Basic Profiling (Manual Sampling)

```python
from PerProVis import PerProVis

# Initialize profiler
profiler = PerProVis(sampling_interval_ms=10)

# Add samples manually
stack_trace = [
    ('main', 'app.py', 10),
    ('process_request', 'handlers.py', 45),
    ('query_database', 'db.py', 123)
]

profiler.add_sample(stack_trace)

# Continue adding samples...
for i in range(100):
    profiler.add_sample(stack_trace)

# Get sample count
print(f"Collected {profiler.get_sample_count()} samples")
```

### Automatic Profiling

```python
from PerProVis import PerProVis
import time

profiler = PerProVis(sampling_interval_ms=10)

# Start profiling
profiler.start_profiling()

# Run your code
def my_function():
    time.sleep(0.1)
    return "result"

for i in range(10):
    my_function()

# Stop profiling
profiler.stop_profiling()

print(f"Profiled for {profiler.get_profiling_duration():.2f} seconds")
print(f"Collected {profiler.get_sample_count()} samples")
```

### Finding Hotspots

```python
from PerProVis import PerProVis

profiler = PerProVis()

# Add samples (from your profiling)
# ... profiling code here ...

# Find top 10 hotspots
hotspots = profiler.find_hotspots(top_n=10)

print("Performance Hotspots:")
for i, hotspot in enumerate(hotspots, 1):
    print(f"\n{i}. {hotspot.function_name} ({hotspot.filename})")
    print(f"   Sample Count: {hotspot.sample_count}")
    print(f"   Percentage: {hotspot.percentage:.2f}%")
    print(f"   Total Time: {hotspot.total_time_ms:.2f}ms")
    print(f"   Avg Time: {hotspot.average_time_ms():.2f}ms")
```

### Generating Flame Graphs

```python
from PerProVis import PerProVis
import json

profiler = PerProVis()

# Add samples
# ... profiling code here ...

# Generate flame graph
flame_graph = profiler.generate_flame_graph()

# Export as JSON
flame_json = profiler.get_flame_graph_json()
print(flame_json)

# Or access the structure directly
print(f"Root node: {flame_graph.name}")
print(f"Total samples: {flame_graph.value}")
print(f"Direct children: {len(flame_graph.children)}")

# Convert to dict for further processing
graph_dict = flame_graph.to_dict()
```

### Call Graph Analysis

```python
from PerProVis import PerProVis

profiler = PerProVis()

# Add samples with nested calls
profiler.add_sample([
    ('main', 'app.py', 10),
    ('process', 'handlers.py', 20),
    ('helper', 'utils.py', 30)
])

# Get call graph
call_graph = profiler.get_call_graph()

print("Call Graph:")
for caller, callees in call_graph.items():
    print(f"{caller} calls:")
    for callee in callees:
        print(f"  - {callee}")
```

### Time-Series Performance

```python
from PerProVis import PerProVis

profiler = PerProVis()

# Add samples over time
# ... profiling code here ...

# Get time-series data (100ms buckets)
time_series = profiler.get_time_series(bucket_size_ms=100)

print("Performance Over Time:")
for bucket in time_series:
    print(f"Time: {bucket['time_ms']}ms, Samples: {bucket['sample_count']}")
```

### Memory Profiling

```python
from PerProVis import PerProVis

profiler = PerProVis()

# Add memory snapshots
profiler.add_memory_snapshot(
    total_bytes=10 * 1024 * 1024,  # 10 MB
    allocations={
        'data_processing': 5 * 1024 * 1024,
        'cache': 3 * 1024 * 1024,
        'buffers': 2 * 1024 * 1024
    },
    stack_trace=[('process_data', 'app.py', 100)]
)

# Track memory over time
for i in range(10):
    # ... application code ...
    profiler.add_memory_snapshot(
        total_bytes=(10 + i) * 1024 * 1024
    )

# Get memory usage over time
memory_usage = profiler.get_memory_usage_over_time()
for snapshot in memory_usage:
    print(f"Time: {snapshot['timestamp']:.2f}, Memory: {snapshot['total_mb']:.2f} MB")
```

### Memory Leak Detection

```python
from PerProVis import PerProVis

profiler = PerProVis()

# Simulate growing memory usage
for i in range(20):
    allocations = {
        'leaky_cache': i * 500 * 1024,  # Growing
        'stable_buffer': 1024 * 1024     # Stable
    }
    profiler.add_memory_snapshot(
        total_bytes=sum(allocations.values()),
        allocations=allocations
    )

# Detect leaks
leaks = profiler.find_memory_leaks()

print("Potential Memory Leaks:")
for leak in leaks:
    print(f"\nAllocation Site: {leak['allocation_site']}")
    print(f"  Initial: {leak['initial_bytes'] / 1024 / 1024:.2f} MB")
    print(f"  Final: {leak['final_bytes'] / 1024 / 1024:.2f} MB")
    print(f"  Growth: {leak['growth_mb']:.2f} MB")
    print(f"  Samples: {leak['sample_count']}")
```

### Profile Comparison

```python
from PerProVis import PerProVis

# Baseline profile
baseline = PerProVis()
# ... collect baseline samples ...
for i in range(100):
    baseline.add_sample([('func_a', 'module.py', 10)])

# Current profile (after optimization)
current = PerProVis()
# ... collect current samples ...
for i in range(50):
    current.add_sample([('func_a', 'module.py', 10)])
for i in range(50):
    current.add_sample([('func_b', 'module.py', 20)])

# Compare profiles
comparison = baseline.compare_profiles(current)

print(f"Baseline samples: {comparison['baseline_samples']}")
print(f"Current samples: {comparison['current_samples']}")
print("\nSignificant Differences:")

for diff in comparison['differences'][:10]:  # Top 10
    print(f"\n{diff['function']}")
    print(f"  Baseline: {diff['baseline_percentage']:.2f}%")
    print(f"  Current: {diff['current_percentage']:.2f}%")
    print(f"  Difference: {diff['difference']:+.2f}%")
    if 'status' in diff:
        print(f"  Status: {diff['status']}")
```

### Exporting Profiles

```python
from PerProVis import PerProVis
import json

profiler = PerProVis()

# ... profiling code here ...

# Export complete profile
profile_data = profiler.export_profile()

# Save to file
with open('profile.json', 'w') as f:
    json.dump(profile_data, f, indent=2)

# Access exported data
print(f"Total samples: {profile_data['sample_count']}")
print(f"Duration: {profile_data['duration_seconds']:.2f}s")
print(f"Top hotspots: {len(profile_data['hotspots'])}")
print(f"Flame graph nodes: {profile_data['flame_graph']['value']}")
```

## Testing

Run the test suite:

```bash
cd python/PerProVis
python test_PerProVis.py
```

Or run specific test classes:

```bash
python test_PerProVis.py TestHotspotDetection
python test_PerProVis.py TestMemoryProfiling
python test_PerProVis.py TestFlameGraph
```

## Implementation Notes

- **Thread-safe**: All operations use locks for concurrent access
- **Manual or Automatic**: Supports both manual sample addition and automatic profiling
- **Efficient**: Caches computed results (hotspots, flame graphs)
- **Flexible**: Customizable sampling intervals and bucket sizes
- **Zero Dependencies**: No external libraries required
- **Memory Efficient**: Configurable sample retention

## API Reference

### PerProVis Class

**Constructor:**
```python
PerProVis(sampling_interval_ms: int = 10)
```

**Methods:**
- `start_profiling()`: Start automatic profiling
- `stop_profiling()`: Stop automatic profiling
- `add_sample(stack_trace, metrics=None)`: Add manual profiling sample
- `add_memory_snapshot(total_bytes, allocations=None, stack_trace=None)`: Add memory snapshot
- `get_sample_count() -> int`: Get number of samples collected
- `get_profiling_duration() -> float`: Get profiling duration in seconds
- `find_hotspots(top_n=10) -> List[Hotspot]`: Find performance hotspots
- `generate_flame_graph() -> FlameGraphNode`: Generate flame graph
- `get_flame_graph_json() -> str`: Get flame graph as JSON
- `get_call_graph() -> Dict[str, List[str]]`: Get function call relationships
- `get_time_series(bucket_size_ms=100) -> List[Dict]`: Get time-series data
- `get_memory_usage_over_time() -> List[Dict]`: Get memory usage history
- `find_memory_leaks() -> List[Dict]`: Detect memory leaks
- `compare_profiles(other) -> Dict`: Compare with another profile
- `export_profile() -> Dict`: Export complete profile data
- `clear()`: Clear all profiling data

### Data Classes

**StackFrame:**
- `function_name`: Function name
- `filename`: Source file
- `line_number`: Line number
- `module`: Module name

**Hotspot:**
- `function_name`: Function name
- `filename`: Source file
- `total_time_ms`: Total time spent
- `sample_count`: Number of samples
- `percentage`: Percentage of total samples
- `callers`: Set of calling functions
- `callees`: Set of called functions

## Example Use Cases

### Profiling a Web Service

```python
from PerProVis import PerProVis
import time

profiler = PerProVis(sampling_interval_ms=10)

def handle_request(request):
    """Simulate request handling"""
    # Manually add profile samples
    profiler.add_sample([
        ('handle_request', 'server.py', 10),
        ('parse_request', 'parser.py', 25)
    ])
    
    time.sleep(0.01)  # Simulate work
    
    profiler.add_sample([
        ('handle_request', 'server.py', 10),
        ('query_database', 'db.py', 50)
    ])
    
    time.sleep(0.02)  # Simulate DB query
    
    profiler.add_sample([
        ('handle_request', 'server.py', 10),
        ('render_response', 'templates.py', 75)
    ])

# Handle multiple requests
for i in range(100):
    handle_request({'path': '/api/users'})

# Analyze performance
hotspots = profiler.find_hotspots(top_n=5)
print("\nTop Bottlenecks:")
for hotspot in hotspots:
    print(f"- {hotspot.function_name}: {hotspot.percentage:.1f}%")
```

### Detecting Performance Regressions

```python
from PerProVis import PerProVis

# Profile baseline version
baseline_profiler = PerProVis()
# ... run baseline code and collect samples ...

# Profile new version
new_profiler = PerProVis()
# ... run new code and collect samples ...

# Compare
comparison = baseline_profiler.compare_profiles(new_profiler)

print("Performance Regression Analysis:")
for diff in comparison['differences']:
    if diff['difference'] > 5.0:  # More than 5% increase
        print(f"\nREGRESSION: {diff['function']}")
        print(f"  Increase: +{diff['difference']:.2f}%")
```

### Long-Running Application Monitoring

```python
from PerProVis import PerProVis
import time

profiler = PerProVis()

def monitor_loop():
    """Monitor application over time"""
    start_time = time.time()
    
    while time.time() - start_time < 60:  # Monitor for 1 minute
        # Collect sample
        profiler.add_sample([
            ('monitor_loop', 'app.py', 10),
            ('process_events', 'events.py', 20)
        ])
        
        # Check memory
        import sys
        memory_usage = sys.getsizeof({}) * 1000  # Simplified
        profiler.add_memory_snapshot(memory_usage)
        
        time.sleep(0.1)
    
    # Analyze results
    print("\nTime-Series Analysis:")
    time_series = profiler.get_time_series(bucket_size_ms=10000)  # 10s buckets
    for bucket in time_series:
        print(f"  {bucket['time_ms']/1000:.0f}s: {bucket['sample_count']} samples")
    
    print("\nMemory Leak Check:")
    leaks = profiler.find_memory_leaks()
    if leaks:
        print("  WARNING: Potential leaks detected!")
        for leak in leaks:
            print(f"    {leak['allocation_site']}: +{leak['growth_mb']:.2f} MB")
    else:
        print("  No leaks detected")

monitor_loop()
```

## Performance Considerations

- **Sampling Overhead**: Lower sampling intervals = higher accuracy but more overhead
- **Memory Usage**: Samples stored in memory; clear periodically for long-running apps
- **Lock Contention**: Thread-safe operations may contend under very high sampling rates
- **Cache Invalidation**: Cache cleared on new samples; call `find_hotspots()` once then reuse
- **Flame Graph Size**: Large applications may generate very large flame graphs

## Best Practices

1. **Choose appropriate sampling interval**: 10-50ms for most applications
2. **Clear old data**: Call `clear()` periodically in long-running apps
3. **Export for analysis**: Export profiles for offline analysis and archival
4. **Compare profiles**: Use profile comparison to track performance changes
5. **Focus on hotspots**: Optimize functions appearing in top hotspots first
6. **Monitor memory**: Track memory usage to detect leaks early
7. **Use manual sampling**: For web services, add samples at request boundaries
8. **Flame graphs for visualization**: Use flame graphs to understand call hierarchies

## License

This implementation is part of the Emu-Soft project and is original code written from scratch.
