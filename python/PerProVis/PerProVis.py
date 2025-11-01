"""
Developed by PowerShield
"""

#!/usr/bin/env python3
"""
PerProVis - Performance Profiling Visualizer

This module provides advanced performance profiling capabilities beyond basic
prometheus, including flame graph generation, hotspot detection, and memory
profiling visualization.

Features:
- CPU profiling with stack trace collection
- Memory profiling and leak detection
- Flame graph data generation
- Hotspot detection and analysis
- Time-series performance metrics
- Call graph visualization data
- Profile comparison (diff)
"""

import time
import threading
import sys
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import hashlib
import json


@dataclass
class StackFrame:
    """Represents a single stack frame"""
    function_name: str
    filename: str
    line_number: int
    module: str = ""
    
    def __hash__(self):
        return hash((self.function_name, self.filename, self.line_number))
    
    def __eq__(self, other):
        if not isinstance(other, StackFrame):
            return False
        return (self.function_name == other.function_name and
                self.filename == other.filename and
                self.line_number == other.line_number)
    
    def to_string(self) -> str:
        """Convert to string representation"""
        return f"{self.function_name} ({self.filename}:{self.line_number})"


@dataclass
class Sample:
    """Profiling sample"""
    timestamp: float
    stack_trace: List[StackFrame]
    thread_id: int
    metrics: Dict[str, Any] = field(default_factory=dict)
    

@dataclass
class Hotspot:
    """Performance hotspot"""
    function_name: str
    filename: str
    total_time_ms: float
    sample_count: int
    percentage: float
    callers: Set[str] = field(default_factory=set)
    callees: Set[str] = field(default_factory=set)
    
    def average_time_ms(self) -> float:
        """Calculate average time per sample"""
        return self.total_time_ms / self.sample_count if self.sample_count > 0 else 0.0


@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: float
    total_bytes: int
    allocations: Dict[str, int] = field(default_factory=dict)
    stack_trace: Optional[List[StackFrame]] = None


@dataclass
class FlameGraphNode:
    """Node in a flame graph"""
    name: str
    value: int  # Sample count or duration
    children: Dict[str, 'FlameGraphNode'] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            'name': self.name,
            'value': self.value
        }
        if self.children:
            result['children'] = [child.to_dict() for child in self.children.values()]
        return result


class PerProVis:
    """Performance Profiling Visualizer"""
    
    def __init__(self, sampling_interval_ms: int = 10):
        """
        Initialize the profiler
        
        Args:
            sampling_interval_ms: Sampling interval in milliseconds
        """
        self.sampling_interval_ms = sampling_interval_ms
        self.samples: List[Sample] = []
        self.memory_snapshots: List[MemorySnapshot] = []
        self.is_profiling = False
        self.profiler_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Cached analysis results
        self._hotspots: Optional[List[Hotspot]] = None
        self._flame_graph: Optional[FlameGraphNode] = None
    
    def start_profiling(self):
        """Start profiling"""
        with self.lock:
            if self.is_profiling:
                raise RuntimeError("Profiling already in progress")
            
            self.is_profiling = True
            self.start_time = time.time()
            self.samples.clear()
            self._hotspots = None
            self._flame_graph = None
            
        # Start profiler thread
        self.profiler_thread = threading.Thread(target=self._profile_loop, daemon=True)
        self.profiler_thread.start()
    
    def stop_profiling(self):
        """Stop profiling"""
        with self.lock:
            if not self.is_profiling:
                return
            
            self.is_profiling = False
            self.end_time = time.time()
        
        # Wait for profiler thread to finish
        if self.profiler_thread:
            self.profiler_thread.join(timeout=1.0)
    
    def _profile_loop(self):
        """Main profiling loop"""
        interval_seconds = self.sampling_interval_ms / 1000.0
        
        while self.is_profiling:
            try:
                # Collect sample
                sample = self._collect_sample()
                if sample:
                    with self.lock:
                        self.samples.append(sample)
            except Exception:
                pass  # Ignore sampling errors
            
            time.sleep(interval_seconds)
    
    def _collect_sample(self) -> Optional[Sample]:
        """Collect a single profiling sample"""
        # Get current stack trace
        frame = sys._current_frames().get(threading.get_ident())
        if not frame:
            return None
        
        stack_trace = []
        current = frame
        depth = 0
        max_depth = 100
        
        while current and depth < max_depth:
            frame_info = StackFrame(
                function_name=current.f_code.co_name,
                filename=current.f_code.co_filename,
                line_number=current.f_lineno,
                module=current.f_globals.get('__name__', '')
            )
            stack_trace.append(frame_info)
            current = current.f_back
            depth += 1
        
        return Sample(
            timestamp=time.time(),
            stack_trace=stack_trace,
            thread_id=threading.get_ident()
        )
    
    def add_sample(self, stack_trace: List[Tuple[str, str, int]], 
                   metrics: Optional[Dict[str, Any]] = None):
        """
        Manually add a profiling sample
        
        Args:
            stack_trace: List of (function_name, filename, line_number) tuples
            metrics: Optional metrics dictionary
        """
        frames = [
            StackFrame(func, file, line)
            for func, file, line in stack_trace
        ]
        
        sample = Sample(
            timestamp=time.time(),
            stack_trace=frames,
            thread_id=threading.get_ident(),
            metrics=metrics or {}
        )
        
        with self.lock:
            self.samples.append(sample)
            # Invalidate cache
            self._hotspots = None
            self._flame_graph = None
    
    def add_memory_snapshot(self, total_bytes: int, 
                           allocations: Optional[Dict[str, int]] = None,
                           stack_trace: Optional[List[Tuple[str, str, int]]] = None):
        """
        Add a memory snapshot
        
        Args:
            total_bytes: Total memory usage in bytes
            allocations: Dictionary of allocation sites to byte counts
            stack_trace: Optional stack trace for allocation context
        """
        frames = None
        if stack_trace:
            frames = [
                StackFrame(func, file, line)
                for func, file, line in stack_trace
            ]
        
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_bytes=total_bytes,
            allocations=allocations or {},
            stack_trace=frames
        )
        
        with self.lock:
            self.memory_snapshots.append(snapshot)
    
    def get_sample_count(self) -> int:
        """Get total number of samples collected"""
        with self.lock:
            return len(self.samples)
    
    def get_profiling_duration(self) -> float:
        """Get profiling duration in seconds"""
        with self.lock:
            if self.start_time:
                end = self.end_time or time.time()
                return end - self.start_time
            return 0.0
    
    def find_hotspots(self, top_n: int = 10) -> List[Hotspot]:
        """
        Find performance hotspots
        
        Args:
            top_n: Number of top hotspots to return
            
        Returns:
            List of hotspots sorted by total time
        """
        with self.lock:
            if self._hotspots:
                return self._hotspots[:top_n]
            
            # Count samples per function
            function_samples = defaultdict(int)
            function_files = {}
            caller_map = defaultdict(set)
            callee_map = defaultdict(set)
            
            for sample in self.samples:
                for i, frame in enumerate(sample.stack_trace):
                    key = f"{frame.function_name}:{frame.filename}"
                    function_samples[key] += 1
                    function_files[key] = (frame.function_name, frame.filename)
                    
                    # Track caller/callee relationships
                    if i > 0:
                        caller_key = f"{sample.stack_trace[i-1].function_name}:{sample.stack_trace[i-1].filename}"
                        caller_map[key].add(caller_key)
                        callee_map[caller_key].add(key)
            
            # Calculate timing
            total_samples = len(self.samples)
            # Calculate duration directly without calling method to avoid lock recursion
            if self.start_time:
                end = self.end_time or time.time()
                duration = end - self.start_time
            else:
                duration = 0.0
            time_per_sample = (duration * 1000) / total_samples if total_samples > 0 else 0
            
            # Create hotspot objects
            hotspots = []
            for key, count in function_samples.items():
                func_name, filename = function_files[key]
                total_time = count * time_per_sample
                percentage = (count / total_samples * 100) if total_samples > 0 else 0
                
                hotspot = Hotspot(
                    function_name=func_name,
                    filename=filename,
                    total_time_ms=total_time,
                    sample_count=count,
                    percentage=percentage,
                    callers=caller_map[key],
                    callees=callee_map[key]
                )
                hotspots.append(hotspot)
            
            # Sort by sample count
            hotspots.sort(key=lambda h: h.sample_count, reverse=True)
            self._hotspots = hotspots
            
            return hotspots[:top_n]
    
    def generate_flame_graph(self) -> FlameGraphNode:
        """
        Generate flame graph data structure
        
        Returns:
            Root node of flame graph
        """
        with self.lock:
            if self._flame_graph:
                return self._flame_graph
            
            root = FlameGraphNode(name="root", value=0)
            
            for sample in self.samples:
                # Process stack from bottom to top
                current = root
                root.value += 1
                
                for frame in reversed(sample.stack_trace):
                    name = f"{frame.function_name} ({frame.filename}:{frame.line_number})"
                    
                    if name not in current.children:
                        current.children[name] = FlameGraphNode(name=name, value=0)
                    
                    current = current.children[name]
                    current.value += 1
            
            self._flame_graph = root
            return root
    
    def get_flame_graph_json(self) -> str:
        """
        Get flame graph as JSON string
        
        Returns:
            JSON representation of flame graph
        """
        root = self.generate_flame_graph()
        return json.dumps(root.to_dict(), indent=2)
    
    def get_call_graph(self) -> Dict[str, List[str]]:
        """
        Generate call graph showing caller-callee relationships
        
        Returns:
            Dictionary mapping functions to their callees
        """
        with self.lock:
            graph = defaultdict(set)
            
            for sample in self.samples:
                for i in range(len(sample.stack_trace) - 1):
                    caller = sample.stack_trace[i].to_string()
                    callee = sample.stack_trace[i + 1].to_string()
                    graph[caller].add(callee)
            
            # Convert sets to lists
            return {k: list(v) for k, v in graph.items()}
    
    def get_time_series(self, bucket_size_ms: int = 100) -> List[Dict[str, Any]]:
        """
        Get time-series performance data
        
        Args:
            bucket_size_ms: Size of time buckets in milliseconds
            
        Returns:
            List of time buckets with sample counts
        """
        with self.lock:
            if not self.samples:
                return []
            
            start_time = self.samples[0].timestamp
            bucket_size = bucket_size_ms / 1000.0
            
            # Group samples into buckets
            buckets = defaultdict(int)
            for sample in self.samples:
                bucket_idx = int((sample.timestamp - start_time) / bucket_size)
                buckets[bucket_idx] += 1
            
            # Create time series
            time_series = []
            max_bucket = max(buckets.keys()) if buckets else 0
            
            for i in range(max_bucket + 1):
                time_series.append({
                    'time_ms': i * bucket_size_ms,
                    'sample_count': buckets.get(i, 0)
                })
            
            return time_series
    
    def get_memory_usage_over_time(self) -> List[Dict[str, Any]]:
        """
        Get memory usage over time
        
        Returns:
            List of memory snapshots with timestamps
        """
        with self.lock:
            return [
                {
                    'timestamp': snap.timestamp,
                    'total_bytes': snap.total_bytes,
                    'total_mb': snap.total_bytes / (1024 * 1024)
                }
                for snap in self.memory_snapshots
            ]
    
    def find_memory_leaks(self) -> List[Dict[str, Any]]:
        """
        Detect potential memory leaks
        
        Returns:
            List of allocation sites with growing memory usage
        """
        with self.lock:
            if len(self.memory_snapshots) < 2:
                return []
            
            # Track allocation growth
            allocation_growth = defaultdict(list)
            
            for snapshot in self.memory_snapshots:
                for site, size in snapshot.allocations.items():
                    allocation_growth[site].append((snapshot.timestamp, size))
            
            # Find growing allocations
            leaks = []
            for site, history in allocation_growth.items():
                if len(history) < 3:
                    continue
                
                # Calculate growth rate
                first_size = history[0][1]
                last_size = history[-1][1]
                growth = last_size - first_size
                
                if growth > 1024 * 1024:  # Growing by more than 1MB
                    leaks.append({
                        'allocation_site': site,
                        'initial_bytes': first_size,
                        'final_bytes': last_size,
                        'growth_bytes': growth,
                        'growth_mb': growth / (1024 * 1024),
                        'sample_count': len(history)
                    })
            
            # Sort by growth
            leaks.sort(key=lambda x: x['growth_bytes'], reverse=True)
            return leaks
    
    def compare_profiles(self, other: 'PerProVis') -> Dict[str, Any]:
        """
        Compare this profile with another profile
        
        Args:
            other: Another PerProVis instance to compare with
            
        Returns:
            Comparison results
        """
        my_hotspots = {f"{h.function_name}:{h.filename}": h 
                      for h in self.find_hotspots(top_n=100)}
        other_hotspots = {f"{h.function_name}:{h.filename}": h 
                         for h in other.find_hotspots(top_n=100)}
        
        all_functions = set(my_hotspots.keys()) | set(other_hotspots.keys())
        
        differences = []
        for func in all_functions:
            my_hot = my_hotspots.get(func)
            other_hot = other_hotspots.get(func)
            
            if my_hot and other_hot:
                diff_percentage = other_hot.percentage - my_hot.percentage
                if abs(diff_percentage) > 1.0:  # More than 1% difference
                    differences.append({
                        'function': func,
                        'baseline_percentage': my_hot.percentage,
                        'current_percentage': other_hot.percentage,
                        'difference': diff_percentage
                    })
            elif other_hot:
                differences.append({
                    'function': func,
                    'baseline_percentage': 0.0,
                    'current_percentage': other_hot.percentage,
                    'difference': other_hot.percentage,
                    'status': 'new'
                })
            elif my_hot:
                differences.append({
                    'function': func,
                    'baseline_percentage': my_hot.percentage,
                    'current_percentage': 0.0,
                    'difference': -my_hot.percentage,
                    'status': 'removed'
                })
        
        # Sort by absolute difference
        differences.sort(key=lambda x: abs(x['difference']), reverse=True)
        
        return {
            'baseline_samples': len(self.samples),
            'current_samples': len(other.samples),
            'baseline_duration': self.get_profiling_duration(),
            'current_duration': other.get_profiling_duration(),
            'differences': differences
        }
    
    def export_profile(self) -> Dict[str, Any]:
        """
        Export complete profile data
        
        Returns:
            Complete profile data as dictionary
        """
        return {
            'sample_count': len(self.samples),
            'duration_seconds': self.get_profiling_duration(),
            'sampling_interval_ms': self.sampling_interval_ms,
            'hotspots': [
                {
                    'function': h.function_name,
                    'filename': h.filename,
                    'total_time_ms': h.total_time_ms,
                    'sample_count': h.sample_count,
                    'percentage': h.percentage
                }
                for h in self.find_hotspots(top_n=20)
            ],
            'flame_graph': self.generate_flame_graph().to_dict(),
            'time_series': self.get_time_series(),
            'memory_snapshots': len(self.memory_snapshots),
            'memory_usage': self.get_memory_usage_over_time()
        }
    
    def clear(self):
        """Clear all profiling data"""
        with self.lock:
            self.samples.clear()
            self.memory_snapshots.clear()
            self._hotspots = None
            self._flame_graph = None
            self.start_time = None
            self.end_time = None
