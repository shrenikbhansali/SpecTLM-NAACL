from pathlib import Path
import hashlib
import pytest
import torch
from followspec.online_bank import FrozenAdapterBank


def test_bank_keeps_one_target_and_one_resident_adapter_and_verifies_files(tmp_path):
    base=torch.nn.Linear(3,3);events=[]
    class Wrapper:
        def __init__(self,name):self.name=name
        def eval(self):return self
        def requires_grad_(self,value):return self
        def unload(self):events.append(('unload',self.name));return base
    def load(model,path):
        assert model is base
        events.append(('load',path));return Wrapper(path)
    class Capture:
        def __init__(self,model,*args,**kwargs):self.model=model
        def __call__(self,*args,**kwargs):return self.model,kwargs['feature_target']
    paths={}
    for name in ['one','two']:
        d=tmp_path/name;d.mkdir();(d/'adapter_model.safetensors').write_bytes(name.encode())
        paths[name]=dict(path=str(d),kind='bank',revision=name,files_sha256={'adapter_model.safetensors':hashlib.sha256(name.encode()).hexdigest()})
    bank=FrozenAdapterBank(base,paths,[1],torch.tensor([1]),loader=load,capture_factory=Capture,pause_check=lambda:None)
    assert bank.capture('one',None,None)[1]=='child'
    bank.capture('one',None,None)
    assert len(events)==1
    assert bank.capture('base',None,None)[1]=='base'  # no extra target or adapter load
    with pytest.raises(ValueError):bank.capture('base',None,None,feature_target='child')
    bank.capture('two',None,None)
    assert [x[0] for x in events]==['load','unload','load']
    assert bank.base is base and bank.resident_adapters==1
    with pytest.raises(ValueError):bank.capture('heldout',None,None)
    (Path(paths['one']['path'])/'adapter_model.safetensors').write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash'):bank.capture('one',None,None)


def test_mixtures_and_heldout_targets_are_not_silently_admitted(tmp_path):
    for kind in ['test','mixture','heldout_acceptance']:
        with pytest.raises(ValueError):FrozenAdapterBank(torch.nn.Linear(2,2),{'x':dict(kind=kind)},[1],torch.tensor([1]))


def test_failed_partial_adapter_load_poisoned_bank_never_retries_silently(tmp_path):
    d=tmp_path/'adapter';d.mkdir();(d/'w').write_bytes(b'x');calls=[]
    def fail(*args):calls.append(1);raise RuntimeError('partial load')
    class Capture:
        def __init__(self,*args,**kwargs):pass
    registry={'x':dict(kind='bank',revision='r',path=str(d),files_sha256={'w':hashlib.sha256(b'x').hexdigest()})}
    bank=FrozenAdapterBank(torch.nn.Linear(2,2),registry,[1],torch.tensor([1]),loader=fail,capture_factory=Capture,pause_check=lambda:None)
    with pytest.raises(RuntimeError,match='partial load'):bank.capture('x',None,None)
    for target in ['base','x']:
        with pytest.raises(RuntimeError,match='unusable'):bank.capture(target,None,None)
    assert len(calls)==1
