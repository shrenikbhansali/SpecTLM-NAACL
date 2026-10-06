import torch
import pytest
from followspec.paired_data import shift_paired,validate_packed


def sample():
    return dict(input_ids=torch.arange(5),loss_mask=torch.tensor([False,False,False,True,True]),
        hidden_states=torch.arange(15).reshape(5,3).float(),base_hidden_states=torch.arange(15).reshape(5,3).float()+10,
        verifier_last_hidden_states=torch.arange(10).reshape(5,2).float(),
        base_verifier_last_hidden_states=torch.arange(10).reshape(5,2).float()+10,
        child_target_logits=torch.arange(20).reshape(5,4).float(),base_target_logits=torch.arange(20).reshape(5,4).float()+1)


def test_same_native_shift_applied_to_both_sides():
    raw=sample();x=shift_paired(raw)
    assert x['input_ids'].tolist()==[1,2,3,4]
    for k in ('hidden_states','base_hidden_states'):torch.testing.assert_close(x[k],raw[k][:-1])
    for k in ('verifier_last_hidden_states','base_verifier_last_hidden_states','child_target_logits','base_target_logits'):
        torch.testing.assert_close(x[k],raw[k][1:])
    assert x['position_ids'].tolist()==[1,2,3,4] and x['lengths'].tolist()==[4]


def test_reject_different_token_alignment_and_missing_paired_features():
    raw=sample();raw['base_hidden_states']=raw['base_hidden_states'][:-1]
    with pytest.raises(ValueError):shift_paired(raw)
    raw=sample();del raw['base_verifier_last_hidden_states']
    with pytest.raises(ValueError):shift_paired(raw)


def test_packing_cannot_score_across_documents():
    batch=dict(input_ids=torch.zeros(1,8,dtype=torch.long),document_ids=torch.tensor([[0,0,0,0,1,1,1,-1]]),loss_mask=torch.tensor([[False,False,True,True,False,False,True,False]]))
    validate_packed(batch,ttt_steps=3)
    batch['loss_mask'][0,4]=True
    with pytest.raises(ValueError,match='document boundary'):validate_packed(batch,ttt_steps=3)
