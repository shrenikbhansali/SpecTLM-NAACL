"""Descriptive matched single-seed evidence; never certifies the three-seed gate."""
import argparse
from collections import defaultdict
import statistics
import subprocess
from datetime import date
from pathlib import Path
from atlas.paired_cells import paired_values
from atlas.run_cell import sha256,write_new
from followspec.evaluate import ARMS,load_measurements,median_interval
from followspec.production_pipeline import checked_stage,finish,new_output,read


def summarize(rows):
    if not rows or {r['seed'] for r in rows}!={0} or {r['K'] for r in rows}!={4}:
        raise ValueError('pilot requires seed0 K4 only')
    groups=defaultdict(dict);identities={};parent=None
    for r in rows:
        key=(r['derivative_id'],r['arm'],r['cell'])
        if key in groups[r['workload']]:raise ValueError('duplicate cell')
        if r['arm'] not in (*ARMS,'Frozen') or (r['pool']=='base')!=(r['derivative_id']=='base') or r['pool'] not in ('base','test'):
            raise ValueError('invalid arm or held-out pool')
        if r['arm'] in identities and identities[r['arm']]!=r['drafter_identity']:raise ValueError('checkpoint mismatch')
        identities[r['arm']]=r['drafter_identity']
        if r['cell'] in ('A00','A01'):
            if parent is not None and parent!=r['target_identity']:raise ValueError('parent target mismatch')
            parent=r['target_identity']
        groups[r['workload']][key]=r
    workloads=[]
    for workload,cells in sorted(groups.items()):
        targets=sorted({t for t,a,c in cells if t!='base'})
        expected={(t,a,c) for t in ['base',*targets] for a in (*ARMS,'Frozen') for c in (('A00',) if t=='base' else ('A00','A10'))}  # replace roles per arm
        expected={(t,a,({'A00':'A01','A10':'A11'}[c] if a!='Frozen' else c)) for t,a,c in expected}
        if not targets or set(cells)!=expected:raise ValueError('incomplete four-arm pilot matrix')
        per_target=[]
        for t in targets:
            frozen=cells[t,'Frozen','A00'];child=cells[t,'Frozen','A10']
            paired_values(frozen,child)
            result=dict(target=t,arms={},comparisons={})
            for a in ARMS:
                base=cells[t,a,'A01'];trained=cells[t,a,'A11']
                if base['target_identity']!=frozen['target_identity'] or trained['target_identity']!=child['target_identity']:
                    raise ValueError('paired target identity mismatch')
                paired_values(base,frozen);paired_values(trained,child)
                result['arms'][a]=dict(parent_child=paired_values(base,trained),child_vs_frozen=paired_values(trained,child))
            result['frozen_parent_child']=paired_values(frozen,child)
            for a in ('Frozen','MVD','PO-D','PO-T'):
                pair=paired_values(cells[t,'FS','A11'],cells[t,a,'A10' if a=='Frozen' else 'A11'])
                result['comparisons'][a]=pair|dict(gain=pair['values'][0]-pair['values'][1])
            per_target.append(result)
        comparisons={}
        for a in ('Frozen','MVD','PO-D','PO-T'):
            gains=[r['comparisons'][a]['gain'] for r in per_target]
            comparisons[a]=dict(n_targets=len(gains),median_gain=statistics.median(gains),mean_gain=statistics.mean(gains),
                ci95_targets_conditional_on_seed=median_interval(gains),win_rate=sum(v>0 for v in gains)/len(gains))
        parents={}
        for a in ARMS:
            pair=paired_values(cells['base',a,'A01'],cells['base','Frozen','A00'])
            parents[a]=pair|dict(relative_change=pair['values'][0]/pair['values'][1]-1)
        workloads.append(dict(workload=workload,n_targets=len(targets),comparisons=comparisons,parent_retention=parents,per_target=per_target))
    return dict(n_training_seeds=1,seed=0,K=4,gate_certified=False,status='pilot',workloads=workloads,
        uncertainty='Bootstrap over fixed held-out targets, conditional on one training seed; no training-seed uncertainty or parent equivalence test.',
        scope='Exploratory fixed panel; retain every outcome, including regressions. Not a representative census or Gate3 decision.')


def report(stage,output):
    root,cfg=checked_stage(stage);ready=read(root/'results.json')
    if cfg['stage']!='evaluation-jobs' or ready.get('checkpoints_ready') is not True:raise ValueError('all pilot checkpoints required')
    records=read(root/'index_k4.json');result=summarize(load_measurements(records))
    result['validation_pending_at_handoff']=ready.get('validation_pending',[])
    hashes={str(Path(r['run_dir'])/name):sha256(Path(r['run_dir'])/name) for r in records for name in ('config.json','results.json','per_prompt.jsonl')}
    out=new_output(output)
    config=dict(stage='pilot-report',evaluation_stage=str(root),evaluation_stage_sha256=sha256(root/'stage_files.json'),
        inputs_sha256=hashes,decision_id='D-38',engine_version='0.31.0',
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    write_new(out/'config.json',config);write_new(out/'results.json',result)
    write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title='D-38 reduced-budget held-out feasibility',landed=str(date.today()),
        status='pilot',what_why='Compare four matched short-training arms with released Frozen drafter on the fixed held-out panel',
        new='K4 acceptance length including bonus token; pairwise D32 zero-step handling; all target outcomes retained',
        artifacts=str(out),config_results=dict(config=config,results=result),
        caveats=result['uncertainty']+' '+result['scope']+' Native validation status is recorded separately.'))
    write_new(out/'stage_files.json',{str(p.relative_to(out)):sha256(p) for p in out.rglob('*') if p.is_file()})
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(report(a.stage,a.output))


if __name__=='__main__':main()
