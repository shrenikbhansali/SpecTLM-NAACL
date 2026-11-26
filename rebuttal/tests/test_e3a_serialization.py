import json
import unittest
from rebuttal.e3a_data import jsonl_line


class E3aSerializationTests(unittest.TestCase):
    def test_unicode_separators_do_not_split_json_records(self):
        row={'raw_prompt':'a\u2028b\u0085c\u2029d','input_ids':[1,2]}
        encoded=jsonl_line(row)
        self.assertEqual(len(encoded.splitlines()),1)
        self.assertEqual(json.loads(encoded),row)
