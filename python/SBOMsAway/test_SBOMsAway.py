import unittest
from SBOMsAway import SBOMsAway

class TestSBOMsAway(unittest.TestCase):
    def test_add_component(self):
        sbom = SBOMsAway()
        sbom.add_component('requests', '2.28.0', 'Apache-2.0')
        stats = sbom.get_statistics()
        self.assertEqual(stats['total_components'], 1)

if __name__ == '__main__':
    unittest.main()
