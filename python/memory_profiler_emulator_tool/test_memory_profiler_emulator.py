"""
Test suite for memory_profiler emulator.
"""

import unittest
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from memory_profiler_emulator import (
    MemorySnapshot,
    LineMemoryStats,
    FunctionMemoryProfile,
    MemoryProfiler,
    LineProfiler,
    MemoryUsageMonitor,
    profile,
    memory_usage,
    show_results
)


class TestMemorySnapshot(unittest.TestCase):
    """Test MemorySnapshot class."""
    
    def test_memory_snapshot_creation(self):
        """Test creating a memory snapshot."""
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_memory=1024 * 1024 * 100,  # 100 MB
            line_number=42,
            filename="test.py",
            function="test_func"
        )
        
        self.assertEqual(snapshot.line_number, 42)
        self.assertEqual(snapshot.filename, "test.py")
        self.assertEqual(snapshot.function, "test_func")
        self.assertGreater(snapshot.timestamp, 0)
    
    def test_memory_mb_conversion(self):
        """Test memory conversion to MB."""
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_memory=2 * 1024 * 1024  # 2 MB in bytes
        )
        
        self.assertAlmostEqual(snapshot.memory_mb(), 2.0, places=1)


class TestLineMemoryStats(unittest.TestCase):
    """Test LineMemoryStats class."""
    
    def test_line_memory_stats_creation(self):
        """Test creating line memory stats."""
        stats = LineMemoryStats(
            line_number=10,
            filename="test.py",
            code="x = [0] * 1000"
        )
        
        self.assertEqual(stats.line_number, 10)
        self.assertEqual(stats.filename, "test.py")
        self.assertEqual(stats.code, "x = [0] * 1000")
        self.assertEqual(stats.occurrences, 0)
    
    def test_avg_memory_calculation(self):
        """Test average memory calculation."""
        stats = LineMemoryStats(
            line_number=10,
            filename="test.py",
            code="test"
        )
        
        # Add some memory usage data
        stats.memory_usage = [
            1 * 1024 * 1024,  # 1 MB
            2 * 1024 * 1024,  # 2 MB
            3 * 1024 * 1024   # 3 MB
        ]
        
        avg = stats.avg_memory_mb()
        self.assertAlmostEqual(avg, 2.0, places=1)
    
    def test_max_memory_calculation(self):
        """Test maximum memory calculation."""
        stats = LineMemoryStats(
            line_number=10,
            filename="test.py",
            code="test"
        )
        
        stats.memory_usage = [
            1 * 1024 * 1024,  # 1 MB
            5 * 1024 * 1024,  # 5 MB
            2 * 1024 * 1024   # 2 MB
        ]
        
        max_mem = stats.max_memory_mb()
        self.assertAlmostEqual(max_mem, 5.0, places=1)
    
    def test_empty_stats(self):
        """Test stats with no data."""
        stats = LineMemoryStats(
            line_number=10,
            filename="test.py",
            code="test"
        )
        
        self.assertEqual(stats.avg_memory_mb(), 0.0)
        self.assertEqual(stats.max_memory_mb(), 0.0)
        self.assertEqual(stats.avg_increment_mb(), 0.0)


class TestFunctionMemoryProfile(unittest.TestCase):
    """Test FunctionMemoryProfile class."""
    
    def test_function_profile_creation(self):
        """Test creating a function memory profile."""
        profile = FunctionMemoryProfile(
            function_name="test_func",
            filename="test.py"
        )
        
        self.assertEqual(profile.function_name, "test_func")
        self.assertEqual(profile.filename, "test.py")
        self.assertEqual(profile.start_memory, 0)
        self.assertEqual(profile.end_memory, 0)
    
    def test_total_increment_calculation(self):
        """Test total memory increment calculation."""
        profile = FunctionMemoryProfile(
            function_name="test_func",
            filename="test.py"
        )
        
        profile.start_memory = 10 * 1024 * 1024  # 10 MB
        profile.end_memory = 15 * 1024 * 1024    # 15 MB
        
        increment = profile.total_increment_mb()
        self.assertAlmostEqual(increment, 5.0, places=1)
    
    def test_peak_memory(self):
        """Test peak memory tracking."""
        profile = FunctionMemoryProfile(
            function_name="test_func",
            filename="test.py"
        )
        
        profile.peak_memory = 20 * 1024 * 1024  # 20 MB
        
        peak = profile.peak_mb()
        self.assertAlmostEqual(peak, 20.0, places=1)


class TestMemoryProfiler(unittest.TestCase):
    """Test MemoryProfiler class."""
    
    def test_profiler_enable_disable(self):
        """Test enabling and disabling profiler."""
        profiler = MemoryProfiler(backend='tracemalloc')
        
        self.assertFalse(profiler.enabled)
        
        profiler.enable()
        self.assertTrue(profiler.enabled)
        
        profiler.disable()
        self.assertFalse(profiler.enabled)
    
    def test_snapshot(self):
        """Test taking memory snapshots."""
        profiler = MemoryProfiler(backend='tracemalloc')
        profiler.enable()
        
        snapshot = profiler.snapshot(
            line_number=10,
            filename="test.py",
            function="test_func"
        )
        
        self.assertIsInstance(snapshot, MemorySnapshot)
        self.assertEqual(snapshot.line_number, 10)
        self.assertEqual(len(profiler.snapshots), 1)
        
        profiler.disable()
    
    def test_add_line_stats(self):
        """Test adding line statistics."""
        profiler = MemoryProfiler(backend='tracemalloc')
        
        profiler.add_line_stats(
            filename="test.py",
            line_number=10,
            memory_usage=1024 * 1024,  # 1 MB
            memory_increment=512 * 1024  # 512 KB
        )
        
        key = ("test.py", 10)
        self.assertIn(key, profiler.line_stats)
        
        stats = profiler.line_stats[key]
        self.assertEqual(stats.occurrences, 1)
        self.assertEqual(len(stats.memory_usage), 1)
    
    def test_reset(self):
        """Test resetting profiler."""
        profiler = MemoryProfiler(backend='tracemalloc')
        profiler.enable()
        
        profiler.snapshot()
        profiler.add_line_stats("test.py", 10, 1024)
        
        self.assertGreater(len(profiler.snapshots), 0)
        self.assertGreater(len(profiler.line_stats), 0)
        
        profiler.reset()
        
        self.assertEqual(len(profiler.snapshots), 0)
        self.assertEqual(len(profiler.line_stats), 0)
        
        profiler.disable()


class TestLineProfiler(unittest.TestCase):
    """Test LineProfiler class."""
    
    def test_line_profiler_decorator(self):
        """Test using LineProfiler as decorator."""
        profiler = LineProfiler(backend='tracemalloc')
        
        @profiler
        def test_function():
            data = [0] * 100
            return sum(data)
        
        result = test_function()
        
        self.assertEqual(result, 0)
        self.assertIn("test_function", profiler.function_profiles)
    
    def test_profile_function(self):
        """Test profiling a function."""
        profiler = LineProfiler(backend='tracemalloc')
        
        def test_function():
            x = [0] * 1000
            y = [1] * 1000
            return sum(x) + sum(y)
        
        result = profiler.profile_function(test_function)
        
        self.assertEqual(result, 1000)
        self.assertIn("test_function", profiler.function_profiles)
        
        profile = profiler.function_profiles["test_function"]
        self.assertGreater(profile.end_memory, 0)


class TestProfileDecorator(unittest.TestCase):
    """Test profile decorator."""
    
    def test_profile_decorator(self):
        """Test @profile decorator."""
        @profile
        def test_function():
            data = [0] * 100
            result = sum(data)
            return result
        
        result = test_function()
        self.assertEqual(result, 0)
    
    def test_profile_with_backend(self):
        """Test @profile decorator with backend parameter."""
        @profile(backend='tracemalloc')
        def test_function():
            data = [0] * 100
            return sum(data)
        
        result = test_function()
        self.assertEqual(result, 0)


class TestMemoryUsageMonitor(unittest.TestCase):
    """Test MemoryUsageMonitor class."""
    
    def test_monitor_start_stop(self):
        """Test starting and stopping monitor."""
        monitor = MemoryUsageMonitor(interval=0.1)
        
        self.assertFalse(monitor.running)
        
        monitor.start()
        self.assertTrue(monitor.running)
        
        # Take some samples
        for _ in range(3):
            monitor.sample()
            time.sleep(0.05)
        
        snapshots = monitor.stop()
        
        self.assertFalse(monitor.running)
        self.assertEqual(len(snapshots), 3)
    
    def test_monitor_samples(self):
        """Test that monitor collects samples."""
        monitor = MemoryUsageMonitor(interval=0.1)
        monitor.start()
        
        elapsed, memory = monitor.sample()
        
        self.assertGreaterEqual(elapsed, 0)
        self.assertGreaterEqual(memory, 0)
        
        monitor.stop()
    
    def test_get_peak_memory(self):
        """Test getting peak memory."""
        monitor = MemoryUsageMonitor(interval=0.1)
        monitor.start()
        
        # Take samples
        monitor.sample()
        data = [0] * 100000  # Allocate some memory
        monitor.sample()
        del data
        monitor.sample()
        
        monitor.stop()
        
        peak = monitor.get_peak_memory()
        self.assertGreater(peak, 0)
    
    def test_get_memory_timeline(self):
        """Test getting memory timeline."""
        monitor = MemoryUsageMonitor(interval=0.1)
        monitor.start()
        
        for _ in range(3):
            monitor.sample()
        
        timeline = monitor.get_memory_timeline()
        
        self.assertEqual(len(timeline), 3)
        # Each entry should be (timestamp, memory)
        for elapsed, memory in timeline:
            self.assertGreaterEqual(elapsed, 0)
            self.assertGreaterEqual(memory, 0)
        
        monitor.stop()


class TestMemoryUsageFunction(unittest.TestCase):
    """Test memory_usage function."""
    
    def test_memory_usage(self):
        """Test memory_usage function."""
        def target():
            data = [0] * 10000
            time.sleep(0.1)
            return sum(data)
        
        samples = memory_usage(target, interval=0.05, timeout=0.5)
        
        self.assertIsInstance(samples, list)
        self.assertGreater(len(samples), 0)
        
        # All samples should be non-negative
        for sample in samples:
            self.assertGreaterEqual(sample, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_full_profiling_workflow(self):
        """Test complete profiling workflow."""
        profiler = LineProfiler(backend='tracemalloc')
        
        def allocate_memory():
            # Allocate memory in steps
            data1 = [0] * 1000
            data2 = [1] * 2000
            result = sum(data1) + sum(data2)
            return result
        
        result = profiler.profile_function(allocate_memory)
        
        self.assertEqual(result, 2000)
        
        # Check profile was created
        self.assertIn("allocate_memory", profiler.function_profiles)
        
        profile = profiler.function_profiles["allocate_memory"]
        self.assertGreaterEqual(profile.end_memory, profile.start_memory)
    
    def test_memory_growth_detection(self):
        """Test detecting memory growth."""
        @profile
        def growing_function():
            data = []
            for i in range(100):
                data.append([0] * 100)
            return len(data)
        
        result = growing_function()
        self.assertEqual(result, 100)
    
    def test_show_results(self):
        """Test show_results function."""
        def test_func():
            x = [0] * 100
            return sum(x)
        
        result = show_results(test_func)
        self.assertEqual(result, 0)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
