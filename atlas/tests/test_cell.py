"""B2 contracts; synthetic fixtures never constitute GPU acceptance evidence."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
from atlas.run_cell import metrics, aggregate, ensure_unpaused, load_prompts, compare_golden


def test_macro_bonus_and_conditional_metrics():
    a=metrics([0,1,2],[4,4,4],4)
    b=metrics([4],[4],4)
    assert a['acceptance_length']==2
    assert a['per_position_acceptance']==pytest.approx([2/3,1/3,0,0])
    assert a['per_position_conditional_acceptance']==[2/3,0.5,0,None]
    result=aggregate([a,b])
    assert result['macro_acceptance_length']==3.5
    assert result['n']==2
    assert result['macro_acceptance_length'] != 1+7/4


@pytest.mark.parametrize('accepted,drafted', [([],[]),([2],[1]),([-1],[4]),([1],[5]),([1,2],[4])])
def test_invalid_counters_fail(accepted,drafted):
    with pytest.raises(ValueError): metrics(accepted,drafted,4)


def test_truncated_draft_conditional_denominator():
    r=metrics([1,2],[1,4],4)
    assert r['per_position_conditional_acceptance'][:3] == [1,1,0]


def test_pause_detected_from_worktree(tmp_path):
    (tmp_path/'tlm-spec-maintenance').mkdir()
    (tmp_path/'tlm-spec-maintenance/EXPERIMENTS_PAUSED.json').write_text('{}')
    wd=tmp_path/'.worktrees/B2';wd.mkdir(parents=True)
    with pytest.raises(RuntimeError,match='paused'): ensure_unpaused(wd)


def test_prompt_duplicate_and_count(tmp_path):
    p=tmp_path/'prompts.jsonl';p.write_text('{"prompt_id":"x","prompt":"hello"}\n'*2)
    with pytest.raises(ValueError,match='duplicate'): load_prompts(p)
    p.write_text('{"prompt_id":"x","prompt":"hello"}\n')
    assert len(load_prompts(p))==1


def test_golden_drift_parity_and_comparable_configs():
    cfg=dict(target='base',target_revision='a'*40,drafter='draft',drafter_revision='b'*40,
             method='eagle3',K=4,prompt_sha256='x',seed=0,max_new_tokens=512,batch_size=1,engine_version='0.31.0')
    def cell(v,**changes): return dict(config=cfg|changes,results={'macro_acceptance_length':v,'n':128,'generation_wall_s':1})
    report=compare_golden(cell(3.1),cell(3.105),cell(2.86,adapter='child'),cell(2.862,target='merged',target_revision='c'*40))
    assert report['repeat_within_ledger_noise_floor']
    assert report['child_negative_shift']
    assert report['lora_merged_within_repeat_difference']
    with pytest.raises(ValueError,match='matched'):
        compare_golden(cell(3.1),cell(3.105,seed=1),cell(2.86),cell(2.86))


def test_dry_run_is_print_only_under_pause(tmp_path):
    p=tmp_path/'prompts.jsonl';p.write_text('{"prompt_id":"x","prompt":"hello"}\n')
    out=tmp_path/'run'
    result=subprocess.run([sys.executable,'-m','atlas.run_cell','--target','base/model','--target-revision','a'*40,
        '--drafter','org/draft','--drafter-revision','b'*40,'--method','eagle3','--prompts',str(p),'--output',str(out),
        '--dry-run'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['dry_run'] is True
    assert not out.exists()


def test_speculators_config_metadata_does_not_require_hf_model_type(tmp_path):
    from atlas.run_cell import read_drafter_config
    config={'architectures':['Eagle3Speculator'],'speculators_model_type':'eagle3','draft_vocab_size':32000}
    (tmp_path/'config.json').write_text(json.dumps(config))
    assert read_drafter_config(str(tmp_path),'a'*40)==config
