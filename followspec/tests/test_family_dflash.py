import torch
from followspec.family_repair import configure_variant, RepairDataset, step_batches
from followspec.tests.test_family_repair import Tiny


def test_full_dflash_keeps_verifier_projection_frozen():
    m=Tiny();m.use_draft_vocab=False
    proof=configure_variant(m,'full',algorithm='dflash')
    assert not m.lm_head.weight.requires_grad
    assert m.fc.weight.requires_grad
    assert 'lm_head.weight' not in proof['trainable_names']


def test_dflash_raw_layout_and_pack_lengths():
    row=dict(input_ids=[1,2,3,4],loss_mask=[False,True,True,True])
    def capture(ids,mask,feature_target):
        raw=dict(input_ids=ids,loss_mask=mask)
        for k in ['hidden_states','base_hidden_states','verifier_last_hidden_states','base_verifier_last_hidden_states','child_target_logits','base_target_logits']:raw[k]=torch.ones(4,2)
        return raw
    sample=RepairDataset([row],capture,algorithm='dflash')[0]
    assert sample['input_ids'].tolist()==row['input_ids']
    assert sample['position_ids'].tolist()==[0,1,2,3]
    assert len(step_batches([row,row],1,6,0,shift=0)[0])==1
