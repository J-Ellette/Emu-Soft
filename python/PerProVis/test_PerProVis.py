"""
Developed by PowerShield, as a performance profiling visualizer

Tests for PerProVis - Performance Profiling Visualizer

This test suite validates the core functionality of PerProVis.
"""

import sys
import os
import time
import threading
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PerProVis import (
    PerformanceProfiler, FunctionCall, FunctionStats,
    profile, profile_block, get_profiler, create_profiler
)


def test_function_call_creation():
    """Test function call creation"""
    print("Testing function call creation...")
    
    call = FunctionCall(
        name="test_func",
        start_time=1000.0,
        end_time=1000.5,
        duration=0.5,
        call_stack=["main", "test_func"]
    )
    
    assert call.name == "test_func"
    assert call.duration == 0.5
    assert len(call.call_stack) == 2
    
    print("✓ Function call creation works")


def test_function_call_to_dict():
    """Test function call serialization"""
    print("Testing function call to_dict...")
    
    call = FunctionCall(
        name="test_func",
        start_time=1000.0,
        end_time=1000.5,
        duration=0.5,
        metadata={"key": "value"}
    )
    
    call_dict = call.to_dict()
    assert call_dict['name'] == "test_func"
    assert call_dict['duration'] == 0.5
    assert call_dict['metadata']['key'] == "value"
    
    print("✓ Function call serialization works")


def test_function_stats_creation():
    """Test function stats creation"""
    print("Testing function stats creation...")
    
    stats = FunctionStats(name="test_func")
    assert stats.name == "test_func"
    assert stats.call_count == 0
    assert stats.total_time == 0.0
    
    print("✓ Function stats creation works")


def test_function_stats_add_call():
    """Test adding calls to stats"""
    print("Testing adding calls to stats...")
    
    stats = FunctionStats(name="test_func")
    
    stats.add_call(duration=0.1)
    assert stats.call_count == 1
    assert abs(stats.total_time - 0.1) < 0.001
    
    stats.add_call(duration=0.2)
    assert stats.call_count == 2
    assert abs(stats.total_time - 0.3) < 0.001
    
    print("✓ Adding calls to stats works")


def test_function_stats_calculations():
    """Test stats calculations"""
    print("Testing stats calculations...")
    
    stats = FunctionStats(name="test_func")
    
    # Add multiple calls
    for i in range(10):
        stats.add_call(duration=float(i) / 10.0)
    
    avg_time = stats.get_avg_time()
    assert avg_time > 0
    
    median_time = stats.get_median_time()
    assert median_time >= 0
    
    p95 = stats.get_percentile(95)
    assert p95 >= median_time
    
    std_dev = stats.get_std_dev()
    assert std_dev >= 0
    
    print("✓ Stats calculations work")


def test_profiler_creation():
    """Test profiler creation"""
    print("Testing profiler creation...")
    
    profiler = create_profiler()
    assert profiler is not None
    assert profiler.enabled is True
    
    profiler_disabled = create_profiler(enabled=False)
    assert profiler_disabled.enabled is False
    
    print("✓ Profiler creation works")


def test_profiler_enable_disable():
    """Test enabling and disabling profiler"""
    print("Testing enable/disable...")
    
    profiler = create_profiler(enabled=True)
    assert profiler.enabled is True
    
    profiler.disable()
    assert profiler.enabled is False
    
    profiler.enable()
    assert profiler.enabled is True
    
    print("✓ Enable/disable works")


def test_profile_block():
    """Test profiling code blocks"""
    print("Testing profile_block...")
    
    profiler = create_profiler()
    
    with profiler.profile_block("test_block"):
        # Simulate work
        sum(range(1000))
    
    stats = profiler.get_function_stats("test_block")
    assert stats is not None
    assert stats.call_count == 1
    assert stats.total_time > 0
    
    print("✓ Profile block works")


def test_profile_block_nested():
    """Test nested profiling blocks"""
    print("Testing nested profile blocks...")
    
    profiler = create_profiler()
    
    with profiler.profile_block("outer"):
        sum(range(1000))
        
        with profiler.profile_block("inner"):
            sum(range(1000))
    
    outer_stats = profiler.get_function_stats("outer")
    inner_stats = profiler.get_function_stats("inner")
    
    assert outer_stats is not None
    assert inner_stats is not None
    assert outer_stats.call_count == 1
    assert inner_stats.call_count == 1
    
    print("✓ Nested profile blocks work")


def test_profile_decorator():
    """Test profile decorator"""
    print("Testing profile decorator...")
    
    profiler = create_profiler()
    
    @profiler.profile_function
    def test_function():
        return sum(range(1000))
    
    # Call function
    result = test_function()
    assert result > 0
    
    # Check stats
    stats = profiler.get_function_stats("test_function")
    assert stats is not None
    assert stats.call_count == 1
    
    print("✓ Profile decorator works")


def test_profile_decorator_multiple_calls():
    """Test decorator with multiple calls"""
    print("Testing decorator with multiple calls...")
    
    profiler = create_profiler()
    
    @profiler.profile_function
    def test_function():
        return sum(range(1000))
    
    # Call multiple times
    for _ in range(5):
        test_function()
    
    stats = profiler.get_function_stats("test_function")
    assert stats.call_count == 5
    assert stats.total_time > 0
    
    print("✓ Decorator with multiple calls works")


def test_profile_decorator_with_custom_name():
    """Test decorator with custom name"""
    print("Testing decorator with custom name...")
    
    profiler = create_profiler()
    
    @profiler.profile_function(name="custom_name")
    def test_function():
        return sum(range(1000))
    
    test_function()
    
    stats = profiler.get_function_stats("custom_name")
    assert stats is not None
    assert stats.call_count == 1
    
    print("✓ Decorator with custom name works")


def test_get_all_function_stats():
    """Test getting all function stats"""
    print("Testing get all function stats...")
    
    profiler = create_profiler()
    
    with profiler.profile_block("func1"):
        sum(range(100))
    
    with profiler.profile_block("func2"):
        sum(range(100))
    
    all_stats = profiler.get_all_function_stats()
    assert len(all_stats) == 2
    assert "func1" in all_stats
    assert "func2" in all_stats
    
    print("✓ Get all function stats works")


def test_get_all_calls():
    """Test getting all calls"""
    print("Testing get all calls...")
    
    profiler = create_profiler()
    
    with profiler.profile_block("test"):
        sum(range(100))
    
    with profiler.profile_block("test"):
        sum(range(100))
    
    all_calls = profiler.get_all_calls()
    assert len(all_calls) == 2
    
    print("✓ Get all calls works")


def test_get_hotspots():
    """Test getting performance hotspots"""
    print("Testing get hotspots...")
    
    profiler = create_profiler()
    
    # Create functions with different performance
    with profiler.profile_block("slow"):
        sum(range(100000))
    
    with profiler.profile_block("fast"):
        sum(range(100))
    
    hotspots = profiler.get_hotspots(limit=5)
    assert len(hotspots) > 0
    
    # Slow should be first
    assert hotspots[0][0] == "slow"
    
    print("✓ Get hotspots works")


def test_get_slowest_calls():
    """Test getting slowest calls"""
    print("Testing get slowest calls...")
    
    profiler = create_profiler()
    
    # Create calls with varying durations
    for i in range(5):
        with profiler.profile_block("varying"):
            sum(range(i * 10000))
    
    slowest = profiler.get_slowest_calls(limit=3)
    assert len(slowest) == 3
    
    # Should be sorted by duration
    assert slowest[0][1] >= slowest[1][1]
    assert slowest[1][1] >= slowest[2][1]
    
    print("✓ Get slowest calls works")


def test_get_summary():
    """Test getting summary statistics"""
    print("Testing get summary...")
    
    profiler = create_profiler()
    
    # Profile some functions
    for _ in range(10):
        with profiler.profile_block("test"):
            sum(range(1000))
    
    summary = profiler.get_summary()
    assert summary['total_calls'] == 10
    assert summary['total_functions'] == 1
    assert summary['total_time'] > 0
    assert summary['avg_call_time'] > 0
    
    print("✓ Get summary works")


def test_clear():
    """Test clearing profiler data"""
    print("Testing clear...")
    
    profiler = create_profiler()
    
    with profiler.profile_block("test"):
        sum(range(1000))
    
    assert len(profiler.get_all_calls()) == 1
    
    profiler.clear()
    
    assert len(profiler.get_all_calls()) == 0
    assert len(profiler.get_all_function_stats()) == 0
    
    print("✓ Clear works")


def test_disabled_profiler():
    """Test that disabled profiler doesn't record"""
    print("Testing disabled profiler...")
    
    profiler = create_profiler(enabled=False)
    
    with profiler.profile_block("test"):
        sum(range(1000))
    
    assert len(profiler.get_all_calls()) == 0
    
    print("✓ Disabled profiler works")


def test_flame_graph_generation():
    """Test flame graph text generation"""
    print("Testing flame graph generation...")
    
    profiler = create_profiler()
    
    # Create some profiled functions
    for _ in range(5):
        with profiler.profile_block("func1"):
            sum(range(10000))
        with profiler.profile_block("func2"):
            sum(range(5000))
    
    flame_graph = profiler.generate_flame_graph_text(width=80)
    assert len(flame_graph) > 0
    assert "Flame Graph" in flame_graph
    
    print("✓ Flame graph generation works")


def test_timeline_generation():
    """Test timeline text generation"""
    print("Testing timeline generation...")
    
    profiler = create_profiler()
    
    # Create sequential calls
    with profiler.profile_block("step1"):
        sum(range(1000))
    
    with profiler.profile_block("step2"):
        sum(range(1000))
    
    timeline = profiler.generate_timeline_text(limit=10)
    assert len(timeline) > 0
    assert "Timeline" in timeline
    
    print("✓ Timeline generation works")


def test_export_to_json():
    """Test JSON export"""
    print("Testing JSON export...")
    
    profiler = create_profiler()
    
    with profiler.profile_block("test"):
        sum(range(1000))
    
    filename = "/tmp/test_profile.json"
    profiler.export_to_json(filename)
    
    assert os.path.exists(filename)
    
    with open(filename, 'r') as f:
        data = json.load(f)
        assert 'summary' in data
        assert 'function_stats' in data
        assert 'calls' in data
    
    os.remove(filename)
    
    print("✓ JSON export works")


def test_export_to_csv():
    """Test CSV export"""
    print("Testing CSV export...")
    
    profiler = create_profiler()
    
    with profiler.profile_block("test"):
        sum(range(1000))
    
    filename = "/tmp/test_profile.csv"
    profiler.export_to_csv(filename)
    
    assert os.path.exists(filename)
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        assert len(lines) >= 2  # Header + at least one data row
    
    os.remove(filename)
    
    print("✓ CSV export works")


def test_global_profiler():
    """Test global profiler functions"""
    print("Testing global profiler...")
    
    # Get global profiler
    profiler = get_profiler()
    profiler.clear()  # Clear any previous data
    
    @profile
    def global_test():
        return sum(range(1000))
    
    global_test()
    
    stats = profiler.get_function_stats("global_test")
    assert stats is not None
    assert stats.call_count == 1
    
    print("✓ Global profiler works")


def test_global_profile_block():
    """Test global profile_block"""
    print("Testing global profile_block...")
    
    profiler = get_profiler()
    profiler.clear()
    
    with profile_block("global_block"):
        sum(range(1000))
    
    stats = profiler.get_function_stats("global_block")
    assert stats is not None
    assert stats.call_count == 1
    
    print("✓ Global profile_block works")


def test_profile_with_metadata():
    """Test profiling with metadata"""
    print("Testing profile with metadata...")
    
    profiler = create_profiler()
    
    with profiler.profile_block("test", user_id=123, action="create"):
        sum(range(1000))
    
    calls = profiler.get_all_calls()
    assert len(calls) == 1
    assert calls[0].metadata['user_id'] == 123
    assert calls[0].metadata['action'] == "create"
    
    print("✓ Profile with metadata works")


def test_thread_safety():
    """Test thread safety"""
    print("Testing thread safety...")
    
    profiler = create_profiler()
    
    @profiler.profile_function
    def worker():
        sum(range(10000))
    
    # Create threads
    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    stats = profiler.get_function_stats("worker")
    assert stats.call_count == 5
    
    print("✓ Thread safety works")


def test_call_stack_tracking():
    """Test call stack tracking"""
    print("Testing call stack tracking...")
    
    profiler = create_profiler()
    
    with profiler.profile_block("outer"):
        with profiler.profile_block("inner"):
            sum(range(1000))
    
    calls = profiler.get_all_calls()
    
    # Find inner call
    inner_call = next(c for c in calls if c.name == "inner")
    assert len(inner_call.call_stack) == 2
    assert "outer" in inner_call.call_stack
    assert "inner" in inner_call.call_stack
    
    print("✓ Call stack tracking works")


def test_multiple_profiler_instances():
    """Test multiple independent profiler instances"""
    print("Testing multiple profiler instances...")
    
    profiler1 = create_profiler()
    profiler2 = create_profiler()
    
    @profiler1.profile_function
    def func1():
        return sum(range(1000))
    
    @profiler2.profile_function
    def func2():
        return sum(range(1000))
    
    func1()
    func2()
    
    # Each profiler should have its own data
    assert len(profiler1.get_all_function_stats()) == 1
    assert len(profiler2.get_all_function_stats()) == 1
    assert "func1" in profiler1.get_all_function_stats()
    assert "func2" in profiler2.get_all_function_stats()
    
    print("✓ Multiple profiler instances work")


def test_print_report():
    """Test print_report (just ensure it doesn't crash)"""
    print("Testing print_report...")
    
    profiler = create_profiler()
    
    @profiler.profile_function
    def test_func():
        return sum(range(10000))
    
    for _ in range(3):
        test_func()
    
    # This should not raise an exception
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        profiler.print_report(top_n=5)
    
    output = f.getvalue()
    assert len(output) > 0
    assert "Performance Profiling Report" in output
    
    print("✓ Print report works")


def run_all_tests():
    """Run all test functions"""
    print("=" * 60)
    print("Running PerProVis Tests")
    print("=" * 60)
    print()
    
    test_functions = [
        test_function_call_creation,
        test_function_call_to_dict,
        test_function_stats_creation,
        test_function_stats_add_call,
        test_function_stats_calculations,
        test_profiler_creation,
        test_profiler_enable_disable,
        test_profile_block,
        test_profile_block_nested,
        test_profile_decorator,
        test_profile_decorator_multiple_calls,
        test_profile_decorator_with_custom_name,
        test_get_all_function_stats,
        test_get_all_calls,
        test_get_hotspots,
        test_get_slowest_calls,
        test_get_summary,
        test_clear,
        test_disabled_profiler,
        test_flame_graph_generation,
        test_timeline_generation,
        test_export_to_json,
        test_export_to_csv,
        test_global_profiler,
        test_global_profile_block,
        test_profile_with_metadata,
        test_thread_safety,
        test_call_stack_tracking,
        test_multiple_profiler_instances,
        test_print_report,
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
