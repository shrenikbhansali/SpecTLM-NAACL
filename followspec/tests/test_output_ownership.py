"""A refused retry must leave the original run byte-for-byte unchanged."""
import json
import pytest
from followspec.train_eagle3 import owned_output


def test_refused_existing_run_keeps_every_file_unchanged(tmp_path):
    out=tmp_path/'completed';out.mkdir()
    (out/'results.json').write_bytes(b'{"loss": 1}\n')
    before={p.name:p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):
        with owned_output(out,0,lambda:None):
            pytest.fail('existing run was entered')
    assert {p.name:p.read_bytes() for p in out.iterdir()}==before


def test_owned_failure_is_recorded_and_original_error_propagates(tmp_path):
    out=tmp_path/'new'
    with pytest.raises(ValueError,match='training failed'):
        with owned_output(out,0,lambda:None):
            (out/'config.json').write_text('{}')
            raise ValueError('training failed')
    assert json.loads((out/'failure.rank0.json').read_text())==dict(error_type='ValueError',error='training failed')
    assert (out/'config.json').read_text()=='{}'


def test_nonzero_rank_does_not_write_without_successful_barrier(tmp_path):
    out=tmp_path/'old';out.mkdir();(out/'results.json').write_text('{}')
    def failed_barrier():raise RuntimeError('rank zero did not create output')
    with pytest.raises(RuntimeError,match='rank zero'):
        with owned_output(out,1,failed_barrier):
            pytest.fail('failed launch was entered')
    assert sorted(p.name for p in out.iterdir())==['results.json']


def test_rank_specific_failure_never_overwrites_existing_failure(tmp_path):
    out=tmp_path/'new'
    with pytest.raises(ValueError):
        with owned_output(out,0,lambda:None):
            (out/'failure.rank0.json').write_text('first failure')
            raise ValueError('later failure')
    assert (out/'failure.rank0.json').read_text()=='first failure'
