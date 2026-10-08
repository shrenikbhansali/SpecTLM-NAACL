import pytest
import torch
from atlas.context_agreement import aligned_completion, summarize_agreement


def test_completion_boundary_and_two_token_feature_shift():
    # Draft index i uses feature[i] + input[i+1], predicts token[i+2].
    draft=torch.tensor([8,9,10,11,12])
    target=torch.tensor([90,91,9,10,11,99])
    a,b,positions=aligned_completion(draft,target,response_start=3)
    assert positions.tolist()==[3,4,5]
    assert a.tolist()==[9,10,11]
    assert b.tolist()==[9,10,11]


def test_full_target_vocabulary_not_conditioned_on_draft_support():
    # A target argmax outside the draft vocabulary remains a disagreement.
    r=summarize_agreement(torch.tensor([3,7,3]),torch.tensor([3,99,7]))
    assert r['matches']==1 and r['n_tokens']==3
    assert r['agreement']==pytest.approx(1/3)


@pytest.mark.parametrize('start',[0,1,6])
def test_invalid_boundaries_fail(start):
    with pytest.raises(ValueError):aligned_completion(torch.arange(5),torch.arange(6),start)


def test_wrong_shape_fails():
    with pytest.raises(ValueError):aligned_completion(torch.arange(6),torch.arange(6),3)


def test_native_first_step_is_prefix_causal_and_mapped(monkeypatch):
    monkeypatch.setenv('TORCH_COMPILE_DISABLE','1')
    from transformers import LlamaConfig
    from speculators.models.eagle3.config import Eagle3SpeculatorConfig
    from speculators.models.eagle3.core import Eagle3DraftModel
    from atlas.context_agreement import first_draft
    torch.manual_seed(4)
    cfg=Eagle3SpeculatorConfig(transformer_layer_config=LlamaConfig(hidden_size=8,intermediate_size=16,
        num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=1,head_dim=4,vocab_size=19,
        attn_implementation='eager'),draft_vocab_size=7,eagle_aux_hidden_state_layer_ids=[1,2,3])
    model=Eagle3DraftModel(cfg).eval()
    with torch.no_grad():
        for weight in model.parameters():weight.normal_(0,.1)
        model.d2t.copy_(torch.arange(7)+1) # full token IDs: 1,3,5,...,13
    ids=torch.tensor([1,4,9,2,5,7,11]);features=torch.randn(7,24);logits=[]
    hook=model.lm_head.register_forward_hook(lambda m,a,o:logits.append(o.detach().clone()))
    with torch.no_grad():
        whole=first_draft(model,ids,features)
        prefix=first_draft(model,ids[:5],features[:5])
    hook.remove()
    torch.testing.assert_close(logits[0][:,:4],logits[1],rtol=1e-5,atol=1e-6)
    assert torch.equal(whole[:4],prefix)
    assert set(whole.tolist())<={1,3,5,7,9,11,13}
