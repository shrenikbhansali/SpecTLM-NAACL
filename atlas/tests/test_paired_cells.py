import json
import pytest
from atlas.run_cell import metrics,aggregate


def fixture(tmp_path,values):
    tmp_path.mkdir(exist_ok=True)
    cfg=dict(K=4,n=len(values),seed=0,max_new_tokens=512,batch_size=8,max_model_len=4096,dtype='bfloat16',temperature=0.,top_p=1.,engine_version='0.31.0',method='eagle3',max_lora_rank=64,gpu_memory_utilization=.75,enable_prefix_caching=False,prompt_sha256='p',code_dirty=False,drafter='draft',drafter_revision='b'*40,target='base',target_revision='a'*40)
    rows=[dict(prompt_id=p,**metrics([] if v is None else [v-1],[] if v is None else [4],4)) for p,v in values.items()]
    (tmp_path/'config.json').write_text(json.dumps(cfg));(tmp_path/'results.json').write_text(json.dumps(aggregate(rows)|dict(engine_version='0.31.0')))
    (tmp_path/'per_prompt.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    return tmp_path


def test_pairwise_uses_shared_nonzero_ids_not_independent_means(tmp_path):
    from atlas.paired_cells import read_cell,paired_values
    a=read_cell(fixture(tmp_path/'a',dict(p0=1,p1=4,p2=None)))
    b=read_cell(fixture(tmp_path/'b',dict(p2=5,p1=2,p0=None)))
    result=paired_values(a,b)
    assert result['values']==[4.,2.] and result['n_paired']==1 and result['n_excluded']==2
    assert result['excluded_prompt_ids']==['p0','p2']
    assert a['value']==2.5 and b['value']==3.5
    c=read_cell(fixture(tmp_path/'c',dict(p0=None,p1=None,p2=None)))
    assert c['value'] is None
    with pytest.raises(ValueError,match='no paired'):paired_values(a,c)
    with pytest.raises(ValueError,match='matched'):paired_values(a,b|dict(settings={'K':2}))


@pytest.mark.parametrize('where,key,value', [('row','zero_step',False),('row','num_accepted_tokens',9),('result','n_zero_step',0),('result','macro_acceptance_length',1)])
def test_loader_rejects_tampered_counts_and_flags(tmp_path,where,key,value):
    from atlas.paired_cells import read_cell
    p=fixture(tmp_path/'a',dict(p0=None,p1=3))
    path=p/('per_prompt.jsonl' if where=='row' else 'results.json')
    if where=='row':
        rows=[json.loads(s) for s in path.read_text().splitlines()];rows[0][key]=value;path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    else:
        result=json.loads(path.read_text());result[key]=value;path.write_text(json.dumps(result))
    with pytest.raises(ValueError):read_cell(p)


def test_legacy_nonzero_records_still_validate(tmp_path):
    from atlas.paired_cells import read_cell
    p=fixture(tmp_path/'a',dict(p0=3));row=json.loads((p/'per_prompt.jsonl').read_text());row.pop('zero_step')
    (p/'per_prompt.jsonl').write_text(json.dumps(row)+'\n')
    (p/'results.json').write_text(json.dumps(dict(n=1,macro_acceptance_length=3.,engine_version='0.31.0')))
    assert read_cell(p)['value']==3.
