import json
from pathlib import Path
import numpy as np
from rebuttal.reduce_e45 import rows,metric
root=Path('/home/heck2/sbhansali8/ReFit');out=root/'rebuttal/review_audit_20261125'
e2=json.loads((root/'rebuttal/E2/reduction_20261125_2010/results.json').read_text());e45=json.loads((root/'rebuttal/E45_verify_20261125_2010/results.json').read_text());result=[]
for t in [0,1]:
 for b in ['speed128','math128']:
  ref=next(r for r in e45['acceptance'] if r['experiment']=='E5' and r['target']==t and r['benchmark']==b and r['variant']=='reference_reuse')
  rr={r['prompt_id']:metric(r,4)[0] for r in rows(root/'rebuttal/runs'/ref['run']/'cell/per_prompt.jsonl') if r['prompt_id'] in set(ref['subset_prompt_ids'])}
  pairs=[]
  for seed in [0,1,2]:
   arms=[]
   for v in ['interface','lora-all']:
    src=next(r for r in e2['sources'] if r['target']==t and r['benchmark']==b and r['variant']==v and r['seed']==seed)
    d={r['prompt_id']:metric(r,4)[0] for r in rows(root/'rebuttal/runs'/src['run']/'cell/per_prompt.jsonl')}
    assert set(d)==set(rr);arms.append(d)
   pairs.append([[rr[q],arms[0][q],arms[1][q]] for q in sorted(rr)])
  a=np.array(pairs);rng=np.random.default_rng(0);si=rng.integers(3,size=(10000,3));qi=rng.integers(128,size=(10000,128));boot=a[si[:,:,None],qi[:,None,:]].mean((1,2));mean=a.mean((0,1));den=boot[:,2]-boot[:,0];assert np.all(den>0)
  ratio=(boot[:,1]-boot[:,0])/den
  result.append(dict(target=t,panel=b,n=128,seeds=[0,1,2],reuse_tau=mean[0],interface_tau=mean[1],whole_lora_tau=mean[2],fraction_whole_lora_gain=(mean[1]-mean[0])/(mean[2]-mean[0]),fraction_ci95=np.quantile(ratio,[.025,.975]).tolist(),definition='(interface - reuse)/(whole-LoRA - reuse), recomputed within every paired seed/query bootstrap sample'))
speeds=[]
for r in e45['timing']:
 if r['arm']=='distilled' and r['reference']=='full':
  w=r['warm'];speeds.append(dict(target=r['target'],panel=r['benchmark'],batch=r['batch'],refit_over_distilled=1/w['token_speedup'],ci95=[1/w['token_ci95'][1],1/w['token_ci95'][0]],status='observed throughput; output-equivalence diagnostic remains open'))
(out/'derived.json').write_text(json.dumps(dict(interface_fraction=result,throughput_ratio=speeds),indent=2)+'\n')
print(json.dumps(result,indent=2));print(json.dumps(speeds,indent=2))
