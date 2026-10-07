from pathlib import Path
from ops.stress_watch import filter_commands


def test_filter_pairs_use_original_reference_baseline_and_fixed_threshold(tmp_path):
    spec=dict(base_snapshot='/base',base_id='base',base_revision='a'*40,drafter_revision='d'*40)
    targets=[dict(model_id='base'),dict(model_id='local/test',adapter='/adapter',revision='e'*40)]
    jobs=filter_commands(spec,targets,tmp_path,Path('/reference.jsonl'),Path('/baseline'))
    assert len(jobs)==1
    name,cmd=jobs[0]
    assert cmd[cmd.index('--baseline')+1]=='/baseline'
    assert cmd[cmd.index('--repetition-threshold')+1]=='0.5'
    assert cmd[cmd.index('--adapter-revision')+1]=='e'*40
    assert cmd[cmd.index('--max-lora-rank')+1]=='128'


def test_lambda_continuation_uses_retried_reference_index_and_separate_lock(tmp_path):
    from ops.stress_watch import lambda_command
    cfg={k:k for k in ('frozen_code','frozen_commit','dispatch_jobs','queue_log','python')}
    cfg['panel']=str(tmp_path/'panel');cfg['evaluation_stage']=str(tmp_path/'evaluation')
    cmd=lambda_command(tmp_path,cfg,'/campaign')
    assert cmd[cmd.index('--reference-index')+1]==str(tmp_path/'report/index_k4.json')
    assert cmd[cmd.index('--lock-name')+1]=='lambda_stress_watch.lock'
    assert cmd[cmd.index('--targets')+1]==str(tmp_path/'panel/targets.json')
