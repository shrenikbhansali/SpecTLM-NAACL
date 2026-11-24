import unittest
from rebuttal.reduce_e2 import contrast


def rows(acceptance):
    return [{'prompt_id': str(i), 'per_step_drafted': [4, 4],
             'per_step_accepted': [a, a]} for i, a in enumerate(acceptance)]


class ReductionTests(unittest.TestCase):
    def test_bootstrap_pairs_seed_and_query(self):
        base = {0: rows([0, 1, 2]), 1: rows([1, 2, 3])}
        new = {0: rows([1, 2, 3]), 1: rows([2, 3, 4])}
        r = contrast(base, new)
        self.assertEqual(r['seeds'], [0, 1])
        self.assertEqual(r['n'], 3)
        self.assertEqual(r['delta_tau'], 1)
        self.assertEqual(r['delta_tau_ci95'], [1, 1])

    def test_query_mismatch_and_duplicate_refused(self):
        with self.assertRaises(ValueError):
            contrast({0: rows([1, 2])}, {0: rows([1])})
        a = rows([1, 2]); a[1]['prompt_id'] = a[0]['prompt_id']
        with self.assertRaises(ValueError):
            contrast({0: a}, {0: rows([1, 2])})

    def test_zero_step_excluded_in_both_arms(self):
        a = rows([0, 1]); b = rows([1, 2])
        b[0].update(per_step_drafted=[], per_step_accepted=[])
        r = contrast({0: a}, {0: b})
        self.assertEqual(r['n'], 1)
        self.assertEqual(r['excluded_zero_step'], 1)


if __name__ == '__main__':
    unittest.main()
