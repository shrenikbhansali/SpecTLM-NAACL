import pytest
from ops.placement import place_job, launcher_placement
from followspec.production import launcher_job


def test_heck_default_and_ice_job_placement(monkeypatch):
    monkeypatch.delenv('SITE',raising=False)
    job=dict(name='test',args=['--task','M4','--','python','-m','atlas.run_cell'])
    assert place_job(job)==job
    assert launcher_placement(job['args'])==['--node','heck-srv4','--gpus','0',*job['args']]
    monkeypatch.setenv('SITE','ice');got=place_job(job,heck_nodes=['heck-srv1'])
    assert got['allowed_nodes']==['slurm']
    assert got['args'][:4]==['--node','slurm','--gpus','slurm']
    assert launcher_placement(got['args'])==got['args']
    assert place_job(got)==got
    with pytest.raises(ValueError,match='placement'):launcher_placement(['--node','heck-srv1','--gpus','0','--','true'])


def test_all_launcher_jobs_propagate_site_and_relocation(monkeypatch,tmp_path):
    import json,hashlib
    from atlas.relocation import Relocation
    old=tmp_path/'old';new=tmp_path/'new';old.mkdir();new.mkdir();(new/'proof').write_text('ok')
    f=tmp_path/'map.json';f.write_text(json.dumps(dict(version=1,prefixes=[dict(source=str(old),destination=str(new))],files_sha256={str(old/'proof'):hashlib.sha256(b'ok').hexdigest()})))
    monkeypatch.setenv('SITE','ice');monkeypatch.setenv('SPECTLM_RELOCATION',str(f));monkeypatch.setenv('SPECTLM_RELOCATION_SHA256',hashlib.sha256(f.read_bytes()).hexdigest())
    spec=dict(python='/ice/python',code_repo='/ice/repo',seed=0,base_id='base',base_revision='a'*40)
    job=launcher_job(spec,'test','M3','/ice/prompts',['-m','followspec.train_eagle3'])
    assert job['allowed_nodes']==['slurm']
    assert 'SPECTLM_RELOCATION='+str(f) in job['args'] and 'SITE=ice' in job['args']
