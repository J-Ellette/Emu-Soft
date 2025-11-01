import unittest
from FlakyTest import FlakyTest

class TestFlakyTest(unittest.TestCase):
    def test_detect_flaky(self):
        detector = FlakyTest()
        detector.record_result('test1', True, 1)
        detector.record_result('test1', False, 2)
        detector.record_result('test1', True, 3)
        flaky = detector.detect_flaky()
        self.assertIn('test1', flaky)

if __name__ == '__main__':
    unittest.main()
