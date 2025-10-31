"""
Test suite for MetricsCollector (Prometheus Emulator)
This file contains comprehensive tests for the Prometheus metrics emulator
"""

import unittest
import time
from MetricsCollector import (
    Counter, Gauge, Histogram, Summary, Registry, Timer,
    REGISTRY, start_http_server, push_to_gateway, generate_latest,
    info, enum, time_function
)


class TestCounter(unittest.TestCase):
    """Test Counter metric"""
    
    def setUp(self):
        self.counter = Counter("test_counter", "Test counter metric")
    
    def test_counter_creation(self):
        """Test counter creation"""
        self.assertEqual(self.counter.name, "test_counter")
        self.assertEqual(self.counter.documentation, "Test counter metric")
        self.assertEqual(self.counter.metric_type, "counter")
    
    def test_counter_increment(self):
        """Test counter increment"""
        self.counter.inc()
        self.assertEqual(self.counter.get(), 1.0)
        
        self.counter.inc(5.0)
        self.assertEqual(self.counter.get(), 6.0)
    
    def test_counter_cannot_decrease(self):
        """Test that counter cannot decrease"""
        with self.assertRaises(ValueError):
            self.counter.inc(-1.0)
    
    def test_counter_with_labels(self):
        """Test counter with labels"""
        counter = Counter("http_requests", "HTTP requests", ["method", "status"])
        
        counter.inc(method="GET", status="200")
        counter.inc(method="GET", status="200")
        counter.inc(method="POST", status="201")
        
        self.assertEqual(counter.get(method="GET", status="200"), 2.0)
        self.assertEqual(counter.get(method="POST", status="201"), 1.0)
        self.assertEqual(counter.get(method="DELETE", status="404"), 0.0)
    
    def test_counter_reset(self):
        """Test counter reset"""
        self.counter.inc(10.0)
        self.counter.reset()
        self.assertEqual(self.counter.get(), 0.0)


class TestGauge(unittest.TestCase):
    """Test Gauge metric"""
    
    def setUp(self):
        self.gauge = Gauge("test_gauge", "Test gauge metric")
    
    def test_gauge_creation(self):
        """Test gauge creation"""
        self.assertEqual(self.gauge.name, "test_gauge")
        self.assertEqual(self.gauge.metric_type, "gauge")
    
    def test_gauge_set(self):
        """Test gauge set"""
        self.gauge.set(42.0)
        self.assertEqual(self.gauge.get(), 42.0)
        
        self.gauge.set(100.0)
        self.assertEqual(self.gauge.get(), 100.0)
    
    def test_gauge_increment(self):
        """Test gauge increment"""
        self.gauge.set(10.0)
        self.gauge.inc(5.0)
        self.assertEqual(self.gauge.get(), 15.0)
    
    def test_gauge_decrement(self):
        """Test gauge decrement"""
        self.gauge.set(10.0)
        self.gauge.dec(3.0)
        self.assertEqual(self.gauge.get(), 7.0)
    
    def test_gauge_with_labels(self):
        """Test gauge with labels"""
        gauge = Gauge("temperature", "Temperature readings", ["location"])
        
        gauge.set(22.5, location="office")
        gauge.set(18.0, location="warehouse")
        
        self.assertEqual(gauge.get(location="office"), 22.5)
        self.assertEqual(gauge.get(location="warehouse"), 18.0)
    
    def test_gauge_current_time(self):
        """Test setting gauge to current time"""
        before = time.time()
        self.gauge.set_to_current_time()
        after = time.time()
        
        value = self.gauge.get()
        self.assertGreaterEqual(value, before)
        self.assertLessEqual(value, after)


class TestHistogram(unittest.TestCase):
    """Test Histogram metric"""
    
    def setUp(self):
        self.histogram = Histogram("test_histogram", "Test histogram", 
                                   buckets=[0.1, 0.5, 1.0, 5.0])
    
    def test_histogram_creation(self):
        """Test histogram creation"""
        self.assertEqual(self.histogram.name, "test_histogram")
        self.assertEqual(self.histogram.metric_type, "histogram")
    
    def test_histogram_observe(self):
        """Test histogram observe"""
        self.histogram.observe(0.3)
        self.histogram.observe(0.7)
        self.histogram.observe(2.0)
        
        self.assertEqual(self.histogram.get_count(), 3)
        self.assertAlmostEqual(self.histogram.get_sum(), 3.0)
    
    def test_histogram_buckets(self):
        """Test histogram buckets"""
        self.histogram.observe(0.05)  # Should be in 0.1 bucket
        self.histogram.observe(0.3)   # Should be in 0.5 bucket
        self.histogram.observe(0.8)   # Should be in 1.0 bucket
        self.histogram.observe(3.0)   # Should be in 5.0 bucket
        
        self.assertEqual(self.histogram.get_bucket(0.1), 1)
        self.assertEqual(self.histogram.get_bucket(0.5), 2)  # Cumulative
        self.assertEqual(self.histogram.get_bucket(1.0), 3)  # Cumulative
        self.assertEqual(self.histogram.get_bucket(5.0), 4)  # Cumulative
    
    def test_histogram_with_labels(self):
        """Test histogram with labels"""
        hist = Histogram("request_duration", "Request duration", 
                        labels=["method"], buckets=[0.1, 0.5, 1.0])
        
        hist.observe(0.2, method="GET")
        hist.observe(0.8, method="GET")
        hist.observe(0.3, method="POST")
        
        self.assertEqual(hist.get_count(method="GET"), 2)
        self.assertEqual(hist.get_count(method="POST"), 1)


class TestSummary(unittest.TestCase):
    """Test Summary metric"""
    
    def setUp(self):
        self.summary = Summary("test_summary", "Test summary")
    
    def test_summary_creation(self):
        """Test summary creation"""
        self.assertEqual(self.summary.name, "test_summary")
        self.assertEqual(self.summary.metric_type, "summary")
    
    def test_summary_observe(self):
        """Test summary observe"""
        self.summary.observe(1.0)
        self.summary.observe(2.0)
        self.summary.observe(3.0)
        
        self.assertEqual(self.summary.get_count(), 3)
        self.assertEqual(self.summary.get_sum(), 6.0)
    
    def test_summary_quantiles(self):
        """Test summary quantiles"""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        for v in values:
            self.summary.observe(float(v))
        
        # Test quantiles
        self.assertEqual(self.summary.get_quantile(0.0), 1.0)  # Min
        self.assertEqual(self.summary.get_quantile(0.5), 5.0)  # Median
        self.assertEqual(self.summary.get_quantile(1.0), 10.0) # Max
    
    def test_summary_with_labels(self):
        """Test summary with labels"""
        summary = Summary("response_size", "Response size", labels=["endpoint"])
        
        summary.observe(100, endpoint="/api/users")
        summary.observe(200, endpoint="/api/users")
        summary.observe(500, endpoint="/api/posts")
        
        self.assertEqual(summary.get_count(endpoint="/api/users"), 2)
        self.assertEqual(summary.get_sum(endpoint="/api/users"), 300)


class TestRegistry(unittest.TestCase):
    """Test Registry"""
    
    def setUp(self):
        self.registry = Registry()
    
    def test_register_metric(self):
        """Test registering a metric"""
        counter = Counter("test", "Test metric")
        self.registry.register(counter)
        
        retrieved = self.registry.get_metric("test")
        self.assertEqual(retrieved, counter)
    
    def test_register_duplicate(self):
        """Test registering duplicate metric raises error"""
        counter1 = Counter("test", "Test 1")
        counter2 = Counter("test", "Test 2")
        
        self.registry.register(counter1)
        with self.assertRaises(ValueError):
            self.registry.register(counter2)
    
    def test_unregister_metric(self):
        """Test unregistering a metric"""
        counter = Counter("test", "Test metric")
        self.registry.register(counter)
        self.registry.unregister(counter)
        
        self.assertIsNone(self.registry.get_metric("test"))
    
    def test_collect_metrics(self):
        """Test collecting metrics"""
        counter = Counter("requests", "Request count")
        counter.inc(5)
        
        self.registry.register(counter)
        output = self.registry.collect()
        
        self.assertIn("requests", output)
        self.assertIn("Request count", output)


class TestTimer(unittest.TestCase):
    """Test Timer context manager"""
    
    def test_timer_context_manager(self):
        """Test using Timer as context manager"""
        histogram = Histogram("duration", "Duration", buckets=[0.1, 0.5, 1.0])
        
        with Timer(histogram):
            time.sleep(0.01)  # Sleep for 10ms
        
        self.assertEqual(histogram.get_count(), 1)
        self.assertGreater(histogram.get_sum(), 0.0)
    
    def test_timer_with_labels(self):
        """Test Timer with labels"""
        histogram = Histogram("request_time", "Request time", 
                             labels=["method"], buckets=[0.1, 0.5])
        
        with Timer(histogram, method="GET"):
            time.sleep(0.01)
        
        self.assertEqual(histogram.get_count(method="GET"), 1)


class TestDecorator(unittest.TestCase):
    """Test time_function decorator"""
    
    def test_time_function_decorator(self):
        """Test timing function with decorator"""
        histogram = Histogram("func_duration", "Function duration", 
                             buckets=[0.1, 0.5])
        
        @time_function(histogram)
        def test_func():
            time.sleep(0.01)
            return "done"
        
        result = test_func()
        
        self.assertEqual(result, "done")
        self.assertEqual(histogram.get_count(), 1)


class TestUtilities(unittest.TestCase):
    """Test utility functions"""
    
    def test_start_http_server(self):
        """Test starting HTTP server"""
        result = start_http_server(9090)
        self.assertTrue(result)
    
    def test_push_to_gateway(self):
        """Test pushing to gateway"""
        result = push_to_gateway("localhost:9091", "test_job")
        self.assertTrue(result)
    
    def test_generate_latest(self):
        """Test generating metrics output"""
        registry = Registry()
        counter = Counter("test", "Test")
        counter.inc()
        registry.register(counter)
        
        output = generate_latest(registry)
        self.assertIn("test", output)
    
    def test_info_metric(self):
        """Test creating info metric"""
        labels = info("app", "Application info", 
                     version="1.0.0", env="production")
        
        self.assertEqual(labels["version"], "1.0.0")
        self.assertEqual(labels["env"], "production")
    
    def test_enum_metric(self):
        """Test creating enum metric"""
        state_gauge = enum("task_state", "Task state", 
                          ["pending", "running", "completed"])
        
        self.assertIsInstance(state_gauge, Gauge)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_metrics_workflow(self):
        """Test complete metrics workflow"""
        registry = Registry()
        
        # Create metrics
        requests = Counter("http_requests_total", "Total HTTP requests",
                          labels=["method", "status"])
        duration = Histogram("http_request_duration_seconds", 
                           "HTTP request duration",
                           labels=["method"],
                           buckets=[0.1, 0.5, 1.0])
        active = Gauge("active_connections", "Active connections")
        
        # Register metrics
        registry.register(requests)
        registry.register(duration)
        registry.register(active)
        
        # Simulate application behavior
        active.set(10)
        
        requests.inc(method="GET", status="200")
        duration.observe(0.25, method="GET")
        
        requests.inc(method="POST", status="201")
        duration.observe(0.8, method="POST")
        
        active.inc(5)
        
        # Verify metrics
        self.assertEqual(requests.get(method="GET", status="200"), 1)
        self.assertEqual(requests.get(method="POST", status="201"), 1)
        self.assertEqual(duration.get_count(method="GET"), 1)
        self.assertEqual(active.get(), 15)
        
        # Collect metrics
        output = registry.collect()
        self.assertIn("http_requests_total", output)
        self.assertIn("http_request_duration_seconds", output)
        self.assertIn("active_connections", output)


if __name__ == "__main__":
    print("Running Prometheus Emulator tests...")
    unittest.main(verbosity=2)
