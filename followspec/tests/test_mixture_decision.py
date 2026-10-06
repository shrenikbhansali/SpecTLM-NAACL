import copy
import pytest
from followspec.mixture_decision import check_numeric


def evidence():
    names=['onehot_0','onehot_1','onehot_2','zero','random_0','random_1','random_2']
    rows=[dict(case=c,prompt_id=str(i),dtype='torch.float32',max_absolute_difference=0 if c=='zero' else 9e-5,max_relative_difference=5.) for c in names for i in range(16)]
    comparisons=[dict(case=c,dtype='torch.float32',max_absolute_difference=0 if c=='zero' else 9e-5,max_relative_difference=5.) for c in names]
    return dict(n=16,comparisons=comparisons,acceptance=False),rows


def test_new_decision_recomputes_strict_absolute_gate_not_old_pass_flags():
    result,rows=evidence();out=check_numeric(result,rows)
    assert out['passed'] and out['n_prompts']==16 and out['max_absolute_difference']==9e-5
    bad=copy.deepcopy(rows);bad[0]['max_absolute_difference']=1e-4
    result['comparisons'][0]['max_absolute_difference']=1e-4
    assert not check_numeric(result,bad)['passed']


def test_missing_duplicate_or_mismatched_record_cannot_pass():
    result,rows=evidence()
    with pytest.raises(ValueError):check_numeric(result,rows[:-1])
    with pytest.raises(ValueError):check_numeric(result,rows[:-1]+[rows[0]])
    result['comparisons'][0]['max_absolute_difference']=1e-8
    with pytest.raises(ValueError,match='summary'):check_numeric(result,rows)
