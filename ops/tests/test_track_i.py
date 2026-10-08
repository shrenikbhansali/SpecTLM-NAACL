from ops.track_i import select_targets, independent_pair
from pathlib import Path
import pytest


def test_stratification_is_reproducible_and_does_not_use_outcomes():
    rows=[dict(base=b,model_id=f'{b}-{i}',type='lora_adapter' if i%2 else 'full_finetune',pool='test',a2_ppl_ratio=i) for b in ['llama','qwen3'] for i in range(40)]
    chosen=select_targets(rows)
    assert len(chosen)==60 and sum(r['base']=='llama' for r in chosen)==30
    reverse=[dict(r,a2_ppl_ratio=100-r['a2_ppl_ratio']) for r in rows[::-1]]
    assert [r['model_id'] for r in chosen]==[r['model_id'] for r in select_targets(reverse)]
    with pytest.raises(ValueError):select_targets(rows[:20])


def test_lora_pair_changes_only_target_adapter_with_pinned_independent_draft(tmp_path):
    r=dict(base='llama',model_id='org/child',revision='b'*40,staged_path='/adapter',type='lora_adapter',pool='test',r='32',license='llama3.1')
    d=dict(id='meta-llama/Llama-3.2-1B-Instruct',path='/draft',revision='d'*40)
    jobs,records=independent_pair(r,d,'/prompts',tmp_path,Path('/code'),'c'*40)
    assert len(jobs)==len(records)==2
    for j,rec in zip(jobs,records):
        a=j['args'];cmd=a[a.index('--')+1:]
        assert cmd[cmd.index('--method')+1]=='draft_model'
        assert cmd[cmd.index('--drafter')+1]=='/draft' and '--draft-vocab-mapping' in cmd
        assert cmd[cmd.index('--max-lora-rank')+1]=='32'
        assert j['allowed_nodes']==['heck-srv4','heck-srv2']
        assert rec['frozen_commit']=='c'*40
    assert '--enable-lora' in records[0]['argv'] and '--adapter' in records[1]['argv']
    assert records[0]['prompt_file']==records[1]['prompt_file']
