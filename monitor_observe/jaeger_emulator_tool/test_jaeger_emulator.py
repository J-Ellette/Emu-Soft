#!/usr/bin/env python3
"""
Test suite for Jaeger Emulator
"""

import unittest
import time
from jaeger_emulator import (
    JaegerEmulator, SpanKind, Span, SpanContext
)


class TestJaegerEmulator(unittest.TestCase):
    """Test cases for Jaeger emulator"""
    
    def setUp(self):
        """Set up test instance"""
        self.jaeger = JaegerEmulator()
    
    def test_tracer_creation(self):
        """Test creating a tracer"""
        tracer = self.jaeger.get_tracer("test-service")
        self.assertIsNotNone(tracer)
        self.assertEqual(tracer.service_name, "test-service")
    
    def test_span_creation(self):
        """Test creating a span"""
        tracer = self.jaeger.get_tracer("test-service")
        span = tracer.start_span("test-operation")
        
        self.assertEqual(span.operation_name, "test-operation")
        self.assertEqual(span.service_name, "test-service")
        self.assertIsNotNone(span.trace_id)
        self.assertIsNotNone(span.span_id)
    
    def test_span_finish(self):
        """Test finishing a span"""
        tracer = self.jaeger.get_tracer("test-service")
        span = tracer.start_span("test-operation")
        time.sleep(0.01)
        tracer.finish_span(span)
        
        self.assertIsNotNone(span.end_time)
        self.assertIsNotNone(span.duration)
        self.assertGreater(span.duration, 0)
    
    def test_child_span(self):
        """Test creating child spans"""
        tracer = self.jaeger.get_tracer("test-service")
        
        parent_span = tracer.start_span("parent")
        context = SpanContext(parent_span.trace_id, parent_span.span_id)
        child_span = tracer.start_span("child", parent=context)
        
        self.assertEqual(child_span.trace_id, parent_span.trace_id)
        self.assertEqual(child_span.parent_span_id, parent_span.span_id)
        
        tracer.finish_span(child_span)
        tracer.finish_span(parent_span)
    
    def test_span_tags(self):
        """Test span tags"""
        tracer = self.jaeger.get_tracer("test-service")
        span = tracer.start_span(
            "test-operation",
            tags={"http.method": "GET", "http.status": 200}
        )
        
        self.assertEqual(span.tags["http.method"], "GET")
        self.assertEqual(span.tags["http.status"], 200)
        tracer.finish_span(span)
    
    def test_trace_storage(self):
        """Test trace storage"""
        tracer = self.jaeger.get_tracer("test-service")
        span = tracer.start_span("test-operation")
        trace_id = span.trace_id
        tracer.finish_span(span)
        
        trace = self.jaeger.get_trace(trace_id)
        self.assertIsNotNone(trace)
        self.assertEqual(trace.trace_id, trace_id)
        self.assertEqual(len(trace.spans), 1)
    
    def test_find_traces(self):
        """Test finding traces"""
        tracer = self.jaeger.get_tracer("test-service")
        
        for i in range(5):
            span = tracer.start_span(f"operation-{i}")
            tracer.finish_span(span)
        
        traces = self.jaeger.find_traces(service="test-service", limit=10)
        self.assertGreaterEqual(len(traces), 5)
    
    def test_get_services(self):
        """Test getting services"""
        tracer1 = self.jaeger.get_tracer("service-1")
        tracer2 = self.jaeger.get_tracer("service-2")
        
        span1 = tracer1.start_span("op1")
        span2 = tracer2.start_span("op2")
        
        tracer1.finish_span(span1)
        tracer2.finish_span(span2)
        
        services = self.jaeger.get_services()
        self.assertIn("service-1", services)
        self.assertIn("service-2", services)
    
    def test_context_propagation(self):
        """Test context propagation via headers"""
        tracer = self.jaeger.get_tracer("test-service")
        span = tracer.start_span("test-operation")
        
        headers = {}
        tracer.inject(span, headers)
        
        self.assertIn("uber-trace-id", headers)
        
        extracted = tracer.extract(headers)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.trace_id, span.trace_id)
        
        tracer.finish_span(span)
    
    def test_dependencies(self):
        """Test service dependency detection"""
        frontend = self.jaeger.get_tracer("frontend")
        api = self.jaeger.get_tracer("api")
        
        root = frontend.start_span("request", kind=SpanKind.SERVER)
        headers = {}
        frontend.inject(root, headers)
        
        parent_context = api.extract(headers)
        child = api.start_span("api-call", parent=parent_context)
        
        api.finish_span(child)
        frontend.finish_span(root)
        
        deps = self.jaeger.get_dependencies()
        self.assertIn("frontend", deps)
        self.assertIn("api", deps["frontend"])
    
    def test_statistics(self):
        """Test trace statistics"""
        tracer = self.jaeger.get_tracer("test-service")
        
        for _ in range(10):
            span = tracer.start_span("test-op")
            time.sleep(0.001)
            tracer.finish_span(span)
        
        stats = self.jaeger.get_trace_statistics()
        self.assertEqual(stats["trace_count"], 10)
        self.assertGreater(stats["avg_duration"], 0)


if __name__ == "__main__":
    unittest.main()
