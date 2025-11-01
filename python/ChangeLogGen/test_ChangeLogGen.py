"""Tests for ChangeLogGen"""
import unittest
from ChangeLogGen import ChangeLogGen

class TestChangeLogGen(unittest.TestCase):
    def setUp(self):
        self.gen = ChangeLogGen()
    
    def test_add_commit(self):
        self.gen.add_commit('abc123', 'feat: add new feature')
        stats = self.gen.get_statistics()
        self.assertEqual(stats['total_commits'], 1)
    
    def test_classify_feature(self):
        self.gen.add_commit('abc123', 'feat: new feature')
        self.assertEqual(self.gen.entries[0].type, 'feature')
    
    def test_generate_changelog(self):
        self.gen.add_commit('abc123', 'feat: new feature')
        changelog = self.gen.generate_changelog('1.0.0')
        self.assertIn('Version 1.0.0', changelog)

if __name__ == '__main__':
    unittest.main()
