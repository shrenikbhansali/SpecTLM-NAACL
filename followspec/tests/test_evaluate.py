import numpy as np
import pytest
from followspec.evaluate import median_interval, paired_summary, parent_tost, schedule


def test_median_bootstrap_covers_known_effect_at_nominal_rate():
    rng=np.random.default_rng(7101);covered=0
    for trial in range(200):
        diff=rng.normal(.2,.5,40)
        low,high=median_interval(diff,resamples=1000,seed=trial)
        covered+=low<=.2<=high
    # Preregistered broad binomial sampling tolerance around nominal95%, n200.
    assert .90<=covered/200<=.995


def test_identical_checkpoint_difference_interval_includes_zero():
    result=paired_summary(np.ones(35)*3,np.ones(35)*3,np.ones(35)*3,resamples=10000)
    assert result['median_gain_ci95']==[0.,0.] and result['median_gain']==0.


def test_pairing_and_relative_retention_do_not_pool_prompts():
    result=paired_summary([3,4],[2,3],[2,4],resamples=10000)
    assert result['n_derivatives']==2 and result['win_rate']==1
    assert result['worst_decile_retention']==1
    with pytest.raises(ValueError):paired_summary([2],[2,3],[2])


def test_parent_tost_uses_relative_margin_and_seed_units():
    result=parent_tost([3.01,2.99,3.0],[3.,3.,3.])
    assert result['equivalent'] and result['n_training_seeds']==3
    assert not parent_tost([3.3,3.4,3.2],[3.,3.,3.])['equivalent']
    with pytest.raises(ValueError):parent_tost([3.],[3.])


def test_schedule_keeps_base_child_prompts_matched_and_never_launches(tmp_path):
    spec=dict(base_id='base',base_revision='a'*40,K=[4],max_new_tokens=512,
        checkpoints=[dict(arm='FS',seed=0,model_id='draft',revision='b'*40)],
        targets=[dict(model_id='child',revision='c'*40,pool='test',workloads={'general':'prompts.jsonl'})])
    plans=schedule(spec,str(tmp_path))
    assert len(plans)==2 and {p['cell'] for p in plans}=={'A01','A11'}
    assert plans[0]['prompt_file']==plans[1]['prompt_file']
    assert not list(tmp_path.iterdir())
    spec['targets'][0]['pool']='bank'
    with pytest.raises(ValueError):schedule(spec,str(tmp_path))


def synthetic_matrix():
    rows=[]
    for target in ['base','child0','child1','child2','child3']:
        for arm in ['Frozen','FS','MVD','PO-D','PO-T']:
            for seed in [0,1,2]:
                cells=['A00','A10'] if arm=='Frozen' else ['A01','A11']
                for cell in cells[:1] if target=='base' else cells:
                    parent=cell in ('A00','A01')
                    rows.append(dict(K=4,workload='general',arm=arm,seed=seed,derivative_id=target,
                        pool='base' if target=='base' else 'test',cell=cell,
                        value=3. if parent else 3.4 if arm=='FS' else 3.1,
                        n_prompts=128,prompt_sha256='p',prompt_ids=['p'],settings={'K':4},
                        target_identity={'model':'base' if parent else target},
                        drafter_identity={'model':arm,'seed':0 if arm=='Frozen' else seed},
                        run_id=f'{target}-{arm}-{seed}-{cell}'))
    return rows


def test_complete_matrix_outputs_seed_averaged_a01_a11_and_detects_bad_pairing():
    from followspec.evaluate import aggregate
    rows=synthetic_matrix();summary,table=aggregate(rows)
    assert summary[0]['numerical_criteria_met'] and summary[0]['owner_gate_decision']=='pending'
    assert all(r['A01']==3. and r['n_training_seeds']==3 for r in table)
    rows[2]['drafter_identity']={'model':'wrong checkpoint'}
    with pytest.raises(ValueError,match='checkpoint'):aggregate(rows)


def test_matrix_rejects_misattributed_target_and_missing_seed():
    from followspec.evaluate import aggregate
    rows=synthetic_matrix()
    next(r for r in rows if r['cell']=='A11')['target_identity']={'model':'other target'}
    with pytest.raises(ValueError,match='target'):aggregate(rows)
    with pytest.raises(ValueError):aggregate([r for r in synthetic_matrix() if r['seed']!=2])


def test_loader_recomputes_counters_and_rejects_corruption(tmp_path):
    import json
    from followspec.evaluate import load_measurements
    from atlas.run_cell import metrics
    record=dict(arm='FS',seed=0,derivative_id='child',pool='test',workload='general',K=4,cell='A11',run_id='run',run_dir=str(tmp_path))
    cfg=dict(code_dirty=False,K=4,seed=0,max_new_tokens=512,batch_size=1,max_model_len=4096,dtype='bfloat16',temperature=0.,top_p=1.,engine_version='0.31.0',
        prompt_sha256='p',target='child',target_revision='a'*40,adapter=None,adapter_revision=None,drafter='trained',drafter_revision='b'*40,method='eagle3',max_lora_rank=64,gpu_memory_utilization=.75,enable_prefix_caching=False)
    (tmp_path/'config.json').write_text(json.dumps(cfg))
    (tmp_path/'results.json').write_text(json.dumps(dict(n=1,macro_acceptance_length=3.,engine_version='0.31.0')))
    raw=dict(prompt_id='p',**metrics([2,2],[4,4],4))
    (tmp_path/'per_prompt.jsonl').write_text(json.dumps(raw)+'\n')
    assert load_measurements([record])[0]['value']==3.
    raw['per_step_drafted']=[1,1]
    (tmp_path/'per_prompt.jsonl').write_text(json.dumps(raw)+'\n')
    with pytest.raises(ValueError):load_measurements([record])


def test_cli_roundtrip_artifacts_and_zero_effect_interval(tmp_path):
    import json,subprocess,sys
    from atlas.run_cell import metrics
    matrix=synthetic_matrix();index=[]
    for i,row in enumerate(matrix):
        path=tmp_path/f'run{i}';path.mkdir()
        # Identical fixed counters for all arms exercise a true null end to end.
        cfg=dict(code_dirty=False,K=4,seed=0,max_new_tokens=512,batch_size=1,max_model_len=4096,dtype='bfloat16',temperature=0.,top_p=1.,engine_version='0.31.0',
            prompt_sha256='p',target=row['target_identity']['model'],target_revision='a'*40,adapter=None,adapter_revision=None,
            drafter=row['arm'],drafter_revision=f"{row['drafter_identity']['seed']:040x}",method='eagle3',max_lora_rank=64,gpu_memory_utilization=.75,enable_prefix_caching=False)
        (path/'config.json').write_text(json.dumps(cfg))
        (path/'results.json').write_text(json.dumps(dict(n=1,macro_acceptance_length=3.,engine_version='0.31.0')))
        (path/'per_prompt.jsonl').write_text(json.dumps(dict(prompt_id='p',**metrics([2,2],[4,4],4)))+'\n')
        index.append({q:row[q] for q in ('K','workload','derivative_id','pool','arm','seed','cell','run_id')}|dict(run_dir=str(path)))
    source=tmp_path/'index.json';source.write_text(json.dumps(index));out=tmp_path/'report'
    subprocess.run([sys.executable,'-m','followspec.evaluate','aggregate','--input',str(source),'--output',str(out)],check=True)
    summary=json.loads((out/'summary.json').read_text())[0]
    assert not summary['numerical_criteria_met']
    assert all(c['median_gain_ci95']==[0.,0.] for c in summary['comparisons'].values())
    assert len((out/'per_seed.csv').read_text().splitlines())==len(matrix)+1
    assert set(json.loads((out/'provenance.json').read_text())['source_run_ids'])=={r['run_id'] for r in matrix}


def test_d32_gate_uses_paired_subsets_for_cells_gains_and_parent_tost():
    import json
    from followspec.evaluate import aggregate
    rows=synthetic_matrix()
    for row in rows:
        row.update(prompt_ids=['p0','p1','p2'],n_prompts=3,prompt_values=dict(p0=3.,p1=3.,p2=3.),n_zero_step=0)
        if row['pool']=='test' and row['arm']=='FS':
            row['prompt_values']=dict(p0=2.,p1=4.,p2=None) if row['cell']=='A01' else dict(p0=None,p1=5.,p2=1.)
            row['n_zero_step']=1
        elif row['pool']=='test' and row['cell']=='A11':
            row['prompt_values']=dict(p0=5.,p1=2.,p2=None);row['n_zero_step']=1
        elif row['pool']=='base' and row['arm']=='FS':
            row['prompt_values']=dict(p0=None,p1=3.,p2=3.);row['n_zero_step']=1
    summary,table=aggregate(rows)
    fs=next(r for r in table if r['arm']=='FS')
    assert fs['A01']==4. and fs['A11']==5. and fs['retention']==1.
    assert all(v['n_excluded']==2 for v in json.loads(fs['pairing_A01_A11']).values())
    assert summary[0]['comparisons']['MVD']['median_gain']==3.
    assert summary[0]['parent_retention']['FS']['equivalent']
    assert all(v['n_excluded']==1 for v in summary[0]['parent_retention']['FS']['pairing'].values())
    details=summary[0]['comparison_pairing']['MVD']['child0']
    assert all(v['n_excluded']==2 for v in details.values())


def test_d32_loader_preserves_zero_records_for_later_pairing(tmp_path):
    from atlas.tests.test_paired_cells import fixture
    from followspec.evaluate import load_measurements
    p=fixture(tmp_path/'cell',dict(p0=None,p1=3))
    record=dict(arm='FS',seed=0,derivative_id='child',pool='test',workload='general',K=4,cell='A11',run_id='run',run_dir=str(p))
    row=load_measurements([record])[0]
    assert row['prompt_values']==dict(p0=None,p1=3.) and row['n_zero_step']==1
    assert row['value']==3. and row['n_prompts']==2 and row['n_valid']==1
