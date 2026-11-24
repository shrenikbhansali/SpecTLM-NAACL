import unittest
from rebuttal.report_e45 import replace_section, interval, wide_acceptance


class ReportTests(unittest.TestCase):
    def test_only_named_section_changes(self):
        text = '# Results\n\n## E4 — Old\nold\n\n## E5 — Old\nkeep\n'
        actual = replace_section(text, 'E4', '## E4 — New\nnew\n')
        self.assertIn('## E5 — Old\nkeep', actual)
        self.assertNotIn('\nold\n', actual)
        with self.assertRaises(ValueError):
            replace_section(text, 'E6', 'missing')

    def test_ci_formatted_without_changing_numbers(self):
        self.assertEqual(interval(2.456, [2.401, 2.508]), '2.46 [2.40, 2.51]')

    def test_wide_csv_keeps_both_benchmarks_and_uncertainty(self):
        common = dict(experiment='E5', kind='acceptance', target=0, variant='distilled_k4', seed=0, K=4,
                      n=128, p1=.6, p1_ci95=[.5,.7], tau_ci95=[2.,3.], run='x')
        result = wide_acceptance([dict(common, benchmark='speed128', tau=2.4), dict(common, benchmark='math128', tau=2.8)], 'E5')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['tau_speed'], 2.4)
        self.assertEqual(result[0]['tau_math'], 2.8)
        self.assertEqual(result[0]['p1_speed'], 60.)
