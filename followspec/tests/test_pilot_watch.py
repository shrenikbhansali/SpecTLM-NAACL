import json
from pathlib import Path
import pytest
from followspec.tests.test_pilot_handoff import pilot,seal


def test_watch_only_notices_sealed_exports_and_failures(tmp_path):
    from followspec.pilot_watch import checkpoint_signature
    _,training,_=pilot(tmp_path)
    for p in (training/'runs').glob('*/results.json'):p.unlink()
    a=checkpoint_signature(training)
    run=training/'runs/m3-d38-fs-s0';p=run/'checkpoints/0/training_state.json';p.write_text('{"epoch":0,"global_step":1,"local_step":0}')
    assert checkpoint_signature(training)==a
    (run/'checkpoints/epoch0_end').symlink_to('0')
    assert checkpoint_signature(training)!=a
    (run/'failure.rank0.json').write_text('{}')
    with pytest.raises(ValueError,match='failed'):checkpoint_signature(training)


def test_dispatch_append_is_idempotent_and_preserves_existing_training(tmp_path):
    from followspec.pilot_watch import append_dispatch
    path=tmp_path/'jobs.jsonl';job={'name':'training','args':['train']};path.write_text(json.dumps(job)+'\n')
    new={'name':'eval','args':['evaluate']}
    assert append_dispatch(path,[new])==1
    assert append_dispatch(path,[new])==0
    assert [json.loads(l) for l in path.read_text().splitlines()]==[job,new]
    with pytest.raises(ValueError,match='identity'):append_dispatch(path,[{'name':'eval','args':['different']}])
