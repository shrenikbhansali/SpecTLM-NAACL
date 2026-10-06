import json
from pathlib import Path
import pytest
import torch
from followspec.token_data import build_manifest,OnlineResponseDataset
from atlas.workloads import prompt_hash


def run(tmp_path,name,target,answer=(4,5)):
    p=tmp_path/name;p.mkdir()
    row=dict(prompt_id='p',sample_id='p',raw_prompt='A training question.',prompt_sha256=prompt_hash('A training question.'),
        generation_target=target,generation_revision='a'*40 if target=='base' else 'b'*40,
        input_ids=[1,2,3]+list(answer),prompt_token_ids=[1,2,3],completion_token_ids=list(answer),
        response_start=3,loss_mask=[False]*3+[True]*len(answer),split='train',acceptance_only=True)
    cfg=dict(schema='followspec_response_tokens_v1',engine_version='0.31.0',acceptance_only=True,base_revision='a'*40,
        derivative_id=target,derivative_revision=row['generation_revision'],prompt_target='c',seed=1,temperature=.6,top_p=.95,max_new_tokens=64,
        max_lora_rank=32,batch_size=32,gpu_type='NVIDIA A40')
    (p/'config.json').write_text(json.dumps(cfg));(p/'results.json').write_text(json.dumps(dict(n=1,assistant_tokens=len(answer))))
    (p/'per_prompt.jsonl').write_text(json.dumps(row)+'\n');return p


def make(arm,path,split='train',forbidden=()):
    return build_manifest(arm,[dict(run=str(path),record_index=0,child_id='c',pair_id='pair',split=split)],
        registry={'c':dict(kind='bank',revision='b'*40)},base_revision='a'*40,initialization_revision='d'*40,
        forbidden_hashes=forbidden,allow_acceptance=True)


def test_manifest_rejects_wrong_response_target_evaluation_leakage_and_changed_sources(tmp_path):
    child=run(tmp_path,'child','c')
    with pytest.raises(ValueError):make('PO-D',child)
    with pytest.raises(ValueError):make('FS',child,forbidden=[prompt_hash('A training question.')])
    manifest=make('FS',child)
    (child/'per_prompt.jsonl').write_text('{}\n')
    with pytest.raises(ValueError,match='changed'):OnlineResponseDataset(manifest,split='train',bank=None,shift=lambda r:r,allow_acceptance=True)


def test_dataset_captures_each_access_without_feature_shards_and_refuses_smoke_by_default(tmp_path):
    child=run(tmp_path,'child','c');manifest=make('PO-T',child)
    class Bank:
        def __init__(self):self.calls=[]
        def capture(self,target,ids,mask,feature_target):
            self.calls.append((target,feature_target));return dict(input_ids=ids,loss_mask=mask)
    bank=Bank()
    with pytest.raises(ValueError,match='acceptance'):OnlineResponseDataset(manifest,split='train',bank=bank,shift=lambda r:r)
    ds=OnlineResponseDataset(manifest,split='train',bank=bank,shift=lambda r:r,allow_acceptance=True)
    assert ds.approx_lengths==[4] and len(ds)==1
    assert ds[0]['tensors']['input_ids'].tolist()==[1,2,3,4,5]
    ds[0];assert bank.calls==[('c','base'),('c','base')]
    assert not list(tmp_path.rglob('*.safetensors'))
