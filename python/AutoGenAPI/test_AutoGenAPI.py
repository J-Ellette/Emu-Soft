"""Tests for AutoGenAPI"""
import unittest
from AutoGenAPI import AutoGenAPI

class TestAutoGenAPI(unittest.TestCase):
    def setUp(self):
        self.api = AutoGenAPI()
    
    def test_record_request(self):
        self.api.record_request('GET', '/users', response_body={'users': []})
        stats = self.api.get_statistics()
        self.assertEqual(stats['total_endpoints'], 1)
    
    def test_generate_markdown(self):
        self.api.record_request('GET', '/users')
        doc = self.api.generate_markdown()
        self.assertIn('# API Documentation', doc)
        self.assertIn('GET /users', doc)

if __name__ == '__main__':
    unittest.main()
