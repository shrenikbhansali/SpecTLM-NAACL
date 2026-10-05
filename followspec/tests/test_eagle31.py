"""Synthetic fixtures test the checker; these are not B11 acceptance evidence."""
import copy
import json
from pathlib import Path
import pytest
from followspec.baselines.eagle31 import compare, validate_draft


def cell(root, name, value):
    path=root/name;path.mkdir()
    cfg=dict(target='meta-llama/Llama-3.1-8B-Instruct',target_revision='a'*40,
        drafter=('RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3' if name=='reference' else '/local/eagle31'),
        drafter_revision='b'*40,method='eagle3',K=4,seed=0,max_new_tokens=512,
        batch_size=1,max_model_len=4096,temperature=0.,top_p=1.,dtype='bfloat16',
        enable_prefix_caching=False,prompt_sha256='c'*64,engine_version='0.31.0',n=128,
        code_commit='d'*40,code_dirty=False)
    if name!='reference':cfg['drafter_files_sha256']={'config.json':'e'*64,'model.safetensors':'f'*64}
    (path/'config.json').write_text(json.dumps(cfg))
    (path/'drafter_config.json').write_text(json.dumps(dict(fc_norm=True,norm_output=True)))
    (path/'results.json').write_text(json.dumps(dict(n=128,macro_acceptance_length=value,
        engine_version='0.31.0',generation_wall_s=3.,gpu_type='NVIDIA H100',K=4)))
    (path/'per_prompt.jsonl').write_text(''.join(json.dumps(dict(prompt_id=str(i),acceptance_length=value))+'\n' for i in range(128)))
    return path


def test_reports_shortfall_without_changing_acceptance_requirement(tmp_path):
    ref=cell(tmp_path,'reference',3.0);new=cell(tmp_path,'new',2.8)
    report=compare(new,ref,expected_prompt_hash='c'*64,engine_version='0.31.0')
    assert report['n']==128 and report['shortfall']==pytest.approx(.2)
    assert report['baseline_met'] is False and report['requirement']=='shortfall reported'
    assert report['difference_ci95']==pytest.approx([-.2,-.2])


@pytest.mark.parametrize('field,value',[('K',8),('prompt_sha256','x'*64),('temperature',.8),('engine_version','0.17.1'),('adapter','child')])
def test_refuses_mismatched_or_nonbase_cells(tmp_path,field,value):
    ref=cell(tmp_path,'reference',3.);new=cell(tmp_path,'new',3.1)
    cfg=json.loads((new/'config.json').read_text());cfg[field]=value
    (new/'config.json').write_text(json.dumps(cfg))
    with pytest.raises(ValueError):compare(new,ref,expected_prompt_hash='c'*64,engine_version='0.31.0')


def test_refuses_duplicate_prompts_and_disabled_eagle31(tmp_path):
    ref=cell(tmp_path,'reference',3.);new=cell(tmp_path,'new',3.1)
    (new/'drafter_config.json').write_text('{"fc_norm":false,"norm_output":true}')
    with pytest.raises(ValueError,match='normalization'):compare(new,ref,expected_prompt_hash='c'*64,engine_version='0.31.0')
    (new/'drafter_config.json').write_text('{"fc_norm":true,"norm_output":true}')
    lines=(new/'per_prompt.jsonl').read_text().splitlines();lines[-1]=lines[0]
    (new/'per_prompt.jsonl').write_text('\n'.join(lines))
    with pytest.raises(ValueError,match='duplicate'):compare(new,ref,expected_prompt_hash='c'*64,engine_version='0.31.0')


def test_draft_config_matches_specbundle_except_requested_norms():
    cfg=json.loads((Path(__file__).parents[1]/'baselines/eagle31_llama.json').read_text())
    validate_draft(cfg)
    assert cfg['hidden_size']==4096 and cfg['draft_vocab_size']==32000
    assert cfg['fc_norm'] is True and cfg['norm_output'] is True
