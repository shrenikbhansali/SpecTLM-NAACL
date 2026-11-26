import unittest
import numpy as np
from rebuttal.planner_analysis import deployment_ratio


class PlannerAnalysisTests(unittest.TestCase):
    def test_ratio_of_macro_effects(self):
        rows=np.array([[.9,.7,.4,.5],[.9,.3,.4,.7]])
        # Mean(d-b)=.1; mean(d-a)=-.3. Mean of per-query ratios would be -.75.
        r=deployment_ratio(rows)
        self.assertAlmostEqual(r['mean'],-1/3)
        self.assertEqual(r['undefined_draws'],0)

    def test_undefined_ratio_is_not_zero(self):
        r=deployment_ratio(np.array([[.5,.2,.3,.5]]))
        self.assertIsNone(r['mean']);self.assertIsNone(r['ci95']);self.assertEqual(r['undefined_draws'],10000)
