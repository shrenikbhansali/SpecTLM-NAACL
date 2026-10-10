import pytest
from pathlib import Path

def test_dflash_timing_opt_in_native_k_and_defaults():
    from atlas.timing_panel import parser,timing_speculation
    base=['--target','t','--target-revision','r','--prompts','p','--frozen-harness','h','--output','o']
    a=parser().parse_args(base);assert a.method=='eagle3' and a.K==4
    a=parser().parse_args(base+['--method','dflash','--K','10','--drafter','d','--drafter-revision','r','--batch-size','1'])
    assert timing_speculation(a)['num_speculative_tokens']==10
    a.draft_vocab_mapping=True
    with pytest.raises(ValueError):timing_speculation(a)

def test_export_only_checkpoint_policy_preserves_default():
    from followspec.family_repair import save_final_trainable
    assert save_final_trainable(False,True,True,[100],100)
    assert not save_final_trainable(True,True,True,[100],100)
    for args in [(True,False,True,[100],100),(True,True,False,[100],100),(True,True,True,[50,100],100)]:
        with pytest.raises(ValueError):save_final_trainable(*args)

def test_x5_scope_cardinality_and_protocol():
    from followspec.rev3_x5 import training_specs
    rows=training_specs()
    assert len(rows)==8 and len({(r['target'],r['arm'],r['seed']) for r in rows})==8
    assert sum(r['target']==0 for r in rows)==6
    assert all(r['workloads']==['speed128','math500','math32-8192'] for r in rows)
