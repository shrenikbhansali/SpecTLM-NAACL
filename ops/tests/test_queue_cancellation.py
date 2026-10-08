from ops.queue import cancel_pending


def test_cancellation_removes_only_pending_and_preserves_job_identity():
    a={'name':'a','args':['unchanged']};b={'name':'b','args':['same']}
    pending,cancelled=cancel_pending([a,b],['a','already-running'])
    assert pending==[b] and cancelled==['a'] and a['args']==['unchanged']
