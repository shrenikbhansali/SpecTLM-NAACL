import unittest
from rebuttal.seal_subsets import reviewed_members


class SubsetReviewTests(unittest.TestCase):
    def test_five_actual_identical_members_are_required(self):
        reviewed = [{'sample_id': str(i), 'x': i} for i in range(12)]
        subset = reviewed[3:10]
        self.assertEqual(reviewed_members(subset, reviewed), subset[:5])
        with self.assertRaises(ValueError):
            reviewed_members(subset[:4], reviewed)
        changed = [dict(r) for r in subset]
        changed[1]['x'] = -1
        with self.assertRaises(ValueError):
            reviewed_members(changed, reviewed)
