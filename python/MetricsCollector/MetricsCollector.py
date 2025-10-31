"""
Developed by PowerShield, as an alternative to prometheus_client

Prometheus Emulator - Metrics Collection and Monitoring
This emulates the core functionality of Prometheus, a monitoring and alerting toolkit
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime
import threading


class Metric:
    """Base class for all metrics"""
    
    def __init__(self, name: str, documentation: str, labels: Optional[List[str]] = None):
        self.name = name
        self.documentation = documentation
        self.labels = labels or []
        self.samples = {}
        self._lock = threading.Lock()
    
    def _get_key(self, label_values: Dict[str, str]) -> str:
        """Generate a key from label values"""
        if not self.labels:
            return ""
        
        label_pairs = sorted(label_values.items())
        return ",".join(f"{k}={v}" for k, v in label_pairs)
    
    def describe(self) -> str:
        """Return metric description in Prometheus format"""
        return f"# HELP {self.name} {self.documentation}\n# TYPE {self.name} {self.metric_type}"


class Counter(Metric):
    """A counter metric that only increases"""
    
    metric_type = "counter"
    
    def __init__(self, name: str, documentation: str, labels: Optional[List[str]] = None):
        super().__init__(name, documentation, labels)
    
    def inc(self, amount: float = 1.0, **label_values):
        """Increment the counter"""
        if amount < 0:
            raise ValueError("Counter can only increase")
        
        with self._lock:
            key = self._get_key(label_values)
            self.samples[key] = self.samples.get(key, 0.0) + amount
    
    def get(self, **label_values) -> float:
        """Get the current counter value"""
        key = self._get_key(label_values)
        return self.samples.get(key, 0.0)
    
    def reset(self):
        """Reset all counters (for testing)"""
        with self._lock:
            self.samples.clear()


class Gauge(Metric):
    """A gauge metric that can increase or decrease"""
    
    metric_type = "gauge"
    
    def __init__(self, name: str, documentation: str, labels: Optional[List[str]] = None):
        super().__init__(name, documentation, labels)
    
    def set(self, value: float, **label_values):
        """Set the gauge to a specific value"""
        with self._lock:
            key = self._get_key(label_values)
            self.samples[key] = value
    
    def inc(self, amount: float = 1.0, **label_values):
        """Increment the gauge"""
        with self._lock:
            key = self._get_key(label_values)
            self.samples[key] = self.samples.get(key, 0.0) + amount
    
    def dec(self, amount: float = 1.0, **label_values):
        """Decrement the gauge"""
        self.inc(-amount, **label_values)
    
    def get(self, **label_values) -> float:
        """Get the current gauge value"""
        key = self._get_key(label_values)
        return self.samples.get(key, 0.0)
    
    def set_to_current_time(self, **label_values):
        """Set the gauge to the current Unix timestamp"""
        self.set(time.time(), **label_values)


class Histogram(Metric):
    """A histogram metric that samples observations"""
    
    metric_type = "histogram"
    
    def __init__(self, name: str, documentation: str, labels: Optional[List[str]] = None,
                 buckets: Optional[List[float]] = None):
        super().__init__(name, documentation, labels)
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
        self.bucket_counts = defaultdict(lambda: defaultdict(int))
        self.sums = defaultdict(float)
        self.counts = defaultdict(int)
    
    def observe(self, amount: float, **label_values):
        """Record an observation"""
        with self._lock:
            key = self._get_key(label_values)
            
            # Update sum and count
            self.sums[key] += amount
            self.counts[key] += 1
            
            # Update buckets
            for bucket in self.buckets:
                if amount <= bucket:
                    self.bucket_counts[key][bucket] += 1
            
            # Also count values that exceed all buckets
            self.bucket_counts[key][float('inf')] += 1
    
    def get_sum(self, **label_values) -> float:
        """Get the sum of all observations"""
        key = self._get_key(label_values)
        return self.sums.get(key, 0.0)
    
    def get_count(self, **label_values) -> int:
        """Get the count of observations"""
        key = self._get_key(label_values)
        return self.counts.get(key, 0)
    
    def get_bucket(self, bucket: float, **label_values) -> int:
        """Get the count for a specific bucket"""
        key = self._get_key(label_values)
        return self.bucket_counts[key].get(bucket, 0)


class Summary(Metric):
    """A summary metric that calculates quantiles"""
    
    metric_type = "summary"
    
    def __init__(self, name: str, documentation: str, labels: Optional[List[str]] = None):
        super().__init__(name, documentation, labels)
        self.observations = defaultdict(list)
        self.sums = defaultdict(float)
        self.counts = defaultdict(int)
    
    def observe(self, amount: float, **label_values):
        """Record an observation"""
        with self._lock:
            key = self._get_key(label_values)
            self.observations[key].append(amount)
            self.sums[key] += amount
            self.counts[key] += 1
    
    def get_sum(self, **label_values) -> float:
        """Get the sum of all observations"""
        key = self._get_key(label_values)
        return self.sums.get(key, 0.0)
    
    def get_count(self, **label_values) -> int:
        """Get the count of observations"""
        key = self._get_key(label_values)
        return self.counts.get(key, 0)
    
    def get_quantile(self, quantile: float, **label_values) -> float:
        """Calculate a quantile (0.0 to 1.0)"""
        key = self._get_key(label_values)
        obs = sorted(self.observations.get(key, []))
        
        if not obs:
            return 0.0
        
        index = int(quantile * (len(obs) - 1))
        return obs[index]


class Registry:
    """Metrics registry"""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()
    
    def register(self, metric: Metric):
        """Register a metric"""
        with self._lock:
            if metric.name in self.metrics:
                raise ValueError(f"Metric {metric.name} already registered")
            self.metrics[metric.name] = metric
    
    def unregister(self, metric: Metric):
        """Unregister a metric"""
        with self._lock:
            if metric.name in self.metrics:
                del self.metrics[metric.name]
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name"""
        return self.metrics.get(name)
    
    def collect(self) -> str:
        """Collect all metrics in Prometheus text format"""
        output = []
        
        for metric in self.metrics.values():
            output.append(metric.describe())
            
            # Add metric samples
            for key, value in metric.samples.items():
                if key:
                    labels = "{" + key + "}"
                else:
                    labels = ""
                output.append(f"{metric.name}{labels} {value}")
        
        return "\n".join(output)


# Global default registry
REGISTRY = Registry()


def start_http_server(port: int, registry: Registry = REGISTRY):
    """Start the Prometheus metrics HTTP server"""
    print(f"Starting Prometheus metrics server on port {port}")
    print(f"Metrics endpoint: http://localhost:{port}/metrics")
    
    # In a real implementation, this would start an HTTP server
    # For the emulator, we just print the message
    return True


def push_to_gateway(gateway: str, job: str, registry: Registry = REGISTRY):
    """Push metrics to a Pushgateway"""
    print(f"Pushing metrics to {gateway} for job '{job}'")
    metrics = registry.collect()
    print(f"Pushed {len(metrics)} bytes of metrics")
    return True


def generate_latest(registry: Registry = REGISTRY) -> str:
    """Generate metrics in Prometheus text format"""
    return registry.collect()


def exposition_format(metric: Metric) -> str:
    """Format a metric in Prometheus exposition format"""
    lines = [metric.describe()]
    
    for key, value in metric.samples.items():
        if key:
            labels = "{" + key + "}"
        else:
            labels = ""
        lines.append(f"{metric.name}{labels} {value}")
    
    return "\n".join(lines)


# Context managers for timing
class Timer:
    """Context manager for timing code blocks"""
    
    def __init__(self, metric: Histogram, **labels):
        self.metric = metric
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.metric.observe(duration, **self.labels)


def time_function(histogram: Histogram, **labels):
    """Decorator to time function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Timer(histogram, **labels):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions
def info(name: str, documentation: str, **labels) -> Dict[str, str]:
    """Create an info metric (implemented as a gauge set to 1)"""
    gauge = Gauge(f"{name}_info", documentation, list(labels.keys()))
    REGISTRY.register(gauge)
    gauge.set(1, **labels)
    return labels


def enum(name: str, documentation: str, states: List[str]) -> Gauge:
    """Create an enum metric (implemented as a gauge)"""
    gauge = Gauge(name, documentation, ["state"])
    REGISTRY.register(gauge)
    return gauge


# Helper class for metric labels
class Labels:
    """Helper class for working with metric labels"""
    
    def __init__(self, **labels):
        self.labels = labels
    
    def __repr__(self):
        return f"Labels({self.labels})"
    
    def to_dict(self):
        return self.labels


if __name__ == "__main__":
    print("Prometheus Emulator")
    print("This module emulates Prometheus metrics collection functionality")
