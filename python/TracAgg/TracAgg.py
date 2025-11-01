"""
Developed by PowerShield, as a distributed tracing aggregator

TracAgg - Distributed Tracing Aggregator for Microservices

This module provides functionality to aggregate, analyze, and visualize
distributed traces from multiple microservices without external dependencies.

Features:
- Trace collection from multiple services
- Trace aggregation and correlation
- Service dependency mapping
- Latency analysis and percentile calculations
- Error rate tracking
- Critical path analysis
- Trace search and filtering
- Service health metrics
- Bottleneck detection

Note: This is a pure Python implementation using only standard library.
"""

import json
import time
import threading
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import statistics


class SpanKind(Enum):
    """Type of span"""
    UNSPECIFIED = 0
    SERVER = 1
    CLIENT = 2
    PRODUCER = 3
    CONSUMER = 4


class StatusCode(Enum):
    """Status codes for spans"""
    OK = 0
    ERROR = 1


@dataclass
class Span:
    """Represents a span in a distributed trace"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    service_name: str
    operation_name: str
    start_time: float
    duration: float
    status: StatusCode = StatusCode.OK
    kind: SpanKind = SpanKind.UNSPECIFIED
    attributes: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'service_name': self.service_name,
            'operation_name': self.operation_name,
            'start_time': self.start_time,
            'duration': self.duration,
            'status': self.status.name,
            'kind': self.kind.name,
            'attributes': self.attributes,
            'error_message': self.error_message
        }


@dataclass
class Trace:
    """Represents a complete distributed trace"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    start_time: float = 0.0
    duration: float = 0.0
    service_count: int = 0
    span_count: int = 0
    error_count: int = 0
    services: Set[str] = field(default_factory=set)
    
    def add_span(self, span: Span):
        """Add a span to the trace"""
        self.spans.append(span)
        self.services.add(span.service_name)
        self.span_count = len(self.spans)
        self.service_count = len(self.services)
        
        if span.status == StatusCode.ERROR:
            self.error_count += 1
        
        # Update trace timing
        if not self.start_time or span.start_time < self.start_time:
            self.start_time = span.start_time
        
        end_time = span.start_time + span.duration
        trace_end = self.start_time + self.duration
        if end_time > trace_end:
            self.duration = end_time - self.start_time
    
    def get_root_span(self) -> Optional[Span]:
        """Get the root span of the trace"""
        for span in self.spans:
            if span.parent_span_id is None:
                return span
        return None
    
    def get_critical_path(self) -> List[Span]:
        """Calculate the critical path (longest duration path) through the trace"""
        if not self.spans:
            return []
        
        # Build parent-child relationships
        children_map = defaultdict(list)
        for span in self.spans:
            if span.parent_span_id:
                children_map[span.parent_span_id].append(span)
        
        def get_path_duration(span: Span) -> Tuple[float, List[Span]]:
            """Recursively calculate max duration path from this span"""
            children = children_map.get(span.span_id, [])
            if not children:
                return span.duration, [span]
            
            max_child_duration = 0.0
            max_child_path = []
            for child in children:
                child_duration, child_path = get_path_duration(child)
                if child_duration > max_child_duration:
                    max_child_duration = child_duration
                    max_child_path = child_path
            
            return span.duration + max_child_duration, [span] + max_child_path
        
        root = self.get_root_span()
        if root:
            _, path = get_path_duration(root)
            return path
        return []


@dataclass
class ServiceMetrics:
    """Metrics for a service"""
    service_name: str
    request_count: int = 0
    error_count: int = 0
    total_duration: float = 0.0
    durations: List[float] = field(default_factory=list)
    
    def add_request(self, duration: float, has_error: bool = False):
        """Add a request to the metrics"""
        self.request_count += 1
        if has_error:
            self.error_count += 1
        self.total_duration += duration
        self.durations.append(duration)
    
    def get_error_rate(self) -> float:
        """Calculate error rate"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def get_avg_duration(self) -> float:
        """Calculate average duration"""
        if self.request_count == 0:
            return 0.0
        return self.total_duration / self.request_count
    
    def get_percentile(self, percentile: float) -> float:
        """Calculate duration percentile"""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        index = int(len(sorted_durations) * percentile / 100)
        return sorted_durations[min(index, len(sorted_durations) - 1)]


class TracAggregator:
    """Aggregates and analyzes distributed traces"""
    
    def __init__(self):
        """Initialize the trace aggregator"""
        self.traces: Dict[str, Trace] = {}
        self.service_metrics: Dict[str, ServiceMetrics] = {}
        self.service_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.lock = threading.Lock()
    
    def ingest_span(self, span: Span):
        """Ingest a single span into the aggregator"""
        with self.lock:
            # Get or create trace
            if span.trace_id not in self.traces:
                self.traces[span.trace_id] = Trace(trace_id=span.trace_id)
            
            trace = self.traces[span.trace_id]
            trace.add_span(span)
            
            # Update service metrics
            if span.service_name not in self.service_metrics:
                self.service_metrics[span.service_name] = ServiceMetrics(
                    service_name=span.service_name
                )
            
            metrics = self.service_metrics[span.service_name]
            metrics.add_request(
                duration=span.duration,
                has_error=(span.status == StatusCode.ERROR)
            )
            
            # Update service dependencies
            if span.parent_span_id:
                # Find parent span to determine calling service
                for s in trace.spans:
                    if s.span_id == span.parent_span_id:
                        if s.service_name != span.service_name:
                            self.service_dependencies[s.service_name].add(
                                span.service_name
                            )
                        break
    
    def ingest_spans(self, spans: List[Span]):
        """Ingest multiple spans"""
        for span in spans:
            self.ingest_span(span)
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a specific trace by ID"""
        with self.lock:
            return self.traces.get(trace_id)
    
    def get_all_traces(self) -> List[Trace]:
        """Get all traces"""
        with self.lock:
            return list(self.traces.values())
    
    def search_traces(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        has_errors: Optional[bool] = None,
        min_span_count: Optional[int] = None
    ) -> List[Trace]:
        """Search for traces matching criteria"""
        with self.lock:
            results = []
            
            for trace in self.traces.values():
                # Filter by service
                if service_name and service_name not in trace.services:
                    continue
                
                # Filter by operation
                if operation_name:
                    has_operation = any(
                        s.operation_name == operation_name for s in trace.spans
                    )
                    if not has_operation:
                        continue
                
                # Filter by duration
                if min_duration and trace.duration < min_duration:
                    continue
                if max_duration and trace.duration > max_duration:
                    continue
                
                # Filter by errors
                if has_errors is not None:
                    if has_errors and trace.error_count == 0:
                        continue
                    if not has_errors and trace.error_count > 0:
                        continue
                
                # Filter by span count
                if min_span_count and trace.span_count < min_span_count:
                    continue
                
                results.append(trace)
            
            return results
    
    def get_service_metrics(self, service_name: str) -> Optional[ServiceMetrics]:
        """Get metrics for a specific service"""
        with self.lock:
            return self.service_metrics.get(service_name)
    
    def get_all_service_metrics(self) -> Dict[str, ServiceMetrics]:
        """Get metrics for all services"""
        with self.lock:
            return dict(self.service_metrics)
    
    def get_service_dependencies(self) -> Dict[str, Set[str]]:
        """Get service dependency graph"""
        with self.lock:
            return {k: set(v) for k, v in self.service_dependencies.items()}
    
    def get_slowest_operations(self, limit: int = 10) -> List[Tuple[str, str, float]]:
        """Get the slowest operations across all services"""
        operation_durations = defaultdict(list)
        
        with self.lock:
            for trace in self.traces.values():
                for span in trace.spans:
                    key = (span.service_name, span.operation_name)
                    operation_durations[key].append(span.duration)
        
        # Calculate average duration for each operation
        operation_avg = []
        for (service, operation), durations in operation_durations.items():
            avg_duration = sum(durations) / len(durations)
            operation_avg.append((service, operation, avg_duration))
        
        # Sort by duration and return top N
        operation_avg.sort(key=lambda x: x[2], reverse=True)
        return operation_avg[:limit]
    
    def get_error_prone_operations(self, limit: int = 10) -> List[Tuple[str, str, float, int]]:
        """Get operations with highest error rates"""
        operation_stats = defaultdict(lambda: {'total': 0, 'errors': 0})
        
        with self.lock:
            for trace in self.traces.values():
                for span in trace.spans:
                    key = (span.service_name, span.operation_name)
                    operation_stats[key]['total'] += 1
                    if span.status == StatusCode.ERROR:
                        operation_stats[key]['errors'] += 1
        
        # Calculate error rates
        error_rates = []
        for (service, operation), stats in operation_stats.items():
            if stats['total'] > 0:
                error_rate = stats['errors'] / stats['total']
                error_rates.append((
                    service,
                    operation,
                    error_rate,
                    stats['errors']
                ))
        
        # Sort by error rate and return top N
        error_rates.sort(key=lambda x: x[2], reverse=True)
        return error_rates[:limit]
    
    def analyze_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Perform detailed analysis of a trace"""
        trace = self.get_trace(trace_id)
        if not trace:
            return None
        
        critical_path = trace.get_critical_path()
        
        analysis = {
            'trace_id': trace_id,
            'total_duration': trace.duration,
            'span_count': trace.span_count,
            'service_count': trace.service_count,
            'services': list(trace.services),
            'error_count': trace.error_count,
            'has_errors': trace.error_count > 0,
            'critical_path': [
                {
                    'service': span.service_name,
                    'operation': span.operation_name,
                    'duration': span.duration
                }
                for span in critical_path
            ],
            'critical_path_duration': sum(s.duration for s in critical_path),
            'service_breakdown': {}
        }
        
        # Calculate time spent in each service
        service_times = defaultdict(float)
        for span in trace.spans:
            service_times[span.service_name] += span.duration
        
        for service, duration in service_times.items():
            analysis['service_breakdown'][service] = {
                'duration': duration,
                'percentage': (duration / trace.duration * 100) if trace.duration > 0 else 0
            }
        
        return analysis
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for all traces"""
        with self.lock:
            if not self.traces:
                return {
                    'total_traces': 0,
                    'total_spans': 0,
                    'total_errors': 0,
                    'services': []
                }
            
            total_spans = sum(t.span_count for t in self.traces.values())
            total_errors = sum(t.error_count for t in self.traces.values())
            all_durations = [t.duration for t in self.traces.values()]
            
            return {
                'total_traces': len(self.traces),
                'total_spans': total_spans,
                'total_errors': total_errors,
                'avg_trace_duration': statistics.mean(all_durations) if all_durations else 0,
                'p50_trace_duration': statistics.median(all_durations) if all_durations else 0,
                'p95_trace_duration': self._percentile(all_durations, 95) if all_durations else 0,
                'p99_trace_duration': self._percentile(all_durations, 99) if all_durations else 0,
                'services': list(self.service_metrics.keys()),
                'service_count': len(self.service_metrics)
            }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def export_to_json(self, filename: str):
        """Export all traces to JSON file"""
        with self.lock:
            data = {
                'traces': [
                    {
                        'trace_id': trace.trace_id,
                        'duration': trace.duration,
                        'span_count': trace.span_count,
                        'services': list(trace.services),
                        'spans': [span.to_dict() for span in trace.spans]
                    }
                    for trace in self.traces.values()
                ]
            }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_from_json(self, filename: str):
        """Import traces from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        for trace_data in data['traces']:
            for span_data in trace_data['spans']:
                span = Span(
                    trace_id=span_data['trace_id'],
                    span_id=span_data['span_id'],
                    parent_span_id=span_data['parent_span_id'],
                    service_name=span_data['service_name'],
                    operation_name=span_data['operation_name'],
                    start_time=span_data['start_time'],
                    duration=span_data['duration'],
                    status=StatusCode[span_data['status']],
                    kind=SpanKind[span_data['kind']],
                    attributes=span_data.get('attributes', {}),
                    error_message=span_data.get('error_message')
                )
                self.ingest_span(span)
    
    def clear(self):
        """Clear all traces and metrics"""
        with self.lock:
            self.traces.clear()
            self.service_metrics.clear()
            self.service_dependencies.clear()


def create_aggregator() -> TracAggregator:
    """Create a new trace aggregator instance"""
    return TracAggregator()


# Convenience function for creating spans
def create_span(
    trace_id: str,
    span_id: str,
    service_name: str,
    operation_name: str,
    start_time: float,
    duration: float,
    parent_span_id: Optional[str] = None,
    status: StatusCode = StatusCode.OK,
    kind: SpanKind = SpanKind.UNSPECIFIED,
    attributes: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> Span:
    """Create a span object"""
    return Span(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        service_name=service_name,
        operation_name=operation_name,
        start_time=start_time,
        duration=duration,
        status=status,
        kind=kind,
        attributes=attributes or {},
        error_message=error_message
    )
