#!/usr/bin/env python3
"""Generate appendix tables, checking focal metrics directly from raw counters."""
import hashlib
import json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
d=json.loads((P/'data/results.json').read_text())

def cell(m, pct=False):
    f=100 if pct else 1; digits=1 if pct else 3
    return r'\stat{'+f"{m['mean']*f:.{digits}f}"+'}{'+f"{m['ci95'][0]*f:.{digits}f}--{m['ci95'][1]*f:.{digits}f}"+'}'

ls=[r'\begin{tabular}{@{}lllcccc@{}}',r'\toprule',r'Panel & Initialization & Scope & $p_1$ (\%) & $\tau$ & $\Delta\tau$ & Recovery (\%) \\',r'\midrule']
for w in ['speed128','math64']:
    for family in ['official','production']:
        for arm in ['fc','full']:
            r=next(r for r in d['d51']['focal'] if (r['family'],r['arm'],r['workload'])==(family,arm,w));s=r['statistics']
            ls.append(' & '.join(['SPEED' if w=='speed128' else 'MATH-64','Official' if family=='official' else 'Second release','Interface' if arm=='fc' else 'Full',cell(s['metrics']['p1'],True),cell(s['metrics']['tau']),cell(s['delta']['tau']),cell(s['recovery'],True)])+r' \\[2pt]')
ls += [r'\bottomrule',r'\end{tabular}']
(P/'tables/robustness.tex').write_text('\n'.join(ls)+'\n')

ls=[r'\begin{tabular}{@{}lcc@{}}',r'\toprule',r'Queries & Interface $\tau$ & Full $\tau$ \\',r'\midrule']
for tag,label in [('self256','Self-elicited 256'),('self1k','Self-elicited 1k'),('self4k','Self-elicited 4k'),('generic4k','Generic 4k'),('generic16k','Generic 16k')]:
    metrics=[]
    for arm in ['fc','full']:
        rows=[r for r in d['ablations'] if r['label']==tag+'-'+arm and r['workload']=='speed128' and r.get('seed')==0 and isinstance(r['step'],int)]
        r=max(rows,key=lambda r:r['step']);metrics.append(cell(r['statistics']['metrics']['tau']))
    ls.append(' & '.join([label,*metrics])+r' \\[2pt]')
ls += [r'\bottomrule',r'\end{tabular}']
(P/'tables/scaling.tex').write_text('\n'.join(ls)+'\n')

raw_hashes=[];summaries=[];prompt_hashes={}
for target in [0,1]:
    for arm in ['reused','fc','full']:
        r=next(r for r in d['d51']['records'] if (r['target'],r['arm'],r['workload'],r['budget'])==(target,'fc' if arm=='reused' else arm,'speed128',16000))
        paths=([r['reuse_paths'][0]] if arm=='reused' else [x['run'] for x in r['sources'][:r['seed_count']]])
        seed_arrays=[]
        for path in paths:
            path=Path(path);c=json.loads((path/'config.json').read_text());res=json.loads((path/'results.json').read_text())
            assert c['code_commit']=='6da2e4265c0398ec0de5affaf23b0bd1df0be445'
            assert c['engine_version']=='0.31.0' and c['K']==4 and c['temperature']==0 and c['batch_size']==8 and c['max_new_tokens']==512
            assert res['gpu_type']=='NVIDIA A40'
            ph=c['prompt_sha256'];assert hashlib.sha256(Path(c['prompts']).read_bytes()).hexdigest()==ph
            assert target not in prompt_hashes or prompt_hashes[target]==ph
            prompt_hashes[target]=ph
            raw=(path/'per_prompt.jsonl').read_bytes();raw_hashes.append({'path':str(path/'per_prompt.jsonl'),'sha256':hashlib.sha256(raw).hexdigest()})
            rr=sorted([json.loads(x) for x in raw.splitlines()],key=lambda x:str(x['prompt_id']));assert len(rr)==128
            values=[]
            for x in rr:
                accepted=x['per_step_accepted'];offered=x['per_step_drafted']
                assert len(accepted)==len(offered)==x['num_drafts']
                assert sum(accepted)==x['num_accepted_tokens'] and sum(offered)==x['num_draft_tokens']
                assert all(0<=a<=k<=4 for a,k in zip(accepted,offered))
                rates=[]
                for depth in range(1,5):
                    eligible=sum(a>=depth-1 and k>=depth for a,k in zip(accepted,offered))
                    rates.append(sum(a>=depth for a in accepted)/eligible if eligible else np.nan)
                tau=1+sum(accepted)/len(accepted)
                assert abs(tau-x['acceptance_length'])<1e-8
                values.append([*rates,len(x['completion_token_ids']),tau])
            seed_arrays.append(values)
        arr=np.array(seed_arrays);point=np.nanmean(arr,axis=(0,1));reference=r['official_reuse'] if arm=='reused' else r['official']
        assert abs(point[0]-reference['metrics']['p1']['mean'])<1e-10
        assert abs(point[5]-reference['metrics']['tau']['mean'])<1e-10
        assert abs(point[4]-reference['metrics']['length']['mean'])<1e-10
        # Reset RNG per arm so all query/seed draws are paired across scopes.
        rng=np.random.default_rng(0);boot=[];nseeds=3 if target==0 else 1
        for _ in range(40):
            si=rng.integers(nseeds,size=(250,nseeds));qi=rng.integers(128,size=(250,128))
            sample=arr[(si%len(arr))[:,:,None],qi[:,None,:]]
            boot.append(np.nanmean(sample,axis=(1,2)))
        boot=np.concatenate(boot);lo,hi=np.nanquantile(boot,[.025,.975],axis=0)
        stats=[dict(mean=float(v),ci95=[float(l),float(h)]) for v,l,h in zip(point,lo,hi)]
        summaries.append(dict(target=target,arm=arm,statistics=stats,n_per_depth=np.sum(np.isfinite(arr[:,:,:4]),axis=1).tolist(),seeds=len(arr)))

ls=[r'\begin{tabular}{@{}llccccc@{}}',r'\toprule',r'Target & Scope & $p_1$ & $p_2$ & $p_3$ & $p_4$ & Output tokens \\',r'\midrule']
for r in summaries:
    ls.append(' & '.join(['R1' if r['target']==0 else 'Nemotron',{'reused':'Reuse','fc':'Interface','full':'Full'}[r['arm']],*[cell(m,True) for m in r['statistics'][:4]],cell(r['statistics'][4])])+r' \\[2pt]')
ls += [r'\bottomrule',r'\end{tabular}']
(P/'tables/depth.tex').write_text('\n'.join(ls)+'\n')
(P/'data/raw-verification.json').write_text(json.dumps(dict(status='passed',check='Focal p1, tau and lengths independently reproduce saved summaries to 1e-10',sources=raw_hashes,depth=summaries),indent=2)+'\n')
print('Generated robustness/scaling/depth tables; focal raw-counter checks pass.')
