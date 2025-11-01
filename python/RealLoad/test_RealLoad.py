import unittest
from RealLoad import RealLoad

class TestRealLoad(unittest.TestCase):
    def test_generate_traffic(self):
        load = RealLoad()
        load.add_pattern('steady', 10, 5)
        traffic = load.generate_traffic('steady')
        self.assertEqual(len(traffic), 50)

if __name__ == '__main__':
    unittest.main()
