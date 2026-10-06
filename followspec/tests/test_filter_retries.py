import json
from pathlib import Path
import pytest
from followspec.production_pipeline import retry_filters,finish,jsonl,read,checked_stage
from atlas.run_cell import write_new


def fixture(tmp_path):
    root=tmp_path/'original';root.mkdir();runs={name:str(root/'runs'/name) for name in ['failed','complete','active']}
    write_new(root/'registry.json',{name:dict(kind='bank',revision='a'*40) for name in runs})
    write_new(root/'filter_runs.json',runs)
    jobs=[]
    for name,dest in runs.items():
        jobs.append(dict(name='original-'+name,args=['--tag','original-'+name,'--','python','-m','atlas.filter_pool',
                    '--derivative-id',name,'--seed','17','--reference','unchanged-reference','--baseline','unchanged-baseline','--output',dest]))
    jsonl(root/'filter_jobs.jsonl',jobs)
    finish(root,dict(stage='materialize',round=1,plan='unchanged-plan',previous=None,spec={'seed':17},reference='unchanged-reference',baseline='unchanged-baseline'),dict(n_candidates=30))
    for path in runs.values():Path(path).mkdir(parents=True)
    write_new(Path(runs['failed'])/'failure.json',dict(error='engine initialization'))
    write_new(Path(runs['complete'])/'results.json',dict(passed=True))
    return root,runs,jobs


def test_retry_preserves_originals_settings_and_complete_or_active_paths(tmp_path):
    root,runs,jobs=fixture(tmp_path);original={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
    out=retry_filters(root,['failed'],tmp_path/'retry')
    changed=read(out/'filter_runs.json');assert changed['complete']==runs['complete'] and changed['active']==runs['active']
    assert changed['failed']!=runs['failed'] and not Path(changed['failed']).exists()
    retried=[json.loads(s) for s in (out/'filter_jobs.jsonl').read_text().splitlines()]
    assert len(retried)==1
    expected=jobs[0]['args'].copy();expected[expected.index('--tag')+1]=retried[0]['name'];expected[expected.index('--output')+1]=changed['failed']
    assert retried[0]['args']==expected
    assert read(out/'registry.json')==read(root/'registry.json')
    _,cfg=checked_stage(out);assert cfg['plan']=='unchanged-plan' and cfg['baseline']=='unchanged-baseline' and cfg['round']==1
    assert all(p.read_bytes()==b for p,b in original.items())
    # Later failure of a previously-active cell uses its retained original job.
    write_new(Path(runs['active'])/'failure.json',dict(error='later engine error'))
    again=retry_filters(out,['active'],tmp_path/'retry2')
    assert read(again/'filter_runs.json')['failed']==changed['failed']
    assert read(again/'filter_runs.json')['active']!=runs['active']


@pytest.mark.parametrize('targets',[[],['unknown'],['complete'],['active'],['failed','failed']])
def test_refuse_unknown_successful_active_or_duplicate_targets_without_creating_output(tmp_path,targets):
    root,_,_=fixture(tmp_path)
    with pytest.raises(ValueError):retry_filters(root,targets,tmp_path/'rejected')
    assert not (tmp_path/'rejected').exists()


def test_refuse_changed_round_or_existing_output(tmp_path):
    root,_,_=fixture(tmp_path);out=tmp_path/'exists';out.mkdir()
    with pytest.raises(FileExistsError):retry_filters(root,['failed'],out)
    (root/'filter_runs.json').write_text('{}')
    with pytest.raises(ValueError,match='stage changed'):retry_filters(root,['failed'],tmp_path/'other')
