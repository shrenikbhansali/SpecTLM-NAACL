from types import SimpleNamespace
import pytest
from followspec.disk_guard import require_free


def test_guard_checks_parent_for_new_output(tmp_path, monkeypatch):
    seen=[]
    def usage(path):
        seen.append(path);return SimpleNamespace(free=250*10**9)
    monkeypatch.setattr('followspec.disk_guard.shutil.disk_usage',usage)
    require_free(tmp_path/'not-created'/'output',250)
    assert seen==[tmp_path]


def test_guard_blocks_below_threshold(tmp_path,monkeypatch):
    monkeypatch.setattr('followspec.disk_guard.shutil.disk_usage',lambda _:SimpleNamespace(free=249*10**9))
    with pytest.raises(RuntimeError,match='free disk'):require_free(tmp_path,250)


def test_disabled_guard_does_not_stat(monkeypatch):
    monkeypatch.setattr('followspec.disk_guard.shutil.disk_usage',lambda _:pytest.fail('disabled'))
    require_free('/missing',0)
