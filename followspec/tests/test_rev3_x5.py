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

def test_reporting_requires_every_planned_seed():
    from followspec.rev3_x5_analysis import seed_group_ready
    assert not seed_group_ready([{'seed':0},{'seed':1}],0)
    assert seed_group_ready([{'seed':0},{'seed':1},{'seed':2}],0)
    assert seed_group_ready([{'seed':0}],1)
    assert not seed_group_ready([{'seed':0},{'seed':0},{'seed':2}],0)

def test_grouped_publication_is_not_launched_twice(tmp_path):
    from followspec.rev3_x5 import publication_complete
    assert not publication_complete(tmp_path)
    for i in range(2):
        (tmp_path/f'group-{i}').mkdir()
    (tmp_path/'group-0/published.json').write_text('{}')
    assert not publication_complete(tmp_path)
    (tmp_path/'group-1/published.json').write_text('{}')
    assert publication_complete(tmp_path)
    simple=tmp_path/'single';simple.mkdir();(simple/'published.json').write_text('{}')
    assert publication_complete(simple)

def test_x5_completion_only_updates_owned_row(tmp_path):
    from followspec.rev3_x5_analysis import ping_board
    p=tmp_path/'MASTER.md';p.write_text('| OTHER | keep |\n| REV3-X5 | task | P0 | codex | D55 | Sun | in progress | codex-1 / now | old |\n')
    assert not ping_board(tmp_path,{'ready_for_review':False},'evidence','stamp')
    assert ping_board(tmp_path,{'ready_for_review':True},'evidence','stamp')
    assert '| OTHER | keep |' in p.read_text() and '| review |' in p.read_text()
    assert not ping_board(tmp_path,{'ready_for_review':True},'evidence','stamp')
