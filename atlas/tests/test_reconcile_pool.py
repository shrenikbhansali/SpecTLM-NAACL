from atlas.curate_pool import stratify
from atlas.reconcile_pool import staging_union, account_discovery
import pytest


def test_stage_sample_plus_every_bank_without_duplicates():
    rows=[dict(model_id=str(i),revision='a'*40,type='lora_adapter',pool='bank' if i<3 else 'test',exclusion='',downloads=i) for i in range(6)]
    selected=stratify(rows,2)
    result=staging_union(rows,selected)
    assert {r['model_id'] for r in result}=={'0','1','2','4','5'}


def test_discovery_errors_cannot_disappear():
    with pytest.raises(ValueError,match='missing'):
        account_discovery({'a','b'},[{'model_id':'a'}])
    assert account_discovery({'a','b'},[{'model_id':'a'},{'model_id':'b'}])==2
