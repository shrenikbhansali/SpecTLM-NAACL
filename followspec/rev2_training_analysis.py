"""D54 matched training scopes and final frozen counter comparisons."""
import argparse,json
from pathlib import Path
import numpy as np
from followspec.rev2_analysis import load_raw,assert_prompts,paired_seed_query
from followspec.review_followup import parts
from ops.track_t import WS,DISPATCH,lines,write
FROZEN='6da2e4265c0398ec0de5affaf23b0bd1df0be445'
MATCH=['data_sha256','forbidden_sha256','batch_plan','seed','steps','ttt_steps','lr','optimizer','weight_decay','scheduler','warmup_ratio','schedule_horizon','token_budget','drafter','target','batch_tokens']

def matched_training(a,b):
    for key in MATCH:
        if a.get(key)!=b.get(key):raise ValueError('unmatched training '+key)
    return True

def combine(reference,cells,oracle=None):
    references=reference if isinstance(reference,list) else [reference]*len(cells)
    if len(references)!=len(cells):raise ValueError('seed counts differ')
    anchor=references[0]
    for c in references+cells+([oracle] if oracle else []):
        assert_prompts(anchor,c)
        for key in ['target','target_revision','max_model_len']:
            if anchor['config'].get(key)!=c['config'].get(key):raise ValueError('unmatched repair '+key)
        if c['config']['code_commit']!=FROZEN and c['config'].get('frozen_harness_commit')!=FROZEN:raise ValueError('not frozen acceptance')
    ids=sorted(k for k in anchor['rows'] if all(c['rows'][k]['p1'] is not None for c in references+cells) and (oracle is None or oracle['rows'][k]['p1'] is not None))
    results={}
    for key in ['p1','tau','length']:
        a=np.array([[c['rows'][k][key] for k in ids] for c in references]);b=np.array([[c['rows'][k][key] for k in ids] for c in cells]);o=None if oracle is None or key!='tau' else [oracle['rows'][k][key] for k in ids]
        results[key]=paired_seed_query(a,b,o)
    conditional=[]
    for depth in range(anchor['config']['K']):
        kk=[k for k in ids if all(c['rows'][k]['conditional'][depth] is not None for c in references+cells)]
        if not kk:conditional.append(None);continue
        a=np.array([[c['rows'][k]['conditional'][depth] for k in kk] for c in references]);b=np.array([[c['rows'][k]['conditional'][depth] for k in kk] for c in cells]);conditional.append(paired_seed_query(a,b))
    return dict(metrics=results,conditional=conditional,paired_ids=ids,reference=[c['source'] for c in references],sources=[c['source'] for c in cells],source_hashes=[c['sha256'] for c in cells],oracle=oracle['source'] if oracle else None)

def e8(stage,panels,out):
    out.mkdir(exist_ok=False);d={j['name']:j for j in lines(DISPATCH)};plan=json.loads((stage/'plan.json').read_text());records=[];pending=[];audits=[]
    def fromjob(name):
        _,i=parts(d[name]);return Path(i[i.index('--output')+1])
    def train_root(t,arm,seed):
        if arm=='interface' and (t==0 or seed==0):return fromjob(f'FIX24-official-t{t}-16k-fc'+(f'-seed{seed}' if seed else ''))
        return stage/f'REV2-E8-t{t}-{arm}-seed{seed}'
    def cell_root(t,arm,seed,w):
        if arm=='interface' and (t==0 or seed==0):
            root=train_root(t,arm,seed);cfg=json.loads((root/'config.json').read_text());step=cfg['steps']
            if w=='math500':
                name='D52-MATH500-official-fc' if t==0 and seed==0 else f'REV2-E14-t{t}-fc-seed{seed}-math500'
            else:name=f'FIX24-official-t{t}-16k-fc'+(f'-seed{seed}' if seed else '')+f'-s{step}-{w}'
            return fromjob(name)
        return stage/'eval'/f'REV2-E8-t{t}-{arm}-seed{seed}-{w}'
    for t in [0,1]:
        for left,right,label in [('decoder-qo','interface','dense50M'),('decoder-r16','interface-r75','lowrank1.229M')]:
            for w,seeds in [('speed128',[0,1,2]),('math64',[0,1,2]),('math500',[0])]:
                aa=[];bb=[]
                for seed in seeds:
                    x,y=cell_root(t,left,seed,w),cell_root(t,right,seed,w)
                    if not (x/'results.json').exists() or not (y/'results.json').exists():pending.append(dict(target=t,contrast=label,seed=seed,workload=w,paths=[str(x),str(y)]));continue
                    ca=json.loads((train_root(t,left,seed)/'config.json').read_text());cb=json.loads((train_root(t,right,seed)/'config.json').read_text());matched_training(ca,cb)
                    a,b=load_raw(x),load_raw(y);assert_prompts(a,b);assert a['config']['code_commit']==b['config']['code_commit']==FROZEN;aa.append(a);bb.append(b);audits.append(dict(target=t,contrast=label,seed=seed,workload=w,passed=True))
                if len(aa)!=len(seeds):continue
                ids=sorted(k for k in aa[0]['rows'] if all(c['rows'][k]['p1'] is not None for c in aa+bb));metrics={}
                for key in ['p1','tau','length']:
                    a=np.array([[c['rows'][k][key] for k in ids] for c in aa]);b=np.array([[c['rows'][k][key] for k in ids] for c in bb]);metrics[key]=paired_seed_query(a,b)
                records.append(dict(target=t,contrast=label,workload=w,metrics=metrics,reference=left,arm=right,sources=[c['source'] for c in aa+bb]))
    write(out/'results.json',dict(status='pilot',records=records,pending=pending,audits=audits))
    text=['# E8 matched location at16k — pilot','', 'Positive difference means interface exceeds decoder. Paired seed and query bootstrap10,000 draws; all three seeds required for SPEED/MATH64 rows. Final-only export/storage choices do not change the checked optimization schedule.','', '| Target | Parameters | Panel | n/seeds | Interface τ | Decoder τ | Δτ [95% CI] | Δp1 [95% CI] |','|---|---|---|---:|---:|---:|---|---|']
    def f(d):return f"{d['mean']:+.3f} [{d['ci95'][0]:+.3f},{d['ci95'][1]:+.3f}]"
    for r in records:
        m=r['metrics'];q=m['tau'];text.append(f"| {r['target']} | {r['contrast']} | {r['workload']} | {q['n']}/{q['seeds']} | {q['arm']['mean']:.3f} | {q['reference']['mean']:.3f} | {f(q['delta'])} | {f(m['p1']['delta'])} |")
    text+=['',f'Pending paired seed/workload inputs: {len(pending)}.'];(out/'report.md').write_text('\n'.join(text)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--panels',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();e8(a.stage,a.panels,a.output)
