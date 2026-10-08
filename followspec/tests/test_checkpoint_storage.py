import json
import os
import pytest
import torch
from safetensors.torch import load_file
from followspec.checkpoint_storage import shared_export, save_trainable_checkpoint


class Config:
    def save_pretrained(self,path):
        (path/'config.json').write_text('{}')

class Model(torch.nn.Module):
    _keys_to_ignore_on_save=['teacher.weight']
    def __init__(self):
        super().__init__();self.fc=torch.nn.Linear(3,2,bias=False)
        self.embed=torch.nn.Embedding(5,3).requires_grad_(False)
        self.teacher=torch.nn.Linear(3,5).requires_grad_(False)
        self.register_buffer('map',torch.arange(5));self.config=Config()


def test_export_exact_and_shares_only_unchanged_tensors(tmp_path):
    m=Model();state=m.state_dict();shared=tmp_path/'shared'
    for i in range(2):
        state['fc.weight']=state['fc.weight']+1
        dest=tmp_path/str(i);shared_export(m,dest,shared,state,{'fc.weight'})
        index=json.loads((dest/'model.safetensors.index.json').read_text())['weight_map']
        loaded={}
        for name in set(index.values()):loaded.update(load_file(dest/name))
        assert set(loaded)==set(state)-{'teacher.weight'}
        for k in loaded:assert torch.equal(state[k],loaded[k])
    a=json.loads((tmp_path/'0/model.safetensors.index.json').read_text())['weight_map']
    b=json.loads((tmp_path/'1/model.safetensors.index.json').read_text())['weight_map']
    assert os.stat(tmp_path/'0'/a['embed.weight']).st_ino==os.stat(tmp_path/'1'/b['embed.weight']).st_ino
    assert os.stat(tmp_path/'0'/a['fc.weight']).st_ino!=os.stat(tmp_path/'1'/b['fc.weight']).st_ino
    with pytest.raises(FileExistsError):shared_export(m,tmp_path/'0',shared,state,{'fc.weight'})


def test_frozen_content_change_gets_distinct_shard(tmp_path):
    m=Model();s=m.state_dict();shared_export(m,tmp_path/'a',tmp_path/'shared',s,{'fc.weight'})
    s['embed.weight']=s['embed.weight']+1
    shared_export(m,tmp_path/'b',tmp_path/'shared',s,{'fc.weight'})
    assert len(list((tmp_path/'shared').glob('*.safetensors')))==2


def test_checkpoint_contains_trainable_weights_and_optimizer_only(tmp_path):
    m=Model();opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad]);m.fc(torch.ones(1,3)).sum().backward();opt.step()
    dest=tmp_path/'checkpoint';save_trainable_checkpoint(m,dest,[opt],{'init':'pinned','step':1})
    saved=load_file(dest/'trainable.safetensors')
    assert set(saved)=={'fc.weight'}
    assert torch.equal(saved['fc.weight'],m.fc.weight.cpu())
    assert (dest/'optimizer_state_dict.pt').exists()
    assert not (dest/'model.safetensors').exists()
    with pytest.raises(FileExistsError):save_trainable_checkpoint(m,dest,[opt],{})


def test_native_optimizer_groups_may_include_frozen_parameters(tmp_path):
    m=Model();opt=torch.optim.AdamW(m.parameters());m.fc(torch.ones(1,3)).sum().backward();opt.step()
    save_trainable_checkpoint(m,tmp_path/'c',[opt],{})
    saved=torch.load(tmp_path/'c/optimizer_state_dict.pt',weights_only=True)[0]
    assert sum(len(g['params']) for g in saved['param_groups'])==1
    assert len(saved['state'])==1
    assert sum(len(g['params']) for g in opt.param_groups)==4


def test_intermediate_saves_weights_without_reading_optimizer(tmp_path):
    from followspec.checkpoint_storage import save_trainable_checkpoint
    import torch
    class ForbiddenOptimizer:
        def state_dict(self):
            raise AssertionError('intermediate save must not serialize optimizer')
    model=torch.nn.Linear(2,3)
    model.bias.requires_grad_(False)
    dest=tmp_path/'intermediate'
    save_trainable_checkpoint(model,dest,[ForbiddenOptimizer()],{'step':50},save_optimizer=False)
    from safetensors.torch import load_file
    assert set(load_file(dest/'trainable.safetensors'))=={'weight'}
    assert not (dest/'optimizer_state_dict.pt').exists()
    import json
    assert json.loads((dest/'trainable_checkpoint.json').read_text())['optimizer_saved'] is False
