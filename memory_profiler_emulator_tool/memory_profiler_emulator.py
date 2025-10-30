"""
memory_profiler emulator - Memory usage profiler for Python programs.
Emulates memory_profiler functionality without external dependencies.

Core features:
- Line-by-line memory usage tracking
- Memory increment tracking per line
- Memory usage over time
- Memory profiling decorators
- Process memory statistics
- Memory leak detection
"""

import sys
import os
import gc
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict
import linecache


@dataclass
class MemorySnapshot:
    """Represents memory state at a specific point in time."""
    timestamp: float
    total_memory: int  # bytes
    line_number: Optional[int] = None
    filename: Optional[str] = None
    function: Optional[str] = None
    
    def memory_mb(self) -> float:
        """Get memory in MB."""
        return self.total_memory / (1024 * 1024)


@dataclass
class LineMemoryStats:
    """Memory statistics for a specific line of code."""
    line_number: int
    filename: str
    code: str
    occurrences: int = 0
    memory_usage: List[int] = field(default_factory=list)  # bytes
    memory_increment: List[int] = field(default_factory=list)  # bytes
    
    def avg_memory_mb(self) -> float:
        """Average memory usage in MB."""
        if not self.memory_usage:
            return 0.0
        return (sum(self.memory_usage) / len(self.memory_usage)) / (1024 * 1024)
    
    def avg_increment_mb(self) -> float:
        """Average memory increment in MB."""
        if not self.memory_increment:
            return 0.0
        return (sum(self.memory_increment) / len(self.memory_increment)) / (1024 * 1024)
    
    def max_memory_mb(self) -> float:
        """Maximum memory usage in MB."""
        if not self.memory_usage:
            return 0.0
        return max(self.memory_usage) / (1024 * 1024)


@dataclass
class FunctionMemoryProfile:
    """Memory profile for a function."""
    function_name: str
    filename: str
    line_stats: Dict[int, LineMemoryStats] = field(default_factory=dict)
    start_memory: int = 0  # bytes
    end_memory: int = 0  # bytes
    peak_memory: int = 0  # bytes
    
    def total_increment_mb(self) -> float:
        """Total memory increment in MB."""
        return (self.end_memory - self.start_memory) / (1024 * 1024)
    
    def peak_mb(self) -> float:
        """Peak memory in MB."""
        return self.peak_memory / (1024 * 1024)


class MemoryProfiler:
    """
    Line-by-line memory profiler using tracemalloc.
    """
    
    def __init__(self, backend: str = 'tracemalloc'):
        """
        Initialize memory profiler.
        
        Args:
            backend: Memory tracking backend ('tracemalloc' or 'psutil')
        """
        self.backend = backend
        self.snapshots: List[MemorySnapshot] = []
        self.line_stats: Dict[Tuple[str, int], LineMemoryStats] = {}
        self.enabled = False
        self.baseline_memory = 0
        
    def enable(self) -> None:
        """Enable memory tracking."""
        if self.enabled:
            return
        
        if self.backend == 'tracemalloc':
            tracemalloc.start()
        
        # Force garbage collection
        gc.collect()
        
        # Record baseline
        self.baseline_memory = self._get_current_memory()
        self.enabled = True
    
    def disable(self) -> None:
        """Disable memory tracking."""
        if not self.enabled:
            return
        
        if self.backend == 'tracemalloc':
            tracemalloc.stop()
        
        self.enabled = False
    
    def _get_current_memory(self) -> int:
        """Get current memory usage in bytes."""
        if self.backend == 'tracemalloc':
            if not tracemalloc.is_tracing():
                return 0
            current, peak = tracemalloc.get_traced_memory()
            return current
        else:
            # Fallback: try to use resource module if available
            try:
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                # maxrss is in kilobytes on most systems, bytes on macOS
                if sys.platform == 'darwin':
                    return usage.ru_maxrss
                else:
                    return usage.ru_maxrss * 1024
            except (ImportError, AttributeError):
                # Last resort: return 0 (profiling won't be accurate)
                return 0
    
    def snapshot(self, line_number: Optional[int] = None, 
                filename: Optional[str] = None,
                function: Optional[str] = None) -> MemorySnapshot:
        """Take a memory snapshot."""
        memory = self._get_current_memory()
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_memory=memory,
            line_number=line_number,
            filename=filename,
            function=function
        )
        self.snapshots.append(snapshot)
        return snapshot
    
    def add_line_stats(self, filename: str, line_number: int, 
                       memory_usage: int, memory_increment: int = 0) -> None:
        """Add memory statistics for a line."""
        key = (filename, line_number)
        
        if key not in self.line_stats:
            # Get the code for this line
            code = linecache.getline(filename, line_number).strip()
            self.line_stats[key] = LineMemoryStats(
                line_number=line_number,
                filename=filename,
                code=code
            )
        
        stats = self.line_stats[key]
        stats.occurrences += 1
        stats.memory_usage.append(memory_usage)
        if memory_increment != 0:
            stats.memory_increment.append(memory_increment)
    
    def get_memory_stats(self, filename: Optional[str] = None) -> Dict[int, LineMemoryStats]:
        """Get memory statistics, optionally filtered by filename."""
        if filename:
            return {
                line_num: stats 
                for (fname, line_num), stats in self.line_stats.items() 
                if fname == filename
            }
        return {line_num: stats for (_, line_num), stats in self.line_stats.items()}
    
    def reset(self) -> None:
        """Reset profiler state."""
        self.snapshots = []
        self.line_stats = {}
        self.baseline_memory = 0


class LineProfiler:
    """
    Decorator-based line-by-line memory profiler.
    """
    
    def __init__(self, backend: str = 'tracemalloc'):
        self.profiler = MemoryProfiler(backend=backend)
        self.function_profiles: Dict[str, FunctionMemoryProfile] = {}
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate a function to profile its memory usage."""
        def wrapper(*args, **kwargs):
            return self.profile_function(func, *args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    def profile_function(self, func: Callable, *args, **kwargs) -> Any:
        """Profile a function's memory usage line by line."""
        # Enable profiling
        self.profiler.enable()
        
        # Get function info
        filename = func.__code__.co_filename
        function_name = func.__name__
        first_line = func.__code__.co_firstlineno
        
        # Create profile
        profile = FunctionMemoryProfile(
            function_name=function_name,
            filename=filename
        )
        
        # Record start memory
        profile.start_memory = self.profiler._get_current_memory()
        
        # Set up tracing
        prev_memory = profile.start_memory
        
        def trace_lines(frame, event, arg):
            nonlocal prev_memory
            
            if event != 'line':
                return trace_lines
            
            # Only trace lines in the target function
            # Check both filename and that we're in the right code object
            if frame.f_code.co_filename != filename or frame.f_code != func.__code__:
                return trace_lines
            
            line_number = frame.f_lineno
            current_memory = self.profiler._get_current_memory()
            increment = current_memory - prev_memory
            
            # Update peak
            if current_memory > profile.peak_memory:
                profile.peak_memory = current_memory
            
            # Add line stats
            self.profiler.add_line_stats(
                filename, line_number, current_memory, increment
            )
            
            # Store in profile
            key = line_number
            if key not in profile.line_stats:
                code = linecache.getline(filename, line_number).strip()
                profile.line_stats[key] = LineMemoryStats(
                    line_number=line_number,
                    filename=filename,
                    code=code
                )
            
            stats = profile.line_stats[key]
            stats.occurrences += 1
            stats.memory_usage.append(current_memory)
            stats.memory_increment.append(increment)
            
            # Update previous memory
            prev_memory = current_memory
            
            return trace_lines
        
        # Install tracer
        old_trace = sys.gettrace()
        sys.settrace(trace_lines)
        
        try:
            result = func(*args, **kwargs)
        finally:
            # Remove tracer
            sys.settrace(old_trace)
            
            # Record end memory
            profile.end_memory = self.profiler._get_current_memory()
            
            # Store profile
            self.function_profiles[function_name] = profile
            
            # Disable profiling
            self.profiler.disable()
        
        return result
    
    def print_stats(self, function_name: Optional[str] = None) -> None:
        """Print memory profiling statistics."""
        if function_name and function_name in self.function_profiles:
            profiles = [self.function_profiles[function_name]]
        else:
            profiles = list(self.function_profiles.values())
        
        for profile in profiles:
            print(f"\n{'='*80}")
            print(f"Function: {profile.function_name} ({Path(profile.filename).name})")
            print(f"Memory increment: {profile.total_increment_mb():+.3f} MB")
            print(f"Peak memory: {profile.peak_mb():.3f} MB")
            print(f"{'='*80}")
            
            if not profile.line_stats:
                print("No line-level statistics collected")
                continue
            
            print(f"{'Line':<6} {'Memory (MB)':>12} {'Increment (MB)':>15} {'Occurrences':>12} Code")
            print("-" * 80)
            
            # Sort by line number
            for line_num in sorted(profile.line_stats.keys()):
                stats = profile.line_stats[line_num]
                print(f"{line_num:<6} {stats.avg_memory_mb():>12.3f} "
                      f"{stats.avg_increment_mb():>15.3f} {stats.occurrences:>12} "
                      f"{stats.code[:40]}")


def profile(func: Optional[Callable] = None, backend: str = 'tracemalloc'):
    """
    Decorator to profile memory usage of a function.
    
    Args:
        func: Function to profile
        backend: Memory tracking backend
    
    Example:
        @profile
        def my_function():
            data = [0] * 1000000
            return data
    """
    profiler = LineProfiler(backend=backend)
    
    if func is None:
        # Called with arguments: @profile(backend='tracemalloc')
        return profiler
    else:
        # Called without arguments: @profile
        return profiler(func)


class MemoryUsageMonitor:
    """Monitor memory usage over time."""
    
    def __init__(self, interval: float = 0.1):
        """
        Initialize memory monitor.
        
        Args:
            interval: Sampling interval in seconds
        """
        self.interval = interval
        self.snapshots: List[Tuple[float, float]] = []  # (timestamp, memory_mb)
        self.running = False
        self.start_time = 0.0
    
    def start(self) -> None:
        """Start monitoring."""
        tracemalloc.start()
        self.running = True
        self.start_time = time.time()
    
    def sample(self) -> Tuple[float, float]:
        """Take a memory sample."""
        if not self.running:
            raise RuntimeError("Monitor is not running")
        
        current, peak = tracemalloc.get_traced_memory()
        memory_mb = current / (1024 * 1024)
        elapsed = time.time() - self.start_time
        
        self.snapshots.append((elapsed, memory_mb))
        return elapsed, memory_mb
    
    def stop(self) -> List[Tuple[float, float]]:
        """Stop monitoring and return snapshots."""
        self.running = False
        tracemalloc.stop()
        return self.snapshots
    
    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        if not self.snapshots:
            return 0.0
        return max(mem for _, mem in self.snapshots)
    
    def get_memory_timeline(self) -> List[Tuple[float, float]]:
        """Get memory usage timeline."""
        return self.snapshots


def memory_usage(func: Callable, interval: float = 0.1, 
                timeout: Optional[float] = None) -> List[float]:
    """
    Get memory usage samples while running a function.
    
    Args:
        func: Function to run
        interval: Sampling interval in seconds
        timeout: Maximum time to sample
    
    Returns:
        List of memory usage values in MB
    """
    import threading
    
    monitor = MemoryUsageMonitor(interval=interval)
    monitor.start()
    
    # Run function in main thread
    start_time = time.time()
    
    # Sample in background
    def sampler():
        while monitor.running:
            monitor.sample()
            time.sleep(interval)
            if timeout and (time.time() - start_time) > timeout:
                break
    
    sampler_thread = threading.Thread(target=sampler, daemon=True)
    sampler_thread.start()
    
    try:
        result = func()
    finally:
        monitor.stop()
        sampler_thread.join(timeout=1.0)
    
    return [mem for _, mem in monitor.snapshots]


# Convenience functions
def show_results(func: Callable, backend: str = 'tracemalloc') -> Any:
    """
    Profile a function and show results immediately.
    
    Args:
        func: Function to profile
        backend: Memory tracking backend
    
    Returns:
        Function result
    """
    profiler = LineProfiler(backend=backend)
    result = profiler.profile_function(func)
    profiler.print_stats()
    return result


if __name__ == "__main__":
    # Example usage
    @profile
    def test_function():
        """Example function to profile."""
        # Allocate some memory
        data1 = [0] * 1000000  # ~4MB
        
        # More allocations
        data2 = [0] * 2000000  # ~8MB
        
        # Process data
        result = sum(data1) + sum(data2)
        
        # Cleanup one
        del data1
        
        return result
    
    print("Starting memory profiler demo...")
    result = test_function()
    print(f"\nFunction result: {result}")
