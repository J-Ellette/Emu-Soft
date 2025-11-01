"""
Developed by PowerShield
"""

#!/usr/bin/env python3
"""
TracAgg - Distributed Tracing Aggregator for Microservices

This module provides a tracing aggregator that collects, correlates, and analyzes
distributed traces from multiple microservices in a system.

Features:
- Trace collection from multiple services
- Span correlation and trace reconstruction
- Service dependency mapping
- Latency analysis and bottleneck detection
- Trace sampling and filtering
- Query and search capabilities
"""

import json
import time
import threading
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib


class SpanKind(Enum):
    """Types of spans"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class TraceStatus(Enum):
    """Trace completion status"""
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    ERROR = "error"


@dataclass
class Span:
    """Individual span in a trace"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    service_name: str
    operation_name: str
    start_time: float
    end_time: Optional[float]
    duration_ms: Optional[float]
    kind: SpanKind
    status_code: int
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate duration if end_time is set"""
        if self.end_time and self.start_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class Trace:
    """Complete trace with multiple spans"""
    trace_id: str
    root_span_id: Optional[str]
    spans: List[Span] = field(default_factory=list)
    services: Set[str] = field(default_factory=set)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: TraceStatus = TraceStatus.INCOMPLETE
    error_count: int = 0
    
    def add_span(self, span: Span):
        """Add a span to the trace"""
        self.spans.append(span)
        self.services.add(span.service_name)
        
        # Update trace timing
        if self.start_time is None or span.start_time < self.start_time:
            self.start_time = span.start_time
        
        if span.end_time:
            if self.end_time is None or span.end_time > self.end_time:
                self.end_time = span.end_time
        
        # Check for errors
        if span.status_code >= 400:
            self.error_count += 1
            self.status = TraceStatus.ERROR
        
        # Calculate duration
        if self.start_time and self.end_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def is_complete(self) -> bool:
        """Check if all spans have ended"""
        return all(span.end_time is not None for span in self.spans)
    
    def get_critical_path(self) -> List[Span]:
        """Get the critical path (longest sequential chain)"""
        if not self.spans:
            return []
        
        # Build span map
        span_map = {span.span_id: span for span in self.spans}
        
        # Find root spans (no parent)
        roots = [s for s in self.spans if not s.parent_span_id]
        if not roots:
            return []
        
        # DFS to find longest path
        def get_path_duration(span: Span, visited: Set[str]) -> Tuple[float, List[Span]]:
            if span.span_id in visited:
                return 0.0, []
            
            visited.add(span.span_id)
            duration = span.duration_ms or 0.0
            best_path = [span]
            max_child_duration = 0.0
            
            # Find children
            children = [s for s in self.spans if s.parent_span_id == span.span_id]
            for child in children:
                child_duration, child_path = get_path_duration(child, visited.copy())
                if child_duration > max_child_duration:
                    max_child_duration = child_duration
                    best_path = [span] + child_path
            
            return duration + max_child_duration, best_path
        
        _, critical_path = get_path_duration(roots[0], set())
        return critical_path


@dataclass
class ServiceDependency:
    """Dependency between two services"""
    from_service: str
    to_service: str
    call_count: int = 0
    total_latency_ms: float = 0.0
    error_count: int = 0
    
    def average_latency_ms(self) -> float:
        """Calculate average latency"""
        return self.total_latency_ms / self.call_count if self.call_count > 0 else 0.0
    
    def error_rate(self) -> float:
        """Calculate error rate"""
        return self.error_count / self.call_count if self.call_count > 0 else 0.0


class TracAgg:
    """Distributed tracing aggregator"""
    
    def __init__(self, retention_seconds: int = 3600):
        """
        Initialize the trace aggregator
        
        Args:
            retention_seconds: How long to retain traces (default: 1 hour)
        """
        self.traces: Dict[str, Trace] = {}
        self.pending_spans: Dict[str, List[Span]] = defaultdict(list)
        self.retention_seconds = retention_seconds
        self.lock = threading.Lock()
        
        # Analytics data
        self.service_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'span_count': 0,
            'total_duration_ms': 0.0,
            'error_count': 0
        })
        self.dependencies: Dict[Tuple[str, str], ServiceDependency] = {}
    
    def ingest_span(self, span_data: Dict[str, Any]) -> str:
        """
        Ingest a span from a service
        
        Args:
            span_data: Span data dictionary
            
        Returns:
            trace_id: The trace ID this span belongs to
        """
        with self.lock:
            # Create span object
            span = Span(
                trace_id=span_data['trace_id'],
                span_id=span_data['span_id'],
                parent_span_id=span_data.get('parent_span_id'),
                service_name=span_data['service_name'],
                operation_name=span_data['operation_name'],
                start_time=span_data['start_time'],
                end_time=span_data.get('end_time'),
                duration_ms=span_data.get('duration_ms'),
                kind=SpanKind(span_data.get('kind', 'internal')),
                status_code=span_data.get('status_code', 200),
                tags=span_data.get('tags', {}),
                logs=span_data.get('logs', [])
            )
            
            # Get or create trace
            trace_id = span.trace_id
            if trace_id not in self.traces:
                self.traces[trace_id] = Trace(
                    trace_id=trace_id,
                    root_span_id=span.span_id if not span.parent_span_id else None
                )
            
            # Add span to trace
            trace = self.traces[trace_id]
            trace.add_span(span)
            
            # Update trace status
            if trace.is_complete():
                trace.status = TraceStatus.COMPLETE if trace.error_count == 0 else TraceStatus.ERROR
            
            # Update statistics
            self._update_stats(span)
            
            return trace_id
    
    def _update_stats(self, span: Span):
        """Update service statistics"""
        service = span.service_name
        stats = self.service_stats[service]
        
        stats['span_count'] += 1
        if span.duration_ms:
            stats['total_duration_ms'] += span.duration_ms
        if span.status_code >= 400:
            stats['error_count'] += 1
        
        # Update dependencies
        if span.kind == SpanKind.CLIENT and span.tags.get('peer.service'):
            peer_service = span.tags['peer.service']
            dep_key = (service, peer_service)
            
            if dep_key not in self.dependencies:
                self.dependencies[dep_key] = ServiceDependency(
                    from_service=service,
                    to_service=peer_service
                )
            
            dep = self.dependencies[dep_key]
            dep.call_count += 1
            if span.duration_ms:
                dep.total_latency_ms += span.duration_ms
            if span.status_code >= 400:
                dep.error_count += 1
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID"""
        with self.lock:
            return self.traces.get(trace_id)
    
    def query_traces(self, 
                     service_name: Optional[str] = None,
                     operation_name: Optional[str] = None,
                     min_duration_ms: Optional[float] = None,
                     max_duration_ms: Optional[float] = None,
                     has_error: Optional[bool] = None,
                     limit: int = 100) -> List[Trace]:
        """
        Query traces with filters
        
        Args:
            service_name: Filter by service
            operation_name: Filter by operation
            min_duration_ms: Minimum trace duration
            max_duration_ms: Maximum trace duration
            has_error: Filter traces with errors
            limit: Maximum number of results
            
        Returns:
            List of matching traces
        """
        with self.lock:
            results = []
            
            for trace in self.traces.values():
                # Apply filters
                if service_name and service_name not in trace.services:
                    continue
                
                if operation_name:
                    if not any(s.operation_name == operation_name for s in trace.spans):
                        continue
                
                if min_duration_ms and (not trace.duration_ms or trace.duration_ms < min_duration_ms):
                    continue
                
                if max_duration_ms and (trace.duration_ms and trace.duration_ms > max_duration_ms):
                    continue
                
                if has_error is not None:
                    if has_error and trace.error_count == 0:
                        continue
                    if not has_error and trace.error_count > 0:
                        continue
                
                results.append(trace)
                
                if len(results) >= limit:
                    break
            
            return results
    
    def get_service_dependencies(self) -> List[ServiceDependency]:
        """Get all service dependencies"""
        with self.lock:
            return list(self.dependencies.values())
    
    def get_service_graph(self) -> Dict[str, List[str]]:
        """
        Get service dependency graph
        
        Returns:
            Dictionary mapping service to list of downstream services
        """
        with self.lock:
            graph = defaultdict(list)
            for dep in self.dependencies.values():
                graph[dep.from_service].append(dep.to_service)
            return dict(graph)
    
    def get_service_stats(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for a service
        
        Args:
            service_name: Service to get stats for (None for all)
            
        Returns:
            Statistics dictionary
        """
        with self.lock:
            if service_name:
                stats = self.service_stats.get(service_name, {})
                if stats.get('span_count', 0) > 0:
                    stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['span_count']
                    stats['error_rate'] = stats['error_count'] / stats['span_count']
                return stats
            else:
                result = {}
                for service, stats in self.service_stats.items():
                    service_stats = dict(stats)
                    if stats['span_count'] > 0:
                        service_stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['span_count']
                        service_stats['error_rate'] = stats['error_count'] / stats['span_count']
                    result[service] = service_stats
                return result
    
    def find_bottlenecks(self, percentile: float = 0.95) -> List[Dict[str, Any]]:
        """
        Find performance bottlenecks
        
        Args:
            percentile: Percentile threshold for identifying slow operations
            
        Returns:
            List of bottleneck information
        """
        with self.lock:
            # Group spans by service and operation
            operations = defaultdict(list)
            for trace in self.traces.values():
                for span in trace.spans:
                    if span.duration_ms:
                        key = (span.service_name, span.operation_name)
                        operations[key].append(span.duration_ms)
            
            # Calculate percentiles
            bottlenecks = []
            for (service, operation), durations in operations.items():
                if not durations:
                    continue
                
                durations_sorted = sorted(durations)
                idx = int(len(durations_sorted) * percentile)
                p_value = durations_sorted[idx] if idx < len(durations_sorted) else durations_sorted[-1]
                avg_duration = sum(durations) / len(durations)
                
                bottlenecks.append({
                    'service': service,
                    'operation': operation,
                    'avg_duration_ms': avg_duration,
                    f'p{int(percentile*100)}_duration_ms': p_value,
                    'sample_count': len(durations)
                })
            
            # Sort by percentile value
            bottlenecks.sort(key=lambda x: x[f'p{int(percentile*100)}_duration_ms'], reverse=True)
            return bottlenecks
    
    def cleanup_old_traces(self):
        """Remove traces older than retention period"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.retention_seconds
            
            old_traces = [
                trace_id for trace_id, trace in self.traces.items()
                if trace.end_time and trace.end_time < cutoff_time
            ]
            
            for trace_id in old_traces:
                del self.traces[trace_id]
            
            return len(old_traces)
    
    def get_trace_count(self) -> int:
        """Get total number of traces stored"""
        with self.lock:
            return len(self.traces)
    
    def export_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a trace in JSON format
        
        Args:
            trace_id: Trace ID to export
            
        Returns:
            Trace data as dictionary or None if not found
        """
        trace = self.get_trace(trace_id)
        if not trace:
            return None
        
        return {
            'trace_id': trace.trace_id,
            'root_span_id': trace.root_span_id,
            'services': list(trace.services),
            'start_time': trace.start_time,
            'end_time': trace.end_time,
            'duration_ms': trace.duration_ms,
            'status': trace.status.value,
            'error_count': trace.error_count,
            'spans': [
                {
                    'span_id': span.span_id,
                    'parent_span_id': span.parent_span_id,
                    'service_name': span.service_name,
                    'operation_name': span.operation_name,
                    'start_time': span.start_time,
                    'end_time': span.end_time,
                    'duration_ms': span.duration_ms,
                    'kind': span.kind.value,
                    'status_code': span.status_code,
                    'tags': span.tags,
                    'logs': span.logs
                }
                for span in trace.spans
            ]
        }
    
    def clear(self):
        """Clear all traces and statistics"""
        with self.lock:
            self.traces.clear()
            self.pending_spans.clear()
            self.service_stats.clear()
            self.dependencies.clear()


def create_span_data(trace_id: str, span_id: str, service_name: str, 
                     operation_name: str, parent_span_id: Optional[str] = None,
                     duration_ms: Optional[float] = None, 
                     status_code: int = 200,
                     kind: str = "internal",
                     tags: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Helper function to create span data
    
    Args:
        trace_id: Trace identifier
        span_id: Span identifier
        service_name: Name of the service
        operation_name: Name of the operation
        parent_span_id: Parent span ID (None for root)
        duration_ms: Duration in milliseconds
        status_code: HTTP-style status code
        kind: Span kind (internal, server, client, producer, consumer)
        tags: Additional tags
        
    Returns:
        Span data dictionary
    """
    start_time = time.time()
    end_time = start_time + (duration_ms / 1000.0) if duration_ms else None
    
    return {
        'trace_id': trace_id,
        'span_id': span_id,
        'parent_span_id': parent_span_id,
        'service_name': service_name,
        'operation_name': operation_name,
        'start_time': start_time,
        'end_time': end_time,
        'duration_ms': duration_ms,
        'kind': kind,
        'status_code': status_code,
        'tags': tags or {},
        'logs': []
    }
