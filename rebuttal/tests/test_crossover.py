import unittest
import numpy as np
from rebuttal.crossover import contrasts, reduce_cells


class CrossoverTests(unittest.TestCase):
    def test_asymmetric_cells_and_interaction(self):
        got = contrasts(np.array([.8, .5, .6, .7]))
        self.assertAlmostEqual(got['feature'], 0.)
        self.assertAlmostEqual(got['policy'], -.1)
        self.assertAlmostEqual(got['interaction'], .4)
        self.assertAlmostEqual(got['d-b'], .2)
        self.assertAlmostEqual(got['d-c'], .1)
        self.assertAlmostEqual(got['feature'] + got['policy'], got['d-a'])

    def test_pairing_preserves_identical_difference(self):
        cells = np.array([[.8,.7,.6,.5], [.4,.3,.2,.1]])
        got = reduce_cells(cells, draws=1000)
        np.testing.assert_allclose(got['d-a']['ci95'], [-.3, -.3], atol=1e-15)
        np.testing.assert_allclose(got['interaction']['ci95'], [0., 0.], atol=1e-15)
        self.assertLess(got['_max_additivity_error'], 1e-14)

    def test_zero_denominator_is_undefined_not_zero(self):
        got = reduce_cells(np.array([[.5,.2,.8,.5]]), draws=100)
        self.assertIsNone(got['feature_share']['mean'])
        self.assertIsNone(got['feature_share']['ci95'])
        self.assertEqual(got['feature_share']['undefined_draws'], 100)

    def test_invalid_shape_and_nonfinite_rejected(self):
        for cells in [np.zeros((2,3)), np.array([[0.,0.,np.nan,0.]])]:
            with self.assertRaises(ValueError):
                reduce_cells(cells)


if __name__ == '__main__':
    unittest.main()
