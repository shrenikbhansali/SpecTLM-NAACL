from ops import queue


def test_a40_evaluation_is_not_popped_for_h200():
    from ops.queue import eligible_job_index
    jobs=[dict(name='eval',allowed_nodes=['heck-srv2']),dict(name='train',allowed_nodes=['heck-srv6'])]
    assert eligible_job_index(jobs,'heck-srv6')==1
    assert eligible_job_index(jobs,'heck-srv2')==0
    assert [j['name'] for j in jobs]==['eval','train']


def test_no_eligible_job_stays_pending():
    from ops.queue import eligible_job_index
    jobs=[dict(name='eval',allowed_nodes=['heck-srv2'])]
    assert eligible_job_index(jobs,'heck-srv6') is None
    assert len(jobs)==1


def test_legacy_jobs_keep_fifo():
    from ops.queue import eligible_job_index
    assert eligible_job_index([dict(name='first'),dict(name='second')],'heck-srv6')==0
    assert eligible_job_index([],'heck-srv6') is None
