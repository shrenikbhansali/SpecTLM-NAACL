import hashlib
import json
import shutil
from pathlib import Path
import pytest
from atlas.relocation import Relocation, read_json, read_jsonl
from followspec.production_pipeline import checked_stage


def fixture(tmp_path):
    old=tmp_path/'heck';new=tmp_path/'ice';old.mkdir()
    (old/'weights').write_bytes(b'sealed weights')
    obj=dict(path=str(old/'weights'),sources={str(old/'weights'):{'sha256':'proof'}},
        prompt=str(old/'weights'),completion=str(old/'weights'),reference=str(old/'weights'),
        argv=['python','--manifest',str(old/'config.json')],rendered_token_ids=[1,2,3])
    (old/'config.json').write_text(json.dumps(obj))
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir()}
    (old/'stage_files.json').write_text(json.dumps(hashes))
    shutil.copytree(old,new)
    manifest=dict(version=1,prefixes=[dict(source=str(old),destination=str(new))],files_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir()})
    f=tmp_path/'relocation.json';f.write_text(json.dumps(manifest))
    return old,new,f,obj


def enable(monkeypatch,path):
    monkeypatch.setenv('SPECTLM_RELOCATION',str(path))
    monkeypatch.setenv('SPECTLM_RELOCATION_SHA256',hashlib.sha256(path.read_bytes()).hexdigest())


def test_readtime_paths_and_original_seals(tmp_path,monkeypatch):
    old,new,f,obj=fixture(tmp_path);before={p.name:p.read_bytes() for p in new.iterdir()};enable(monkeypatch,f)
    root,cfg=checked_stage(new)
    assert cfg['path']==str(new/'weights') and list(cfg['sources'])==[str(new/'weights')]
    assert cfg['argv'][-1]==str(new/'config.json')
    for key in ['prompt','completion','reference','rendered_token_ids']:assert cfg[key]==obj[key]
    assert before=={p.name:p.read_bytes() for p in new.iterdir()}
    assert read_json(old/'config.json')==cfg
    monkeypatch.delenv('SPECTLM_RELOCATION');assert read_json(new/'config.json')==obj


def test_every_hash_rechecked_missing_tamper_and_pinned_map(tmp_path,monkeypatch):
    old,new,f,obj=fixture(tmp_path);enable(monkeypatch,f)
    read_json(new/'config.json')
    (new/'weights').write_bytes(b'wrong')
    with pytest.raises(ValueError,match='changed'):Relocation.from_file(f).verify()
    (new/'weights').unlink()
    with pytest.raises(ValueError,match='missing'):Relocation.from_file(f).verify()
    f.write_text(f.read_text()+' ')
    with pytest.raises(ValueError,match='relocation manifest changed'):read_json(new/'config.json')


def test_reject_traversal_collisions_and_prefix_boundaries(tmp_path):
    old,new,f,obj=fixture(tmp_path);r=Relocation.from_file(f);r.verify()
    assert r.path(str(old)+'-other/file')==str(old)+'-other/file'
    with pytest.raises(ValueError,match='traversal'):r.path(str(old/'..'/'outside'))
    d=json.loads(f.read_text());d['prefixes'].append(dict(source=str(old),destination=str(new/'other')))
    with pytest.raises(ValueError,match='duplicate'):Relocation(d)
    d=json.loads(f.read_text());d['files_sha256'][str(old/'..'/'other')]='0'*64
    with pytest.raises(ValueError,match='traversal'):Relocation(d)


def test_copied_sealed_training_and_evaluation_without_source(tmp_path,monkeypatch):
    from followspec.tests.test_evaluation_jobs import completed_training
    from followspec.training_jobs import training_jobs
    from followspec.evaluation_jobs import evaluation_jobs
    old=tmp_path/'heck';new=tmp_path/'ice';old.mkdir()
    training,targets=completed_training(old)
    files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in old.rglob('*') if p.is_file() and '.git' not in p.parts}
    shutil.copytree(old,new)
    f=tmp_path/'map.json';f.write_text(json.dumps(dict(version=1,prefixes=[dict(source=str(old),destination=str(new))],files_sha256=files)))
    old.rename(tmp_path/'unavailable');enable(monkeypatch,f);monkeypatch.setenv('SITE','ice')
    before={p:Path(p).read_bytes() for p in (new/'final/stage_files.json',new/'training/stage_files.json')}
    train=training_jobs(new/'final',new/'new-training',python='/ice/train-python',training_seeds=[0],job_prefix='ice-m3')
    evaluation=evaluation_jobs(new/'training',new/'targets.json',new/'new-eval',python='/ice/eval-python',training_seeds=[0],job_prefix='ice-eval')
    for stage in [train,evaluation]:
        jobs=[json.loads(s) for s in (stage/'jobs.jsonl').read_text().splitlines()]
        assert jobs and all(j['allowed_nodes']==['slurm'] and j['args'][:4]==['--node','slurm','--gpus','slurm'] for j in jobs)
        assert str(old) not in json.dumps(jobs)
    assert before=={p:p.read_bytes() for p in before}
    assert len(read_json(evaluation/'index_k4.json'))==15


def test_reject_overlapping_source_destination(tmp_path):
    old,new,f,obj=fixture(tmp_path);d=json.loads(f.read_text());d['prefixes'][0]['destination']=str(old/'copy')
    with pytest.raises(ValueError,match='overlap'):Relocation(d)
