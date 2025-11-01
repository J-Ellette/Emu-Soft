import unittest
from APICon import APICon

class TestAPICon(unittest.TestCase):
    def test_validate_request(self):
        api = APICon()
        api.add_contract('/users', 'POST', {'required': ['name']}, {})
        valid = api.validate_request('/users', 'POST', {'name': 'John'})
        self.assertTrue(valid)

if __name__ == '__main__':
    unittest.main()
