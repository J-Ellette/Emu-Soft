"""
Tests for Prometheus Client Emulator

This test suite validates the core functionality of the Prometheus client emulator.
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prometheus_client_emulator import (
    Counter, Gauge, Histogram, Summary,
    CollectorRegistry, generate_latest,
    REGISTRY, ProcessCollector, PlatformCollector
)


def test_counter():
    """Test counter metric"""
    print("Testing counter metric...")
    
    registry = CollectorRegistry()
    counter = Counter('test_counter', 'Test counter')
    registry.register(counter)
    
    counter.inc()
    assert counter._values[()] == 1.0
    
    counter.inc(5)
    assert counter._values[()] == 6.0
    
    try:
        counter.inc(-1)
        assert False, "Should not allow negative increment"
    except ValueError:
        pass
    
    print("✓ Counter metric works")


def test_counter_with_labels():
    """Test counter with labels"""
    print("Testing counter with labels...")
    
    registry = CollectorRegistry()
    counter = Counter('test_counter_labels', 'Test counter with labels', ('method', 'status'))
    registry.register(counter)
    
    counter.inc(labels={'method': 'GET', 'status': '200'})
    counter.inc(2, labels={'method': 'GET', 'status': '200'})
    counter.inc(labels={'method': 'POST', 'status': '201'})
    
    samples = counter.collect()
    assert len(samples) == 2
    
    # Check values
    for labels_dict, value in samples:
        if labels_dict == {'method': 'GET', 'status': '200'}:
            assert value == 3.0
        elif labels_dict == {'method': 'POST', 'status': '201'}:
            assert value == 1.0
    
    print("✓ Counter with labels works")


def test_counter_labels_method():
    """Test counter labels() method"""
    print("Testing counter labels() method...")
    
    registry = CollectorRegistry()
    counter = Counter('test_counter_child', 'Test counter child', ('endpoint',))
    registry.register(counter)
    
    api_counter = counter.labels(endpoint='/api')
    api_counter.inc()
    api_counter.inc(4)
    
    web_counter = counter.labels(endpoint='/web')
    web_counter.inc(2)
    
    samples = counter.collect()
    assert len(samples) == 2
    
    for labels_dict, value in samples:
        if labels_dict == {'endpoint': '/api'}:
            assert value == 5.0
        elif labels_dict == {'endpoint': '/web'}:
            assert value == 2.0
    
    print("✓ Counter labels() method works")


def test_gauge():
    """Test gauge metric"""
    print("Testing gauge metric...")
    
    registry = CollectorRegistry()
    gauge = Gauge('test_gauge', 'Test gauge')
    registry.register(gauge)
    
    gauge.set(10)
    assert gauge._values[()] == 10.0
    
    gauge.inc(5)
    assert gauge._values[()] == 15.0
    
    gauge.dec(3)
    assert gauge._values[()] == 12.0
    
    gauge.set_to_current_time()
    assert gauge._values[()] > 0
    
    print("✓ Gauge metric works")


def test_gauge_with_labels():
    """Test gauge with labels"""
    print("Testing gauge with labels...")
    
    registry = CollectorRegistry()
    gauge = Gauge('test_gauge_labels', 'Test gauge with labels', ('server',))
    registry.register(gauge)
    
    gauge.set(100, labels={'server': 'web-1'})
    gauge.set(200, labels={'server': 'web-2'})
    
    gauge.inc(50, labels={'server': 'web-1'})
    gauge.dec(25, labels={'server': 'web-2'})
    
    samples = gauge.collect()
    assert len(samples) == 2
    
    for labels_dict, value in samples:
        if labels_dict == {'server': 'web-1'}:
            assert value == 150.0
        elif labels_dict == {'server': 'web-2'}:
            assert value == 175.0
    
    print("✓ Gauge with labels works")


def test_gauge_labels_method():
    """Test gauge labels() method"""
    print("Testing gauge labels() method...")
    
    registry = CollectorRegistry()
    gauge = Gauge('test_gauge_child', 'Test gauge child', ('region',))
    registry.register(gauge)
    
    us_gauge = gauge.labels(region='us-west')
    us_gauge.set(100)
    us_gauge.inc(10)
    us_gauge.dec(5)
    
    eu_gauge = gauge.labels(region='eu-central')
    eu_gauge.set(200)
    
    samples = gauge.collect()
    assert len(samples) == 2
    
    for labels_dict, value in samples:
        if labels_dict == {'region': 'us-west'}:
            assert value == 105.0
        elif labels_dict == {'region': 'eu-central'}:
            assert value == 200.0
    
    print("✓ Gauge labels() method works")


def test_histogram():
    """Test histogram metric"""
    print("Testing histogram metric...")
    
    registry = CollectorRegistry()
    histogram = Histogram(
        'test_histogram',
        'Test histogram',
        buckets=(.1, .5, 1.0, 5.0, float('inf'))
    )
    registry.register(histogram)
    
    histogram.observe(0.05)
    histogram.observe(0.3)
    histogram.observe(0.8)
    histogram.observe(3.0)
    histogram.observe(10.0)
    
    samples = histogram.collect()
    
    # Check that we have bucket, sum, and count samples
    bucket_samples = [s for s in samples if s[1] == '_bucket']
    sum_samples = [s for s in samples if s[1] == '_sum']
    count_samples = [s for s in samples if s[1] == '_count']
    
    assert len(bucket_samples) == 5  # One for each bucket
    assert len(sum_samples) == 1
    assert len(count_samples) == 1
    
    # Check sum and count
    assert sum_samples[0][2] == 0.05 + 0.3 + 0.8 + 3.0 + 10.0
    assert count_samples[0][2] == 5
    
    print("✓ Histogram metric works")


def test_histogram_timer():
    """Test histogram timer"""
    print("Testing histogram timer...")
    
    registry = CollectorRegistry()
    histogram = Histogram('test_histogram_timer', 'Test histogram timer')
    registry.register(histogram)
    
    with histogram.time():
        time.sleep(0.01)
    
    samples = histogram.collect()
    count_samples = [s for s in samples if s[1] == '_count']
    assert count_samples[0][2] == 1
    
    print("✓ Histogram timer works")


def test_histogram_with_labels():
    """Test histogram with labels"""
    print("Testing histogram with labels...")
    
    registry = CollectorRegistry()
    histogram = Histogram(
        'test_histogram_labels',
        'Test histogram with labels',
        ('method',),
        buckets=(.1, 1.0, float('inf'))
    )
    registry.register(histogram)
    
    histogram.observe(0.05, labels={'method': 'GET'})
    histogram.observe(0.5, labels={'method': 'GET'})
    histogram.observe(2.0, labels={'method': 'POST'})
    
    samples = histogram.collect()
    
    # Check we have samples for both label sets
    get_count = [s for s in samples if s[1] == '_count' and s[0] == {'method': 'GET'}]
    post_count = [s for s in samples if s[1] == '_count' and s[0] == {'method': 'POST'}]
    
    assert get_count[0][2] == 2
    assert post_count[0][2] == 1
    
    print("✓ Histogram with labels works")


def test_summary():
    """Test summary metric"""
    print("Testing summary metric...")
    
    registry = CollectorRegistry()
    summary = Summary('test_summary', 'Test summary')
    registry.register(summary)
    
    summary.observe(10)
    summary.observe(20)
    summary.observe(30)
    
    samples = summary.collect()
    
    sum_samples = [s for s in samples if s[1] == '_sum']
    count_samples = [s for s in samples if s[1] == '_count']
    
    assert len(sum_samples) == 1
    assert len(count_samples) == 1
    assert sum_samples[0][2] == 60
    assert count_samples[0][2] == 3
    
    print("✓ Summary metric works")


def test_summary_timer():
    """Test summary timer"""
    print("Testing summary timer...")
    
    registry = CollectorRegistry()
    summary = Summary('test_summary_timer', 'Test summary timer')
    registry.register(summary)
    
    with summary.time():
        time.sleep(0.01)
    
    samples = summary.collect()
    count_samples = [s for s in samples if s[1] == '_count']
    assert count_samples[0][2] == 1
    
    print("✓ Summary timer works")


def test_summary_with_labels():
    """Test summary with labels"""
    print("Testing summary with labels...")
    
    registry = CollectorRegistry()
    summary = Summary('test_summary_labels', 'Test summary with labels', ('endpoint',))
    registry.register(summary)
    
    summary.observe(100, labels={'endpoint': '/api'})
    summary.observe(200, labels={'endpoint': '/api'})
    summary.observe(50, labels={'endpoint': '/web'})
    
    samples = summary.collect()
    
    api_sum = [s for s in samples if s[1] == '_sum' and s[0] == {'endpoint': '/api'}]
    web_sum = [s for s in samples if s[1] == '_sum' and s[0] == {'endpoint': '/web'}]
    
    assert api_sum[0][2] == 300
    assert web_sum[0][2] == 50
    
    print("✓ Summary with labels works")


def test_registry():
    """Test collector registry"""
    print("Testing collector registry...")
    
    registry = CollectorRegistry()
    
    counter1 = Counter('counter1', 'Counter 1')
    counter2 = Counter('counter2', 'Counter 2')
    
    registry.register(counter1)
    registry.register(counter2)
    
    collectors = registry.collect()
    assert len(collectors) == 2
    assert counter1 in collectors
    assert counter2 in collectors
    
    registry.unregister(counter1)
    collectors = registry.collect()
    assert len(collectors) == 1
    assert counter2 in collectors
    
    print("✓ Collector registry works")


def test_registry_duplicate():
    """Test registry duplicate prevention"""
    print("Testing registry duplicate prevention...")
    
    registry = CollectorRegistry()
    counter = Counter('test_counter', 'Test counter')
    
    registry.register(counter)
    
    try:
        registry.register(counter)
        assert False, "Should not allow duplicate registration"
    except ValueError:
        pass
    
    print("✓ Registry duplicate prevention works")


def test_generate_latest():
    """Test metrics generation"""
    print("Testing metrics generation...")
    
    registry = CollectorRegistry()
    
    counter = Counter('test_counter', 'A test counter')
    registry.register(counter)
    counter.inc(5)
    
    gauge = Gauge('test_gauge', 'A test gauge')
    registry.register(gauge)
    gauge.set(42)
    
    output = generate_latest(registry)
    
    assert '# HELP test_counter A test counter' in output
    assert '# TYPE test_counter counter' in output
    assert 'test_counter 5' in output
    
    assert '# HELP test_gauge A test gauge' in output
    assert '# TYPE test_gauge gauge' in output
    assert 'test_gauge 42' in output
    
    print("✓ Metrics generation works")


def test_generate_latest_with_labels():
    """Test metrics generation with labels"""
    print("Testing metrics generation with labels...")
    
    registry = CollectorRegistry()
    
    counter = Counter('http_requests', 'HTTP requests', ('method', 'status'))
    registry.register(counter)
    counter.inc(10, labels={'method': 'GET', 'status': '200'})
    counter.inc(5, labels={'method': 'POST', 'status': '201'})
    
    output = generate_latest(registry)
    
    assert 'http_requests{method="GET",status="200"} 10' in output
    assert 'http_requests{method="POST",status="201"} 5' in output
    
    print("✓ Metrics generation with labels works")


def test_get_sample_value():
    """Test getting sample values"""
    print("Testing get sample value...")
    
    registry = CollectorRegistry()
    
    counter = Counter('test_counter', 'Test counter')
    registry.register(counter)
    counter.inc(10)
    
    value = registry.get_sample_value('test_counter')
    assert value == 10.0
    
    counter_with_labels = Counter('labeled_counter', 'Labeled counter', ('key',))
    registry.register(counter_with_labels)
    counter_with_labels.inc(5, labels={'key': 'value'})
    
    value = registry.get_sample_value('labeled_counter', {'key': 'value'})
    assert value == 5.0
    
    print("✓ Get sample value works")


def test_process_collector():
    """Test process collector"""
    print("Testing process collector...")
    
    registry = CollectorRegistry()
    process_collector = ProcessCollector(registry)
    
    # Check that metrics were registered
    collectors = registry.collect()
    names = [c.name for c in collectors]
    
    assert 'process_cpu_seconds_total' in names
    assert 'process_start_time_seconds' in names
    
    print("✓ Process collector works")


def test_platform_collector():
    """Test platform collector"""
    print("Testing platform collector...")
    
    registry = CollectorRegistry()
    platform_collector = PlatformCollector(registry)
    
    # Check that metrics were registered
    collectors = registry.collect()
    names = [c.name for c in collectors]
    
    assert 'python_info' in names
    
    print("✓ Platform collector works")


def test_histogram_buckets_validation():
    """Test histogram buckets validation"""
    print("Testing histogram buckets validation...")
    
    try:
        # Unsorted buckets should raise error
        histogram = Histogram('test', 'test', buckets=(1.0, 0.5, 0.1))
        assert False, "Should not allow unsorted buckets"
    except ValueError:
        pass
    
    print("✓ Histogram buckets validation works")


def test_label_validation():
    """Test label validation"""
    print("Testing label validation...")
    
    counter = Counter('test_counter', 'Test', ('label1', 'label2'))
    
    try:
        # Missing label
        counter.inc(labels={'label1': 'value'})
        assert False, "Should require all labels"
    except ValueError:
        pass
    
    try:
        # Extra label
        counter.inc(labels={'label1': 'value', 'label2': 'value', 'label3': 'value'})
        assert False, "Should not allow extra labels"
    except ValueError:
        pass
    
    print("✓ Label validation works")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Prometheus Client Emulator Tests")
    print("=" * 60)
    
    tests = [
        test_counter,
        test_counter_with_labels,
        test_counter_labels_method,
        test_gauge,
        test_gauge_with_labels,
        test_gauge_labels_method,
        test_histogram,
        test_histogram_timer,
        test_histogram_with_labels,
        test_summary,
        test_summary_timer,
        test_summary_with_labels,
        test_registry,
        test_registry_duplicate,
        test_generate_latest,
        test_generate_latest_with_labels,
        test_get_sample_value,
        test_process_collector,
        test_platform_collector,
        test_histogram_buckets_validation,
        test_label_validation,
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
