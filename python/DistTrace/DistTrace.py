"""
Developed by PowerShield, as an alternative to Jaeger
"""

#!/usr/bin/env python3
"""
Jaeger Emulator - Distributed Tracing

This module emulates core Jaeger functionality including:
- Span creation and management
- Trace context propagation
- Tag and log management
- Trace collection and storage
- Trace querying
- Service dependency graph
"""

import time
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class SpanKind(Enum):
    """Span kinds"""
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"


@dataclass
class SpanLog:
    """Log entry within a span"""
    timestamp: float
    fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanReference:
    """Reference to another span"""
    ref_type: str  # "CHILD_OF" or "FOLLOWS_FROM"
    trace_id: str
    span_id: str


@dataclass
class Span:
    """Distributed trace span"""
    trace_id: str
    span_id: str
    operation_name: str
    start_time: float
    service_name: str
    parent_span_id: Optional[str] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[SpanLog] = field(default_factory=list)
    references: List[SpanReference] = field(default_factory=list)
    kind: SpanKind = SpanKind.INTERNAL
    status_code: int = 0
    status_message: str = ""


@dataclass
class Trace:
    """Complete distributed trace"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    
    def add_span(self, span: Span):
        """Add span to trace"""
        self.spans.append(span)
        
        # Update trace metadata
        if span.service_name not in self.services:
            self.services.append(span.service_name)
        
        if self.start_time is None or span.start_time < self.start_time:
            self.start_time = span.start_time
        
        if span.end_time:
            if self.end_time is None or span.end_time > self.end_time:
                self.end_time = span.end_time
        
        if self.start_time and self.end_time:
            self.duration = self.end_time - self.start_time


@dataclass
class Service:
    """Service information"""
    name: str
    operations: List[str] = field(default_factory=list)
    span_count: int = 0
    trace_count: int = 0


class SpanContext:
    """Trace context for span propagation"""
    
    def __init__(self, trace_id: str, span_id: str, parent_span_id: Optional[str] = None):
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.baggage: Dict[str, str] = {}
    
    def set_baggage_item(self, key: str, value: str):
        """Set baggage item"""
        self.baggage[key] = value
    
    def get_baggage_item(self, key: str) -> Optional[str]:
        """Get baggage item"""
        return self.baggage.get(key)
    
    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers for propagation"""
        headers = {
            "uber-trace-id": f"{self.trace_id}:{self.span_id}:{self.parent_span_id or '0'}:1"
        }
        
        for key, value in self.baggage.items():
            headers[f"uberctx-{key}"] = value
        
        return headers
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> Optional['SpanContext']:
        """Extract context from HTTP headers"""
        trace_header = headers.get("uber-trace-id")
        if not trace_header:
            return None
        
        parts = trace_header.split(":")
        if len(parts) < 4:
            return None
        
        trace_id, span_id, parent_id, _ = parts
        parent_span_id = parent_id if parent_id != "0" else None
        
        context = cls(trace_id, span_id, parent_span_id)
        
        # Extract baggage
        for key, value in headers.items():
            if key.startswith("uberctx-"):
                baggage_key = key[8:]
                context.baggage[baggage_key] = value
        
        return context


class JaegerTracer:
    """Jaeger tracer for creating and managing spans"""
    
    def __init__(self, service_name: str, emulator: 'DistTrace'):
        self.service_name = service_name
        self.emulator = emulator
        self.active_spans: List[Span] = []
    
    def start_span(self, operation_name: str, 
                   parent: Optional[SpanContext] = None,
                   tags: Optional[Dict[str, Any]] = None,
                   kind: SpanKind = SpanKind.INTERNAL) -> Span:
        """Start a new span"""
        if parent:
            trace_id = parent.trace_id
            parent_span_id = parent.span_id
        else:
            trace_id = self._generate_trace_id()
            parent_span_id = None
        
        span = Span(
            trace_id=trace_id,
            span_id=self._generate_span_id(),
            operation_name=operation_name,
            start_time=time.time(),
            service_name=self.service_name,
            parent_span_id=parent_span_id,
            kind=kind
        )
        
        if tags:
            span.tags.update(tags)
        
        # Add standard tags
        span.tags["span.kind"] = kind.value
        span.tags["component"] = self.service_name
        
        self.active_spans.append(span)
        return span
    
    def finish_span(self, span: Span):
        """Finish a span"""
        span.end_time = time.time()
        span.duration = span.end_time - span.start_time
        
        if span in self.active_spans:
            self.active_spans.remove(span)
        
        self.emulator.report_span(span)
    
    def inject(self, span: Span, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject span context into headers"""
        context = SpanContext(span.trace_id, span.span_id, span.parent_span_id)
        headers.update(context.to_headers())
        return headers
    
    def extract(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """Extract span context from headers"""
        return SpanContext.from_headers(headers)
    
    def _generate_trace_id(self) -> str:
        """Generate a trace ID"""
        return secrets.token_hex(16)
    
    def _generate_span_id(self) -> str:
        """Generate a span ID"""
        return secrets.token_hex(8)


class DistTrace:
    """Main Jaeger emulator class"""
    
    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.services: Dict[str, Service] = {}
        self.span_buffer: List[Span] = []
    
    def get_tracer(self, service_name: str) -> JaegerTracer:
        """Get a tracer for a service"""
        if service_name not in self.services:
            self.services[service_name] = Service(name=service_name)
        return JaegerTracer(service_name, self)
    
    def report_span(self, span: Span):
        """Report a completed span"""
        self.span_buffer.append(span)
        
        # Get or create trace
        if span.trace_id not in self.traces:
            self.traces[span.trace_id] = Trace(trace_id=span.trace_id)
        
        trace = self.traces[span.trace_id]
        trace.add_span(span)
        
        # Update service info
        if span.service_name not in self.services:
            self.services[span.service_name] = Service(name=span.service_name)
        
        service = self.services[span.service_name]
        service.span_count += 1
        
        if span.operation_name not in service.operations:
            service.operations.append(span.operation_name)
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID"""
        return self.traces.get(trace_id)
    
    def find_traces(self, service: Optional[str] = None,
                   operation: Optional[str] = None,
                   tags: Optional[Dict[str, Any]] = None,
                   min_duration: Optional[float] = None,
                   max_duration: Optional[float] = None,
                   limit: int = 20) -> List[Trace]:
        """Find traces matching criteria"""
        results = []
        
        for trace in self.traces.values():
            # Filter by service
            if service and service not in trace.services:
                continue
            
            # Filter by operation
            if operation:
                has_operation = any(s.operation_name == operation for s in trace.spans)
                if not has_operation:
                    continue
            
            # Filter by tags
            if tags:
                matches = False
                for span in trace.spans:
                    if all(span.tags.get(k) == v for k, v in tags.items()):
                        matches = True
                        break
                if not matches:
                    continue
            
            # Filter by duration
            if trace.duration:
                if min_duration and trace.duration < min_duration:
                    continue
                if max_duration and trace.duration > max_duration:
                    continue
            
            results.append(trace)
            
            if len(results) >= limit:
                break
        
        # Sort by start time (most recent first)
        results.sort(key=lambda t: t.start_time or 0, reverse=True)
        
        return results
    
    def get_services(self) -> List[str]:
        """Get list of all services"""
        return list(self.services.keys())
    
    def get_operations(self, service: str) -> List[str]:
        """Get operations for a service"""
        if service in self.services:
            return self.services[service].operations
        return []
    
    def get_dependencies(self) -> Dict[str, List[str]]:
        """Get service dependency graph"""
        dependencies: Dict[str, set] = {}
        
        for trace in self.traces.values():
            # Build parent-child relationships
            span_map = {s.span_id: s for s in trace.spans}
            
            for span in trace.spans:
                if span.parent_span_id and span.parent_span_id in span_map:
                    parent_span = span_map[span.parent_span_id]
                    
                    # Create dependency
                    if parent_span.service_name != span.service_name:
                        if parent_span.service_name not in dependencies:
                            dependencies[parent_span.service_name] = set()
                        dependencies[parent_span.service_name].add(span.service_name)
        
        # Convert sets to lists
        return {k: list(v) for k, v in dependencies.items()}
    
    def get_trace_statistics(self, service: Optional[str] = None) -> Dict[str, Any]:
        """Get trace statistics"""
        traces_list = list(self.traces.values())
        
        if service:
            traces_list = [t for t in traces_list if service in t.services]
        
        if not traces_list:
            return {
                "trace_count": 0,
                "span_count": 0,
                "avg_duration": 0,
                "max_duration": 0,
                "min_duration": 0
            }
        
        durations = [t.duration for t in traces_list if t.duration is not None]
        span_counts = [len(t.spans) for t in traces_list]
        
        return {
            "trace_count": len(traces_list),
            "span_count": sum(span_counts),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "avg_spans_per_trace": sum(span_counts) / len(span_counts) if span_counts else 0
        }
    
    def clear(self):
        """Clear all traces"""
        self.traces.clear()
        self.span_buffer.clear()


# Example usage
if __name__ == "__main__":
    # Create Jaeger emulator
    jaeger = DistTrace()
    
    # Get tracer for frontend service
    frontend_tracer = jaeger.get_tracer("frontend")
    
    # Start root span
    root_span = frontend_tracer.start_span(
        "HTTP GET /api/users",
        kind=SpanKind.SERVER,
        tags={"http.method": "GET", "http.url": "/api/users"}
    )
    
    # Simulate some work
    time.sleep(0.01)
    
    # Create child span for API call
    api_tracer = jaeger.get_tracer("api-service")
    headers = {}
    frontend_tracer.inject(root_span, headers)
    
    # Extract context in API service
    parent_context = api_tracer.extract(headers)
    api_span = api_tracer.start_span(
        "GET /users",
        parent=parent_context,
        kind=SpanKind.SERVER,
        tags={"http.method": "GET"}
    )
    
    time.sleep(0.02)
    
    # Database call
    db_tracer = jaeger.get_tracer("database")
    db_headers = {}
    api_tracer.inject(api_span, db_headers)
    db_context = db_tracer.extract(db_headers)
    
    db_span = db_tracer.start_span(
        "SELECT users",
        parent=db_context,
        kind=SpanKind.CLIENT,
        tags={"db.type": "postgresql", "db.statement": "SELECT * FROM users"}
    )
    
    time.sleep(0.03)
    
    # Finish spans
    db_tracer.finish_span(db_span)
    api_tracer.finish_span(api_span)
    frontend_tracer.finish_span(root_span)
    
    # Query traces
    print(f"Total traces: {len(jaeger.traces)}")
    print(f"Services: {jaeger.get_services()}")
    
    # Get the trace
    trace = list(jaeger.traces.values())[0]
    print(f"\nTrace {trace.trace_id}:")
    print(f"  Services: {trace.services}")
    print(f"  Duration: {trace.duration * 1000:.2f}ms")
    print(f"  Spans: {len(trace.spans)}")
    
    for span in trace.spans:
        indent = "  " * (1 + (1 if span.parent_span_id else 0))
        print(f"{indent}- {span.service_name}: {span.operation_name} ({span.duration * 1000:.2f}ms)")
    
    # Get dependencies
    deps = jaeger.get_dependencies()
    print(f"\nDependencies:")
    for service, depends_on in deps.items():
        print(f"  {service} -> {', '.join(depends_on)}")
    
    # Statistics
    stats = jaeger.get_trace_statistics()
    print(f"\nStatistics:")
    print(f"  Traces: {stats['trace_count']}")
    print(f"  Spans: {stats['span_count']}")
    print(f"  Avg duration: {stats['avg_duration'] * 1000:.2f}ms")
