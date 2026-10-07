import copy
import pytest


def manifest(arm,n=32):
    rows=[]
    for i in range(n):
        parent=i%8>=6
        rows.append(dict(sample_id=str(i),split='train',child_id='base' if parent else 'a',length=11,
                         assistant_tokens=4,data_kind='general' if parent or i%2 else 'magpie',data_role='parent' if parent else 'child'))
    return dict(arm=arm,samples=rows+[dict(sample_id='val',split='val')],token_budget=n*10,optimizer_steps=8)


def test_subset_preserves_exact_prefix_validation_and_ratios():
    from followspec.pilot_data import subset_manifests
    original={a:manifest(a) for a in ('FS','MVD','PO-D','PO-T')};before=copy.deepcopy(original)
    selected,proof=subset_manifests(original,max_tokens=170)
    assert original==before and proof['token_budget']==160
    for arm,m in selected.items():
        assert m['samples']==before[arm]['samples'][:16]+before[arm]['samples'][-1:]
        assert m['parent_sample_share']==.25 and m['assistant_loss_tokens']==64
        assert proof['counts'][arm]==16


def test_small_budget_cannot_drop_a_target():
    from followspec.pilot_data import subset_manifests
    original={a:manifest(a) for a in ('FS','MVD','PO-D','PO-T')}
    for m in original.values():m['samples'][16]['child_id']='late-target'
    with pytest.raises(ValueError,match='common.*prefix'):
        subset_manifests(original,max_tokens=170)


def test_bad_composition_is_refused():
    from followspec.pilot_data import subset_manifests
    original={a:manifest(a) for a in ('FS','MVD','PO-D','PO-T')}
    original['FS']['samples'][0]['data_kind']='general'
    with pytest.raises(ValueError,match='composition'):
        subset_manifests(original,max_tokens=170)


def test_budget_must_reduce_full_data():
    from followspec.pilot_data import subset_manifests
    with pytest.raises(ValueError,match='smaller'):
        subset_manifests({a:manifest(a) for a in ('FS','MVD','PO-D','PO-T')},max_tokens=400)


def test_matching_uses_tokens_not_equal_sample_counts():
    from followspec.pilot_data import subset_manifests
    source={a:manifest(a) for a in ('FS','MVD','PO-D','PO-T')}
    source['MVD']=manifest('MVD',64)
    for r in source['MVD']['samples']:
        if r['split']=='train':r['length']=6
    source['MVD']['token_budget']=320
    result,proof=subset_manifests(source,max_tokens=170)
    assert proof['token_budget']==160 and proof['counts']['FS']==16 and proof['counts']['MVD']==32
    assert {m['token_budget'] for m in result.values()}=={160}
