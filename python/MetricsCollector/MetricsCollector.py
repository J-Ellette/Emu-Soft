"""
Developed by PowerShield, as an alternative to prometheus_client

Prometheus Client Emulator - Metrics collection without external dependencies

This module emulates core Prometheus client functionality for metrics collection.
It provides a clean API for defining and tracking metrics (counters, gauges, histograms, summaries).

Features:
- Counter metrics (monotonically increasing values)
- Gauge metrics (arbitrary up/down values)
- Histogram metrics (observations with configurable buckets)
- Summary metrics (observations with quantiles)
- Labels for multi-dimensional metrics
- Registry for metric collection
- Text format exposition (Prometheus scrape format)
- Decorator support for timing functions
- Process and platform metrics collectors
- Thread-safe operations

Note: This is a simplified implementation focusing on core functionality.
Advanced features like remote write and push gateway are not included.
"""

import time
import threading
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
from collections import defaultdict
from functools import wraps
import platform


class MetricType:
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Metric:
    """Base class for metrics"""
    
    def __init__(self, name: str, documentation: str, labelnames: Tuple[str, ...] = ()):
        self.name = name
        self.documentation = documentation
        self.labelnames = labelnames
        self._lock = threading.Lock()
    
    def _validate_labels(self, labels: Dict[str, str]):
        """Validate that labels match the metric definition"""
        if set(labels.keys()) != set(self.labelnames):
            raise ValueError(f"Labels {set(labels.keys())} don't match expected {set(self.labelnames)}")


class Counter(Metric):
    """Counter metric - monotonically increasing value"""
    
    def __init__(self, name: str, documentation: str, labelnames: Tuple[str, ...] = ()):
        super().__init__(name, documentation, labelnames)
        self._values: Dict[Tuple, float] = defaultdict(float)
        self._type = MetricType.COUNTER
    
    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment the counter"""
        if amount < 0:
            raise ValueError("Counter can only increase")
        
        labels = labels or {}
        self._validate_labels(labels)
        
        label_key = tuple(sorted(labels.items()))
        
        with self._lock:
            self._values[label_key] += amount
    
    def labels(self, **labels) -> 'CounterChild':
        """Return a child counter with labels"""
        self._validate_labels(labels)
        return CounterChild(self, labels)
    
    def collect(self) -> List[Tuple[Dict[str, str], float]]:
        """Collect all metric samples"""
        with self._lock:
            return [
                (dict(label_key), value)
                for label_key, value in self._values.items()
            ]


class CounterChild:
    """Child counter with specific label values"""
    
    def __init__(self, parent: Counter, labels: Dict[str, str]):
        self._parent = parent
        self._labels = labels
    
    def inc(self, amount: float = 1.0):
        """Increment the counter"""
        self._parent.inc(amount, self._labels)


class Gauge(Metric):
    """Gauge metric - arbitrary up/down value"""
    
    def __init__(self, name: str, documentation: str, labelnames: Tuple[str, ...] = ()):
        super().__init__(name, documentation, labelnames)
        self._values: Dict[Tuple, float] = defaultdict(float)
        self._type = MetricType.GAUGE
    
    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment the gauge"""
        labels = labels or {}
        self._validate_labels(labels)
        
        label_key = tuple(sorted(labels.items()))
        
        with self._lock:
            self._values[label_key] += amount
    
    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement the gauge"""
        labels = labels or {}
        self._validate_labels(labels)
        
        label_key = tuple(sorted(labels.items()))
        
        with self._lock:
            self._values[label_key] -= amount
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set the gauge to a specific value"""
        labels = labels or {}
        self._validate_labels(labels)
        
        label_key = tuple(sorted(labels.items()))
        
        with self._lock:
            self._values[label_key] = value
    
    def set_to_current_time(self, labels: Optional[Dict[str, str]] = None):
        """Set the gauge to the current Unix timestamp"""
        self.set(time.time(), labels)
    
    def labels(self, **labels) -> 'GaugeChild':
        """Return a child gauge with labels"""
        self._validate_labels(labels)
        return GaugeChild(self, labels)
    
    def collect(self) -> List[Tuple[Dict[str, str], float]]:
        """Collect all metric samples"""
        with self._lock:
            return [
                (dict(label_key), value)
                for label_key, value in self._values.items()
            ]


class GaugeChild:
    """Child gauge with specific label values"""
    
    def __init__(self, parent: Gauge, labels: Dict[str, str]):
        self._parent = parent
        self._labels = labels
    
    def inc(self, amount: float = 1.0):
        """Increment the gauge"""
        self._parent.inc(amount, self._labels)
    
    def dec(self, amount: float = 1.0):
        """Decrement the gauge"""
        self._parent.dec(amount, self._labels)
    
    def set(self, value: float):
        """Set the gauge"""
        self._parent.set(value, self._labels)
    
    def set_to_current_time(self):
        """Set the gauge to current time"""
        self._parent.set_to_current_time(self._labels)


class Histogram(Metric):
    """Histogram metric - observations with buckets"""
    
    DEFAULT_BUCKETS = (.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf'))
    
    def __init__(self, name: str, documentation: str, 
                 labelnames: Tuple[str, ...] = (),
                 buckets: Sequence[float] = DEFAULT_BUCKETS):
        super().__init__(name, documentation, labelnames)
        self.buckets = list(buckets)
        if self.buckets != sorted(self.buckets):
            raise ValueError("Buckets must be sorted")
        if float('inf') not in self.buckets:
            self.buckets.append(float('inf'))
        
        self._type = MetricType.HISTOGRAM
        self._buckets: Dict[Tuple, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self._sums: Dict[Tuple, float] = defaultdict(float)
        self._counts: Dict[Tuple, int] = defaultdict(int)
    
    def observe(self, amount: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        labels = labels or {}
        self._validate_labels(labels)
        
        label_key = tuple(sorted(labels.items()))
        
        with self._lock:
            # Update sum and count
            self._sums[label_key] += amount
            self._counts[label_key] += 1
            
            # Update buckets
            for bucket in self.buckets:
                if amount <= bucket:
                    self._buckets[label_key][bucket] += 1
    
    def labels(self, **labels) -> 'HistogramChild':
        """Return a child histogram with labels"""
        self._validate_labels(labels)
        return HistogramChild(self, labels)
    
    def time(self, labels: Optional[Dict[str, str]] = None):
        """Time a block of code (context manager)"""
        return HistogramTimer(self, labels)
    
    def collect(self) -> List[Tuple[Dict[str, str], str, Any]]:
        """Collect all metric samples"""
        samples = []
        with self._lock:
            for label_key in self._counts.keys():
                labels_dict = dict(label_key)
                
                # Bucket samples
                for bucket in self.buckets:
                    bucket_labels = labels_dict.copy()
                    bucket_labels['le'] = str(bucket) if bucket != float('inf') else '+Inf'
                    samples.append((bucket_labels, '_bucket', self._buckets[label_key][bucket]))
                
                # Sum and count
                samples.append((labels_dict, '_sum', self._sums[label_key]))
                samples.append((labels_dict, '_count', self._counts[label_key]))
        
        return samples


class HistogramChild:
    """Child histogram with specific label values"""
    
    def __init__(self, parent: Histogram, labels: Dict[str, str]):
        self._parent = parent
        self._labels = labels
    
    def observe(self, amount: float):
        """Observe a value"""
        self._parent.observe(amount, self._labels)
    
    def time(self):
        """Time a block of code"""
        return self._parent.time(self._labels)


class HistogramTimer:
    """Context manager for timing code blocks"""
    
    def __init__(self, histogram: Histogram, labels: Optional[Dict[str, str]]):
        self._histogram = histogram
        self._labels = labels
        self._start = None
    
    def __enter__(self):
        self._start = time.time()
        return self
    
    def __exit__(self, typ, value, traceback):
        duration = time.time() - self._start
        self._histogram.observe(duration, self._labels)


class Summary(Metric):
    """Summary metric - observations with quantiles"""
    
    def __init__(self, name: str, documentation: str, labelnames: Tuple[str, ...] = ()):
        super().__init__(name, documentation, labelnames)
        self._type = MetricType.SUMMARY
        self._observations: Dict[Tuple, List[float]] = defaultdict(list)
        self._sums: Dict[Tuple, float] = defaultdict(float)
        self._counts: Dict[Tuple, int] = defaultdict(int)
    
    def observe(self, amount: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value"""
        labels = labels or {}
        self._validate_labels(labels)
        
        label_key = tuple(sorted(labels.items()))
        
        with self._lock:
            self._observations[label_key].append(amount)
            self._sums[label_key] += amount
            self._counts[label_key] += 1
    
    def labels(self, **labels) -> 'SummaryChild':
        """Return a child summary with labels"""
        self._validate_labels(labels)
        return SummaryChild(self, labels)
    
    def time(self, labels: Optional[Dict[str, str]] = None):
        """Time a block of code (context manager)"""
        return SummaryTimer(self, labels)
    
    def collect(self) -> List[Tuple[Dict[str, str], str, Any]]:
        """Collect all metric samples"""
        samples = []
        with self._lock:
            for label_key in self._counts.keys():
                labels_dict = dict(label_key)
                
                # Sum and count
                samples.append((labels_dict, '_sum', self._sums[label_key]))
                samples.append((labels_dict, '_count', self._counts[label_key]))
        
        return samples


class SummaryChild:
    """Child summary with specific label values"""
    
    def __init__(self, parent: Summary, labels: Dict[str, str]):
        self._parent = parent
        self._labels = labels
    
    def observe(self, amount: float):
        """Observe a value"""
        self._parent.observe(amount, self._labels)
    
    def time(self):
        """Time a block of code"""
        return self._parent.time(self._labels)


class SummaryTimer:
    """Context manager for timing code blocks"""
    
    def __init__(self, summary: Summary, labels: Optional[Dict[str, str]]):
        self._summary = summary
        self._labels = labels
        self._start = None
    
    def __enter__(self):
        self._start = time.time()
        return self
    
    def __exit__(self, typ, value, traceback):
        duration = time.time() - self._start
        self._summary.observe(duration, self._labels)


class CollectorRegistry:
    """Registry for collecting metrics"""
    
    def __init__(self):
        self._collectors: List[Metric] = []
        self._lock = threading.Lock()
    
    def register(self, collector: Metric):
        """Register a collector"""
        with self._lock:
            if collector in self._collectors:
                raise ValueError(f"Collector {collector.name} already registered")
            self._collectors.append(collector)
    
    def unregister(self, collector: Metric):
        """Unregister a collector"""
        with self._lock:
            if collector in self._collectors:
                self._collectors.remove(collector)
    
    def collect(self) -> List[Metric]:
        """Get all registered collectors"""
        with self._lock:
            return self._collectors.copy()
    
    def get_sample_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get the value of a specific metric sample"""
        labels = labels or {}
        label_key = tuple(sorted(labels.items()))
        
        with self._lock:
            for collector in self._collectors:
                if collector.name == name:
                    samples = collector.collect()
                    for sample_labels, value in samples:
                        sample_key = tuple(sorted(sample_labels.items()))
                        if sample_key == label_key:
                            return value
        return None


# Global default registry
REGISTRY = CollectorRegistry()


def generate_latest(registry: Optional[CollectorRegistry] = None) -> str:
    """Generate metrics in Prometheus text format"""
    if registry is None:
        registry = REGISTRY
    
    output = []
    
    for collector in registry.collect():
        # HELP line
        output.append(f"# HELP {collector.name} {collector.documentation}")
        
        # TYPE line
        output.append(f"# TYPE {collector.name} {collector._type}")
        
        # Samples
        if isinstance(collector, (Counter, Gauge)):
            samples = collector.collect()
            for labels_dict, value in samples:
                if labels_dict:
                    label_str = ','.join([f'{k}="{v}"' for k, v in sorted(labels_dict.items())])
                    output.append(f"{collector.name}{{{label_str}}} {value}")
                else:
                    output.append(f"{collector.name} {value}")
        
        elif isinstance(collector, Histogram):
            samples = collector.collect()
            for labels_dict, suffix, value in samples:
                if labels_dict:
                    label_str = ','.join([f'{k}="{v}"' for k, v in sorted(labels_dict.items())])
                    output.append(f"{collector.name}{suffix}{{{label_str}}} {value}")
                else:
                    output.append(f"{collector.name}{suffix} {value}")
        
        elif isinstance(collector, Summary):
            samples = collector.collect()
            for labels_dict, suffix, value in samples:
                if labels_dict:
                    label_str = ','.join([f'{k}="{v}"' for k, v in sorted(labels_dict.items())])
                    output.append(f"{collector.name}{suffix}{{{label_str}}} {value}")
                else:
                    output.append(f"{collector.name}{suffix} {value}")
        
        output.append("")  # Empty line between metrics
    
    return '\n'.join(output)


# Process metrics collector
class ProcessCollector:
    """Collector for process metrics"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        if registry is None:
            registry = REGISTRY
        
        self.cpu_seconds = Counter(
            'process_cpu_seconds_total',
            'Total user and system CPU time spent in seconds.',
            ()
        )
        
        self.open_fds = Gauge(
            'process_open_fds',
            'Number of open file descriptors.',
            ()
        )
        
        self.max_fds = Gauge(
            'process_max_fds',
            'Maximum number of open file descriptors.',
            ()
        )
        
        self.virtual_memory_bytes = Gauge(
            'process_virtual_memory_bytes',
            'Virtual memory size in bytes.',
            ()
        )
        
        self.resident_memory_bytes = Gauge(
            'process_resident_memory_bytes',
            'Resident memory size in bytes.',
            ()
        )
        
        self.start_time_seconds = Gauge(
            'process_start_time_seconds',
            'Start time of the process since unix epoch in seconds.',
            ()
        )
        
        # Set start time
        self.start_time_seconds.set(time.time())
        
        # Register with registry
        registry.register(self.cpu_seconds)
        registry.register(self.open_fds)
        registry.register(self.max_fds)
        registry.register(self.virtual_memory_bytes)
        registry.register(self.resident_memory_bytes)
        registry.register(self.start_time_seconds)


# Platform metrics collector
class PlatformCollector:
    """Collector for platform metrics"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        if registry is None:
            registry = REGISTRY
        
        self.python_info = Gauge(
            'python_info',
            'Python platform information.',
            ('version', 'implementation', 'major', 'minor', 'patchlevel')
        )
        
        # Set platform info
        version_info = sys.version_info
        self.python_info.set(
            1,
            {
                'version': platform.python_version(),
                'implementation': platform.python_implementation(),
                'major': str(version_info.major),
                'minor': str(version_info.minor),
                'patchlevel': str(version_info.micro),
            }
        )
        
        registry.register(self.python_info)


if __name__ == "__main__":
    # Example usage
    
    # Counter
    requests_total = Counter(
        'requests_total',
        'Total number of requests',
        ('method', 'endpoint')
    )
    REGISTRY.register(requests_total)
    
    requests_total.inc(labels={'method': 'GET', 'endpoint': '/api/users'})
    requests_total.inc(2, labels={'method': 'POST', 'endpoint': '/api/users'})
    
    # Counter with labels
    http_requests = Counter('http_requests_total', 'Total HTTP requests', ('method',))
    REGISTRY.register(http_requests)
    
    get_requests = http_requests.labels(method='GET')
    get_requests.inc()
    get_requests.inc()
    
    # Gauge
    temperature = Gauge('temperature_celsius', 'Current temperature in Celsius')
    REGISTRY.register(temperature)
    
    temperature.set(23.5)
    temperature.inc(1.5)
    temperature.dec(0.5)
    
    # Histogram
    request_duration = Histogram(
        'request_duration_seconds',
        'Request duration in seconds',
        buckets=(.01, .05, .1, .5, 1.0, 5.0, float('inf'))
    )
    REGISTRY.register(request_duration)
    
    request_duration.observe(0.05)
    request_duration.observe(0.15)
    request_duration.observe(0.75)
    
    # Histogram with timer
    with request_duration.time():
        time.sleep(0.01)  # Simulate work
    
    # Summary
    response_size = Summary('response_size_bytes', 'Response size in bytes')
    REGISTRY.register(response_size)
    
    response_size.observe(1024)
    response_size.observe(2048)
    response_size.observe(512)
    
    # Generate output
    print(generate_latest())
