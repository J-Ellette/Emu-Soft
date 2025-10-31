"""
Tests for OpenCensus Emulator

This test suite validates the core functionality of the OpenCensus emulator.
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from opencensus_emulator import (
    Span, Tracer, SpanKind, StatusCode, Status, Annotation,
    AlwaysSampler, NeverSampler, ProbabilitySampler,
    InMemoryExporter, ConsoleExporter, Propagator, TraceContext,
    configure_tracer, get_tracer, start_span, end_span, span,
    get_current_span, execution_context
)


def test_span_creation():
    """Test span creation"""
    print("Testing span creation...")
    
    tracer = Tracer()
    span = tracer.start_span("test_span")
    
    assert span.name == "test_span"
    assert span.trace_id is not None
    assert span.span_id is not None
    assert span.parent_span_id is None
    assert span.is_recording() is True
    
    print("✓ Span creation works")


def test_span_attributes():
    """Test span attributes"""
    print("Testing span attributes...")
    
    tracer = Tracer()
    span = tracer.start_span("test_span")
    
    span.add_attribute("key1", "value1")
    span.add_attributes({"key2": "value2", "key3": 123})
    
    assert span.attributes["key1"] == "value1"
    assert span.attributes["key2"] == "value2"
    assert span.attributes["key3"] == 123
    
    print("✓ Span attributes work")


def test_span_annotations():
    """Test span annotations"""
    print("Testing span annotations...")
    
    tracer = Tracer()
    span = tracer.start_span("test_span")
    
    span.add_annotation("Event 1", key="value")
    span.add_annotation("Event 2")
    
    assert len(span.annotations) == 2
    assert span.annotations[0].description == "Event 1"
    assert span.annotations[0].attributes["key"] == "value"
    assert span.annotations[1].description == "Event 2"
    
    print("✓ Span annotations work")


def test_span_status():
    """Test span status"""
    print("Testing span status...")
    
    tracer = Tracer()
    span = tracer.start_span("test_span")
    
    span.set_status(StatusCode.OK)
    assert span.status.code == StatusCode.OK
    
    span.set_status(StatusCode.INTERNAL, "Error message")
    assert span.status.code == StatusCode.INTERNAL
    assert span.status.message == "Error message"
    
    print("✓ Span status works")


def test_span_finish():
    """Test span finishing"""
    print("Testing span finishing...")
    
    tracer = Tracer()
    span = tracer.start_span("test_span")
    
    assert span.is_recording() is True
    assert span.end_time is None
    
    time.sleep(0.01)
    span.finish()
    
    assert span.is_recording() is False
    assert span.end_time is not None
    assert span.get_duration() > 0
    
    print("✓ Span finishing works")


def test_span_context_manager():
    """Test span as context manager"""
    print("Testing span context manager...")
    
    tracer = Tracer()
    span = tracer.start_span("test_span")
    
    with span:
        assert span.is_recording() is True
        time.sleep(0.01)
    
    assert span.is_recording() is False
    assert span.get_duration() > 0
    
    print("✓ Span context manager works")


def test_span_context_manager_with_exception():
    """Test span context manager with exception"""
    print("Testing span context manager with exception...")
    
    tracer = Tracer()
    span = tracer.start_span("test_span")
    
    try:
        with span:
            raise ValueError("Test error")
    except ValueError:
        pass
    
    assert span.is_recording() is False
    assert span.status.code == StatusCode.INTERNAL
    assert "Test error" in span.status.message
    assert len(span.annotations) > 0
    
    print("✓ Span context manager with exception works")


def test_parent_child_spans():
    """Test parent-child span relationships"""
    print("Testing parent-child span relationships...")
    
    tracer = Tracer()
    parent = tracer.start_span("parent")
    child = tracer.start_span("child", parent_span=parent)
    
    assert child.parent_span_id == parent.span_id
    assert child.trace_id == parent.trace_id
    assert parent.child_span_count == 1
    
    print("✓ Parent-child span relationships work")


def test_nested_spans():
    """Test nested spans with context"""
    print("Testing nested spans with context...")
    
    tracer = Tracer()
    
    with tracer.span("root") as root:
        with tracer.span("child1") as child1:
            assert child1.parent_span_id == root.span_id
            assert child1.trace_id == root.trace_id
            
            with tracer.span("grandchild") as grandchild:
                assert grandchild.parent_span_id == child1.span_id
                assert grandchild.trace_id == root.trace_id
        
        with tracer.span("child2") as child2:
            assert child2.parent_span_id == root.span_id
            assert child2.trace_id == root.trace_id
    
    print("✓ Nested spans with context work")


def test_span_kinds():
    """Test different span kinds"""
    print("Testing span kinds...")
    
    tracer = Tracer()
    
    server_span = tracer.start_span("server", kind=SpanKind.SERVER)
    assert server_span.kind == SpanKind.SERVER
    
    client_span = tracer.start_span("client", kind=SpanKind.CLIENT)
    assert client_span.kind == SpanKind.CLIENT
    
    producer_span = tracer.start_span("producer", kind=SpanKind.PRODUCER)
    assert producer_span.kind == SpanKind.PRODUCER
    
    consumer_span = tracer.start_span("consumer", kind=SpanKind.CONSUMER)
    assert consumer_span.kind == SpanKind.CONSUMER
    
    print("✓ Span kinds work")


def test_always_sampler():
    """Test always sampler"""
    print("Testing always sampler...")
    
    sampler = AlwaysSampler()
    tracer = Tracer(sampler=sampler)
    
    span1 = tracer.start_span("test1")
    span2 = tracer.start_span("test2")
    
    assert sampler.should_sample(span1) is True
    assert sampler.should_sample(span2) is True
    
    print("✓ Always sampler works")


def test_never_sampler():
    """Test never sampler"""
    print("Testing never sampler...")
    
    sampler = NeverSampler()
    tracer = Tracer(sampler=sampler)
    
    span1 = tracer.start_span("test1")
    span2 = tracer.start_span("test2")
    
    assert sampler.should_sample(span1) is False
    assert sampler.should_sample(span2) is False
    
    print("✓ Never sampler works")


def test_probability_sampler():
    """Test probability sampler"""
    print("Testing probability sampler...")
    
    # Test 100% sampling
    sampler = ProbabilitySampler(1.0)
    tracer = Tracer(sampler=sampler)
    span = tracer.start_span("test")
    assert sampler.should_sample(span) is True
    
    # Test 0% sampling
    sampler = ProbabilitySampler(0.0)
    tracer = Tracer(sampler=sampler)
    span = tracer.start_span("test")
    assert sampler.should_sample(span) is False
    
    # Test invalid probability
    try:
        ProbabilitySampler(1.5)
        assert False, "Should not allow probability > 1.0"
    except ValueError:
        pass
    
    print("✓ Probability sampler works")


def test_in_memory_exporter():
    """Test in-memory exporter"""
    print("Testing in-memory exporter...")
    
    exporter = InMemoryExporter()
    tracer = Tracer(exporter=exporter)
    
    span1 = tracer.start_span("test1")
    span1.finish()
    tracer.end_span(span1)
    
    span2 = tracer.start_span("test2")
    span2.finish()
    tracer.end_span(span2)
    
    exported_spans = exporter.get_spans()
    assert len(exported_spans) == 2
    assert exported_spans[0].name == "test1"
    assert exported_spans[1].name == "test2"
    
    exporter.clear()
    assert len(exporter.get_spans()) == 0
    
    print("✓ In-memory exporter works")


def test_tracer_get_spans():
    """Test tracer span collection"""
    print("Testing tracer span collection...")
    
    tracer = Tracer()
    
    span1 = tracer.start_span("test1")
    span2 = tracer.start_span("test2")
    
    spans = tracer.get_spans()
    assert len(spans) == 2
    assert spans[0].name == "test1"
    assert spans[1].name == "test2"
    
    tracer.clear_spans()
    assert len(tracer.get_spans()) == 0
    
    print("✓ Tracer span collection works")


def test_trace_context():
    """Test trace context"""
    print("Testing trace context...")
    
    context = TraceContext("0123456789abcdef0123456789abcdef", "0123456789abcdef", 1)
    
    # Test to_header
    header = context.to_header()
    assert header == "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"
    
    # Test from_header
    parsed = TraceContext.from_header(header)
    assert parsed is not None
    assert parsed.trace_id == context.trace_id
    assert parsed.span_id == context.span_id
    assert parsed.trace_options == context.trace_options
    
    # Test invalid header
    invalid = TraceContext.from_header("invalid")
    assert invalid is None
    
    print("✓ Trace context works")


def test_propagator():
    """Test trace context propagation"""
    print("Testing trace context propagation...")
    
    tracer = Tracer()
    span = tracer.start_span("test_span")
    
    # Inject context
    headers = {}
    Propagator.inject(span, headers)
    
    assert 'traceparent' in headers
    assert span.trace_id in headers['traceparent']
    assert span.span_id in headers['traceparent']
    
    # Extract context
    extracted = Propagator.extract(headers)
    assert extracted is not None
    assert extracted.trace_id == span.trace_id
    assert extracted.span_id == span.span_id
    
    # Extract from empty headers
    empty_extracted = Propagator.extract({})
    assert empty_extracted is None
    
    print("✓ Trace context propagation works")


def test_global_tracer():
    """Test global tracer configuration"""
    print("Testing global tracer configuration...")
    
    exporter = InMemoryExporter()
    configure_tracer(exporter=exporter)
    
    tracer = get_tracer()
    assert tracer is not None
    assert tracer.exporter == exporter
    
    print("✓ Global tracer configuration works")


def test_global_span_functions():
    """Test global span functions"""
    print("Testing global span functions...")
    
    configure_tracer()
    
    with span("test_span") as s:
        s.add_attribute("key", "value")
        current = get_current_span()
        assert current == s
        assert current.name == "test_span"
        assert current.attributes["key"] == "value"
    
    print("✓ Global span functions work")


def test_execution_context():
    """Test execution context"""
    print("Testing execution context...")
    
    tracer = Tracer()
    span1 = tracer.start_span("span1")
    
    execution_context.set_current_span(span1)
    current = execution_context.get_current_span()
    assert current == span1
    
    execution_context.clear()
    current = execution_context.get_current_span()
    assert current is None
    
    print("✓ Execution context works")


def test_span_links():
    """Test span links"""
    print("Testing span links...")
    
    tracer = Tracer()
    span1 = tracer.start_span("span1")
    span2 = tracer.start_span("span2")
    
    span2.add_link(span1.trace_id, span1.span_id, "FOLLOWS_FROM", reason="test")
    
    assert len(span2.links) == 1
    assert span2.links[0].trace_id == span1.trace_id
    assert span2.links[0].span_id == span1.span_id
    assert span2.links[0].link_type == "FOLLOWS_FROM"
    assert span2.links[0].attributes["reason"] == "test"
    
    print("✓ Span links work")


def test_concurrent_spans():
    """Test concurrent span creation"""
    print("Testing concurrent span creation...")
    
    import threading
    
    exporter = InMemoryExporter()
    tracer = Tracer(exporter=exporter)
    
    def create_spans():
        for i in range(10):
            span = tracer.start_span(f"span_{i}")
            span.add_attribute("thread", threading.current_thread().name)
            span.finish()
            tracer.end_span(span)
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=create_spans)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Should have 30 spans (3 threads * 10 spans)
    exported = exporter.get_spans()
    assert len(exported) == 30
    
    print("✓ Concurrent span creation works")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running OpenCensus Emulator Tests")
    print("=" * 60)
    
    tests = [
        test_span_creation,
        test_span_attributes,
        test_span_annotations,
        test_span_status,
        test_span_finish,
        test_span_context_manager,
        test_span_context_manager_with_exception,
        test_parent_child_spans,
        test_nested_spans,
        test_span_kinds,
        test_always_sampler,
        test_never_sampler,
        test_probability_sampler,
        test_in_memory_exporter,
        test_tracer_get_spans,
        test_trace_context,
        test_propagator,
        test_global_tracer,
        test_global_span_functions,
        test_execution_context,
        test_span_links,
        test_concurrent_spans,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
