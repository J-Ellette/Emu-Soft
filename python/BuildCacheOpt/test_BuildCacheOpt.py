import unittest
from BuildCacheOpt import BuildCacheOpt

class TestBuildCacheOpt(unittest.TestCase):
    def test_optimize(self):
        cache = BuildCacheOpt(max_size_mb=100)
        cache.add_entry('entry1', 60)
        cache.add_entry('entry2', 60)
        cache.record_hit('entry2')
        to_remove = cache.optimize()
        self.assertIn('entry1', to_remove)

if __name__ == '__main__':
    unittest.main()
