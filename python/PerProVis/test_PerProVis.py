"""
Developed by PowerShield
"""

#!/usr/bin/env python3
"""
Test suite for PerProVis - Performance Profiling Visualizer

Tests core functionality including:
- Sample collection
- Hotspot detection
- Flame graph generation
- Memory profiling
- Profile comparison
"""

import unittest
import time
from PerProVis import PerProVis, StackFrame, Hotspot


class TestBasicProfiling(unittest.TestCase):
    """Test basic profiling functionality"""
    
    def setUp(self):
        """Set up test profiler"""
        self.profiler = PerProVis(sampling_interval_ms=10)
    
    def test_initialization(self):
        """Test profiler initialization"""
        self.assertEqual(self.profiler.sampling_interval_ms, 10)
        self.assertEqual(self.profiler.get_sample_count(), 0)
        self.assertFalse(self.profiler.is_profiling)
    
    def test_manual_sample_addition(self):
        """Test manually adding samples"""
        stack = [
            ('main', 'test.py', 10),
            ('process', 'test.py', 20),
            ('compute', 'test.py', 30)
        ]
        
        self.profiler.add_sample(stack)
        self.assertEqual(self.profiler.get_sample_count(), 1)
        
        self.profiler.add_sample(stack)
        self.assertEqual(self.profiler.get_sample_count(), 2)
    
    def test_profiling_duration(self):
        """Test profiling duration tracking"""
        self.profiler.start_time = time.time()
        time.sleep(0.1)
        self.profiler.end_time = time.time()
        
        duration = self.profiler.get_profiling_duration()
        self.assertGreater(duration, 0.09)
        self.assertLess(duration, 0.2)
    
    def test_clear_data(self):
        """Test clearing profiling data"""
        stack = [('func1', 'file1.py', 10)]
        self.profiler.add_sample(stack)
        self.assertEqual(self.profiler.get_sample_count(), 1)
        
        self.profiler.clear()
        self.assertEqual(self.profiler.get_sample_count(), 0)


class TestHotspotDetection(unittest.TestCase):
    """Test hotspot detection"""
    
    def setUp(self):
        """Set up test profiler with sample data"""
        self.profiler = PerProVis()
        self.profiler.start_time = time.time()
        
        # Add samples simulating a program with hotspots
        # Function A appears in 50% of samples
        # Function B appears in 30% of samples
        # Function C appears in 20% of samples
        
        for i in range(50):
            self.profiler.add_sample([
                ('main', 'main.py', 10),
                ('function_a', 'module.py', 20)
            ])
        
        for i in range(30):
            self.profiler.add_sample([
                ('main', 'main.py', 10),
                ('function_b', 'module.py', 30)
            ])
        
        for i in range(20):
            self.profiler.add_sample([
                ('main', 'main.py', 10),
                ('function_c', 'module.py', 40)
            ])
        
        self.profiler.end_time = time.time()
    
    def test_find_hotspots(self):
        """Test finding performance hotspots"""
        hotspots = self.profiler.find_hotspots(top_n=5)
        
        self.assertGreater(len(hotspots), 0)
        self.assertLessEqual(len(hotspots), 5)
        
        # Hotspots should be sorted by sample count
        for i in range(len(hotspots) - 1):
            self.assertGreaterEqual(
                hotspots[i].sample_count,
                hotspots[i + 1].sample_count
            )
    
    def test_hotspot_percentages(self):
        """Test hotspot percentage calculation"""
        hotspots = self.profiler.find_hotspots(top_n=10)
        
        # Main should appear in all 100 samples
        main_hotspot = next((h for h in hotspots if h.function_name == 'main'), None)
        self.assertIsNotNone(main_hotspot)
        self.assertEqual(main_hotspot.sample_count, 100)
        self.assertAlmostEqual(main_hotspot.percentage, 100.0, places=1)
    
    def test_hotspot_timing(self):
        """Test hotspot timing calculations"""
        hotspots = self.profiler.find_hotspots(top_n=10)
        
        for hotspot in hotspots:
            self.assertGreater(hotspot.total_time_ms, 0)
            self.assertGreater(hotspot.sample_count, 0)
            avg_time = hotspot.average_time_ms()
            self.assertGreater(avg_time, 0)


class TestFlameGraph(unittest.TestCase):
    """Test flame graph generation"""
    
    def setUp(self):
        """Set up test profiler"""
        self.profiler = PerProVis()
    
    def test_flame_graph_generation(self):
        """Test generating flame graph"""
        # Add samples with nested calls
        self.profiler.add_sample([
            ('main', 'main.py', 1),
            ('func_a', 'module.py', 10),
            ('func_b', 'module.py', 20)
        ])
        
        self.profiler.add_sample([
            ('main', 'main.py', 1),
            ('func_a', 'module.py', 10),
            ('func_c', 'module.py', 30)
        ])
        
        flame_graph = self.profiler.generate_flame_graph()
        
        self.assertEqual(flame_graph.name, 'root')
        self.assertEqual(flame_graph.value, 2)  # 2 samples
        self.assertGreater(len(flame_graph.children), 0)
    
    def test_flame_graph_json(self):
        """Test flame graph JSON export"""
        self.profiler.add_sample([
            ('main', 'main.py', 1),
            ('process', 'module.py', 10)
        ])
        
        json_str = self.profiler.get_flame_graph_json()
        self.assertIsInstance(json_str, str)
        self.assertIn('root', json_str)
        self.assertIn('value', json_str)
    
    def test_flame_graph_structure(self):
        """Test flame graph structural properties"""
        # Add multiple samples with same initial path
        for i in range(10):
            self.profiler.add_sample([
                ('main', 'main.py', 1),
                ('process', 'module.py', 10)
            ])
        
        flame_graph = self.profiler.generate_flame_graph()
        
        # Root should have value equal to total samples
        self.assertEqual(flame_graph.value, 10)
        
        # Convert to dict to check structure
        graph_dict = flame_graph.to_dict()
        self.assertIn('name', graph_dict)
        self.assertIn('value', graph_dict)


class TestCallGraph(unittest.TestCase):
    """Test call graph generation"""
    
    def setUp(self):
        """Set up test profiler"""
        self.profiler = PerProVis()
    
    def test_call_graph_generation(self):
        """Test generating call graph"""
        # Add samples showing call relationships
        self.profiler.add_sample([
            ('main', 'main.py', 1),
            ('process', 'module.py', 10),
            ('helper', 'module.py', 20)
        ])
        
        call_graph = self.profiler.get_call_graph()
        
        self.assertIsInstance(call_graph, dict)
        self.assertGreater(len(call_graph), 0)
    
    def test_call_graph_relationships(self):
        """Test call graph caller-callee relationships"""
        self.profiler.add_sample([
            ('func_a', 'module.py', 10),
            ('func_b', 'module.py', 20),
            ('func_c', 'module.py', 30)
        ])
        
        call_graph = self.profiler.get_call_graph()
        
        # func_a should call func_b
        func_a_key = 'func_a (module.py:10)'
        self.assertIn(func_a_key, call_graph)
        
        callees = call_graph[func_a_key]
        self.assertIsInstance(callees, list)


class TestTimeSeries(unittest.TestCase):
    """Test time-series data generation"""
    
    def setUp(self):
        """Set up test profiler"""
        self.profiler = PerProVis()
    
    def test_time_series_generation(self):
        """Test generating time-series data"""
        # Add samples at different times
        base_time = time.time()
        
        for i in range(10):
            self.profiler.add_sample([('func', 'file.py', 1)])
        
        time_series = self.profiler.get_time_series(bucket_size_ms=100)
        
        self.assertIsInstance(time_series, list)
        self.assertGreater(len(time_series), 0)
    
    def test_time_series_buckets(self):
        """Test time-series bucket structure"""
        self.profiler.add_sample([('func', 'file.py', 1)])
        
        time_series = self.profiler.get_time_series(bucket_size_ms=50)
        
        for bucket in time_series:
            self.assertIn('time_ms', bucket)
            self.assertIn('sample_count', bucket)
            self.assertGreaterEqual(bucket['sample_count'], 0)


class TestMemoryProfiling(unittest.TestCase):
    """Test memory profiling functionality"""
    
    def setUp(self):
        """Set up test profiler"""
        self.profiler = PerProVis()
    
    def test_memory_snapshot_addition(self):
        """Test adding memory snapshots"""
        self.profiler.add_memory_snapshot(
            total_bytes=1024 * 1024,
            allocations={'site1': 512 * 1024, 'site2': 512 * 1024}
        )
        
        self.assertEqual(len(self.profiler.memory_snapshots), 1)
    
    def test_memory_usage_over_time(self):
        """Test memory usage tracking"""
        # Add snapshots with increasing memory
        for i in range(5):
            self.profiler.add_memory_snapshot(
                total_bytes=(i + 1) * 1024 * 1024
            )
        
        usage = self.profiler.get_memory_usage_over_time()
        
        self.assertEqual(len(usage), 5)
        
        # Memory should be increasing
        for i in range(len(usage) - 1):
            self.assertLess(usage[i]['total_bytes'], usage[i + 1]['total_bytes'])
    
    def test_memory_leak_detection(self):
        """Test memory leak detection"""
        # Simulate a memory leak
        for i in range(10):
            allocations = {
                'leaky_function': i * 200 * 1024,  # Growing
                'stable_function': 100 * 1024       # Stable
            }
            self.profiler.add_memory_snapshot(
                total_bytes=sum(allocations.values()),
                allocations=allocations
            )
        
        leaks = self.profiler.find_memory_leaks()
        
        self.assertGreater(len(leaks), 0)
        
        # leaky_function should be detected
        leak_sites = [leak['allocation_site'] for leak in leaks]
        self.assertIn('leaky_function', leak_sites)
    
    def test_memory_leak_threshold(self):
        """Test memory leak detection threshold"""
        # Add small growth (under threshold)
        for i in range(5):
            self.profiler.add_memory_snapshot(
                total_bytes=1024 * 1024,
                allocations={'small_growth': i * 1024}
            )
        
        leaks = self.profiler.find_memory_leaks()
        
        # Should not detect small growth
        self.assertEqual(len(leaks), 0)


class TestProfileComparison(unittest.TestCase):
    """Test profile comparison"""
    
    def setUp(self):
        """Set up test profilers"""
        self.baseline = PerProVis()
        self.current = PerProVis()
        
        # Baseline profile
        for i in range(100):
            self.baseline.add_sample([
                ('main', 'main.py', 1),
                ('func_a', 'module.py', 10)
            ])
        
        # Current profile with different distribution
        for i in range(50):
            self.current.add_sample([
                ('main', 'main.py', 1),
                ('func_a', 'module.py', 10)
            ])
        
        for i in range(50):
            self.current.add_sample([
                ('main', 'main.py', 1),
                ('func_b', 'module.py', 20)
            ])
    
    def test_profile_comparison(self):
        """Test comparing two profiles"""
        comparison = self.baseline.compare_profiles(self.current)
        
        self.assertIn('baseline_samples', comparison)
        self.assertIn('current_samples', comparison)
        self.assertIn('differences', comparison)
        
        self.assertEqual(comparison['baseline_samples'], 100)
        self.assertEqual(comparison['current_samples'], 100)
    
    def test_comparison_differences(self):
        """Test detecting differences in profiles"""
        comparison = self.baseline.compare_profiles(self.current)
        
        differences = comparison['differences']
        self.assertGreater(len(differences), 0)
        
        # func_b should be marked as new
        func_b_diff = next(
            (d for d in differences if 'func_b' in d['function']),
            None
        )
        self.assertIsNotNone(func_b_diff)
        if func_b_diff:
            self.assertEqual(func_b_diff.get('status'), 'new')


class TestExport(unittest.TestCase):
    """Test profile export"""
    
    def setUp(self):
        """Set up test profiler"""
        self.profiler = PerProVis()
        self.profiler.start_time = time.time()
        
        # Add some samples
        for i in range(10):
            self.profiler.add_sample([
                ('main', 'main.py', 1),
                ('process', 'module.py', 10)
            ])
        
        self.profiler.end_time = time.time()
    
    def test_export_profile(self):
        """Test exporting complete profile"""
        exported = self.profiler.export_profile()
        
        self.assertIn('sample_count', exported)
        self.assertIn('duration_seconds', exported)
        self.assertIn('hotspots', exported)
        self.assertIn('flame_graph', exported)
        self.assertIn('time_series', exported)
        
        self.assertEqual(exported['sample_count'], 10)
        self.assertGreater(exported['duration_seconds'], 0)
    
    def test_export_hotspots(self):
        """Test exported hotspot data"""
        exported = self.profiler.export_profile()
        
        hotspots = exported['hotspots']
        self.assertIsInstance(hotspots, list)
        self.assertGreater(len(hotspots), 0)
        
        for hotspot in hotspots:
            self.assertIn('function', hotspot)
            self.assertIn('filename', hotspot)
            self.assertIn('sample_count', hotspot)
            self.assertIn('percentage', hotspot)


class TestStackFrame(unittest.TestCase):
    """Test StackFrame class"""
    
    def test_stack_frame_equality(self):
        """Test stack frame equality"""
        frame1 = StackFrame('func', 'file.py', 10)
        frame2 = StackFrame('func', 'file.py', 10)
        frame3 = StackFrame('func', 'file.py', 20)
        
        self.assertEqual(frame1, frame2)
        self.assertNotEqual(frame1, frame3)
    
    def test_stack_frame_hash(self):
        """Test stack frame hashing"""
        frame1 = StackFrame('func', 'file.py', 10)
        frame2 = StackFrame('func', 'file.py', 10)
        
        # Same frames should have same hash
        self.assertEqual(hash(frame1), hash(frame2))
        
        # Can be used in sets
        frame_set = {frame1, frame2}
        self.assertEqual(len(frame_set), 1)
    
    def test_stack_frame_to_string(self):
        """Test stack frame string representation"""
        frame = StackFrame('my_function', 'module.py', 42)
        string_repr = frame.to_string()
        
        self.assertIn('my_function', string_repr)
        self.assertIn('module.py', string_repr)
        self.assertIn('42', string_repr)


if __name__ == '__main__':
    unittest.main()
