import unittest
from rebuttal.reduce_e45 import acceptance_contrast,timing_contrast,matched_reference_rows
class E45AnalysisTests(unittest.TestCase):
 def test_reference_subset_requires_identical_rendered_prefix(self):
  prompts=[{'prompt_id':str(i),'rendered_token_ids':[1,i]} for i in range(4)]
  raw=[{'prompt_id':str(i),'value':i} for i in range(4)]
  self.assertEqual(matched_reference_rows(raw,prompts,prompts[:2]),raw[:2])
  with self.assertRaises(ValueError):matched_reference_rows(raw,prompts,prompts[1:3])
  changed=[dict(prompts[0],rendered_token_ids=[3,4])]
  with self.assertRaises(ValueError):matched_reference_rows(raw,prompts,changed)
 def test_seed_query_paired_constant_delta_arbitrary_k(self):
  def rows(a,k):return [{'prompt_id':str(i),'per_step_accepted':[a],'per_step_drafted':[k]} for i in range(4)]
  r=acceptance_contrast({0:rows(1,4),1:rows(1,4)},{0:rows(3,5),1:rows(3,5)},4,5)
  self.assertEqual(r['delta_tau'],2);self.assertEqual(r['delta_tau_ci95'],[2,2]);self.assertEqual(r['n'],4)
 def test_zero_steps_excluded_pairwise(self):
  a=[{'prompt_id':'x','per_step_accepted':[],'per_step_drafted':[]},{'prompt_id':'y','per_step_accepted':[1],'per_step_drafted':[4]}]
  b=[{'prompt_id':'x','per_step_accepted':[2],'per_step_drafted':[4]},{'prompt_id':'y','per_step_accepted':[2],'per_step_drafted':[4]}]
  r=acceptance_contrast({0:a},{0:b},4,4);self.assertEqual(r['n'],1);self.assertEqual(r['excluded_zero_step'],1)
 def test_timing_pairs_process_and_prompt_batch(self):
  def records(scale):
   return [{'config':{'prompt_sha256':'h','target_revision':'x','batch_size':1,'max_new_tokens':512,'seed':0,'max_model_len':4096,'temperature':0,'gpu_memory_utilization':.7},'timing':{'startup_s':1,'passes':[{'batches':[{'prompt_ids':['a'],'wall_s':scale},{'prompt_ids':['b'],'wall_s':2*scale}],'per_prompt':[{'prompt_id':'a','completion_token_ids':[1,2]},{'prompt_id':'b','completion_token_ids':[1,2,3]}]} for _ in range(4)]}} for _ in range(3)]
  r=timing_contrast(records(1),records(2));self.assertEqual(r['warm']['panel_speedup'],2);self.assertEqual(r['warm']['panel_ci95'],[2,2])
  with self.assertRaises(ValueError):timing_contrast(records(1)[:2],records(2))
