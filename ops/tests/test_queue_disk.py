import json
from types import SimpleNamespace
import pytest
from ops import queue


def test_disk_guard_default_does_not_probe(monkeypatch):
    monkeypatch.setattr(queue, 'disk_free_gb', lambda path: pytest.fail('legacy default must not query disk'))
    assert queue.disk_admission('/missing', 0) is None


def test_disk_guard_reports_low_space(monkeypatch):
    monkeypatch.setattr(queue, 'disk_free_gb', lambda path: 249.9)
    assert queue.disk_admission('/unused', 250) == 249.9
    assert queue.disk_admission('/unused', 249) is None


def test_queue_disk_hold_preserves_job_until_space_returns(tmp_path,monkeypatch):
    jobs=tmp_path/'jobs';jobs.write_text(json.dumps(dict(name='same',args=['unchanged']))+'\n')
    log=tmp_path/'log';out=tmp_path/'run';out.mkdir();(out/'exit_code').write_text('0')
    probes=iter([240,400]);monkeypatch.setattr(queue,'disk_free_gb',lambda path:next(probes))
    monkeypatch.setattr(queue,'gpu_busy',lambda *a:False);monkeypatch.setattr(queue,'reserved',lambda *a:set())
    calls=[]
    def launch(cmd,**kw):
        calls.append(cmd);return SimpleNamespace(returncode=0,stdout='launched\n  '+str(out),stderr='')
    monkeypatch.setattr(queue.subprocess,'run',launch);monkeypatch.setattr(queue.time,'sleep',lambda n:None)
    queue.dispatch(SimpleNamespace(slots='node:0',jobs=str(jobs),log=str(log),owner='test',poll=0,min_free_gb=250,disk_path=str(tmp_path)))
    events=[json.loads(l) for l in log.read_text().splitlines()]
    assert [r['event'] for r in events]==['disk_hold','launched','finished','queue_empty']
    assert len(calls)==1 and calls[0][-1]=='unchanged'
    assert events[0]['pending']==1 and events[1]['name']=='same'
