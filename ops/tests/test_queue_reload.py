import importlib.util
import json
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('reload_queue',Path(__file__).parents[1]/'queue.py')
queue=importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)


def test_new_jobs_append_without_relaunching_or_reordering(tmp_path):
    p=tmp_path/'jobs.jsonl';first={'name':'one','args':['original']};second={'name':'two','args':['new'],'allowed_nodes':['heck-srv3']}
    p.write_text(json.dumps(first)+'\n');known={}
    assert queue.reload_pending(p,known,set())==[first]
    p.write_text(json.dumps(first)+'\n'+json.dumps(second)+'\n')
    assert queue.reload_pending(p,known,{'one'})==[second]
    assert queue.reload_pending(p,known,{'one','two'})==[]


def test_reload_rejects_changed_job_identity(tmp_path):
    p=tmp_path/'jobs.jsonl';p.write_text('{"name":"one","args":["changed"]}\n')
    with pytest.raises(ValueError,match='changed'):
        queue.reload_pending(p,{'one':{'name':'one','args':['original']}},{'one'})


@pytest.mark.parametrize('row',[{'name':'one','args':[],'allowed_nodes':[]},{'name':'one','args':[],'allowed_nodes':'heck-srv3'}])
def test_reload_keeps_placement_validation(tmp_path,row):
    p=tmp_path/'jobs.jsonl';p.write_text(json.dumps(row)+'\n')
    with pytest.raises(ValueError,match='allowed_nodes'):queue.reload_pending(p,{},set())
