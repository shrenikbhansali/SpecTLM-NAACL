import subprocess
import sys
from pathlib import Path
import pytest
from ops import queue


def test_second_process_cannot_claim_same_owner_then_release(tmp_path):
    from ops.queue import acquire_owner_lock
    lock=acquire_owner_lock('method-M1',tmp_path)
    script='from ops.queue import acquire_owner_lock; import sys; lock=acquire_owner_lock(sys.argv[1],sys.argv[2])'
    args=[sys.executable,'-c',script,'method-M1',str(tmp_path)]
    busy=subprocess.run(args,capture_output=True,text=True)
    assert busy.returncode!=0 and 'already has a dispatcher' in busy.stderr
    lock.close()
    assert subprocess.run(args,capture_output=True,text=True).returncode==0


def test_different_owners_can_dispatch_independently(tmp_path):
    from ops.queue import acquire_owner_lock
    first=acquire_owner_lock('method',tmp_path);second=acquire_owner_lock('other',tmp_path)
    first.close();second.close()


def test_empty_owner_is_rejected(tmp_path):
    from ops.queue import acquire_owner_lock
    with pytest.raises(ValueError,match='owner'):acquire_owner_lock('',tmp_path)
