import unittest
from Chaos import Chaos

class TestChaos(unittest.TestCase):
    def test_add_scenario(self):
        chaos = Chaos()
        chaos.add_scenario('network_delay', 'Add network delay', lambda: None)
        stats = chaos.get_statistics()
        self.assertEqual(stats['total_scenarios'], 1)

if __name__ == '__main__':
    unittest.main()
