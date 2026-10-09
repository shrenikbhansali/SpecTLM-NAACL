"""Attach operator-verified timing/cost tables to a raw acceptance snapshot."""
import json,hashlib,argparse
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();ws=a.workspace;out=a.output;d50=ws/'artifacts/P3_D50_20261009_0200';inputs={}
 def read(p):
  p=Path(p);b=p.read_bytes();inputs[str(p)]=hashlib.sha256(b).hexdigest();return json.loads(b)
 def verified(p):
  d=read(p)
  for q,h in d.get('input_sha256',{}).items():
   assert hashlib.sha256(Path(q).read_bytes()).hexdigest()==h,q
  return d
 def fmt(v,ci):return f'{v:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]'
 def table(name,header,rows):
  (out/f'{name}.md').open('x').write('\n'.join('| '+' | '.join(map(str,r))+' |' for r in [header,['---']*len(header),*rows])+'\n')
  def esc(x):return str(x).replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')
  (out/f'{name}.tex').open('x').write('\n'.join(['% Pilot; estimates explicitly labelled.',r'\begin{tabular}{'+'l'*len(header)+'}',r'\hline']+[' & '.join(map(esc,r))+r' \\' for r in [header,*rows]]+[r'\hline',r'\end{tabular}'])+'\n')
 timing=verified(d50/'E6-timing/timing/snapshot-20261009_025012/results.json') if (d50/'E6-timing/timing/snapshot-20261009_025012/results.json').exists() else verified(sorted((d50/'E6-timing/timing').glob('snapshot-*/results.json'))[-1])
 independent=verified(d50/'E3-timing/analysis/snapshot-20261009_030417/results.json');model=verified(d50/'cost-model/snapshot-20261009_025042/results.json');pred={(r['batch_size'],r['arm']):r for r in model['predictions'] if 'validation' in r and r.get('data') in ['16k','reused','oracle','generic16k']};tt=[]
 for target,source in [('R1',timing),('R1',independent)]:
  for r in source['records']:
   if r['reference']!='none':continue
   b,arm=r['batch_size'],r['arm'];w=r['metrics']['warm'];cold=r['metrics']['cold'];p=pred.get((b,arm));pr='--';err='--'
   if p:pr=fmt(p['predicted_speedup'],p['predicted_speedup_ci95']);err=f"{100*(p['predicted_tokens_per_second']/p['validation']['measured_tokens_per_second']-1):.2f}%"
   tt.append([target,b,arm,f"{r['n_queries']} / {r.get('n_process_replicates',3)}",fmt(w['panel_time_speedup'],w['paired_process_batch_ci95']),fmt(w['token_throughput_ratio'],w['token_throughput_ci95']),fmt(cold['startup_inclusive_speedup'],cold['startup_inclusive_ci95']),pr,err])
 nemo=ws/'artifacts/P6_Nemo_20261009_1428/analysis'
 ns=sorted(nemo.glob('snapshot-*/results.json'))
 if ns:
  nmodels=sorted((nemo.parent/'cost-model').glob('snapshot-*/results.json'));npred={(r['batch_size'],r['arm']):r for r in verified(nmodels[-1])['predictions']} if nmodels else {}
  for r in verified(ns[-1])['records']:
   if r['reference']!='none':continue
   w=r['metrics']['warm'];c=r['metrics']['cold'];p=npred.get((r['batch_size'],r['arm']));pr=fmt(p['predicted_speedup'],p['predicted_speedup_ci95']) if p else '--';err=f"{p['validation']['prediction_relative_error']:+.2%}" if p and p['validation'] else '--';tt.append(['Nemotron',r['batch_size'],r['arm'],f"{r['n_queries']} / {r['n_process_replicates']}",fmt(w['panel_time_speedup'],w['paired_process_batch_ci95']),fmt(w['token_throughput_ratio'],w['token_throughput_ci95']),fmt(c['startup_inclusive_speedup'],c['startup_inclusive_ci95']),pr,err])
 table('speedup',['Target','Batch','Arm','n / processes','Warm panel speedup','Measured token speedup','First panel + startup','Predicted token speedup','TPS prediction error'],tt)
 result=read(out/'results.json');costs=[];seen=set()
 for r in result['records']:
  if r['campaign']!='three-seed' and any(q['label']==r['label'] and q['target']==r['target'] and isinstance(q['step'],int) and q['step']>r['step'] for q in result['records']):continue
  if r['campaign'] not in ['three-seed','FIX24_20261009_1420','P3_E5c64k_20261009_1420'] and r.get('label') not in ['E4-scratch16k','E5-second-epoch','E7-production-t1-16k-fc','E7-production-t1-16k-full']:continue
  key=(r['target'],r['label'],str(r['step']))
  if key in seen:continue
  seen.add(key);cc=r.get('cost_operator_verified');cc=cc if isinstance(cc,list) else [cc]
  for seed,c in enumerate(cc):
   if not c:continue
   costs.append(['R1' if r['target']==0 else 'Nemotron',r['label'],seed if len(cc)>1 else r.get('seed',0),r['step'],f"{c.get('data_gpu_hours',float('nan')):.3f}",f"{c.get('training_gpu_hours',c.get('incremental_training_gpu_hours',0)+c.get('prior_training_gpu_hours',0)):.3f}",f"{c.get('total_gpu_hours',float('nan')):.3f}",'measured; shared data charged once per alternative'])
 table('repair-cost',['Target','Arm','Seed','Step','Data GPUh','Train GPUh','Total GPUh','Scope'],costs)
 estimate=verified(ws/'artifacts/P6_D49_recipe_estimate_20261008_1800/estimate.json');(out/'dedicated-estimate.json').open('x').write(json.dumps(estimate,indent=2)+'\n')
 table('dedicated-estimate',['Hypothetical epochs','Estimated data + train A40 GPUh','Scope'],[[ep,f"{min(r['total_gpu_hours_proxy'] for r in estimate['scenarios'] if r['epochs']==ep):.0f}–{max(r['total_gpu_hours_proxy'] for r in estimate['scenarios'] if r['epochs']==ep):.0f}",'532k–646k examples; 557–2048 tokens; actual oracle recipe unknown'] for ep in [1,10,40]])
 (out/'supplement-provenance.json').open('x').write(json.dumps(dict(status='pilot',input_sha256=inputs,validation='Existing operator/raw-verified sources; all recorded input hashes rechecked',timing='3 processes x3 warm passes; paired process/query-batch CIs; first panel after compile; startup separate',cost='Measured online capture/data/train GPUh, not campaign total. Shared generation counted once per alternative. Dedicated cost is a sensitivity estimate, not actual oracle cost or confidence interval.'),indent=2)+'\n')
 with (out/'report.md').open('a') as f:f.write('\nTiming/cost: [measured and predicted speedups](speedup.md), [repair costs](repair-cost.md), [dedicated-cost sensitivity estimate](dedicated-estimate.md). All have LaTeX companions. Timing compares the same input IDs, but greedy output sequences can differ; lengths and token-normalized throughput are retained. Available A40 placement is not randomized exclusive-host timing. Model fits use earlier R1 conditions with 16k held out, K4 only. Any Nemotron predictions are explicitly cross-target transfer stress tests, not a calibrated Nemotron model; independent-drafter predictions are unavailable. Dedicated estimates are not the oracle\'s actual bill; upstream TTT7 differs from our measured TTT3, and 40 epochs is a code default, not a known oracle training schedule.\n')
 print(out)
if __name__=='__main__':main()
