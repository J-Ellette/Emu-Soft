"""
Developed by PowerShield, as an alternative to py-spy


py-spy emulator - Sampling profiler for Python programs.
Emulates py-spy functionality without external dependencies.

Core features:
- Statistical sampling profiler
- Stack trace collection
- Flame graph data generation
- Top-like live view data
- Function timing statistics
- Minimal performance overhead
"""

import sys
import time
import threading
import traceback
import signal
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
import json


@dataclass
class StackFrame:
    """Represents a single stack frame."""
    filename: str
    function: str
    line_number: int
    
    def __hash__(self):
        return hash((self.filename, self.function, self.line_number))
    
    def __eq__(self, other):
        if not isinstance(other, StackFrame):
            return False
        return (self.filename == other.filename and 
                self.function == other.function and 
                self.line_number == other.line_number)
    
    def __repr__(self):
        return f"{self.function} ({Path(self.filename).name}:{self.line_number})"


@dataclass
class ProfileData:
    """Container for profiling data."""
    samples: List[List[StackFrame]] = field(default_factory=list)
    sample_count: int = 0
    duration: float = 0.0
    sample_rate: float = 100  # Hz
    
    def add_sample(self, stack: List[StackFrame]) -> None:
        """Add a stack trace sample."""
        self.samples.append(stack)
        self.sample_count += 1
    
    def get_function_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get per-function statistics."""
        function_counts = Counter()
        function_self_counts = Counter()
        
        for stack in self.samples:
            if not stack:
                continue
            
            # Count function appearances (includes time spent in callees)
            for frame in stack:
                key = f"{frame.function} ({Path(frame.filename).name})"
                function_counts[key] += 1
            
            # Count self time (top of stack only)
            if stack:
                top_frame = stack[0]
                key = f"{top_frame.function} ({Path(top_frame.filename).name})"
                function_self_counts[key] += 1
        
        stats = {}
        total_samples = self.sample_count or 1
        
        for func, count in function_counts.items():
            self_count = function_self_counts.get(func, 0)
            stats[func] = {
                'total_time': count / self.sample_rate,
                'self_time': self_count / self.sample_rate,
                'total_percent': (count / total_samples) * 100,
                'self_percent': (self_count / total_samples) * 100,
                'samples': count,
                'self_samples': self_count
            }
        
        return stats
    
    def get_flame_graph_data(self) -> List[Tuple[str, int]]:
        """Generate flame graph data (stack;trace format)."""
        stack_counts = Counter()
        
        for stack in self.samples:
            if not stack:
                continue
            
            # Build stack string (bottom to top)
            stack_str = ';'.join(reversed([
                f"{frame.function}:{Path(frame.filename).name}:{frame.line_number}"
                for frame in stack
            ]))
            
            stack_counts[stack_str] += 1
        
        return sorted(stack_counts.items(), key=lambda x: x[1], reverse=True)
    
    def get_hot_paths(self, top_n: int = 10) -> List[Tuple[List[StackFrame], int]]:
        """Get the most frequently sampled call stacks."""
        stack_counts = Counter()
        stack_map = {}
        
        for stack in self.samples:
            if not stack:
                continue
            
            # Use tuple of frames as key
            stack_key = tuple(stack)
            stack_counts[stack_key] += 1
            stack_map[stack_key] = stack
        
        hot_paths = []
        for stack_key, count in stack_counts.most_common(top_n):
            hot_paths.append((stack_map[stack_key], count))
        
        return hot_paths


class SamplingProfiler:
    """
    Statistical sampling profiler using threading and signal-based sampling.
    """
    
    def __init__(self, sample_rate: float = 100):
        """
        Initialize the profiler.
        
        Args:
            sample_rate: Samples per second (Hz)
        """
        self.sample_rate = sample_rate
        self.interval = 1.0 / sample_rate
        self.profile_data = ProfileData(sample_rate=sample_rate)
        self.running = False
        self.sampler_thread: Optional[threading.Thread] = None
        self.target_thread_id: Optional[int] = None
        self.start_time: float = 0.0
        self.stop_time: float = 0.0
        
    def start(self) -> None:
        """Start profiling."""
        if self.running:
            raise RuntimeError("Profiler is already running")
        
        self.running = True
        self.start_time = time.time()
        self.target_thread_id = threading.current_thread().ident
        
        # Start sampler thread
        self.sampler_thread = threading.Thread(target=self._sample_loop, daemon=True)
        self.sampler_thread.start()
    
    def stop(self) -> ProfileData:
        """Stop profiling and return collected data."""
        if not self.running:
            raise RuntimeError("Profiler is not running")
        
        self.running = False
        self.stop_time = time.time()
        
        # Wait for sampler thread to finish
        if self.sampler_thread:
            self.sampler_thread.join(timeout=2.0)
        
        self.profile_data.duration = self.stop_time - self.start_time
        return self.profile_data
    
    def _sample_loop(self) -> None:
        """Sampling loop (runs in separate thread)."""
        while self.running:
            # Collect stack trace
            stack = self._get_stack_trace()
            if stack:
                self.profile_data.add_sample(stack)
            
            # Sleep until next sample
            time.sleep(self.interval)
    
    def _get_stack_trace(self) -> List[StackFrame]:
        """Get current stack trace of the main thread."""
        stack_frames = []
        
        # Get all frames for all threads
        for thread_id, frame in sys._current_frames().items():
            if thread_id == self.target_thread_id:
                # Walk the stack from top to bottom
                current_frame = frame
                while current_frame is not None:
                    code = current_frame.f_code
                    filename = code.co_filename
                    function = code.co_name
                    line_number = current_frame.f_lineno
                    
                    # Filter out profiler frames
                    module_file = Path(__file__).name
                    if module_file not in filename:
                        stack_frames.append(StackFrame(
                            filename=filename,
                            function=function,
                            line_number=line_number
                        ))
                    
                    current_frame = current_frame.f_back
                
                break
        
        return stack_frames


class ProfilerContext:
    """Context manager for profiling code blocks."""
    
    def __init__(self, sample_rate: float = 100):
        self.profiler = SamplingProfiler(sample_rate=sample_rate)
        self.profile_data: Optional[ProfileData] = None
    
    def __enter__(self):
        self.profiler.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.profile_data = self.profiler.stop()
        return False
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get function statistics."""
        if self.profile_data:
            return self.profile_data.get_function_stats()
        return {}
    
    def print_stats(self, top_n: int = 20) -> None:
        """Print profiling statistics."""
        if not self.profile_data:
            print("No profiling data available")
            return
        
        stats = self.profile_data.get_function_stats()
        
        print(f"\nProfiling Results ({self.profile_data.duration:.2f}s, "
              f"{self.profile_data.sample_count} samples)")
        print("=" * 100)
        print(f"{'Function':<50} {'Total%':>8} {'Self%':>8} {'Total(s)':>10} {'Self(s)':>10}")
        print("-" * 100)
        
        # Sort by total time
        sorted_stats = sorted(stats.items(), 
                            key=lambda x: x[1]['total_time'], 
                            reverse=True)
        
        for func_name, data in sorted_stats[:top_n]:
            print(f"{func_name:<50} {data['total_percent']:>7.1f}% "
                  f"{data['self_percent']:>7.1f}% {data['total_time']:>10.3f} "
                  f"{data['self_time']:>10.3f}")


def profile(sample_rate: float = 100):
    """
    Decorator to profile a function.
    
    Args:
        sample_rate: Samples per second
    
    Example:
        @profile(sample_rate=100)
        def my_function():
            # code to profile
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            profiler = SamplingProfiler(sample_rate=sample_rate)
            profiler.start()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                profile_data = profiler.stop()
                
                # Print results
                print(f"\n=== Profile: {func.__name__} ===")
                stats = profile_data.get_function_stats()
                sorted_stats = sorted(stats.items(), 
                                    key=lambda x: x[1]['total_time'], 
                                    reverse=True)
                
                for func_name, data in sorted_stats[:10]:
                    print(f"{func_name:<50} {data['total_percent']:>7.1f}% "
                          f"{data['total_time']:>8.3f}s")
        
        return wrapper
    return decorator


class TopView:
    """Provides a 'top'-like live view of profiling data."""
    
    def __init__(self, sample_rate: float = 10):
        """
        Initialize top view.
        
        Args:
            sample_rate: Update rate in Hz (lower than profiler rate)
        """
        self.sample_rate = sample_rate
        self.profiler = SamplingProfiler(sample_rate=sample_rate)
        self.running = False
    
    def start(self, duration: Optional[float] = None) -> None:
        """
        Start live profiling view.
        
        Args:
            duration: How long to run (None = run until interrupted)
        """
        self.running = True
        self.profiler.start()
        
        start_time = time.time()
        
        try:
            while self.running:
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # Get current stats
                stats = self.profiler.profile_data.get_function_stats()
                
                # Clear screen (cross-platform)
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Print header
                elapsed = time.time() - start_time
                print(f"py-spy top - {elapsed:.1f}s elapsed, "
                      f"{self.profiler.profile_data.sample_count} samples")
                print("=" * 100)
                print(f"{'Function':<50} {'Total%':>8} {'Self%':>8} {'Samples':>10}")
                print("-" * 100)
                
                # Sort and display top functions
                sorted_stats = sorted(stats.items(), 
                                    key=lambda x: x[1]['total_percent'], 
                                    reverse=True)
                
                for func_name, data in sorted_stats[:20]:
                    print(f"{func_name:<50} {data['total_percent']:>7.1f}% "
                          f"{data['self_percent']:>7.1f}% {data['samples']:>10}")
                
                # Update interval
                time.sleep(1.0 / self.sample_rate)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self) -> ProfileData:
        """Stop profiling."""
        self.running = False
        return self.profiler.stop()


def record(target_func: Callable, sample_rate: float = 100, 
          output_file: Optional[str] = None) -> ProfileData:
    """
    Record profiling data for a function.
    
    Args:
        target_func: Function to profile
        sample_rate: Samples per second
        output_file: Optional file to save flame graph data
    
    Returns:
        ProfileData object
    """
    profiler = SamplingProfiler(sample_rate=sample_rate)
    profiler.start()
    
    try:
        target_func()
    finally:
        profile_data = profiler.stop()
    
    if output_file:
        # Save flame graph data
        flame_data = profile_data.get_flame_graph_data()
        with open(output_file, 'w') as f:
            for stack, count in flame_data:
                f.write(f"{stack} {count}\n")
        print(f"Flame graph data saved to {output_file}")
    
    return profile_data


def top(duration: Optional[float] = None, sample_rate: float = 10) -> ProfileData:
    """
    Display live 'top'-like profiling view.
    
    Args:
        duration: How long to run (None = until interrupted)
        sample_rate: Update rate in Hz
    
    Returns:
        ProfileData object
    """
    top_view = TopView(sample_rate=sample_rate)
    top_view.start(duration=duration)
    return top_view.profiler.profile_data


# Convenience functions matching py-spy CLI
def dump(sample_rate: float = 100) -> List[StackFrame]:
    """
    Dump current stack trace (single sample).
    
    Args:
        sample_rate: Not used, kept for API compatibility
    
    Returns:
        Current stack trace
    """
    profiler = SamplingProfiler(sample_rate=sample_rate)
    profiler.target_thread_id = threading.current_thread().ident
    return profiler._get_stack_trace()


if __name__ == "__main__":
    # Example usage
    def fibonacci(n):
        """Example function to profile."""
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)
    
    def test_function():
        """Test function with some work."""
        result = 0
        for i in range(100):
            result += fibonacci(20)
        return result
    
    print("Starting profiler demo...")
    
    # Using context manager
    with ProfilerContext(sample_rate=100) as profiler:
        test_function()
    
    profiler.print_stats(top_n=15)
    
    # Get flame graph data
    flame_data = profiler.profile_data.get_flame_graph_data()
    print(f"\nFlame graph data: {len(flame_data)} unique stacks")
