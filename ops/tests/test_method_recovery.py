import json
from pathlib import Path
import pytest
from ops import method_recovery as recovery


def fixture(tmp_path):
    prompt=tmp_path/'prompts.jsonl';prompt.write_text('fixture\n')
    run=tmp_path/'failed';run.mkdir();(run/'failure.json').write_text('{"error":"engine startup failed"}')
    cfg={'prompt_sha256':recovery.sha(prompt),'code_dirty':False,'source_sha256':'source','engine_version':'0.31.0'}
    (run/'config.json').write_text(json.dumps(cfg))
    launcher=tmp_path/'launcher';launcher.mkdir();(launcher/'exit_code').write_text('1');(launcher/'launch.log').write_text('No available memory for the cache blocks')
    argv=['python','-m','atlas.run_cell','--prompts',str(prompt),'--output',str(run),'--K','4']
    record=dict(run_id='eval-one',run_dir=str(run),argv=argv,env={'VLLM_CACHE_ROOT':str(run/'cache')},K=4)
    job=dict(name='eval-one',args=['--tag','eval-one','--code-repo','frozen','--',*argv],allowed_nodes=['heck-srv2'])
    return record,job,launcher,prompt


def test_retry_preserves_command_and_failed_artifact(tmp_path):
    r,j,l,p=fixture(tmp_path);before=(Path(r['run_dir'])/'failure.json').read_bytes()
    record,job,proof=recovery.retry_plan(r,j,l,tmp_path/'retry',attempt=1,expected_prompt_sha=recovery.sha(p),expected_source_sha='source')
    assert record['run_id']=='eval-one-retry1' and job['name']==record['run_id']
    actual=record['argv'].copy();actual[actual.index('--output')+1]=r['run_dir'];assert actual==r['argv']
    assert proof['retry_of']==r['run_id'] and proof['failed_attempt_sha256']
    assert (Path(r['run_dir'])/'failure.json').read_bytes()==before
    assert job['allowed_nodes']==['heck-srv1','heck-srv3','heck-srv4','heck-srv5']
    assert not (tmp_path/'retry').exists()


@pytest.mark.parametrize('kind',['success','inflight','noncollision','prompt_changed','source_changed','argv_changed','budget'])
def test_refuse_unsafe_or_unnecessary_retry(tmp_path,kind):
    r,j,l,p=fixture(tmp_path);expected=recovery.sha(p);attempt=1
    if kind=='success':(Path(r['run_dir'])/'results.json').write_text('{}')
    elif kind=='inflight':(l/'exit_code').unlink()
    elif kind=='noncollision':(l/'launch.log').write_text('invalid checkpoint shape')
    elif kind=='prompt_changed':p.write_text('changed')
    elif kind=='source_changed':
        c=json.loads((Path(r['run_dir'])/'config.json').read_text());c['source_sha256']='changed';(Path(r['run_dir'])/'config.json').write_text(json.dumps(c))
    elif kind=='argv_changed':j['args'][-1]='8'
    else:attempt=2
    with pytest.raises(ValueError):recovery.retry_plan(r,j,l,tmp_path/'retry',attempt=attempt,expected_prompt_sha=expected,expected_source_sha='source')


def test_overlay_keeps_unaffected_cells_and_requires_terminal_success(tmp_path):
    r,j,l,p=fixture(tmp_path);rr,jj,proof=recovery.retry_plan(r,j,l,tmp_path/'retry',attempt=1,expected_prompt_sha=recovery.sha(p),expected_source_sha='source')
    effective=recovery.apply_overlay([r],{r['run_id']:dict(record=rr,proof=proof)})
    assert effective==[rr] and r['run_id']=='eval-one'
    bad=dict(rr);bad['K']=8
    with pytest.raises(ValueError):recovery.apply_overlay([r],{r['run_id']:dict(record=bad,proof=proof)})


def test_existing_dispatch_never_changes_or_duplicates(tmp_path):
    p=tmp_path/'dispatch.jsonl';p.write_text('{"name":"one","args":[]}\n')
    jobs=[dict(name='one',args=[],allowed_nodes=['different']),dict(name='two',args=['new'])]
    recovery.append_jobs(p,jobs);recovery.append_jobs(p,jobs)
    assert [j['name'] for j in recovery.lines(p)]==['one','two']
    with pytest.raises(ValueError):recovery.append_jobs(p,[dict(name='one',args=['changed'])])


def test_startup_free_memory_collision_is_retryable(tmp_path):
    r,j,l,p=fixture(tmp_path)
    (l/'launch.log').write_text('ValueError: Free memory on device cuda:0 (13.75/44.42 GiB) on startup is less than desired GPU memory utilization (0.7, 31.09 GiB).')
    rr,jj,proof=recovery.retry_plan(r,j,l,tmp_path/'retry',attempt=1,expected_prompt_sha=recovery.sha(p),expected_source_sha='source')
    assert rr['retry_of']==r['run_id']
