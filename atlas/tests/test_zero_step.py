"""D32: missing observations are never fabricated as acceptance length one."""
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
from atlas.run_cell import metrics,aggregate


def test_zero_counters_are_explicit_and_undefined_and_macro_excludes_them():
    zero=metrics([],[],4)
    assert zero['zero_step'] is True
    assert zero['num_drafts']==zero['num_draft_tokens']==zero['num_accepted_tokens']==0
    assert zero['acceptance_length'] is None and zero['draft_token_acceptance_rate'] is None
    assert zero['per_step_accepted']==zero['per_step_drafted']==zero['accepted_lengths']==[]
    assert zero['per_position_conditional_acceptance']==[None]*4
    result=aggregate([zero,metrics([2],[4],4)])
    assert result['n']==1 and result['n_total']==2 and result['n_zero_step']==1
    assert result['macro_acceptance_length']==3 and result['prompt_bootstrap_95_ci']==[3,3]
    empty=aggregate([zero])
    assert empty['n']==0 and empty['n_zero_step']==1
    assert empty['macro_acceptance_length'] is None and empty['prompt_bootstrap_95_ci'] is None
    json.dumps(empty,allow_nan=False)


def test_engine_summary_missing_detail_must_not_be_misclassified_as_zero():
    from atlas.run_cell import request_metrics
    raw=dict(num_spec_tokens=4,histogram=[0]*5,num_draft_tokens=0,per_step_accepted=[],per_step_drafted=[])
    assert request_metrics(raw,4)['zero_step']
    for changes in [dict(histogram=[1,0,0,0,0]),dict(num_draft_tokens=1),dict(histogram=[-1,1,0,0,0]),dict(num_spec_tokens=2)]:
        with pytest.raises((ValueError,RuntimeError)):request_metrics(raw|changes,4)
    with pytest.raises((ValueError,RuntimeError)):request_metrics(None,4)


def test_real_main_writes_zero_and_next_request_and_completes(monkeypatch,tmp_path):
    import atlas.run_cell as cell
    prompts=tmp_path/'prompts.jsonl';prompts.write_text(''.join(json.dumps(dict(prompt_id=f'p{i}',prompt='hello'))+'\n' for i in range(2)))
    class LLM:
        def __init__(self,**kwargs):pass
        def generate(self,batch,*args,**kwargs):
            results=[]
            for i,_ in enumerate(batch):
                raw=dict(num_spec_tokens=4,histogram=[0]*5 if i==0 else [0,0,1,0,0],num_draft_tokens=0 if i==0 else 4,per_step_accepted=[] if i==0 else [2],per_step_drafted=[] if i==0 else [4])
                results.append(SimpleNamespace(prompt_token_ids=[1],outputs=[SimpleNamespace(text='' if i==0 else 'ok',token_ids=[2],spec_decode_metrics=raw)]))
            return results
    monkeypatch.setitem(sys.modules,'vllm',SimpleNamespace(LLM=LLM,SamplingParams=lambda **kw:kw))
    monkeypatch.setitem(sys.modules,'torch',SimpleNamespace(cuda=SimpleNamespace(get_device_name=lambda _: 'synthetic')))
    monkeypatch.setattr(cell.importlib.metadata,'version',lambda _: '0.31.0')
    monkeypatch.setattr(cell.subprocess,'check_output',lambda args,**kw:'' if 'status' in args else 'a'*40)
    monkeypatch.setattr(cell,'read_drafter_config',lambda *args:{})
    out=tmp_path/'run';monkeypatch.setattr(sys,'argv',['run_cell','--target','base','--target-revision','a'*40,'--drafter','draft','--drafter-revision','b'*40,'--method','eagle3','--prompts',str(prompts),'--output',str(out),'--batch-size','2'])
    cell.main()
    rows=[json.loads(s) for s in (out/'per_prompt.jsonl').read_text().splitlines()]
    assert [r['zero_step'] for r in rows]==[True,False]
    assert not (out/'failure.json').exists()
    assert json.loads((out/'results.json').read_text())['n_zero_step']==1
