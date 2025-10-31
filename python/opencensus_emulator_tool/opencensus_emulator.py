"""
OpenCensus Emulator - Distributed tracing without external dependencies

This module emulates core OpenCensus functionality for distributed tracing.
It provides a clean API for creating traces, spans, and context propagation.

Features:
- Trace and span creation
- Parent-child span relationships
- Span attributes (tags/labels)
- Span annotations (events)
- Span status tracking
- Context propagation
- Trace exporters (in-memory, console)
- Sampling strategies
- Thread-local context management
- Time-series span tracking

Note: This is a simplified implementation focusing on core functionality.
Advanced features like real-time export to tracing backends are not included.
"""

import time
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum


class SpanKind(Enum):
    """Span kinds"""
    UNSPECIFIED = 0
    SERVER = 1
    CLIENT = 2
    PRODUCER = 3
    CONSUMER = 4


class StatusCode(Enum):
    """Status codes for spans"""
    OK = 0
    CANCELLED = 1
    UNKNOWN = 2
    INVALID_ARGUMENT = 3
    DEADLINE_EXCEEDED = 4
    NOT_FOUND = 5
    ALREADY_EXISTS = 6
    PERMISSION_DENIED = 7
    RESOURCE_EXHAUSTED = 8
    FAILED_PRECONDITION = 9
    ABORTED = 10
    OUT_OF_RANGE = 11
    UNIMPLEMENTED = 12
    INTERNAL = 13
    UNAVAILABLE = 14
    DATA_LOSS = 15
    UNAUTHENTICATED = 16


@dataclass
class Annotation:
    """Annotation (event) in a span"""
    description: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Link:
    """Link to another span"""
    trace_id: str
    span_id: str
    link_type: str = "UNSPECIFIED"
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Status:
    """Status of a span"""
    code: StatusCode = StatusCode.OK
    message: str = ""


class Span:
    """Represents a span in a trace"""
    
    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str] = None,
        kind: SpanKind = SpanKind.UNSPECIFIED,
        start_time: Optional[float] = None,
    ):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.kind = kind
        self.start_time = start_time or time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.annotations: List[Annotation] = []
        self.links: List[Link] = []
        self.status = Status()
        self.child_span_count = 0
        self._lock = threading.Lock()
    
    def add_attribute(self, key: str, value: Any):
        """Add an attribute to the span"""
        with self._lock:
            self.attributes[key] = value
    
    def add_attributes(self, attributes: Dict[str, Any]):
        """Add multiple attributes to the span"""
        with self._lock:
            self.attributes.update(attributes)
    
    def add_annotation(self, description: str, **attributes):
        """Add an annotation (event) to the span"""
        with self._lock:
            annotation = Annotation(
                description=description,
                attributes=attributes
            )
            self.annotations.append(annotation)
    
    def add_link(self, trace_id: str, span_id: str, link_type: str = "UNSPECIFIED", **attributes):
        """Add a link to another span"""
        with self._lock:
            link = Link(
                trace_id=trace_id,
                span_id=span_id,
                link_type=link_type,
                attributes=attributes
            )
            self.links.append(link)
    
    def set_status(self, code: StatusCode, message: str = ""):
        """Set the status of the span"""
        with self._lock:
            self.status = Status(code=code, message=message)
    
    def finish(self, end_time: Optional[float] = None):
        """Finish the span"""
        with self._lock:
            if self.end_time is None:
                self.end_time = end_time or time.time()
    
    def is_recording(self) -> bool:
        """Check if the span is still recording"""
        return self.end_time is None
    
    def get_duration(self) -> Optional[float]:
        """Get the duration of the span in seconds"""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None:
            # Record error
            self.set_status(StatusCode.INTERNAL, str(exc_val))
            self.add_annotation("exception", type=exc_type.__name__, message=str(exc_val))
        self.finish()
        return False


class Tracer:
    """Tracer for creating and managing spans"""
    
    def __init__(self, exporter: Optional['Exporter'] = None, sampler: Optional['Sampler'] = None):
        self.exporter = exporter
        self.sampler = sampler or AlwaysSampler()
        self._spans: List[Span] = []
        self._lock = threading.Lock()
    
    def start_span(
        self,
        name: str,
        parent_span: Optional[Span] = None,
        kind: SpanKind = SpanKind.UNSPECIFIED,
    ) -> Span:
        """Start a new span"""
        # Get trace context
        if parent_span:
            trace_id = parent_span.trace_id
            parent_span_id = parent_span.span_id
            parent_span.child_span_count += 1
        else:
            # Check for current span in context
            current_span = execution_context.get_current_span()
            if current_span:
                trace_id = current_span.trace_id
                parent_span_id = current_span.span_id
                current_span.child_span_count += 1
            else:
                trace_id = self._generate_trace_id()
                parent_span_id = None
        
        # Generate span ID
        span_id = self._generate_span_id()
        
        # Create span
        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            kind=kind,
        )
        
        # Apply sampling
        if not self.sampler.should_sample(span):
            # Return a no-op span
            return span
        
        # Store span
        with self._lock:
            self._spans.append(span)
        
        return span
    
    def end_span(self, span: Span):
        """End a span"""
        span.finish()
        
        # Export if we have an exporter
        if self.exporter:
            self.exporter.export([span])
    
    def get_spans(self) -> List[Span]:
        """Get all spans"""
        with self._lock:
            return self._spans.copy()
    
    def clear_spans(self):
        """Clear all spans"""
        with self._lock:
            self._spans.clear()
    
    @staticmethod
    def _generate_trace_id() -> str:
        """Generate a trace ID"""
        return uuid.uuid4().hex
    
    @staticmethod
    def _generate_span_id() -> str:
        """Generate a span ID"""
        return uuid.uuid4().hex[:16]
    
    @contextmanager
    def span(self, name: str, **kwargs):
        """Context manager for creating a span"""
        # Save the previous span
        previous_span = execution_context.get_current_span()
        
        span = self.start_span(name, **kwargs)
        execution_context.set_current_span(span)
        try:
            yield span
        finally:
            self.end_span(span)
            # Restore the previous span
            execution_context.set_current_span(previous_span)


class Sampler:
    """Base class for samplers"""
    
    def should_sample(self, span: Span) -> bool:
        """Determine if a span should be sampled"""
        raise NotImplementedError


class AlwaysSampler(Sampler):
    """Sampler that always samples"""
    
    def should_sample(self, span: Span) -> bool:
        return True


class NeverSampler(Sampler):
    """Sampler that never samples"""
    
    def should_sample(self, span: Span) -> bool:
        return False


class ProbabilitySampler(Sampler):
    """Sampler that samples with a given probability"""
    
    def __init__(self, probability: float):
        if not 0.0 <= probability <= 1.0:
            raise ValueError("Probability must be between 0.0 and 1.0")
        self.probability = probability
    
    def should_sample(self, span: Span) -> bool:
        import random
        return random.random() < self.probability


class Exporter:
    """Base class for exporters"""
    
    def export(self, spans: List[Span]):
        """Export spans"""
        raise NotImplementedError


class InMemoryExporter(Exporter):
    """Exporter that stores spans in memory"""
    
    def __init__(self):
        self.spans: List[Span] = []
        self._lock = threading.Lock()
    
    def export(self, spans: List[Span]):
        """Export spans to memory"""
        with self._lock:
            self.spans.extend(spans)
    
    def get_spans(self) -> List[Span]:
        """Get all exported spans"""
        with self._lock:
            return self.spans.copy()
    
    def clear(self):
        """Clear all spans"""
        with self._lock:
            self.spans.clear()


class ConsoleExporter(Exporter):
    """Exporter that prints spans to console"""
    
    def export(self, spans: List[Span]):
        """Export spans to console"""
        for span in spans:
            print(f"\n--- Span: {span.name} ---")
            print(f"Trace ID: {span.trace_id}")
            print(f"Span ID: {span.span_id}")
            if span.parent_span_id:
                print(f"Parent Span ID: {span.parent_span_id}")
            print(f"Kind: {span.kind.name}")
            print(f"Start: {span.start_time}")
            print(f"End: {span.end_time}")
            print(f"Duration: {span.get_duration():.6f}s" if span.get_duration() else "In progress")
            print(f"Status: {span.status.code.name}")
            if span.status.message:
                print(f"Status Message: {span.status.message}")
            if span.attributes:
                print(f"Attributes: {span.attributes}")
            if span.annotations:
                print(f"Annotations: {len(span.annotations)}")
                for ann in span.annotations:
                    print(f"  - {ann.description}: {ann.attributes}")
            if span.links:
                print(f"Links: {len(span.links)}")


class ExecutionContext:
    """Thread-local execution context for storing current span"""
    
    def __init__(self):
        self._local = threading.local()
    
    def set_current_span(self, span: Optional[Span]):
        """Set the current span"""
        self._local.span = span
    
    def get_current_span(self) -> Optional[Span]:
        """Get the current span"""
        return getattr(self._local, 'span', None)
    
    def clear(self):
        """Clear the current span"""
        self._local.span = None


# Global execution context
execution_context = ExecutionContext()


class TraceContext:
    """Trace context for propagation"""
    
    def __init__(self, trace_id: str, span_id: str, trace_options: int = 1):
        self.trace_id = trace_id
        self.span_id = span_id
        self.trace_options = trace_options
    
    def to_header(self) -> str:
        """Convert to W3C Trace Context header format"""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_options:02x}"
    
    @classmethod
    def from_header(cls, header: str) -> Optional['TraceContext']:
        """Parse W3C Trace Context header"""
        try:
            parts = header.split('-')
            if len(parts) != 4 or parts[0] != '00':
                return None
            
            trace_id = parts[1]
            span_id = parts[2]
            trace_options = int(parts[3], 16)
            
            return cls(trace_id, span_id, trace_options)
        except (ValueError, IndexError):
            return None


class Propagator:
    """Propagator for trace context"""
    
    TRACEPARENT_HEADER = 'traceparent'
    TRACESTATE_HEADER = 'tracestate'
    
    @staticmethod
    def inject(span: Span, carrier: Dict[str, str]):
        """Inject trace context into carrier (e.g., HTTP headers)"""
        context = TraceContext(span.trace_id, span.span_id)
        carrier[Propagator.TRACEPARENT_HEADER] = context.to_header()
    
    @staticmethod
    def extract(carrier: Dict[str, str]) -> Optional[TraceContext]:
        """Extract trace context from carrier"""
        header = carrier.get(Propagator.TRACEPARENT_HEADER)
        if header:
            return TraceContext.from_header(header)
        return None


# Global tracer instance
_tracer: Optional[Tracer] = None


def configure_tracer(exporter: Optional[Exporter] = None, sampler: Optional[Sampler] = None):
    """Configure the global tracer"""
    global _tracer
    _tracer = Tracer(exporter=exporter, sampler=sampler)


def get_tracer() -> Tracer:
    """Get the global tracer"""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def start_span(name: str, **kwargs) -> Span:
    """Start a new span using the global tracer"""
    return get_tracer().start_span(name, **kwargs)


def end_span(span: Span):
    """End a span using the global tracer"""
    get_tracer().end_span(span)


@contextmanager
def span(name: str, **kwargs):
    """Context manager for creating a span"""
    tracer = get_tracer()
    with tracer.span(name, **kwargs) as s:
        yield s


def get_current_span() -> Optional[Span]:
    """Get the current span from context"""
    return execution_context.get_current_span()


if __name__ == "__main__":
    # Example usage
    
    # Configure tracer with console exporter
    configure_tracer(exporter=ConsoleExporter())
    
    # Create a root span
    with span("root_operation") as root:
        root.add_attribute("user_id", "12345")
        root.add_attribute("method", "POST")
        
        # Add an annotation
        root.add_annotation("Processing started", step=1)
        
        time.sleep(0.01)
        
        # Create a child span
        with span("database_query") as db_span:
            db_span.add_attribute("query", "SELECT * FROM users")
            db_span.add_attribute("database", "postgres")
            time.sleep(0.02)
            
        # Create another child span
        with span("api_call", kind=SpanKind.CLIENT) as api_span:
            api_span.add_attribute("url", "https://api.example.com/data")
            api_span.add_attribute("method", "GET")
            time.sleep(0.015)
            
            # Add an annotation
            api_span.add_annotation("Response received", status_code=200)
        
        root.add_annotation("Processing completed", step=2)
    
    # Get all spans
    tracer = get_tracer()
    print(f"\n\nTotal spans created: {len(tracer.get_spans())}")
    
    # Example with context propagation
    print("\n\n=== Context Propagation Example ===")
    
    with span("service_a") as span_a:
        span_a.add_attribute("service", "service-a")
        
        # Inject context into headers
        headers = {}
        Propagator.inject(span_a, headers)
        print(f"Propagated headers: {headers}")
        
        # Simulate sending request to another service
        # In service B:
        context = Propagator.extract(headers)
        if context:
            print(f"Extracted trace_id: {context.trace_id}")
            print(f"Extracted span_id: {context.span_id}")
