"""
Developed by PowerShield, as a performance profiling visualizer

PerProVis - Performance Profiling Visualizer

This module provides functionality to profile, analyze, and visualize
application performance without external dependencies.

Features:
- Function-level profiling with timing and call counts
- Call stack tracking and visualization
- Memory usage tracking
- CPU time measurement
- Flame graph generation (text-based)
- Performance hotspot detection
- Timeline visualization
- Statistical analysis of performance data
- Export to various formats (JSON, CSV, text)

Note: This is a pure Python implementation using only standard library.
"""

import time
import sys
import threading
import traceback
import json
import csv
from typing import Any, Callable, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
from functools import wraps
from contextlib import contextmanager
import statistics


@dataclass
class FunctionCall:
    """Represents a single function call"""
    name: str
    start_time: float
    end_time: float
    duration: float
    memory_delta: int = 0
    call_stack: List[str] = field(default_factory=list)
    thread_id: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'memory_delta': self.memory_delta,
            'call_stack': self.call_stack,
            'thread_id': self.thread_id,
            'metadata': self.metadata
        }


@dataclass
class FunctionStats:
    """Statistics for a function"""
    name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    durations: List[float] = field(default_factory=list)
    total_memory: int = 0
    
    def add_call(self, duration: float, memory_delta: int = 0):
        """Add a function call"""
        self.call_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.durations.append(duration)
        self.total_memory += memory_delta
    
    def get_avg_time(self) -> float:
        """Get average execution time"""
        if self.call_count == 0:
            return 0.0
        return self.total_time / self.call_count
    
    def get_median_time(self) -> float:
        """Get median execution time"""
        if not self.durations:
            return 0.0
        return statistics.median(self.durations)
    
    def get_percentile(self, percentile: float) -> float:
        """Get percentile execution time"""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        index = int(len(sorted_durations) * percentile / 100)
        return sorted_durations[min(index, len(sorted_durations) - 1)]
    
    def get_std_dev(self) -> float:
        """Get standard deviation of execution time"""
        if len(self.durations) < 2:
            return 0.0
        return statistics.stdev(self.durations)


class PerformanceProfiler:
    """Main performance profiler class"""
    
    def __init__(self, enabled: bool = True):
        """Initialize the profiler"""
        self.enabled = enabled
        self.calls: List[FunctionCall] = []
        self.function_stats: Dict[str, FunctionStats] = {}
        self.call_stacks: Dict[int, List[Tuple[str, float]]] = defaultdict(list)
        self.lock = threading.Lock()
        self._memory_tracking = False
    
    def enable(self):
        """Enable profiling"""
        self.enabled = True
    
    def disable(self):
        """Disable profiling"""
        self.enabled = False
    
    def clear(self):
        """Clear all profiling data"""
        with self.lock:
            self.calls.clear()
            self.function_stats.clear()
            self.call_stacks.clear()
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage (approximation)"""
        # Note: This is a simple approximation since we're avoiding external dependencies
        # In production, you'd use psutil or similar
        return sys.getsizeof(self.calls) + sys.getsizeof(self.function_stats)
    
    @contextmanager
    def profile_block(self, name: str, **metadata):
        """Context manager for profiling a code block"""
        if not self.enabled:
            yield
            return
        
        thread_id = threading.get_ident()
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage() if self._memory_tracking else 0
        
        # Push to call stack
        with self.lock:
            self.call_stacks[thread_id].append((name, start_time))
            current_stack = [item[0] for item in self.call_stacks[thread_id]]
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage() if self._memory_tracking else 0
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            # Pop from call stack
            with self.lock:
                self.call_stacks[thread_id].pop()
                
                # Record the call
                call = FunctionCall(
                    name=name,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    memory_delta=memory_delta,
                    call_stack=current_stack.copy(),
                    thread_id=thread_id,
                    metadata=metadata
                )
                self.calls.append(call)
                
                # Update statistics
                if name not in self.function_stats:
                    self.function_stats[name] = FunctionStats(name=name)
                self.function_stats[name].add_call(duration, memory_delta)
    
    def profile_function(self, func: Optional[Callable] = None, name: Optional[str] = None):
        """Decorator for profiling functions"""
        def decorator(f: Callable) -> Callable:
            func_name = name or f.__name__
            
            @wraps(f)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return f(*args, **kwargs)
                
                with self.profile_block(func_name):
                    return f(*args, **kwargs)
            
            return wrapper
        
        if func is None:
            return decorator
        else:
            return decorator(func)
    
    def get_function_stats(self, name: str) -> Optional[FunctionStats]:
        """Get statistics for a specific function"""
        with self.lock:
            return self.function_stats.get(name)
    
    def get_all_function_stats(self) -> Dict[str, FunctionStats]:
        """Get statistics for all functions"""
        with self.lock:
            return dict(self.function_stats)
    
    def get_all_calls(self) -> List[FunctionCall]:
        """Get all recorded function calls"""
        with self.lock:
            return list(self.calls)
    
    def get_hotspots(self, limit: int = 10) -> List[Tuple[str, float, int]]:
        """Get performance hotspots (slowest functions by total time)"""
        with self.lock:
            hotspots = []
            for name, stats in self.function_stats.items():
                hotspots.append((name, stats.total_time, stats.call_count))
            
            hotspots.sort(key=lambda x: x[1], reverse=True)
            return hotspots[:limit]
    
    def get_slowest_calls(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get slowest individual function calls"""
        with self.lock:
            calls_with_duration = [(call.name, call.duration) for call in self.calls]
            calls_with_duration.sort(key=lambda x: x[1], reverse=True)
            return calls_with_duration[:limit]
    
    def get_call_tree(self, root_only: bool = True) -> Dict[str, Any]:
        """Build a call tree from recorded calls"""
        with self.lock:
            if not self.calls:
                return {}
            
            # Group calls by thread
            thread_calls = defaultdict(list)
            for call in self.calls:
                thread_calls[call.thread_id].append(call)
            
            # Sort calls by start time for each thread
            for thread_id in thread_calls:
                thread_calls[thread_id].sort(key=lambda c: c.start_time)
            
            # Build tree structure
            tree = {}
            for thread_id, calls in thread_calls.items():
                if root_only:
                    # Only include root calls (depth 1)
                    root_calls = [c for c in calls if len(c.call_stack) == 1]
                    tree[f"thread_{thread_id}"] = self._build_tree_node(root_calls)
                else:
                    tree[f"thread_{thread_id}"] = self._build_tree_node(calls)
            
            return tree
    
    def _build_tree_node(self, calls: List[FunctionCall]) -> List[Dict[str, Any]]:
        """Build tree nodes from calls"""
        nodes = []
        for call in calls:
            nodes.append({
                'name': call.name,
                'duration': call.duration,
                'start_time': call.start_time,
                'call_count': 1
            })
        return nodes
    
    def generate_flame_graph_text(self, width: int = 80) -> str:
        """Generate a text-based flame graph"""
        with self.lock:
            if not self.function_stats:
                return "No profiling data available"
            
            # Sort functions by total time
            sorted_funcs = sorted(
                self.function_stats.items(),
                key=lambda x: x[1].total_time,
                reverse=True
            )
            
            # Get total time
            total_time = sum(stats.total_time for _, stats in sorted_funcs)
            
            if total_time == 0:
                return "No profiling data available"
            
            # Generate text bars
            lines = []
            lines.append("=" * width)
            lines.append("Performance Flame Graph (Horizontal)")
            lines.append("=" * width)
            
            for name, stats in sorted_funcs[:20]:  # Top 20
                percentage = (stats.total_time / total_time) * 100
                bar_length = int((stats.total_time / total_time) * (width - 30))
                bar = "█" * bar_length
                
                lines.append(f"{name[:25]:25} {bar} {percentage:5.1f}% ({stats.call_count} calls)")
            
            lines.append("=" * width)
            return "\n".join(lines)
    
    def generate_timeline_text(self, limit: int = 50) -> str:
        """Generate a text-based timeline visualization"""
        with self.lock:
            if not self.calls:
                return "No profiling data available"
            
            # Sort calls by start time
            sorted_calls = sorted(self.calls, key=lambda c: c.start_time)[:limit]
            
            if not sorted_calls:
                return "No profiling data available"
            
            # Calculate relative times
            start_time = sorted_calls[0].start_time
            end_time = max(c.end_time for c in sorted_calls)
            total_duration = end_time - start_time
            
            if total_duration == 0:
                return "Timeline duration is zero"
            
            lines = []
            lines.append("=" * 80)
            lines.append("Performance Timeline (First {} calls)".format(limit))
            lines.append("=" * 80)
            
            for call in sorted_calls:
                relative_start = call.start_time - start_time
                percentage = (relative_start / total_duration) * 100
                
                lines.append(
                    f"{percentage:6.2f}% | {call.name[:40]:40} | "
                    f"{call.duration*1000:8.2f}ms | depth={len(call.call_stack)}"
                )
            
            lines.append("=" * 80)
            return "\n".join(lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of profiling data"""
        with self.lock:
            if not self.calls or not self.function_stats:
                return {
                    'total_calls': 0,
                    'total_functions': 0,
                    'total_time': 0.0,
                    'avg_call_time': 0.0
                }
            
            total_time = sum(stats.total_time for stats in self.function_stats.values())
            total_calls = sum(stats.call_count for stats in self.function_stats.values())
            
            all_durations = []
            for stats in self.function_stats.values():
                all_durations.extend(stats.durations)
            
            return {
                'total_calls': total_calls,
                'total_functions': len(self.function_stats),
                'total_time': total_time,
                'avg_call_time': statistics.mean(all_durations) if all_durations else 0.0,
                'median_call_time': statistics.median(all_durations) if all_durations else 0.0,
                'p95_call_time': self._percentile(all_durations, 95) if all_durations else 0.0,
                'p99_call_time': self._percentile(all_durations, 99) if all_durations else 0.0,
                'min_call_time': min(all_durations) if all_durations else 0.0,
                'max_call_time': max(all_durations) if all_durations else 0.0,
            }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def export_to_json(self, filename: str):
        """Export profiling data to JSON"""
        # Get summary first (needs lock)
        summary = self.get_summary()
        
        # Then get the rest under lock
        with self.lock:
            data = {
                'summary': summary,
                'function_stats': {
                    name: {
                        'call_count': stats.call_count,
                        'total_time': stats.total_time,
                        'avg_time': stats.get_avg_time(),
                        'min_time': stats.min_time,
                        'max_time': stats.max_time,
                        'median_time': stats.get_median_time(),
                        'std_dev': stats.get_std_dev()
                    }
                    for name, stats in self.function_stats.items()
                },
                'calls': [call.to_dict() for call in self.calls]
            }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_to_csv(self, filename: str):
        """Export function statistics to CSV"""
        with self.lock:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Function', 'Call Count', 'Total Time (s)',
                    'Avg Time (s)', 'Min Time (s)', 'Max Time (s)',
                    'Median Time (s)', 'Std Dev (s)'
                ])
                
                for name, stats in sorted(
                    self.function_stats.items(),
                    key=lambda x: x[1].total_time,
                    reverse=True
                ):
                    writer.writerow([
                        name,
                        stats.call_count,
                        f"{stats.total_time:.6f}",
                        f"{stats.get_avg_time():.6f}",
                        f"{stats.min_time:.6f}",
                        f"{stats.max_time:.6f}",
                        f"{stats.get_median_time():.6f}",
                        f"{stats.get_std_dev():.6f}"
                    ])
    
    def print_report(self, top_n: int = 20):
        """Print a formatted profiling report"""
        print("\n" + "=" * 80)
        print("Performance Profiling Report")
        print("=" * 80)
        
        summary = self.get_summary()
        print(f"\nSummary:")
        print(f"  Total Functions: {summary['total_functions']}")
        print(f"  Total Calls: {summary['total_calls']}")
        print(f"  Total Time: {summary['total_time']:.4f}s")
        print(f"  Average Call Time: {summary['avg_call_time']*1000:.2f}ms")
        print(f"  Median Call Time: {summary['median_call_time']*1000:.2f}ms")
        print(f"  P95 Call Time: {summary['p95_call_time']*1000:.2f}ms")
        print(f"  P99 Call Time: {summary['p99_call_time']*1000:.2f}ms")
        
        print(f"\nTop {top_n} Hotspots (by total time):")
        print(f"{'Function':<40} {'Total Time':<15} {'Calls':<10} {'Avg Time':<15}")
        print("-" * 80)
        
        hotspots = self.get_hotspots(limit=top_n)
        for name, total_time, call_count in hotspots:
            avg_time = total_time / call_count if call_count > 0 else 0
            print(f"{name[:40]:<40} {total_time:>10.4f}s    {call_count:>8}   {avg_time*1000:>10.2f}ms")
        
        print("\n" + "=" * 80)


# Global profiler instance
_global_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance"""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler


def profile(func: Optional[Callable] = None, name: Optional[str] = None):
    """Decorator to profile a function using global profiler"""
    profiler = get_profiler()
    return profiler.profile_function(func, name)


@contextmanager
def profile_block(name: str, **metadata):
    """Context manager to profile a code block using global profiler"""
    profiler = get_profiler()
    with profiler.profile_block(name, **metadata):
        yield


def create_profiler(enabled: bool = True) -> PerformanceProfiler:
    """Create a new profiler instance"""
    return PerformanceProfiler(enabled=enabled)
