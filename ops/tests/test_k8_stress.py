import copy
from pathlib import Path
import pytest
from ops.k8_stress import k8_job,matched_indexes


def pair():
    argv=['python','-m','atlas.run_cell','--K','4','--output','/old/cell','--prompts','/prompts','--seed','0']
    r=dict(run_id='eval-FS-s0-k4-A11-x',run_dir='/old/cell',K=4,arm='FS',seed=0,derivative_id='test',workload='code',cell='A11',pool='test',prompt_file='/prompts',argv=argv,env={'VLLM_CACHE_ROOT':'/old/cache'})
    j=dict(name=r['run_id'],allowed_nodes=['heck-srv4'],args=['--k','4','--tag',r['run_id'],'--','python','-u',*argv[1:]])
    return r,j


def test_k_only_derivation_preserves_exact_controls_and_sources(tmp_path):
    r,j=pair();original=copy.deepcopy((r,j));rr,jj=k8_job(r,j,tmp_path)
    assert (r,j)==original and rr['K']==8 and jj['args'][jj['args'].index('--k')+1]=='8'
    restored=copy.deepcopy(rr)
    for k in ('run_id','run_dir','K','env'):restored[k]=r[k]
    restored['argv'][restored['argv'].index('--K')+1]='4';restored['argv'][restored['argv'].index('--output')+1]=r['run_dir']
    assert restored==r
    args=jj['args'];args[args.index('--k')+1]='4';args[args.index('--K')+1]='4';args[args.index('--output')+1]=r['run_dir'];args[args.index('--tag')+1]=r['run_id']
    jj['name']=j['name'];assert jj==j
    assert str(tmp_path) in rr['run_dir'] and '-k8-' in rr['run_id']


def test_mismatched_source_command_and_k_rejected(tmp_path):
    r,j=pair();j['args'][-1]='1'
    with pytest.raises(ValueError,match='command'):k8_job(r,j,tmp_path)
    r,j=pair();r['K']=8
    with pytest.raises(ValueError,match='K4'):k8_job(r,j,tmp_path)


def test_all_variants_reuse_only_same_k8_controls():
    rows=[]
    for arm in ['FS','MVD','PO-D','PO-T','Frozen']:
        r,_=pair();r.update(arm=arm,K=8,run_id=arm);rows.append(r)
    fs={l:[dict(rows[0],run_id='FS-'+l)] for l in ['000','003','030']}
    indexes=matched_indexes(rows,fs)
    assert set(indexes)=={'000','003','010','030'}
    assert all({r['arm'] for r in group}=={'FS','MVD','PO-D','PO-T','Frozen'} for group in indexes.values())
    assert len({r['run_id'] for group in indexes.values() for r in group})==8
    with pytest.raises(ValueError,match='matched'):matched_indexes(rows,{'000':[]})


def test_summary_keeps_regressions_and_rejects_mismatched_targets():
    from types import SimpleNamespace
    from atlas.paired_cells import paired_values
    from followspec.stress_quality import acceptance_interval
    from ops.k8_stress import summarize
    rows=[]
    for arm,value in [('Frozen',2.),('FS',2.5),('MVD',2.6),('PO-D',2.4),('PO-T',2.7)]:
        for child in [False,True]:
            rows.append(dict(arm=arm,seed=0,K=8,derivative_id='test',pool='test',workload='code',
                cell=('A10' if child else 'A00') if arm=='Frozen' else ('A11' if child else 'A01'),
                target_identity='child' if child else 'parent',prompt_values={'x':value if child else 3.},
                prompt_ids=['x'],prompt_sha256='h',settings={'K':8}))
    m={'followspec.evaluate':SimpleNamespace(load_measurements=lambda _:rows),'followspec.pilot_report':SimpleNamespace(paired_values=paired_values)}
    q=SimpleNamespace(acceptance_interval=acceptance_interval);result=summarize([],m,q)
    c=result['rows'][0]['fs_vs_controls']
    assert c['MVD']['gain']==pytest.approx(-.1) and c['PO-D']['gain']==pytest.approx(.1)
    assert c['PO-T']['gain']==pytest.approx(-.2) and c['Frozen']['gain']==pytest.approx(.5)
    assert not result['gate_certified'] and result['K']==8
    rows[-1]['target_identity']='wrong'
    with pytest.raises(ValueError,match='identity'):summarize([],m,q)
