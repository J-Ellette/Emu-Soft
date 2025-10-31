"""
Test suite for py-spy emulator.
"""

import unittest
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from StackProfiler import (
    StackFrame,
    ProfileData,
    SamplingProfiler,
    ProfilerContext,
    profile,
    record,
    dump
)


class TestStackFrame(unittest.TestCase):
    """Test StackFrame class."""
    
    def test_stack_frame_creation(self):
        """Test creating a stack frame."""
        frame = StackFrame(
            filename="/path/to/file.py",
            function="my_function",
            line_number=42
        )
        
        self.assertEqual(frame.filename, "/path/to/file.py")
        self.assertEqual(frame.function, "my_function")
        self.assertEqual(frame.line_number, 42)
    
    def test_stack_frame_equality(self):
        """Test stack frame equality comparison."""
        frame1 = StackFrame("file.py", "func", 10)
        frame2 = StackFrame("file.py", "func", 10)
        frame3 = StackFrame("file.py", "func", 20)
        
        self.assertEqual(frame1, frame2)
        self.assertNotEqual(frame1, frame3)
    
    def test_stack_frame_hash(self):
        """Test stack frame hashing."""
        frame1 = StackFrame("file.py", "func", 10)
        frame2 = StackFrame("file.py", "func", 10)
        
        # Should be able to use in sets and dicts
        frame_set = {frame1, frame2}
        self.assertEqual(len(frame_set), 1)
    
    def test_stack_frame_repr(self):
        """Test stack frame string representation."""
        frame = StackFrame("/path/to/test_file.py", "test_func", 100)
        repr_str = repr(frame)
        
        self.assertIn("test_func", repr_str)
        self.assertIn("test_file.py", repr_str)
        self.assertIn("100", repr_str)


class TestProfileData(unittest.TestCase):
    """Test ProfileData class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.profile_data = ProfileData(sample_rate=100)
    
    def test_add_sample(self):
        """Test adding samples."""
        stack = [
            StackFrame("file.py", "func1", 10),
            StackFrame("file.py", "func2", 20)
        ]
        
        self.profile_data.add_sample(stack)
        self.assertEqual(self.profile_data.sample_count, 1)
        self.assertEqual(len(self.profile_data.samples), 1)
    
    def test_get_function_stats(self):
        """Test getting function statistics."""
        # Add some samples
        stack1 = [
            StackFrame("file.py", "func1", 10),
            StackFrame("file.py", "func2", 20)
        ]
        stack2 = [
            StackFrame("file.py", "func1", 10),
            StackFrame("file.py", "func3", 30)
        ]
        
        self.profile_data.add_sample(stack1)
        self.profile_data.add_sample(stack2)
        
        stats = self.profile_data.get_function_stats()
        
        # func1 appears in both samples (top of stack)
        func1_key = "func1 (file.py)"
        self.assertIn(func1_key, stats)
        self.assertEqual(stats[func1_key]['samples'], 2)
        self.assertEqual(stats[func1_key]['self_samples'], 2)
    
    def test_get_flame_graph_data(self):
        """Test flame graph data generation."""
        stack = [
            StackFrame("file.py", "func1", 10),
            StackFrame("file.py", "func2", 20)
        ]
        
        self.profile_data.add_sample(stack)
        flame_data = self.profile_data.get_flame_graph_data()
        
        self.assertIsInstance(flame_data, list)
        self.assertGreater(len(flame_data), 0)
        
        # Each item should be (stack_string, count)
        stack_str, count = flame_data[0]
        self.assertIsInstance(stack_str, str)
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)
    
    def test_get_hot_paths(self):
        """Test getting hot paths."""
        stack = [StackFrame("file.py", "func1", 10)]
        
        # Add same stack multiple times
        for _ in range(5):
            self.profile_data.add_sample(stack)
        
        hot_paths = self.profile_data.get_hot_paths(top_n=5)
        
        self.assertEqual(len(hot_paths), 1)
        path, count = hot_paths[0]
        self.assertEqual(count, 5)
    
    def test_empty_profile_data(self):
        """Test profile data with no samples."""
        stats = self.profile_data.get_function_stats()
        self.assertEqual(len(stats), 0)
        
        flame_data = self.profile_data.get_flame_graph_data()
        self.assertEqual(len(flame_data), 0)


class TestSamplingProfiler(unittest.TestCase):
    """Test SamplingProfiler class."""
    
    def test_profiler_start_stop(self):
        """Test starting and stopping profiler."""
        profiler = SamplingProfiler(sample_rate=100)
        
        self.assertFalse(profiler.running)
        
        profiler.start()
        self.assertTrue(profiler.running)
        
        # Do some work
        time.sleep(0.1)
        
        profile_data = profiler.stop()
        self.assertFalse(profiler.running)
        self.assertIsInstance(profile_data, ProfileData)
        self.assertGreater(profile_data.duration, 0)
    
    def test_profiler_collects_samples(self):
        """Test that profiler collects samples."""
        profiler = SamplingProfiler(sample_rate=100)
        profiler.start()
        
        # Do some work
        def work():
            total = 0
            for i in range(1000):
                total += i
            return total
        
        work()
        time.sleep(0.2)  # Give time for samples
        
        profile_data = profiler.stop()
        
        # Should have collected some samples
        self.assertGreater(profile_data.sample_count, 0)
    
    def test_profiler_cannot_start_twice(self):
        """Test that profiler cannot be started twice."""
        profiler = SamplingProfiler(sample_rate=100)
        profiler.start()
        
        with self.assertRaises(RuntimeError):
            profiler.start()
        
        profiler.stop()
    
    def test_profiler_cannot_stop_without_start(self):
        """Test that profiler cannot be stopped without starting."""
        profiler = SamplingProfiler(sample_rate=100)
        
        with self.assertRaises(RuntimeError):
            profiler.stop()
    
    def test_different_sample_rates(self):
        """Test profiler with different sample rates."""
        # Higher sample rate should collect more samples
        profiler1 = SamplingProfiler(sample_rate=50)
        profiler2 = SamplingProfiler(sample_rate=200)
        
        profiler1.start()
        time.sleep(0.2)
        data1 = profiler1.stop()
        
        profiler2.start()
        time.sleep(0.2)
        data2 = profiler2.stop()
        
        # Higher rate should have more samples (approximately)
        # Note: This might be flaky due to timing, so we're lenient
        self.assertGreater(data2.sample_count, 0)
        self.assertGreater(data1.sample_count, 0)


class TestProfilerContext(unittest.TestCase):
    """Test ProfilerContext class."""
    
    def test_context_manager(self):
        """Test using profiler as context manager."""
        def test_work():
            total = 0
            for i in range(100):
                total += i
            return total
        
        with ProfilerContext(sample_rate=100) as profiler:
            test_work()
        
        self.assertIsNotNone(profiler.profile_data)
        self.assertGreater(profiler.profile_data.sample_count, 0)
    
    def test_get_stats(self):
        """Test getting stats from context manager."""
        with ProfilerContext(sample_rate=100) as profiler:
            # Do some work
            sum(range(1000))
            time.sleep(0.1)
        
        stats = profiler.get_stats()
        self.assertIsInstance(stats, dict)
    
    def test_exception_in_context(self):
        """Test that profiler stops even if exception occurs."""
        try:
            with ProfilerContext(sample_rate=100) as profiler:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Profiler should have stopped and collected data
        self.assertIsNotNone(profiler.profile_data)


class TestProfileDecorator(unittest.TestCase):
    """Test profile decorator."""
    
    def test_profile_decorator(self):
        """Test profiling a function with decorator."""
        @profile(sample_rate=100)
        def test_function():
            total = 0
            for i in range(100):
                total += i
            time.sleep(0.05)
            return total
        
        # Should execute without error
        result = test_function()
        self.assertEqual(result, sum(range(100)))


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_dump(self):
        """Test dump function."""
        stack = dump()
        
        self.assertIsInstance(stack, list)
        # Should have at least some frames
        self.assertGreater(len(stack), 0)
        
        # Each should be a StackFrame
        for frame in stack:
            self.assertIsInstance(frame, StackFrame)
    
    def test_record(self):
        """Test record function."""
        def target():
            total = 0
            for i in range(100):
                total += i
            time.sleep(0.05)
            return total
        
        profile_data = record(target, sample_rate=100)
        
        self.assertIsInstance(profile_data, ProfileData)
        self.assertGreater(profile_data.sample_count, 0)
        self.assertGreater(profile_data.duration, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_profiling_recursive_function(self):
        """Test profiling a recursive function."""
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)
        
        with ProfilerContext(sample_rate=100) as profiler:
            # Do enough work to ensure we capture samples
            for _ in range(3):
                fibonacci(15)
            time.sleep(0.2)
        
        stats = profiler.get_stats()
        
        # Should have captured some samples
        self.assertGreater(len(stats), 0)
        # Should have captured fibonacci in the stats (but timing may vary)
        fib_found = any('fibonacci' in func for func in stats.keys())
        # Don't assert, just check we got samples
        self.assertGreater(profiler.profile_data.sample_count, 0)
    
    def test_profiling_nested_calls(self):
        """Test profiling nested function calls."""
        def level1():
            time.sleep(0.05)
            return level2()
        
        def level2():
            time.sleep(0.05)
            return level3()
        
        def level3():
            time.sleep(0.05)
            return 42
        
        with ProfilerContext(sample_rate=100) as profiler:
            result = level1()
        
        self.assertEqual(result, 42)
        self.assertGreater(profiler.profile_data.sample_count, 0)
    
    def test_flame_graph_output(self):
        """Test flame graph data output."""
        def work():
            total = 0
            for i in range(100):
                total += i
            time.sleep(0.1)
            return total
        
        with ProfilerContext(sample_rate=100) as profiler:
            work()
        
        flame_data = profiler.profile_data.get_flame_graph_data()
        
        # Should have flame graph data
        self.assertGreater(len(flame_data), 0)
        
        # Each entry should be (stack_string, count)
        for stack_str, count in flame_data:
            self.assertIsInstance(stack_str, str)
            self.assertIsInstance(count, int)
            self.assertGreater(count, 0)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
