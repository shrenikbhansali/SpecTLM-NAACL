import pytest
import torch
from atlas.transport_native import align_eagle_step, expanded_logprobs, capture_eagle_unroll


def test_alignment_uses_bonus_token_anchor_and_stays_inside_saved_answer():
    labels=torch.arange(8*3).reshape(8,3)
    draft=torch.arange(7*2).reshape(7,2)
    p,q,anchors=align_eagle_step(labels,draft,response_start=3,step=0)
    assert anchors.tolist()==[3,4,5,6]
    assert torch.equal(p,labels[3:7]) and torch.equal(q,draft[2:6])
    p,q,anchors=align_eagle_step(labels,draft,response_start=3,step=2)
    assert anchors.tolist()==[3,4]
    assert torch.equal(p,labels[5:7]) and torch.equal(q,draft[2:4])
    with pytest.raises(ValueError):align_eagle_step(labels,draft,response_start=7,step=0)


def test_expansion_uses_offsets_and_preserves_zero_support():
    logits=torch.tensor([[1.,2.]])
    result=expanded_logprobs(logits,torch.tensor([0,2]),vocab_size=4)
    assert torch.isneginf(result[0,1]) and torch.isneginf(result[0,2])
    assert torch.equal(result[:,[0,3]],logits.log_softmax(-1))
    assert result.exp().sum()==pytest.approx(1)
    with pytest.raises(ValueError):expanded_logprobs(logits,torch.tensor([0,-1]),4)


def test_capture_observes_native_heads_and_removes_hook_after_error():
    class NativeContract(torch.nn.Module):
        def __init__(self):
            super().__init__();self.lm_head=torch.nn.Linear(6,4)
        def forward(self,hidden_states,input_ids,document_ids,ttt_steps):
            assert input_ids.tolist()==[[2,3,4]]
            assert torch.equal(hidden_states,features[:,:-1])
            assert torch.equal(document_ids,torch.zeros_like(input_ids))
            for _ in range(ttt_steps):self.lm_head(hidden_states)
    features=torch.randn(1,4,6);ids=torch.tensor([[1,2,3,4]]);model=NativeContract().eval()
    outputs=capture_eagle_unroll(model,features,ids,2)
    assert len(outputs)==2 and outputs[0].shape==(3,4)
    assert not model.lm_head._forward_hooks
    def failed(**kwargs):raise RuntimeError('native error')
    model.forward=failed
    with pytest.raises(RuntimeError):capture_eagle_unroll(model,features,ids,2)
    assert not model.lm_head._forward_hooks
