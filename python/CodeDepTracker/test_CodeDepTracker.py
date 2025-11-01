import unittest
from CodeDepTracker import CodeDepTracker

class TestCodeDepTracker(unittest.TestCase):
    def test_track_usage(self):
        tracker = CodeDepTracker()
        tracker.mark_deprecated('old_func', '1.0', 'new_func')
        tracker.record_usage('old_func', 'file.py:10')
        report = tracker.get_report()
        self.assertIn('old_func', report)

if __name__ == '__main__':
    unittest.main()
