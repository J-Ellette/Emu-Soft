import unittest
from TransDepVulScan import TransDepVulScan

class TestTransDepVulScan(unittest.TestCase):
    def test_scan(self):
        scanner = TransDepVulScan()
        scanner.add_dependency('myapp', ['requests'])
        scanner.add_vulnerability('requests', 'CVE-2023-1234', 'HIGH', 'Test vuln')
        result = scanner.scan('myapp')
        self.assertIn('requests', result)

if __name__ == '__main__':
    unittest.main()
