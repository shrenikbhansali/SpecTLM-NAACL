import json
import pytest
from atlas.transport_sources import prepare_pair
from atlas.run_cell import sha256


def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj))


def test_pair_preparation_uses_actual_target_pin_and_exact_saved_contexts(tmp_path):
    prompts=tmp_path/'prompts.jsonl';prompts.write_text(json.dumps(dict(prompt_id='p',rendered_token_ids=[1,2],derivative_id='reference-origin'))+'\n')
    adapter=tmp_path/'adapter';adapter.mkdir()
    proof=tmp_path/'filter';write(proof/'config.json',dict(derivative_id='c'));write(proof/'target_provenance.json',dict(revision='c'*40));write(proof/'results.json',dict(accepted=True))
    cfg=dict(target='b',target_revision='b'*40,drafter='d',drafter_revision='d'*40,method='eagle3',K=4,seed=0,
        prompts=str(prompts),prompt_sha256=sha256(prompts),max_new_tokens=64,batch_size=1,max_lora_rank=128,enable_lora=True,engine_version='0.31.0')
    record=dict(prompt_id='p',prompt_token_ids=[1,2],completion_token_ids=[3,4])
    for arm in ['base','child']:
        p=tmp_path/arm;write(p/'config.json',cfg|dict(adapter=str(adapter) if arm=='child' else None,adapter_revision='c'*40 if arm=='child' else None))
        write(p/'results.json',dict(n=1,gpu_type='NVIDIA A40'))
        (p/'per_prompt.jsonl').write_text(json.dumps(record)+'\n')
    pair=dict(derivative_id='c',revision='c'*40,adapter=str(adapter),filter_run=str(proof))
    rows,meta=prepare_pair(tmp_path,pair)
    assert rows[0]['input_ids']==[1,2,3,4] and rows[0]['assistant_mask']==[0,0,1,1]
    assert meta['derivative_id']=='c' and meta['workload']=='fixed shared acceptance reference'
    assert meta['reference_origin_ids']==['reference-origin']
    with pytest.raises(ValueError):prepare_pair(tmp_path,pair|dict(revision='x'*40))
    (tmp_path/'base/per_prompt.jsonl').write_text(json.dumps(record|dict(prompt_token_ids=[2,1]))+'\n')
    with pytest.raises(ValueError):prepare_pair(tmp_path,pair)
