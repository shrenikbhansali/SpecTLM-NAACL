import torch,pytest
from followspec.repair_continuation import restore_optimizer_by_name, continuation_batches


def test_saved_optimizer_restores_only_identical_named_order():
 m=torch.nn.Linear(2,1);o=torch.optim.AdamW(m.parameters(),lr=.1);m(torch.ones(1,2)).sum().backward();o.step()
 payload=o.state_dict();payload['parameter_names']={i:n for i,(n,p) in zip(payload['param_groups'][0]['params'],m.named_parameters())}
 new=torch.optim.AdamW(m.parameters(),lr=.1);restore_optimizer_by_name(m,[new],[payload]);assert len(new.state)==2
 for p in m.parameters():torch.testing.assert_close(new.state[p]['exp_avg'],o.state[p]['exp_avg'])
 payload['parameter_names'][0]='wrong'
 with pytest.raises(ValueError,match='name'):restore_optimizer_by_name(m,[new],[payload])


def test_second_epoch_keeps_every_sample_once_without_replaying_first():
 rows=[dict(input_ids=list(range(n))) for n in [6,8,9,13,7]]
 a=continuation_batches(rows,15,0,0);b=continuation_batches(rows,15,0,1)
 assert sorted(i for batch in b for i in batch)==list(range(len(rows)))
 assert a!=b and b==continuation_batches(rows,15,0,1)
 assert all(sum(len(rows[i]['input_ids'])-1 for i in batch)<=15 for batch in b)


def test_compact_state_inflates_around_frozen_parameters(tmp_path):
 from followspec.checkpoint_storage import save_trainable_checkpoint
 m=torch.nn.Sequential(torch.nn.Linear(2,2),torch.nn.Linear(2,1));m[0].requires_grad_(False)
 old=torch.optim.AdamW(m.named_parameters(),lr=.01);m(torch.ones(1,2)).sum().backward();old.step()
 save_trainable_checkpoint(m,tmp_path/'c',[old],{})
 payload=torch.load(tmp_path/'c/optimizer_state_dict.pt',weights_only=True)
 new=torch.optim.AdamW(m.named_parameters(),lr=.01);restore_optimizer_by_name(m,[new],payload)
 assert len(new.param_groups[0]['params'])==4 and len(new.state)==2
 for p in m[1].parameters():torch.testing.assert_close(new.state[p]['exp_avg'],old.state[p]['exp_avg'])
 assert all(p not in new.state for p in m[0].parameters())
