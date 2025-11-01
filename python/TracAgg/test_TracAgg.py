"""
Developed by PowerShield
"""

#!/usr/bin/env python3
"""
Test suite for TracAgg - Distributed Tracing Aggregator

Tests core functionality including:
- Span ingestion
- Trace reconstruction
- Service dependency mapping
- Performance analysis
- Query capabilities
"""

import unittest
import time
from TracAgg import TracAgg, create_span_data, SpanKind, TraceStatus


class TestTracAggBasic(unittest.TestCase):
    """Test basic trace aggregation"""
    
    def setUp(self):
        """Set up test aggregator"""
        self.agg = TracAgg()
    
    def test_ingest_single_span(self):
        """Test ingesting a single span"""
        span_data = create_span_data(
            trace_id='trace1',
            span_id='span1',
            service_name='api-gateway',
            operation_name='GET /users',
            duration_ms=100.0
        )
        
        trace_id = self.agg.ingest_span(span_data)
        self.assertEqual(trace_id, 'trace1')
        
        trace = self.agg.get_trace('trace1')
        self.assertIsNotNone(trace)
        self.assertEqual(len(trace.spans), 1)
        self.assertEqual(trace.trace_id, 'trace1')
    
    def test_ingest_multiple_spans_same_trace(self):
        """Test ingesting multiple spans in the same trace"""
        # Root span
        span1 = create_span_data(
            trace_id='trace1',
            span_id='span1',
            service_name='api-gateway',
            operation_name='GET /users',
            duration_ms=200.0
        )
        
        # Child span
        span2 = create_span_data(
            trace_id='trace1',
            span_id='span2',
            parent_span_id='span1',
            service_name='user-service',
            operation_name='query_users',
            duration_ms=150.0
        )
        
        self.agg.ingest_span(span1)
        self.agg.ingest_span(span2)
        
        trace = self.agg.get_trace('trace1')
        self.assertEqual(len(trace.spans), 2)
        self.assertEqual(len(trace.services), 2)
        self.assertIn('api-gateway', trace.services)
        self.assertIn('user-service', trace.services)
    
    def test_trace_count(self):
        """Test getting trace count"""
        self.assertEqual(self.agg.get_trace_count(), 0)
        
        span1 = create_span_data('trace1', 'span1', 'service1', 'op1')
        span2 = create_span_data('trace2', 'span2', 'service1', 'op2')
        
        self.agg.ingest_span(span1)
        self.assertEqual(self.agg.get_trace_count(), 1)
        
        self.agg.ingest_span(span2)
        self.assertEqual(self.agg.get_trace_count(), 2)


class TestTraceReconstruction(unittest.TestCase):
    """Test trace reconstruction"""
    
    def setUp(self):
        """Set up test aggregator"""
        self.agg = TracAgg()
    
    def test_trace_timing(self):
        """Test trace timing calculation"""
        # Create spans at different times
        span1 = create_span_data(
            trace_id='trace1',
            span_id='span1',
            service_name='service1',
            operation_name='op1',
            duration_ms=100.0
        )
        
        time.sleep(0.01)
        
        span2 = create_span_data(
            trace_id='trace1',
            span_id='span2',
            parent_span_id='span1',
            service_name='service2',
            operation_name='op2',
            duration_ms=50.0
        )
        
        self.agg.ingest_span(span1)
        self.agg.ingest_span(span2)
        
        trace = self.agg.get_trace('trace1')
        self.assertIsNotNone(trace.start_time)
        self.assertIsNotNone(trace.end_time)
        self.assertIsNotNone(trace.duration_ms)
        self.assertGreater(trace.duration_ms, 0)
    
    def test_trace_status_complete(self):
        """Test trace status when all spans complete"""
        span = create_span_data(
            trace_id='trace1',
            span_id='span1',
            service_name='service1',
            operation_name='op1',
            duration_ms=100.0,
            status_code=200
        )
        
        self.agg.ingest_span(span)
        trace = self.agg.get_trace('trace1')
        
        self.assertTrue(trace.is_complete())
        self.assertEqual(trace.status, TraceStatus.COMPLETE)
    
    def test_trace_status_error(self):
        """Test trace status when spans have errors"""
        span = create_span_data(
            trace_id='trace1',
            span_id='span1',
            service_name='service1',
            operation_name='op1',
            duration_ms=100.0,
            status_code=500
        )
        
        self.agg.ingest_span(span)
        trace = self.agg.get_trace('trace1')
        
        self.assertEqual(trace.status, TraceStatus.ERROR)
        self.assertEqual(trace.error_count, 1)
    
    def test_critical_path(self):
        """Test critical path calculation"""
        # Create a trace with branching
        # span1 (100ms)
        #   -> span2 (50ms)
        #   -> span3 (80ms)
        #      -> span4 (40ms)
        
        spans = [
            create_span_data('trace1', 'span1', 'svc1', 'op1', duration_ms=100.0),
            create_span_data('trace1', 'span2', 'svc2', 'op2', parent_span_id='span1', duration_ms=50.0),
            create_span_data('trace1', 'span3', 'svc3', 'op3', parent_span_id='span1', duration_ms=80.0),
            create_span_data('trace1', 'span4', 'svc4', 'op4', parent_span_id='span3', duration_ms=40.0),
        ]
        
        for span in spans:
            self.agg.ingest_span(span)
        
        trace = self.agg.get_trace('trace1')
        critical_path = trace.get_critical_path()
        
        # Critical path should be span1 -> span3 -> span4
        self.assertEqual(len(critical_path), 3)
        self.assertEqual(critical_path[0].span_id, 'span1')
        self.assertEqual(critical_path[1].span_id, 'span3')
        self.assertEqual(critical_path[2].span_id, 'span4')


class TestServiceDependencies(unittest.TestCase):
    """Test service dependency tracking"""
    
    def setUp(self):
        """Set up test aggregator"""
        self.agg = TracAgg()
    
    def test_dependency_detection(self):
        """Test detecting service dependencies"""
        # Client span from api-gateway to user-service
        span = create_span_data(
            trace_id='trace1',
            span_id='span1',
            service_name='api-gateway',
            operation_name='call_user_service',
            duration_ms=100.0,
            kind='client',
            tags={'peer.service': 'user-service'}
        )
        
        self.agg.ingest_span(span)
        
        deps = self.agg.get_service_dependencies()
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].from_service, 'api-gateway')
        self.assertEqual(deps[0].to_service, 'user-service')
        self.assertEqual(deps[0].call_count, 1)
    
    def test_dependency_metrics(self):
        """Test dependency metrics calculation"""
        # Multiple calls with different latencies
        for i in range(5):
            span = create_span_data(
                trace_id=f'trace{i}',
                span_id=f'span{i}',
                service_name='api-gateway',
                operation_name='call_user_service',
                duration_ms=100.0 + i * 10,
                kind='client',
                tags={'peer.service': 'user-service'}
            )
            self.agg.ingest_span(span)
        
        # Add an error
        error_span = create_span_data(
            trace_id='trace_error',
            span_id='span_error',
            service_name='api-gateway',
            operation_name='call_user_service',
            duration_ms=200.0,
            kind='client',
            status_code=500,
            tags={'peer.service': 'user-service'}
        )
        self.agg.ingest_span(error_span)
        
        deps = self.agg.get_service_dependencies()
        self.assertEqual(len(deps), 1)
        
        dep = deps[0]
        self.assertEqual(dep.call_count, 6)
        self.assertEqual(dep.error_count, 1)
        self.assertAlmostEqual(dep.error_rate(), 1/6, places=2)
        self.assertGreater(dep.average_latency_ms(), 0)
    
    def test_service_graph(self):
        """Test service dependency graph generation"""
        # Create a simple graph: A -> B -> C
        #                         A -> D
        spans = [
            create_span_data('t1', 's1', 'A', 'op1', kind='client', 
                           tags={'peer.service': 'B'}),
            create_span_data('t2', 's2', 'B', 'op2', kind='client', 
                           tags={'peer.service': 'C'}),
            create_span_data('t3', 's3', 'A', 'op3', kind='client', 
                           tags={'peer.service': 'D'}),
        ]
        
        for span in spans:
            self.agg.ingest_span(span)
        
        graph = self.agg.get_service_graph()
        
        self.assertIn('A', graph)
        self.assertIn('B', graph['A'])
        self.assertIn('D', graph['A'])
        self.assertIn('B', graph)
        self.assertIn('C', graph['B'])


class TestQueryCapabilities(unittest.TestCase):
    """Test trace query capabilities"""
    
    def setUp(self):
        """Set up test aggregator with sample data"""
        self.agg = TracAgg()
        
        # Create diverse traces
        traces_data = [
            ('trace1', 'service1', 'op1', 50.0, 200),
            ('trace2', 'service1', 'op2', 150.0, 200),
            ('trace3', 'service2', 'op1', 100.0, 500),
            ('trace4', 'service2', 'op3', 200.0, 200),
            ('trace5', 'service1', 'op1', 75.0, 404),
        ]
        
        for trace_id, service, op, duration, status in traces_data:
            span = create_span_data(
                trace_id=trace_id,
                span_id=f'{trace_id}_span',
                service_name=service,
                operation_name=op,
                duration_ms=duration,
                status_code=status
            )
            self.agg.ingest_span(span)
    
    def test_query_by_service(self):
        """Test querying traces by service"""
        traces = self.agg.query_traces(service_name='service1')
        self.assertEqual(len(traces), 3)
        
        for trace in traces:
            self.assertIn('service1', trace.services)
    
    def test_query_by_operation(self):
        """Test querying traces by operation"""
        traces = self.agg.query_traces(operation_name='op1')
        self.assertEqual(len(traces), 3)
        
        for trace in traces:
            ops = [s.operation_name for s in trace.spans]
            self.assertIn('op1', ops)
    
    def test_query_by_duration(self):
        """Test querying traces by duration"""
        traces = self.agg.query_traces(min_duration_ms=100.0, max_duration_ms=200.0)
        
        for trace in traces:
            self.assertGreaterEqual(trace.duration_ms, 100.0)
            self.assertLessEqual(trace.duration_ms, 200.0)
    
    def test_query_with_errors(self):
        """Test querying traces with errors"""
        error_traces = self.agg.query_traces(has_error=True)
        self.assertEqual(len(error_traces), 2)
        
        for trace in error_traces:
            self.assertGreater(trace.error_count, 0)
        
        success_traces = self.agg.query_traces(has_error=False)
        for trace in success_traces:
            self.assertEqual(trace.error_count, 0)
    
    def test_query_limit(self):
        """Test query result limiting"""
        traces = self.agg.query_traces(limit=2)
        self.assertLessEqual(len(traces), 2)


class TestAnalytics(unittest.TestCase):
    """Test analytics capabilities"""
    
    def setUp(self):
        """Set up test aggregator"""
        self.agg = TracAgg()
    
    def test_service_statistics(self):
        """Test service statistics calculation"""
        # Create spans for service
        for i in range(10):
            span = create_span_data(
                trace_id=f'trace{i}',
                span_id=f'span{i}',
                service_name='test-service',
                operation_name='test-op',
                duration_ms=100.0 + i * 10,
                status_code=200 if i < 8 else 500
            )
            self.agg.ingest_span(span)
        
        stats = self.agg.get_service_stats('test-service')
        
        self.assertEqual(stats['span_count'], 10)
        self.assertEqual(stats['error_count'], 2)
        self.assertAlmostEqual(stats['error_rate'], 0.2, places=2)
        self.assertGreater(stats['avg_duration_ms'], 0)
    
    def test_all_services_statistics(self):
        """Test getting statistics for all services"""
        services = ['service1', 'service2', 'service3']
        
        for service in services:
            span = create_span_data(
                trace_id=f'trace_{service}',
                span_id=f'span_{service}',
                service_name=service,
                operation_name='op',
                duration_ms=100.0
            )
            self.agg.ingest_span(span)
        
        all_stats = self.agg.get_service_stats()
        
        self.assertEqual(len(all_stats), 3)
        for service in services:
            self.assertIn(service, all_stats)
            self.assertEqual(all_stats[service]['span_count'], 1)
    
    def test_bottleneck_detection(self):
        """Test bottleneck detection"""
        # Create spans with varying durations
        for i in range(100):
            duration = 100.0 if i < 95 else 500.0  # 5% are slow
            span = create_span_data(
                trace_id=f'trace{i}',
                span_id=f'span{i}',
                service_name='service1',
                operation_name='slow_op',
                duration_ms=duration
            )
            self.agg.ingest_span(span)
        
        bottlenecks = self.agg.find_bottlenecks(percentile=0.95)
        
        self.assertGreater(len(bottlenecks), 0)
        self.assertEqual(bottlenecks[0]['service'], 'service1')
        self.assertEqual(bottlenecks[0]['operation'], 'slow_op')
        self.assertGreater(bottlenecks[0]['p95_duration_ms'], 400.0)


class TestTraceExport(unittest.TestCase):
    """Test trace export functionality"""
    
    def setUp(self):
        """Set up test aggregator"""
        self.agg = TracAgg()
    
    def test_export_trace(self):
        """Test exporting a trace"""
        span = create_span_data(
            trace_id='trace1',
            span_id='span1',
            service_name='service1',
            operation_name='op1',
            duration_ms=100.0,
            tags={'key': 'value'}
        )
        
        self.agg.ingest_span(span)
        
        exported = self.agg.export_trace('trace1')
        
        self.assertIsNotNone(exported)
        self.assertEqual(exported['trace_id'], 'trace1')
        self.assertEqual(len(exported['spans']), 1)
        self.assertEqual(exported['spans'][0]['service_name'], 'service1')
        self.assertEqual(exported['spans'][0]['tags']['key'], 'value')
    
    def test_export_nonexistent_trace(self):
        """Test exporting a non-existent trace"""
        exported = self.agg.export_trace('nonexistent')
        self.assertIsNone(exported)


class TestCleanup(unittest.TestCase):
    """Test cleanup functionality"""
    
    def test_cleanup_old_traces(self):
        """Test cleaning up old traces"""
        agg = TracAgg(retention_seconds=1)
        
        # Create an old trace
        span = create_span_data(
            trace_id='old_trace',
            span_id='span1',
            service_name='service1',
            operation_name='op1',
            duration_ms=100.0
        )
        agg.ingest_span(span)
        
        # Verify trace exists
        self.assertEqual(agg.get_trace_count(), 1)
        
        # Wait for retention period
        time.sleep(1.1)
        
        # Cleanup
        removed = agg.cleanup_old_traces()
        
        self.assertGreater(removed, 0)
        self.assertEqual(agg.get_trace_count(), 0)
    
    def test_clear(self):
        """Test clearing all data"""
        span = create_span_data('trace1', 'span1', 'service1', 'op1')
        self.agg = TracAgg()
        self.agg.ingest_span(span)
        
        self.assertEqual(self.agg.get_trace_count(), 1)
        
        self.agg.clear()
        
        self.assertEqual(self.agg.get_trace_count(), 0)
        self.assertEqual(len(self.agg.get_service_dependencies()), 0)


if __name__ == '__main__':
    unittest.main()
