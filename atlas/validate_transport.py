"""Join audited real B9 sources and report the preregistered acceptance checks."""
import argparse
from datetime import date
import json
from pathlib import Path
import subprocess
import numpy as np
from atlas.transport import validate_diagonals,rank_correlation
from atlas.transport_sources import prepare_pair
from atlas.run_cell import sha256,write_new


def collect(plan_path,capture_root):
    plan_path=Path(plan_path);plan=json.loads(plan_path.read_text());records=[];evidence={}
    if len(plan['pairs'])!=10:raise ValueError('fixed10-derivative acceptance plan required')
    speed=Path(plan.get('source_speed_file',''))
    if not speed.is_file() or sha256(speed)!=plan.get('source_speed_sha256'):raise ValueError('actual frozen SPEED source required')
    prompt_ids=[json.loads(s)['prompt_id'] for s in speed.read_text().splitlines()[:5]]
    if prompt_ids!=plan.get('prompt_ids') or any(not p.startswith('speed-') for p in prompt_ids):raise ValueError('wrong acceptance workload')
    for pair in plan['pairs']:
        root=plan_path.parent/f"d{pair['index']:02d}";_,source=prepare_pair(root,pair)
        if source['prompt_sha256']!=plan['prompt_sha256'] or source['reference_prompt_ids']!=prompt_ids:raise ValueError('cell used a different workload')
        capture=Path(capture_root)/f"d{pair['index']:02d}"/ 'capture'
        if (capture/'failure.json').exists():raise ValueError('failed native capture')
        cfg=json.loads((capture/'config.json').read_text());result=json.loads((capture/'results.json').read_text())
        cell=json.loads((root/'child/config.json').read_text())
        if cfg['derivative_id']!=pair['derivative_id'] or cfg['derivative_revision']!=pair['revision'] or cfg['prompt_sha256']!=source['prompt_sha256']:
            raise ValueError('offline/source identity differs')
        if cfg['base_revision']!=cell['target_revision'] or cfg['drafter_revision']!=cell['drafter_revision'] or cfg['steps']!=4:
            raise ValueError('offline model or unroll differs')
        if cfg.get('method','eagle3')!='eagle3' or not result['diagnostic'] or result['n_prompts']!=5:raise ValueError('wrong bounded diagnostic')
        if any(cfg['source'][k]!=source[k] for k in ['source_config_sha256','source_records_sha256']):raise ValueError('offline used different saved sequences')
        def diagonal(which):
            selected=[r for r in result['cells'] if r['unroll_position']==0 and r['head']=='frozen_drafter' and r['feature_source']==which and r['label_source']==which]
            if len(selected)!=1 or not selected[0]['diagnostic']:raise ValueError('missing or duplicate native diagonal')
            return selected[0]
        b,c=diagonal('base'),diagonal('child')
        record=dict(derivative_id=pair['derivative_id'],revision=pair['revision'],n_prompts=5,n_positions=b['n'],
            offline_A00=b['top1_agreement'],offline_A10=c['top1_agreement'],overlap_A00=b['overlap'],overlap_A10=c['overlap'])
        for label,arm in [('A00','base'),('A10','child')]:
            record[label]=json.loads((root/arm/'results.json').read_text())['macro_acceptance_length']
        records.append(record)
        for p in [root/'base/config.json',root/'base/results.json',root/'child/config.json',root/'child/results.json',
                  root/'child/per_prompt.jsonl',capture/'config.json',capture/'results.json',capture/'per_prompt.jsonl']:
            evidence[str(p.resolve())]=sha256(p)
    return records,evidence


def uncertainty(records,seed=0,resamples=2000):
    x=np.array([[r['offline_A00'],r['offline_A10']] for r in records]);y=np.array([[r['A00'],r['A10']] for r in records])
    rng=np.random.default_rng(seed);rho=[];sign=[];undefined=0
    for indices in rng.integers(0,len(records),size=(resamples,len(records))):
        a,b=x[indices],y[indices];r=rank_correlation(a.ravel().tolist(),b.ravel().tolist())
        if r is None:undefined+=1
        else:rho.append(r)
        sign.append(float(np.mean(np.sign(a[:,1]-a[:,0])==np.sign(b[:,1]-b[:,0]))))
    return dict(unit='derivative pairs',seed=seed,resamples=resamples,undefined_spearman_resamples=undefined,
        spearman_95_ci=np.quantile(rho,[.025,.975]).tolist() if rho else None,sign_agreement_95_ci=np.quantile(sign,[.025,.975]).tolist())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True);p.add_argument('--captures',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();records,evidence=collect(a.plan,a.captures)
    primary=validate_diagonals(records);primary['bootstrap']=uncertainty(records)
    secondary=validate_diagonals([r|dict(offline_A00=r['overlap_A00'],offline_A10=r['overlap_A10']) for r in records])
    secondary.update(primary_validation_metric='distribution overlap (secondary only)',acceptance_decision=False)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    cfg=dict(plan=str(Path(a.plan).resolve()),plan_sha256=sha256(a.plan),source_sha256=evidence,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),producer_sha256=sha256(__file__),
        scope='B9 builder acceptance, not production atlas result',primary='first-position top-1 agreement',thresholds=dict(spearman=.8,sign=.9))
    result=dict(passed=primary['passed'],primary=primary,secondary_overlap=secondary,diagnostic=True)
    write_new(out/'config.json',cfg);write_new(out/'results.json',result)
    with (out/'per_derivative.jsonl').open('x') as f:
        for r in records:f.write(json.dumps(r,allow_nan=False)+'\n')
    write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=str(date.today()),status='pilot',
        what_why='Verify offline diagnostic diagonal cells against native vLLM acceptance',new='Fixed10 derivatives, matched A00/A10 and saved child sequences',
        artifacts=str(out.resolve()),config_results=dict(config=cfg,results=result),caveats='Five prompts per derivative, one seed; diagnostic. Failed thresholds block B9 acceptance, not unrelated pipelines.'))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
