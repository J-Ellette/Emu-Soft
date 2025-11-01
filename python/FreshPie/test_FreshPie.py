"""Tests for FreshPie"""

import unittest
from FreshPie import FreshPie

class TestFreshPie(unittest.TestCase):
    """Test FreshPie"""
    
    def setUp(self):
        """Set up test"""
        self.tool = FreshPie()
    
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
