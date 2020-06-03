import unittest
from DataSynthesizer.lib.utils import normalize_given_distribution


class TestDS(unittest.TestCase):
    def test_unittest(self):
        num1 = 3
        num2 = 10
        self.assertEqual(num1+num2, 13)

    def test_normalize_given_distribution(self):
        nums = [1, 2, 19]
        res = normalize_given_distribution(nums)
        self.assertEqual(sum(res), 1)
        self.assertEqual(res[0] * 2, res[1])
    


if __name__ == '__main__':
    unittest.main()