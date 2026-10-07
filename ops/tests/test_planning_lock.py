from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from ops.planning_lock import locked_evaluation


def test_shared_export_planners_serialize(tmp_path):
    entered=Event();release=Event();second=Event()
    def first(training):entered.set();assert release.wait(5);return 1
    def other(training):second.set();return 2
    with ThreadPoolExecutor(2) as pool:
        a=pool.submit(locked_evaluation,first,tmp_path)
        assert entered.wait(2)
        b=pool.submit(locked_evaluation,other,tmp_path/'.')
        assert not second.wait(.15)
        release.set();assert a.result(2)==1 and b.result(2)==2


def test_distinct_stages_remain_independent_and_exception_releases(tmp_path):
    a=tmp_path/'a';b=tmp_path/'b';a.mkdir();b.mkdir();entered=Event();release=Event()
    def first(training):entered.set();assert release.wait(5)
    with ThreadPoolExecutor(2) as pool:
        f=pool.submit(locked_evaluation,first,a);assert entered.wait(2)
        assert pool.submit(locked_evaluation,lambda training:True,b).result(1)
        release.set();f.result(2)
    def fail(training):raise ValueError('original error')
    with pytest.raises(ValueError,match='original error'):locked_evaluation(fail,a)
    assert locked_evaluation(lambda training:True,a)
