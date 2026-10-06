import copy
import json
from pathlib import Path
import pytest
import torch
from followspec.mixture import mix,sha
from followspec.mixture_targets import validate_mixture,validate_registry


def registry_fixture(tmp_path):
    # Real factor files and the actual B3 manifest; no made-up mixture hashes.
    from safetensors.torch import save_file
    registry={}
    for i,name in enumerate(['a','b']):
        d=tmp_path/name;d.mkdir()
        cfg=dict(base_model_name_or_path='base',peft_type='LORA',r=2,lora_alpha=2,target_modules=['q_proj'])
        (d/'adapter_config.json').write_text(json.dumps(cfg))
        save_file({'base_model.model.model.layers.0.self_attn.q_proj.lora_A.weight':torch.ones(2,3),
                   'base_model.model.model.layers.0.self_attn.q_proj.lora_B.weight':torch.ones(3,2)*(i+1)},str(d/'adapter_model.safetensors'))
        registry[name]=dict(kind='bank',path=str(d),revision=str(i+1)*40,files_sha256={f:sha(d/f) for f in ['adapter_config.json','adapter_model.safetensors']})
    dest=tmp_path/'mixed';mix([registry[k]['path'] for k in ['a','b']],[.4,.6],1.,dest,max_lora_rank=8)
    registry['mixed']=dict(kind='mixture',path=str(dest),revision=sha(dest/'mixture_manifest.json'),source_ids=['a','b'],
        files_sha256={f:sha(dest/f) for f in ['adapter_config.json','adapter_model.safetensors','mixture_manifest.json']},acceptance_only=True)
    return registry


def test_bounded_mixture_requires_pinned_bank_sources_and_refuses_production(tmp_path):
    reg=registry_fixture(tmp_path)
    validate_registry(reg,allow_acceptance=True)
    with pytest.raises(ValueError,match='acceptance'):validate_registry(reg)
    bad=copy.deepcopy(reg);bad['a']['kind']='test'
    with pytest.raises(ValueError,match='bank'):validate_mixture('mixed',bad,allow_acceptance=True)
    bad=copy.deepcopy(reg);bad['mixed']['source_ids']=['b','a']
    with pytest.raises(ValueError,match='source'):validate_mixture('mixed',bad,allow_acceptance=True)


def test_changed_mixture_file_or_missing_admission_is_rejected(tmp_path):
    reg=registry_fixture(tmp_path);reg['mixed']['acceptance_only']=False
    with pytest.raises(ValueError,match='admission'):validate_registry(reg)
    reg['mixed']['acceptance_only']=True
    (Path(reg['mixed']['path'])/'adapter_config.json').write_text('{}')
    with pytest.raises(ValueError,match='hash'):validate_registry(reg,allow_acceptance=True)


def admission_fixture(tmp_path):
    import math
    from atlas.run_cell import sha256
    reg=registry_fixture(tmp_path);ref=tmp_path/'reference';ref.mkdir()
    queries=[dict(prompt_id=f'general-{i}',prompt=f'A training question {i}',split='training') for i in range(128)]
    (ref/'queries.jsonl').write_text(''.join(json.dumps(q)+'\n' for q in queries))
    (ref/'reference.jsonl').write_text(''.join(json.dumps(dict(prompt_id=q['prompt_id']))+'\n' for q in queries))
    rc=dict(source_prompts=str(ref/'queries.jsonl'),prompt_sha256=sha256(ref/'queries.jsonl'),reference_sha256=sha256(ref/'reference.jsonl'))
    (ref/'config.json').write_text(json.dumps(rc))
    pool=tmp_path/'pool.csv';pool.write_text('model_id,in_bank,revision,base_revision\n'+''.join(f"{k},True,{reg[k]['revision']},{'f'*40}\n" for k in ['a','b']))
    paths={}
    for name,ppl in [('a',2.),('b',4.),('mixed',3.)]:
        d=tmp_path/('score_'+name);d.mkdir();paths[name]=str(d)
        cfg=dict(derivative_id=name,engine_version='0.31.0',reference=str(ref/'reference.jsonl'),reference_sha256=rc['reference_sha256'],
            base_revision='f'*40,max_reference_tokens=2048,ppl_definition='fixed_prompt_tokens',max_lora_rank=128,seed=0)
        (d/'config.json').write_text(json.dumps(cfg));(d/'target_provenance.json').write_text(json.dumps(dict(revision=reg[name]['revision'],files_sha256=reg[name]['files_sha256'])))
        (d/'results.json').write_text(json.dumps(dict(loadable=True,ppl=ppl,scored_tokens=128)))
        (d/'per_prompt.jsonl').write_text(''.join(json.dumps(dict(prompt_id=q['prompt_id'],scored_tokens=1,nll_sum=math.log(ppl)))+'\n' for q in queries))
    return reg,paths,pool,ref


def test_admission_recomputes_worst_bank_bound_and_requires_complete_bank(tmp_path):
    from followspec.mixture_targets import collect_admission
    reg,paths,pool,ref=admission_fixture(tmp_path)
    r,e=collect_admission('mixed',reg,paths['mixed'],{k:paths[k] for k in ['a','b']},pool)
    assert r['accepted'] and r['mixture_ppl']==pytest.approx(3) and r['worst_bank_ppl']==pytest.approx(4)
    with pytest.raises(ValueError,match='every frozen bank'):collect_admission('mixed',reg,paths['mixed'],{'a':paths['a']},pool)
    p=Path(paths['mixed'])/'results.json';data=json.loads(p.read_text());data['ppl']=1;p.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='summary'):collect_admission('mixed',reg,paths['mixed'],{k:paths[k] for k in ['a','b']},pool)


def test_a2_speed_reference_cannot_be_used_as_mixture_training_general_set(tmp_path):
    from followspec.mixture_targets import collect_admission
    reg,paths,pool,ref=admission_fixture(tmp_path)
    rows=[json.loads(s) for s in (ref/'queries.jsonl').read_text().splitlines()]
    rows[0]['split']='evaluation';rows[0]['prompt_id']='speed-0'
    (ref/'queries.jsonl').write_text(''.join(json.dumps(q)+'\n' for q in rows))
    with pytest.raises(ValueError,match='never SPEED'):collect_admission('mixed',reg,paths['mixed'],{k:paths[k] for k in ['a','b']},pool)


def test_mixture_rendering_uses_pinned_base_template_without_an_a2_filter_argument(tmp_path,monkeypatch):
    import sys,types
    from followspec.render_inputs import main
    from followspec.tests.test_render_inputs import Tokenizer
    reg=registry_fixture(tmp_path);registry=tmp_path/'registry.json';registry.write_text(json.dumps(reg))
    base=tmp_path/('f'*40);base.mkdir();(base/'tokenizer.json').write_text('{}');(base/'tokenizer_config.json').write_text(json.dumps(dict(chat_template='template')))
    prompts=tmp_path/'prompts.jsonl';prompts.write_text(json.dumps(dict(prompt_id='p',prompt='A training question?',split='training'))+'\n')
    tok=Tokenizer();tok.chat_template='template'
    monkeypatch.setitem(sys.modules,'transformers',types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *a,**k:tok)))
    out=tmp_path/'rendered';monkeypatch.setattr(sys,'argv',['render','--base-snapshot',str(base),'--base-id','base','--base-revision','f'*40,
        '--tokenizer',str(base),'--tokenizer-revision','f'*40,'--derivative-id','mixed','--target-registry',str(registry),'--acceptance-smoke',
        '--prompts',str(prompts),'--output',str(out)])
    main()
    cfg=json.loads((out/'config.json').read_text())
    assert cfg['acceptance_only'] and cfg['prompt_target_revision']==reg['mixed']['revision']
    assert 'filter_results_sha256' not in cfg and cfg['mixture_registry']['entry']['source_ids']==['a','b']


def test_production_admission_is_recomputed_and_a_failed_bound_cannot_be_promoted(tmp_path):
    from followspec.mixture_targets import collect_admission
    import math
    reg,paths,pool,ref=admission_fixture(tmp_path)
    bank_runs={k:paths[k] for k in ['a','b']}
    result,evidence=collect_admission('mixed',reg,paths['mixed'],bank_runs,pool)
    proof=tmp_path/'admission';proof.mkdir()
    (proof/'config.json').write_text(json.dumps(dict(mixture_filter_run=paths['mixed'],bank_filter_runs=bank_runs,pool_manifest=str(pool),evidence_sha256=evidence)))
    (proof/'results.json').write_text(json.dumps(result))
    reg['mixed'].update(acceptance_only=False,admission=dict(path=str(proof),files_sha256={f:sha(proof/f) for f in ['config.json','results.json']}))
    validate_registry(reg)
    d=Path(paths['mixed']);rows=[json.loads(s) for s in (d/'per_prompt.jsonl').read_text().splitlines()]
    for row in rows:row['nll_sum']=math.log(5.)
    (d/'per_prompt.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    data=json.loads((d/'results.json').read_text());data['ppl']=5.;(d/'results.json').write_text(json.dumps(data))
    bad,_=collect_admission('mixed',reg,paths['mixed'],bank_runs,pool);assert not bad['accepted']
    with pytest.raises(ValueError,match='admission'):validate_registry(reg)


def test_mvd_never_uses_mixture_targets_even_in_bounded_acceptance(tmp_path):
    from followspec.token_data import build_manifest
    reg=registry_fixture(tmp_path)
    with pytest.raises(ValueError,match='MVD'):
        build_manifest('MVD',[dict(child_id='mixed',run='unused')],registry=reg,base_revision='f'*40,initialization_revision='d'*40,allow_acceptance=True)
