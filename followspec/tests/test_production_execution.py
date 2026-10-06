"""New M2 jobs can use a clean updated checkout without editing old stages."""
import json
import subprocess
import sys
from pathlib import Path
import pytest
from followspec.production_pipeline import finish,write_new,read


def repo(path,lock='same engine'):
    path.mkdir();subprocess.run(['git','init','-q',str(path)],check=True)
    p=path/'atlas/env';p.mkdir(parents=True);(p/'requirements.lock').write_text(lock)
    subprocess.run(['git','-C',str(path),'add','.'],check=True)
    subprocess.run(['git','-C',str(path),'-c','user.name=test','-c','user.email=test@localhost','commit','-qm','fixture'],check=True)
    return path


def test_execution_override_preserves_spec_and_rejects_dirty_or_different_engine(tmp_path):
    from followspec.production_pipeline import execution_spec
    old=repo(tmp_path/'old');new=repo(tmp_path/'new')
    spec=dict(code_repo=str(old),seed=101,base_revision='a'*40)
    assert execution_spec(spec,None)==spec
    updated=execution_spec(spec,str(new))
    assert updated['code_repo']==str(new) and spec['code_repo']==str(old)
    assert updated['execution_code_commit']==subprocess.check_output(['git','-C',str(new),'rev-parse','HEAD'],text=True).strip()
    bad=repo(tmp_path/'bad','different engine')
    with pytest.raises(ValueError,match='engine'):execution_spec(spec,str(bad))
    (new/'atlas/env/requirements.lock').write_text('dirty')
    with pytest.raises(ValueError,match='clean'):execution_spec(spec,str(new))


def test_mixture_job_uses_explicit_fix5_flag_and_keeps_source_stage_unchanged(tmp_path,monkeypatch):
    from followspec.production_pipeline import mixture_prompts
    old=repo(tmp_path/'old');new=repo(tmp_path/'new')
    general=tmp_path/'general.jsonl';general.write_text('{"prompt":"general"}\n')
    forbidden=tmp_path/'eval.jsonl';forbidden.write_text('{"prompt":"evaluation"}\n')
    spec=dict(code_repo=str(old),python=sys.executable,seed=101,base_id='base',base_revision='a'*40,
              base_snapshot='/base',general_prompts=str(general),forbidden_files=[str(forbidden)])
    source=tmp_path/'admission';source.mkdir()
    write_new(source/'registry.json',{'mix':dict(kind='mixture',path='/mix',revision='b'*64)})
    finish(source,dict(stage='admit',spec=spec),dict(ready=True))
    before={p:p.read_bytes() for p in source.iterdir()}
    monkeypatch.setattr('followspec.mixture_targets.validate_registry',lambda reg:None)
    out=mixture_prompts(str(source),str(tmp_path/'jobs'),[],code_repo=str(new),d23_oversampling=True)
    job=json.loads((out/'jobs.jsonl').read_text().splitlines()[0]);args=job['args']
    assert args[args.index('--code-repo')+1]==str(new)
    assert '--d23-oversampling' in args[args.index('--')+1:]
    assert read(out/'config.json')['spec']['execution_code_commit']
    assert all(p.read_bytes()==b for p,b in before.items())
    legacy=mixture_prompts(str(source),str(tmp_path/'legacy'),[])
    assert '--d23-oversampling' not in json.loads((legacy/'jobs.jsonl').read_text().splitlines()[0])['args']
