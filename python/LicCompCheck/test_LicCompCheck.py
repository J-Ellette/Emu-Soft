import unittest
from LicCompCheck import LicCompCheck

class TestLicCompCheck(unittest.TestCase):
    def test_check_compliance(self):
        checker = LicCompCheck()
        checker.set_policy(allowed=['MIT', 'Apache-2.0'])
        checker.add_component('pkg1', 'MIT')
        checker.add_component('pkg2', 'GPL')
        result = checker.check_compliance()
        self.assertEqual(len(result['violations']), 1)

if __name__ == '__main__':
    unittest.main()
