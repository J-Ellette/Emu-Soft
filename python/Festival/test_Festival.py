"""Tests for Festival"""

import unittest
from Festival import Festival

class TestFestival(unittest.TestCase):
    """Test Festival"""
    
    def setUp(self):
        """Set up test"""
        self.tool = Festival()
    
    def test_process(self):
        """Test processing"""
        result = self.tool.process('test_item')
        self.assertTrue(result)
    
    def test_get_statistics(self):
        """Test statistics"""
        self.tool.process('item1')
        self.tool.process('item2')
        stats = self.tool.get_statistics()
        self.assertEqual(stats['total_processed'], 2)

if __name__ == '__main__':
    unittest.main()
