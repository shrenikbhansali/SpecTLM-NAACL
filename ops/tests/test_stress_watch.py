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
