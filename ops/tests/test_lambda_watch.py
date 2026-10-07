import copy
import pytest
from ops.lambda_watch import reuse_controls, sealed


def record(arm='MVD',out='new'):
    return dict(arm=arm,seed=0,derivative_id='test',workload='own',K=4,cell='A11',run_id=out,run_dir=out,
                argv=['python','-m','atlas.run_cell','--drafter','same','--output',out],env={})


def test_controls_reused_with_exact_command_and_fs_always_new():
    new=record();old=record(out='old');fs=record('FS')
    assert reuse_controls([new,fs],[old])==[old,fs]


def test_changed_controls_rejected():
    old=record(out='old');old['argv'][4]='changed'
    with pytest.raises(ValueError,match='checkpoint'):reuse_controls([record()],[old])
    with pytest.raises(ValueError,match='missing'):reuse_controls([record()],[])


def test_seal_requires_final_symlink_and_exact_budget(tmp_path):
    import json
    ck=tmp_path/'checkpoints/0';ck.mkdir(parents=True)
    state=ck/'training_state.json';state.write_text(json.dumps(dict(epoch=0,global_step=249,local_step=0)))
    assert not sealed(tmp_path,250)
    (ck.parent/'epoch0_end').symlink_to('0')
    with pytest.raises(ValueError,match='budget'):sealed(tmp_path,250)
    state.write_text(json.dumps(dict(epoch=0,global_step=250,local_step=0)))
    assert sealed(tmp_path,250)


def test_identical_immutable_control_export_may_move(tmp_path):
    for name in ('old','new'):
        d=tmp_path/name;d.mkdir();(d/'model.safetensors').write_bytes(b'fixture');(d/'config.json').write_text('{}')
    old=record(out='old-output');new=record()
    old['argv'][4]=str(tmp_path/'old');new['argv'][4]=str(tmp_path/'new')
    assert reuse_controls([new],[old])==[old]
    (tmp_path/'new/model.safetensors').write_bytes(b'changed')
    with pytest.raises(ValueError,match='checkpoint'):reuse_controls([new],[old])
