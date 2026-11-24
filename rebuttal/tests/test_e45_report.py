import unittest
from rebuttal.report_e45 import replace_section, interval


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
