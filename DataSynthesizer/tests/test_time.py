import unittest
import time
from datetime import datetime


@unittest.mock.patch('time.time', unittest.mock.MagicMock(return_value=datetime(2020, 1, 1, 0, 0, 0, 000000).timestamp()))
class TestPreCheck(unittest.TestCase):
    def test_unittest(self):
        num1 = 3
        num2 = 10
        self.assertEqual(num1+num2, 13)
        
    def test_mock_timestamp(self):
        self.assertEqual(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3],
                         '2020-01-01_00-00-00-000')


if __name__ == '__main__':
    unittest.main()