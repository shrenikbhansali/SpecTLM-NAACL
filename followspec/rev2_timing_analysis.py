"""D54 independent process/prompt-batch bootstrap of measured timing only."""
import argparse,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
from followspec.rev2_analysis import summary

def contrast(arm,base):
    if len(arm)!=3 or len(base)!=3:raise ValueError('three completed processes required')
    vv=[];rr=[];tv=[];tr=[];sv=[];sr=[];mismatches=[]
    for x,y in zip(arm,base,strict=True):
        for k in ['prompt_sha256','target_revision','batch_size','max_new_tokens','seed','max_model_len','temperature','gpu_memory_utilization']:
            if x['config'].get(k)!=y['config'].get(k):raise ValueError('unmatched timing '+k)
        xt=x['timing'];yt=y['timing'];sv.append(xt['startup_s']);sr.append(yt['startup_s']);xs=[];ys=[];xo=[];yo=[];mism=[]
        for a,b in zip(xt['passes'],yt['passes'],strict=True):
            assert [r['prompt_ids'] for r in a['batches']]==[r['prompt_ids'] for r in b['batches']]
            ad={r['prompt_id']:r['completion_token_ids'] for r in a['per_prompt']};bd={r['prompt_id']:r['completion_token_ids'] for r in b['per_prompt']};assert ad.keys()==bd.keys()
            xs.append([r['wall_s'] for r in a['batches']]);ys.append([r['wall_s'] for r in b['batches']]);xo.append([sum(len(ad[k]) for k in r['prompt_ids']) for r in a['batches']]);yo.append([sum(len(bd[k]) for k in r['prompt_ids']) for r in b['batches']]);mism.append(sum(ad[k]!=bd[k] for k in ad))
        vv.append(xs);rr.append(ys);tv.append(xo);tr.append(yo);mismatches.append(mism)
    vv,rr,tv,tr=map(np.asarray,[vv,rr,tv,tr]);ns,_,nb=vv.shape;rng=np.random.default_rng(0);ri=rng.integers(ns,size=(10000,ns));bi=rng.integers(nb,size=(10000,nb));metrics={}
    for phase,ii in [('cold',[0]),('warm',[1,2,3])]:
        v,r,vt,rt=[x[:,ii,:].mean(1) for x in [vv,rr,tv,tr]]
        vs,rs,vts,rts=[x[ri[:,:,None],bi[:,None,:]].sum(2).mean(1) for x in [v,r,vt,rt]]
        metrics[phase]=dict(panel_speedup=summary(rs/vs,r.sum()/v.sum()),token_speedup=summary((vts/vs)/(rts/rs),(vt.sum()/v.sum())/(rt.sum()/r.sum())),arm_panel_s=float(v.sum(1).mean()),base_panel_s=float(r.sum(1).mean()),arm_tokens=float(vt.sum(1).mean()),base_tokens=float(rt.sum(1).mean()),process_speedups=(r.sum(1)/v.sum(1)).tolist())
        if phase=='cold':metrics[phase]['startup_inclusive_speedup']=summary((rs+np.asarray(sr)[ri].mean(1))/(vs+np.asarray(sv)[ri].mean(1)),(r.sum(1)+sr).mean()/(v.sum(1)+sv).mean())
    return dict(n=arm[0]['config']['n'],processes=3,warm_passes_per_process=3,metrics=metrics,output_mismatch_by_process_pass=mismatches,sources=[x['path'] for x in arm+base],source_hashes=[x['sha256'] for x in arm+base])

def analyze(plans,out):
    out.mkdir(exist_ok=False);groups=defaultdict(dict);pending=[]
    for plan in plans:
        for r in json.loads(plan.read_text()):
            if 'batch' not in r or 'replicate' not in r:continue
            p=Path(r['run_dir'])
            if not (p/'timing.json').exists() or not (p/'results.json').exists():pending.append(r['name']);continue
            c=json.loads((p/'config.json').read_text());t=json.loads((p/'timing.json').read_text())
            assert c['harness_commit']=='6da2e4265c0398ec0de5affaf23b0bd1df0be445' and c['engine_version']=='0.31.0' and c['gpu_type']=='NVIDIA A40'
            assert c['temperature']==0 and c['seed']==0 and not c['enable_prefix_caching'] and len(t['passes'])==4
            for z in t['passes']:
                assert abs(sum(b['wall_s'] for b in z['batches'])-z['generation_wall_s'])<1e-7
                assert z['n']==c['n'] and z['output_tokens']==sum(len(v['completion_token_ids']) for v in z['per_prompt'])
            arm=r['arm'].replace('official-','');arm='reuse' if arm=='reused' else arm;key=(r['experiment'],r['target'],r['batch']);k=(arm,r['replicate']);assert k not in groups[key]
            groups[key][k]=dict(config=c,timing=t,path=str(p),sha256=hashlib.sha256((p/'timing.json').read_bytes()).hexdigest())
    records=[]
    for key,cells in sorted(groups.items()):
        for arm in sorted({x[0] for x in cells}-{'none'}):
            for ref in ['none','reuse']:
                if arm==ref or any((a,i) not in cells for a in [arm,ref] for i in range(3)):continue
                result=contrast([cells[arm,i] for i in range(3)],[cells[ref,i] for i in range(3)]);records.append(dict(experiment=key[0],target=key[1],batch=key[2],arm=arm,reference=ref)|result)
    (out/'results.json').write_text(json.dumps(dict(status='pilot',records=records,pending=pending,uncertainty='10000 paired process and prompt-batch resamples; repeats averaged within process; available A40 placement, not randomized exclusive-host assignment'),indent=2))
    text=['# REV2 measured timing — pilot','', 'No acceptance numbers are inferred here. Three completed processes required per arm. Cold means first full panel after engine compile/warmup; startup-inclusive is separate. Output-length differences are retained.','', '| Experiment | Target | Batch | Arm / reference | n/processes | Warm panel speedup [95% CI] | Warm token ratio [95% CI] | Cold+startup [95% CI] |','|---|---|---:|---|---:|---|---|---|']
    def f(v):return f"{v['mean']:.3f} [{v['ci95'][0]:.3f},{v['ci95'][1]:.3f}]"
    for r in records:text.append(f"| {r['experiment']} | {r['target']} | {r['batch']} | {r['arm']} / {r['reference']} | {r['n']}/3 | {f(r['metrics']['warm']['panel_speedup'])} | {f(r['metrics']['warm']['token_speedup'])} | {f(r['metrics']['cold']['startup_inclusive_speedup'])} |")
    text+=['',f'Pending timing processes: {len(pending)}.'];(out/'report.md').write_text('\n'.join(text)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plans',nargs='+',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.plans,a.output)
