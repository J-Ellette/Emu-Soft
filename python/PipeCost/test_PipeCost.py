import unittest
from PipeCost import PipeCost

class TestPipeCost(unittest.TestCase):
    def test_cost_calculation(self):
        cost = PipeCost()
        cost.add_run('build', 10, 0.5)
        total = cost.get_total_cost()
        self.assertEqual(total, 5.0)

if __name__ == '__main__':
    unittest.main()
