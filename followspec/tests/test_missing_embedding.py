"""FIX-24: detect the checkpoint omission, never replace production tensors."""
import torch
from safetensors.torch import save_file
from followspec.missing_embedding import fill_missing_embedding, checkpoint_keys, tensor_sha256

class Draft(torch.nn.Module):
    def __init__(self):
        super().__init__();self.embed_tokens=torch.nn.Embedding(5,3);self.fc=torch.nn.Linear(3,3)

def test_official_missing_embedding_uses_exact_target_and_preserves_other_state(tmp_path,monkeypatch):
    m=Draft();m.embed_tokens.weight.requires_grad_(False);before={k:v.clone() for k,v in m.state_dict().items()}
    save_file({'fc.weight':m.fc.weight.detach()},tmp_path/'model.safetensors')
    target=torch.arange(15,dtype=torch.bfloat16).reshape(5,3)/16
    monkeypatch.setattr('followspec.missing_embedding.target_embedding',lambda p:target)
    rng=torch.random.get_rng_state().clone();proof=fill_missing_embedding(m,tmp_path,'target')
    assert torch.equal(m.embed_tokens.weight,target.float())
    assert tensor_sha256(m.embed_tokens.weight)==tensor_sha256(target.float())
    assert torch.equal(m.embed_tokens.weight.to(torch.bfloat16),target)
    assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items() if k!='embed_tokens.weight')
    assert not m.embed_tokens.weight.requires_grad and torch.equal(rng,torch.random.get_rng_state())
    assert proof['source']=='target_missing_checkpoint_embedding'

def test_production_embedding_keeps_full_state_rng_and_forward_exact(tmp_path,monkeypatch):
    m=Draft();save_file(m.state_dict(),tmp_path/'model.safetensors');before={k:tensor_sha256(v) for k,v in m.state_dict().items()};y=m.fc(m.embed_tokens(torch.tensor([1,2]))).detach().clone()
    def forbidden(_):raise AssertionError('must not read target for production')
    monkeypatch.setattr('followspec.missing_embedding.target_embedding',forbidden)
    rng=torch.random.get_rng_state().clone();proof=fill_missing_embedding(m,tmp_path,'target')
    assert before=={k:tensor_sha256(v) for k,v in m.state_dict().items()}
    assert torch.equal(y,m.fc(m.embed_tokens(torch.tensor([1,2]))))
    assert torch.equal(rng,torch.random.get_rng_state()) and proof['source']=='checkpoint'

def test_sharded_index_and_missing_shape_guard(tmp_path,monkeypatch):
    import json,pytest
    (tmp_path/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{'fc.weight':'one.safetensors'}}))
    assert checkpoint_keys(tmp_path)=={'fc.weight'}
    m=Draft();old=m.embed_tokens.weight.clone();monkeypatch.setattr('followspec.missing_embedding.target_embedding',lambda p:torch.zeros(2,2))
    with pytest.raises(ValueError,match='shape'):fill_missing_embedding(m,tmp_path,'target')
    assert torch.equal(old,m.embed_tokens.weight)


def test_probe_is_bounded_and_does_not_update_state():
    from followspec.missing_embedding import probe_batches,state_hashes
    class M(torch.nn.Module):
        def __init__(self):super().__init__();self.w=torch.nn.Parameter(torch.ones(1))
        def forward(self,x):return x,x.sum(),{'count':torch.tensor(1.)}
    m=M();before=state_hashes(m);r=probe_batches(m,[{'x':torch.ones(2)}]*3,{},2)
    assert len(r)==2 and before==state_hashes(m) and m.w.grad is None
