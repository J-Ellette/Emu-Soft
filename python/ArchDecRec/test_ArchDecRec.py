"""Tests for ArchDecRec"""
import unittest
from ArchDecRec import ArchDecRec

class TestArchDecRec(unittest.TestCase):
    def setUp(self):
        self.adr = ArchDecRec()
    
    def test_create_adr(self):
        num = self.adr.create_adr('Use microservices', 'Need scalability', 
                                  'Use microservices', 'Better scaling')
        self.assertEqual(num, 1)
    
    def test_get_adr(self):
        self.adr.create_adr('Test', 'ctx', 'dec', 'cons')
        adr = self.adr.get_adr(1)
        self.assertIsNotNone(adr)
        self.assertEqual(adr.title, 'Test')
    
    def test_update_status(self):
        num = self.adr.create_adr('Test', 'ctx', 'dec', 'cons')
        self.adr.update_status(num, 'accepted')
        adr = self.adr.get_adr(num)
        self.assertEqual(adr.status, 'accepted')
    
    def test_generate_markdown(self):
        num = self.adr.create_adr('Test ADR', 'context', 'decision', 'consequences')
        md = self.adr.generate_markdown(num)
        self.assertIn('# ADR 1', md)
        self.assertIn('Test ADR', md)

if __name__ == '__main__':
    unittest.main()
