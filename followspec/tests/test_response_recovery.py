import json
from pathlib import Path
import pytest
from atlas.run_cell import write_new
from followspec.production_pipeline import finish,jsonl,read


def stage(tmp_path):
    out=tmp_path/'original';out.mkdir();failed=tmp_path/'failed';failed.mkdir();good=tmp_path/'good';good.mkdir()
    write_new(failed/'config.json',{'seed':3});write_new(failed/'failure.json',{'error':'cache init'})
    write_new(good/'results.json',{'n':10})
    write_new(out/'response_runs.json',{'base':{'child':str(failed),'base':str(failed)},'child':{'child':str(good),'base':str(good)}})
    write_new(out/'assignment.json',{'queries':{'base':[],'child':[]}})
    jobs=[dict(name=name,args=['--tag',name,'--seed','3','--','python','-m','followspec.generate_responses','--seed','3','--prompts','same-prompts','--output',str(path)]) for name,path in [('base',failed),('child',good)]]
    jsonl(out/'jobs.jsonl',jobs);finish(out,dict(stage='responses',spec={'seed':3},input_sha256={}),dict(n_gpu_jobs=2))
    return out,failed,good,jobs


def test_only_failed_job_rebound_success_and_controls_preserved(tmp_path):
    from followspec.response_recovery import retry_responses
    root,failed,good,jobs=stage(tmp_path);before=(root/'stage_files.json').read_bytes()
    out=retry_responses(root,[failed],tmp_path/'retry')
    runs=read(out/'response_runs.json');assert runs['base']['child']==runs['base']['base']!=str(failed)
    assert runs['child']=={'child':str(good),'base':str(good)}
    retry=[json.loads(s) for s in (out/'jobs.jsonl').read_text().splitlines()];assert len(retry)==1
    old=jobs[0]['args'];new=retry[0]['args'];assert old[old.index('--')+1:-1]==new[new.index('--')+1:-1]
    assert new[-1]==runs['base']['base'] and read(out/'results.json')['n_reused_sources']==1
    assert len((out/'effective_jobs.jsonl').read_text().splitlines())==2
    assert (root/'stage_files.json').read_bytes()==before and (failed/'failure.json').exists()


def test_complete_source_cannot_be_retried(tmp_path):
    from followspec.response_recovery import retry_responses
    root,failed,good,_=stage(tmp_path)
    with pytest.raises(ValueError,match='failed'):retry_responses(root,[good],tmp_path/'retry')
    assert not (tmp_path/'retry').exists()


def test_unrelated_failure_refused(tmp_path):
    from followspec.response_recovery import retry_responses
    root,failed,good,_=stage(tmp_path);other=tmp_path/'other';other.mkdir();write_new(other/'failure.json',{})
    with pytest.raises(ValueError,match='referenced'):retry_responses(root,[other],tmp_path/'retry')


def test_changed_plan_refused(tmp_path):
    from followspec.response_recovery import retry_responses
    root,failed,_,_=stage(tmp_path);(root/'assignment.json').write_text('{}')
    with pytest.raises(ValueError,match='stage changed'):retry_responses(root,[failed],tmp_path/'retry')


def test_retry_overlay_can_retry_a_later_original_failure(tmp_path):
    from followspec.response_recovery import retry_responses
    root,failed,good,_=stage(tmp_path);out=retry_responses(root,[failed],tmp_path/'retry')
    # Fixture models an original active source becoming failed later.
    (good/'results.json').unlink();write_new(good/'config.json',{});write_new(good/'failure.json',{'error':'later'})
    second=retry_responses(out,[good],tmp_path/'retry2')
    assert read(second/'response_runs.json')['base']==read(out/'response_runs.json')['base']
    assert len((second/'effective_jobs.jsonl').read_text().splitlines())==2
