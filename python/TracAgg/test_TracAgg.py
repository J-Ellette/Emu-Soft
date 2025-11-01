"""
Developed by PowerShield, as a distributed tracing aggregator

Tests for TracAgg - Distributed Tracing Aggregator

This test suite validates the core functionality of TracAgg.
"""

import sys
import os
import time
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from TracAgg import (
    TracAggregator, Span, Trace, ServiceMetrics, SpanKind, StatusCode,
    create_span, create_aggregator
)


def test_span_creation():
    """Test span creation"""
    print("Testing span creation...")
    
    span = create_span(
        trace_id="trace-1",
        span_id="span-1",
        service_name="api",
        operation_name="handle_request",
        start_time=1000.0,
        duration=0.5
    )
    
    assert span.trace_id == "trace-1"
    assert span.span_id == "span-1"
    assert span.service_name == "api"
    assert span.operation_name == "handle_request"
    assert span.start_time == 1000.0
    assert span.duration == 0.5
    assert span.status == StatusCode.OK
    
    print("✓ Span creation works")


def test_span_with_error():
    """Test span with error status"""
    print("Testing span with error...")
    
    span = create_span(
        trace_id="trace-1",
        span_id="span-1",
        service_name="api",
        operation_name="process",
        start_time=1000.0,
        duration=0.1,
        status=StatusCode.ERROR,
        error_message="Database connection failed"
    )
    
    assert span.status == StatusCode.ERROR
    assert span.error_message == "Database connection failed"
    
    print("✓ Span with error works")


def test_span_to_dict():
    """Test span serialization"""
    print("Testing span to_dict...")
    
    span = create_span(
        trace_id="trace-1",
        span_id="span-1",
        service_name="api",
        operation_name="handle",
        start_time=1000.0,
        duration=0.5,
        attributes={"http.method": "GET", "http.status": 200}
    )
    
    span_dict = span.to_dict()
    assert span_dict['trace_id'] == "trace-1"
    assert span_dict['service_name'] == "api"
    assert span_dict['attributes']['http.method'] == "GET"
    
    print("✓ Span serialization works")


def test_trace_creation():
    """Test trace creation and span addition"""
    print("Testing trace creation...")
    
    trace = Trace(trace_id="trace-1")
    assert trace.trace_id == "trace-1"
    assert trace.span_count == 0
    assert trace.service_count == 0
    
    span1 = create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5)
    trace.add_span(span1)
    
    assert trace.span_count == 1
    assert trace.service_count == 1
    assert "api" in trace.services
    
    span2 = create_span("trace-1", "span-2", "db", "query", 1000.1, 0.2)
    trace.add_span(span2)
    
    assert trace.span_count == 2
    assert trace.service_count == 2
    assert "db" in trace.services
    
    print("✓ Trace creation works")


def test_trace_timing():
    """Test trace timing calculation"""
    print("Testing trace timing...")
    
    trace = Trace(trace_id="trace-1")
    
    span1 = create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5)
    span2 = create_span("trace-1", "span-2", "db", "query", 1000.2, 0.3)
    
    trace.add_span(span1)
    trace.add_span(span2)
    
    # Start time should be the earliest span start
    assert trace.start_time == 1000.0
    
    # Duration should cover all spans
    # span2 ends at 1000.2 + 0.3 = 1000.5
    # trace starts at 1000.0
    # so duration should be 0.5
    assert trace.duration == 0.5
    
    print("✓ Trace timing works")


def test_trace_root_span():
    """Test getting root span"""
    print("Testing root span retrieval...")
    
    trace = Trace(trace_id="trace-1")
    
    span1 = create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5)
    span2 = create_span("trace-1", "span-2", "db", "query", 1000.1, 0.2, parent_span_id="span-1")
    
    trace.add_span(span1)
    trace.add_span(span2)
    
    root = trace.get_root_span()
    assert root is not None
    assert root.span_id == "span-1"
    assert root.parent_span_id is None
    
    print("✓ Root span retrieval works")


def test_trace_critical_path():
    """Test critical path calculation"""
    print("Testing critical path calculation...")
    
    trace = Trace(trace_id="trace-1")
    
    # Create a tree of spans
    span1 = create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.1)
    span2 = create_span("trace-1", "span-2", "user", "get", 1000.1, 0.3, parent_span_id="span-1")
    span3 = create_span("trace-1", "span-3", "cache", "get", 1000.15, 0.05, parent_span_id="span-1")
    span4 = create_span("trace-1", "span-4", "db", "query", 1000.2, 0.2, parent_span_id="span-2")
    
    trace.add_span(span1)
    trace.add_span(span2)
    trace.add_span(span3)
    trace.add_span(span4)
    
    critical_path = trace.get_critical_path()
    
    # Critical path should be: span1 -> span2 -> span4
    assert len(critical_path) == 3
    assert critical_path[0].span_id == "span-1"
    assert critical_path[1].span_id == "span-2"
    assert critical_path[2].span_id == "span-4"
    
    print("✓ Critical path calculation works")


def test_aggregator_creation():
    """Test aggregator creation"""
    print("Testing aggregator creation...")
    
    aggregator = create_aggregator()
    assert aggregator is not None
    assert len(aggregator.get_all_traces()) == 0
    
    print("✓ Aggregator creation works")


def test_aggregator_ingest_span():
    """Test ingesting spans"""
    print("Testing span ingestion...")
    
    aggregator = TracAggregator()
    
    span = create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5)
    aggregator.ingest_span(span)
    
    trace = aggregator.get_trace("trace-1")
    assert trace is not None
    assert trace.span_count == 1
    
    print("✓ Span ingestion works")


def test_aggregator_ingest_multiple_spans():
    """Test ingesting multiple spans"""
    print("Testing multiple span ingestion...")
    
    aggregator = TracAggregator()
    
    spans = [
        create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5),
        create_span("trace-1", "span-2", "db", "query", 1000.1, 0.2),
        create_span("trace-2", "span-3", "api", "handle", 2000.0, 0.3),
    ]
    
    aggregator.ingest_spans(spans)
    
    assert len(aggregator.get_all_traces()) == 2
    
    trace1 = aggregator.get_trace("trace-1")
    assert trace1.span_count == 2
    
    trace2 = aggregator.get_trace("trace-2")
    assert trace2.span_count == 1
    
    print("✓ Multiple span ingestion works")


def test_service_metrics():
    """Test service metrics calculation"""
    print("Testing service metrics...")
    
    aggregator = TracAggregator()
    
    # Add spans for a service
    for i in range(10):
        span = create_span(
            f"trace-{i}",
            f"span-{i}",
            "api",
            "handle",
            float(i * 100),
            0.1 + i * 0.01,
            status=StatusCode.ERROR if i % 5 == 0 else StatusCode.OK
        )
        aggregator.ingest_span(span)
    
    metrics = aggregator.get_service_metrics("api")
    assert metrics is not None
    assert metrics.request_count == 10
    assert metrics.error_count == 2  # i=0 and i=5
    assert metrics.get_error_rate() == 0.2  # 2/10
    
    avg_duration = metrics.get_avg_duration()
    assert avg_duration > 0
    
    print("✓ Service metrics work")


def test_service_metrics_percentiles():
    """Test service metrics percentile calculation"""
    print("Testing service metrics percentiles...")
    
    metrics = ServiceMetrics(service_name="test")
    
    # Add durations
    for i in range(100):
        metrics.add_request(duration=float(i) / 100.0)
    
    p50 = metrics.get_percentile(50)
    p95 = metrics.get_percentile(95)
    p99 = metrics.get_percentile(99)
    
    assert p50 < p95 < p99
    assert p50 >= 0.0
    
    print("✓ Service metrics percentiles work")


def test_service_dependencies():
    """Test service dependency tracking"""
    print("Testing service dependencies...")
    
    aggregator = TracAggregator()
    
    # Create a trace with service dependencies
    spans = [
        create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5),
        create_span("trace-1", "span-2", "user", "get", 1000.1, 0.2, parent_span_id="span-1"),
        create_span("trace-1", "span-3", "order", "list", 1000.15, 0.15, parent_span_id="span-1"),
        create_span("trace-1", "span-4", "db", "query", 1000.2, 0.1, parent_span_id="span-2"),
    ]
    
    aggregator.ingest_spans(spans)
    
    dependencies = aggregator.get_service_dependencies()
    
    # api should call user and order
    assert "user" in dependencies["api"]
    assert "order" in dependencies["api"]
    
    # user should call db
    assert "db" in dependencies["user"]
    
    print("✓ Service dependencies work")


def test_search_traces_by_service():
    """Test searching traces by service"""
    print("Testing trace search by service...")
    
    aggregator = TracAggregator()
    
    spans = [
        create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5),
        create_span("trace-2", "span-2", "user", "get", 2000.0, 0.3),
        create_span("trace-3", "span-3", "api", "process", 3000.0, 0.2),
    ]
    
    aggregator.ingest_spans(spans)
    
    api_traces = aggregator.search_traces(service_name="api")
    assert len(api_traces) == 2
    
    user_traces = aggregator.search_traces(service_name="user")
    assert len(user_traces) == 1
    
    print("✓ Trace search by service works")


def test_search_traces_by_duration():
    """Test searching traces by duration"""
    print("Testing trace search by duration...")
    
    aggregator = TracAggregator()
    
    spans = [
        create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.1),
        create_span("trace-2", "span-2", "api", "handle", 2000.0, 0.5),
        create_span("trace-3", "span-3", "api", "handle", 3000.0, 1.0),
    ]
    
    aggregator.ingest_spans(spans)
    
    slow_traces = aggregator.search_traces(min_duration=0.4)
    assert len(slow_traces) == 2
    
    fast_traces = aggregator.search_traces(max_duration=0.2)
    assert len(fast_traces) == 1
    
    print("✓ Trace search by duration works")


def test_search_traces_by_errors():
    """Test searching traces by error status"""
    print("Testing trace search by errors...")
    
    aggregator = TracAggregator()
    
    spans = [
        create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5, status=StatusCode.OK),
        create_span("trace-2", "span-2", "api", "handle", 2000.0, 0.3, status=StatusCode.ERROR),
        create_span("trace-3", "span-3", "api", "handle", 3000.0, 0.2, status=StatusCode.OK),
    ]
    
    aggregator.ingest_spans(spans)
    
    error_traces = aggregator.search_traces(has_errors=True)
    assert len(error_traces) == 1
    
    success_traces = aggregator.search_traces(has_errors=False)
    assert len(success_traces) == 2
    
    print("✓ Trace search by errors works")


def test_slowest_operations():
    """Test finding slowest operations"""
    print("Testing slowest operations...")
    
    aggregator = TracAggregator()
    
    # Add various operations with different durations
    spans = [
        create_span("trace-1", "span-1", "api", "slow_op", 1000.0, 1.0),
        create_span("trace-2", "span-2", "api", "slow_op", 2000.0, 0.9),
        create_span("trace-3", "span-3", "api", "fast_op", 3000.0, 0.1),
        create_span("trace-4", "span-4", "user", "medium_op", 4000.0, 0.5),
    ]
    
    aggregator.ingest_spans(spans)
    
    slowest = aggregator.get_slowest_operations(limit=2)
    assert len(slowest) == 2
    
    # First should be slow_op
    assert slowest[0][1] == "slow_op"
    assert slowest[0][2] > slowest[1][2]  # First is slower than second
    
    print("✓ Slowest operations work")


def test_error_prone_operations():
    """Test finding error-prone operations"""
    print("Testing error-prone operations...")
    
    aggregator = TracAggregator()
    
    # Add operations with different error rates
    for i in range(10):
        aggregator.ingest_span(create_span(
            f"trace-{i}",
            f"span-{i}",
            "api",
            "risky_op",
            float(i * 100),
            0.1,
            status=StatusCode.ERROR if i % 2 == 0 else StatusCode.OK
        ))
    
    for i in range(10, 20):
        aggregator.ingest_span(create_span(
            f"trace-{i}",
            f"span-{i}",
            "api",
            "safe_op",
            float(i * 100),
            0.1,
            status=StatusCode.OK
        ))
    
    error_prone = aggregator.get_error_prone_operations(limit=2)
    
    # risky_op should be first with 50% error rate
    assert error_prone[0][1] == "risky_op"
    assert error_prone[0][2] == 0.5  # 50% error rate
    
    print("✓ Error-prone operations work")


def test_analyze_trace():
    """Test trace analysis"""
    print("Testing trace analysis...")
    
    aggregator = TracAggregator()
    
    spans = [
        create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5),
        create_span("trace-1", "span-2", "user", "get", 1000.1, 0.2, parent_span_id="span-1"),
        create_span("trace-1", "span-3", "db", "query", 1000.15, 0.15, parent_span_id="span-2"),
    ]
    
    aggregator.ingest_spans(spans)
    
    analysis = aggregator.analyze_trace("trace-1")
    
    assert analysis is not None
    assert analysis['trace_id'] == "trace-1"
    assert analysis['span_count'] == 3
    assert analysis['service_count'] == 3
    assert len(analysis['services']) == 3
    assert 'critical_path' in analysis
    assert 'service_breakdown' in analysis
    
    # Check service breakdown
    assert 'api' in analysis['service_breakdown']
    assert 'user' in analysis['service_breakdown']
    assert 'db' in analysis['service_breakdown']
    
    print("✓ Trace analysis works")


def test_summary_statistics():
    """Test summary statistics"""
    print("Testing summary statistics...")
    
    aggregator = TracAggregator()
    
    # Add multiple traces
    for i in range(50):
        span = create_span(
            f"trace-{i}",
            f"span-{i}",
            f"service-{i % 3}",
            "operation",
            float(i * 100),
            0.1 + i * 0.01
        )
        aggregator.ingest_span(span)
    
    stats = aggregator.get_summary_statistics()
    
    assert stats['total_traces'] == 50
    assert stats['total_spans'] == 50
    assert stats['service_count'] == 3
    assert stats['avg_trace_duration'] > 0
    assert 'p50_trace_duration' in stats
    assert 'p95_trace_duration' in stats
    assert 'p99_trace_duration' in stats
    
    print("✓ Summary statistics work")


def test_export_import_json():
    """Test export and import to JSON"""
    print("Testing JSON export/import...")
    
    aggregator = TracAggregator()
    
    spans = [
        create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5),
        create_span("trace-1", "span-2", "db", "query", 1000.1, 0.2),
    ]
    
    aggregator.ingest_spans(spans)
    
    # Export to file
    filename = "/tmp/test_traces.json"
    aggregator.export_to_json(filename)
    
    # Verify file exists and is valid JSON
    assert os.path.exists(filename)
    
    with open(filename, 'r') as f:
        data = json.load(f)
        assert 'traces' in data
        assert len(data['traces']) == 1
    
    # Import into new aggregator
    new_aggregator = TracAggregator()
    new_aggregator.import_from_json(filename)
    
    assert len(new_aggregator.get_all_traces()) == 1
    trace = new_aggregator.get_trace("trace-1")
    assert trace.span_count == 2
    
    # Cleanup
    os.remove(filename)
    
    print("✓ JSON export/import works")


def test_clear():
    """Test clearing aggregator"""
    print("Testing clear...")
    
    aggregator = TracAggregator()
    
    span = create_span("trace-1", "span-1", "api", "handle", 1000.0, 0.5)
    aggregator.ingest_span(span)
    
    assert len(aggregator.get_all_traces()) == 1
    
    aggregator.clear()
    
    assert len(aggregator.get_all_traces()) == 0
    assert len(aggregator.get_all_service_metrics()) == 0
    
    print("✓ Clear works")


def test_thread_safety():
    """Test thread safety of aggregator"""
    print("Testing thread safety...")
    
    import threading
    
    aggregator = TracAggregator()
    
    def ingest_spans_thread(thread_id):
        for i in range(10):
            span = create_span(
                f"trace-{thread_id}-{i}",
                f"span-{thread_id}-{i}",
                f"service-{thread_id}",
                "operation",
                float(i * 100),
                0.1
            )
            aggregator.ingest_span(span)
    
    # Create multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=ingest_spans_thread, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Should have 50 traces (5 threads * 10 spans each)
    assert len(aggregator.get_all_traces()) == 50
    
    # Should have 5 services
    assert len(aggregator.get_all_service_metrics()) == 5
    
    print("✓ Thread safety works")


def run_all_tests():
    """Run all test functions"""
    print("=" * 60)
    print("Running TracAgg Tests")
    print("=" * 60)
    print()
    
    test_functions = [
        test_span_creation,
        test_span_with_error,
        test_span_to_dict,
        test_trace_creation,
        test_trace_timing,
        test_trace_root_span,
        test_trace_critical_path,
        test_aggregator_creation,
        test_aggregator_ingest_span,
        test_aggregator_ingest_multiple_spans,
        test_service_metrics,
        test_service_metrics_percentiles,
        test_service_dependencies,
        test_search_traces_by_service,
        test_search_traces_by_duration,
        test_search_traces_by_errors,
        test_slowest_operations,
        test_error_prone_operations,
        test_analyze_trace,
        test_summary_statistics,
        test_export_import_json,
        test_clear,
        test_thread_safety,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
