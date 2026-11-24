import unittest
from rebuttal.seal_reviewed import validate_review
class ReviewTests(unittest.TestCase):
 def test_requires_exact_five_inspected_rows(self):
  rows=[{'sample_id':str(i),'x':i} for i in range(8)]
  validate_review(rows,rows[:5])
  with self.assertRaises(ValueError):validate_review(rows,rows[:4])
  changed=[r.copy() for r in rows];changed[2]['x']=99
  with self.assertRaises(ValueError):validate_review(changed,rows[:5])
