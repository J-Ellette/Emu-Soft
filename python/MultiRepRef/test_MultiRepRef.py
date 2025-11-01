import unittest
from MultiRepRef import MultiRepRef

class TestMultiRepRef(unittest.TestCase):
    def test_track_refactoring(self):
        ref = MultiRepRef()
        ref.add_task('repo1', 'file.py', 'rename function')
        ref.mark_complete('repo1', 'file.py')
        progress = ref.get_progress()
        self.assertEqual(progress['completed'], 1)

if __name__ == '__main__':
    unittest.main()
