import unittest
from rebuttal.e8_lite import apportioned_counts, replaced_indices


class E8LiteTests(unittest.TestCase):
    def test_same_language_proportions_and_exact_totals(self):
        weights={'arb':5,'eng':3,'fra':1,'spa':1,'tha':1,'vie':1}
        for n in [128,4000]:
            x=apportioned_counts(weights,n)
            self.assertEqual(sum(x.values()),n)
            self.assertTrue(all(abs(x[k]-n*v/12)<=1 for k,v in weights.items()))

    def test_fixed_uniform_replacement(self):
        x=replaced_indices(16000,4000)
        self.assertEqual(len(x),4000);self.assertEqual(len(set(x)),4000)
        self.assertEqual(x,replaced_indices(16000,4000))
        self.assertEqual(x,sorted(x))
