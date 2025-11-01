import unittest
from DataMig import DataMig

class TestDataMig(unittest.TestCase):
    def test_check_rollback(self):
        mig = DataMig()
        mig.add_migration('001', 'CREATE TABLE users', 'DROP TABLE users')
        mig.add_migration('002', 'ALTER TABLE users ADD COLUMN email', None)
        result = mig.check_rollback_safety()
        self.assertEqual(len(result['safe']), 1)
        self.assertEqual(len(result['unsafe']), 1)

if __name__ == '__main__':
    unittest.main()
