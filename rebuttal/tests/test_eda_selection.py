import unittest
import numpy as np
from rebuttal.eda_selection import MomentAccumulator, fit_pca, score_response, select_indices
class SelectionTests(unittest.TestCase):
 def test_streaming_covariance_equals_direct(self):
  x=np.random.default_rng(0).normal(size=(61,7));m=MomentAccumulator(7)
  for part in np.array_split(x,8):m.add(part)
  np.testing.assert_allclose(m.mean,x.mean(0));np.testing.assert_allclose(m.covariance(),np.cov(x,rowvar=False),atol=1e-14)
 def test_pca_whitened_distance_and_quantile(self):
  x=np.random.default_rng(1).normal(size=(50,4));m=MomentAccumulator(4);m.add(x);state=fit_pca(m,3)
  y=np.random.default_rng(2).normal(size=(9,4));z=(y-state['mean'])@state['components']
  expected=np.quantile((z*z/state['eigenvalues']).sum(1),.9)
  self.assertAlmostEqual(score_response(y,state,.9),expected)
 def test_selection_is_high_score_and_ties_deterministic(self):
  self.assertEqual(select_indices([2,1,5,2],2),[2,0])
