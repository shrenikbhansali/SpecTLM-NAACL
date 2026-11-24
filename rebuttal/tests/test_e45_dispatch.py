import unittest
from rebuttal.e45_dispatch import choose_model,raw_scores
from rebuttal.timing import extend_parser
from atlas.timing_panel import parser

class E45DispatchTests(unittest.TestCase):
 def test_selection_requires_exact_heldout_ids_and_all_grid_cells(self):
  grid=[{'lr':lr,'epochs':ep,'name':f'{lr}-{ep}'} for lr in [1e-5,2e-5] for ep in [1,3]]
  records={x['name']:[{'prompt_id':str(i),'per_step_accepted':[j%4],'per_step_drafted':[4]} for i in range(4)] for j,x in enumerate(grid)}
  self.assertEqual(choose_model(grid,records,{str(i) for i in range(4)})['epochs'],3)
  with self.assertRaises(ValueError):choose_model(grid,{k:v for k,v in list(records.items())[:3]},{str(i) for i in range(4)})
  with self.assertRaises(ValueError):choose_model(grid,records,{'wrong'})
 def test_small_k_timing_is_opt_in(self):
  original=parser();self.assertNotIn(3,next(a for a in original._actions if a.dest=='K').choices)
  updated=extend_parser(parser());self.assertIn(3,next(a for a in updated._actions if a.dest=='K').choices)
 def test_raw_arbitrary_k_counts_bonus(self):
  self.assertEqual(raw_scores({'per_step_accepted':[2,5],'per_step_drafted':[5,5]},5),(4.5,1.))
  with self.assertRaises(ValueError):raw_scores({'per_step_accepted':[5],'per_step_drafted':[4]},4)
