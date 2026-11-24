import unittest
import torch
from rebuttal.kd import full_kl, factor_logits, split_rows, response_hidden, pack_by_responses

class KDTests(unittest.TestCase):
 def test_forward_kl_and_gradients_full_vocab(self):
  torch.manual_seed(7)
  h=torch.randn(7,5,dtype=torch.double,requires_grad=True);w=torch.randn(13,5,dtype=torch.double,requires_grad=True)
  th=torch.randn(7,9,dtype=torch.double);tw=torch.randn(13,9,dtype=torch.double)
  loss=full_kl(h,w,th,tw,chunk=2);lp=(th@tw.T).log_softmax(-1);lq=(h@w.T).log_softmax(-1)
  ref=(lp.exp()*(lp-lq)).sum()/7
  torch.testing.assert_close(loss,ref)
  a=torch.autograd.grad(loss,(h,w),retain_graph=True);b=torch.autograd.grad(ref,(h,w))
  for x,y in zip(a,b):torch.testing.assert_close(x,y)
 def test_factorization_matches_teacher_linear(self):
  h=torch.randn(5,7);w=torch.randn(11,7)
  torch.testing.assert_close(factor_logits(h,w),torch.nn.functional.linear(h,w))
 def test_response_alignment_includes_first_answer(self):
  row={'input_ids':[10,11,12,13,14],'response_start':3,'loss_mask':[False]*3+[True]*2}
  hidden=torch.arange(5).reshape(5,1)
  self.assertEqual(response_hidden(hidden,row).flatten().tolist(),[2,3])
 def test_split_is_disjoint_and_reproducible(self):
  rows=[{'sample_id':str(i),'prompt_sha256':str(i),'response_start':2,'input_ids':[1,2,3]} for i in range(300)]
  tr,va=split_rows(rows,256,0);self.assertEqual(len(tr),44);self.assertEqual(len(va),256)
  self.assertFalse(set(tr)&set(va));self.assertEqual((tr,va),split_rows(rows,256,0))
 def test_response_budget_every_sample_once_per_epoch(self):
  rows=[{'response_start':4,'input_ids':list(range(n+4))} for n in [3,5,6,2]]
  batches=pack_by_responses(rows,[0,1,2,3],8,2,0)
  flat=[i for b in batches for i in b]
  self.assertEqual(sorted(flat),[0,0,1,1,2,2,3,3])
  self.assertTrue(all(sum(len(rows[i]['input_ids'])-rows[i]['response_start'] for i in b)<=8 for b in batches))
