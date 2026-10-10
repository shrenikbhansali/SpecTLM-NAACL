from pathlib import Path
import pytest

def test_only_failed_e9_can_be_superseded():
    from followspec.rev2_recovery import active_attempts
    old=dict(name='old',experiment='E9',target=0,arm='fc',data_label='long4k',seed=0,kind='train')
    new=old|dict(name='retry',replaces_job='old')
    with pytest.raises(ValueError):active_attempts({'old':old,'retry':new},{})
    rows,evidence=active_attempts({'old':old,'retry':new},{'old':'1'})
    assert list(rows)==['retry'] and evidence[0]['failed_job']=='old'
    with pytest.raises(ValueError):active_attempts({'old':old,'retry':new|dict(arm='full')},{'old':'1'})

def test_retry_preserves_data_objective_and_changes_only_storage_and_packing():
    from followspec.rev2_recovery import retry_job
    from followspec.review_followup import parts
    source={'name':'old','args':['--tag','old','--code-repo','oldcode','--','--output','oldout','--batch-tokens','4096','--shared-export-root','oldshared','--data','same-data','--variant','fc','--one-epoch','--offload-saved-tensors']}
    record=dict(name='old',run_dir='oldout',experiment='E9',kind='train',target=0,arm='fc',seed=0,data_label='long4k')
    job,row=retry_job(source,record,Path('/newstage'),Path('/newcode'))
    o,i=parts(job)
    assert i[i.index('--batch-tokens')+1]=='2304' and i[i.index('--data')+1]=='same-data'
    assert '--offload-saved-tensors' in i and '--one-epoch' in i
    assert row['replaces_job']=='old' and job['name']==row['name']!='old'
    assert source['args'][source['args'].index('--batch-tokens')+1]=='4096'
