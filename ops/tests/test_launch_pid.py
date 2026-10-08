from ops.launch import collect_pid
from ops.track_t import is_queue_command


def test_nowait_preserves_pid_file_without_sleeping(tmp_path,monkeypatch):
    sleeps=[]
    monkeypatch.setattr('ops.launch.time.sleep',lambda x:sleeps.append(x))
    assert collect_pid(tmp_path,wait=False) is None and sleeps==[]
    (tmp_path/'pid').write_text('123\n')
    assert collect_pid(tmp_path,wait=False)==123 and sleeps==[]
    assert collect_pid(tmp_path,wait=True)==123


def test_default_retains_50_visibility_retries(tmp_path,monkeypatch):
    sleeps=[]
    monkeypatch.setattr('ops.launch.time.sleep',lambda x:sleeps.append(x))
    assert collect_pid(tmp_path,wait=True) is None
    assert sleeps==[.2]*50


def test_queue_guard_ignores_shells_and_python_inline_mentions():
    assert is_queue_command(['python','/code/ops/queue.py','--jobs','/dispatch'])
    assert not is_queue_command(['bash','-c','python /code/ops/queue.py'])
    assert not is_queue_command(['python','-c',"x='/code/ops/queue.py'"])
