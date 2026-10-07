import copy
import pytest


def rows():
    out=[]
    for target in ('base','test-a','test-b'):
        for arm in ('Frozen','FS','MVD','PO-D','PO-T'):
            for parent in ([True] if target=='base' else [True,False]):
                cell=('A00' if parent else 'A10') if arm=='Frozen' else ('A01' if parent else 'A11')
                value=3 if arm=='FS' else 2
                out.append(dict(K=4,workload='general',seed=0,pool='base' if target=='base' else 'test',derivative_id=target,arm=arm,cell=cell,
                    run_id=f'{target}-{arm}-{cell}',prompt_ids=['1','2'],prompt_sha256=target,settings={'K':4},
                    target_identity={'model':'base' if parent else target},drafter_identity={'model':arm},
                    value=value,n_prompts=2,n_zero_step=0,prompt_values={'1':value,'2':value}))
    return out


def test_single_seed_reports_all_controls_without_gate_or_seed_inference():
    from followspec.pilot_report import summarize
    s=summarize(rows());g=s['workloads'][0]
    assert s['gate_certified'] is False and s['n_training_seeds']==1
    assert g['n_targets']==2 and len(g['per_target'])==2
    assert set(g['comparisons'])=={'Frozen','MVD','PO-D','PO-T'}
    assert g['comparisons']['MVD']['median_gain']==1
    assert g['comparisons']['MVD']['ci95_targets_conditional_on_seed']==[1,1]
    assert g['parent_retention']['FS']['relative_change']==.5
    assert 'equivalent' not in g['parent_retention']['FS']


@pytest.mark.parametrize('change',['missing','settings','target','checkpoint','seed'])
def test_refuses_unmatched_or_incomplete_pilot(change):
    from followspec.pilot_report import summarize
    r=rows()
    if change=='missing':r.pop()
    elif change=='settings':r[-1]['settings']={'K':8}
    elif change=='target':r[-1]['target_identity']={'model':'different'}
    elif change=='checkpoint':r[-1]['drafter_identity']={'model':'different'}
    else:r[-1]['seed']=1
    with pytest.raises(ValueError):summarize(r)


def test_losses_are_retained_and_zero_step_pairs_are_explicit():
    from followspec.pilot_report import summarize
    r=rows()
    for row in r:
        if row['arm']=='FS' and row['pool']=='test' and row['cell']=='A11':row['prompt_values']={'1':None,'2':1}
    s=summarize(r)['workloads'][0]
    assert s['comparisons']['Frozen']['median_gain']==-1
    assert s['comparisons']['MVD']['win_rate']==0
    assert s['per_target'][0]['comparisons']['MVD']['n_paired']==1
    assert s['per_target'][0]['comparisons']['MVD']['excluded_prompt_ids']==['1']
