import unittest
import numpy as np
from followspec.rev5_analysis import rank_correlation, amortize

class AnalysisTests(unittest.TestCase):
    def test_rank_not_magnitude(self):
        r=rank_correlation(np.arange(8), -np.exp(np.arange(8)), draws=100)
        self.assertAlmostEqual(r['rho'],-1.)
        self.assertAlmostEqual(r['ci95'][1],-1.)
    def test_constant_undefined(self):
        self.assertIsNone(rank_correlation([1,1,1],[1,2,3])['rho'])
    def test_amortization_counts_batch_once(self):
        r=amortize(np.full((3,4),2.),np.full((3,4),4.),32,1,draws=100)
        self.assertEqual(r['seconds_saved_per_request']['mean'],.25)
        self.assertEqual(r['requests']['mean'],14400.)
    def test_regression_does_not_break_even(self):
        r=amortize(np.full((3,4),4.),np.full((3,4),2.),32,1,draws=100)
        self.assertIsNone(r['requests']['mean'])
        self.assertEqual(r['positive_savings_fraction'],0.)
