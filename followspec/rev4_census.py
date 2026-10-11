"""D56 pooled own-domain census; overlapping histories explicitly retained."""
import argparse,csv,json
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from followspec.rev2_analysis import load_raw,assert_prompts,summary
from ops.track_t import WS,write,sha

def memberships(history):
 tags=history.split('+');out=[]
 for group,match in [('quantization',['quantization']),('merge',['merge']),('abliteration',['abliteration']),('on_policy_RL',['on_policy_RL','on_policy_RL_claim']),('preference',['offline_preference']),('SFT',['SFT']),('distillation',['teacher_distillation','self_distillation','distillation_teacher_unspecified'])]:
  if any(x in tags for x in match):out.append(group)
 return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False)
 source=WS/'reports/REV2-evidence-20261010/census.csv';rows=list(csv.DictReader(source.open()));groups=defaultdict(list);used=[];rng=np.random.default_rng(20261011)
 for row in rows:
  if row['population']!='historical174' or row['workload']!='derivative-own-64':continue
  # Field values are audited below: no fallback workload silently included.
  aa,bb=load_raw(row['A00']),load_raw(row['A10']);assert_prompts(aa,bb);ids=sorted(k for k in aa['rows'] if aa['rows'][k]['p1'] is not None and bb['rows'][k]['p1'] is not None);x=np.array([aa['rows'][k]['p1'] for k in ids]);y=np.array([bb['rows'][k]['p1'] for k in ids]);jj=rng.integers(len(ids),size=(10000,len(ids)));draw=y[jj].mean(1)/x[jj].mean(1);point=y.mean()/x.mean()
  used.append(row|dict(categories=memberships(row['history'])))
  for g in memberships(row['history']):groups[g,row['method']].append((row,point,draw,len(ids)))
 if not used:raise ValueError('No own-domain rows: inspect workload labels; do not silently relabel')
 result=[]
 for (group,method),items in sorted(groups.items()):
  n=len(items);points=np.array([x[1] for x in items]);pool=np.stack([x[2] for x in items]);ii=rng.integers(n,size=(10000,n));jj=rng.integers(10000,size=(10000,n));draw=pool[ii,jj].mean(1)
  result.append(dict(category=group,drafter=method,checkpoints=n,families=dict(Counter(x[0]['family'] for x in items)),prompt_pairs=sum(x[3] for x in items),p1_retention=summary(draw,points.mean()),models=[x[0]['model'] for x in items]))
 write(a.output/'pooled.json',result);write(a.output/'provenance.json',dict(source=str(source),source_sha256=sha(source),selected_method_rows=len(used),unique_models=len({r['model'] for r in used}),histories=dict(Counter(r['history'] for r in used)),membership='multi-label exact recorded history tags; combination checkpoints occur in each applicable category; unknown/repack/adversarial omitted from category summaries, retained in census',used=used))
 text=['# Y9 pooled own-domain census — pilot','','Both families pooled, equal checkpoint weights,10,000 hierarchical checkpoint/paired-query draws. Categories overlap for recorded multistage histories; group differences are associations. Unknown histories excluded from category means, retained in provenance. General-fallback queries excluded.','','| Category | Drafter | Checkpoints | Family counts | Query pairs | p1 retention [95% CI] |','|---|---|---:|---|---:|---|']
 for r in result:
  q=r['p1_retention'];text.append(f"| {r['category']} | {r['drafter']} | {r['checkpoints']} | {r['families']} | {r['prompt_pairs']} | {q['mean']:.3f} [{q['ci95'][0]:.3f},{q['ci95'][1]:.3f}] |")
 (a.output/'report.md').write_text('\n'.join(text)+'\n')
 # Reuse predeclared eligibility inventory, not an outcome-selected subset.
 filters=json.loads((WS/'artifacts/REV2_A2_eligible_source_20261010_0500/filters.json').read_text());write(a.output/'focused-filter-provenance.json',filters)
 eligible=list(csv.DictReader((WS/'artifacts/REV2_A2_eligible_source_20261010_0500/selected.csv').open()))
 ids={r['model'] for r in eligible if r['population']=='focused21_prespecified_eligible' and r['workload']=='speed128'}
 assert len(ids)==21
 focus=[r for r in rows if r['population']=='focused25_including_controls' and r['workload']=='speed128' and r['model'] in ids];assert len(focus)==42
 with (a.output/'focused21.csv').open('x') as f:
  w=csv.DictWriter(f,fieldnames=list(focus[0]));w.writeheader();w.writerows(focus)
 tab=['# Focused21 SPEED-128 checkpoint results','','Existing predeclared eligibility: excludes two pretrained controls and two collapsed GRPO checkpoints; all rows remain in source census.','','| Model | Family | Lineage | History | Drafter | n | p1 retention [95% CI] |','|---|---|---|---|---|---:|---|']
 for r in focus:tab.append(f"| {r['model']} | {r['family']} | {r['lineage']} | {r['history']} | {r['method']} | {r['n']} | {float(r['p1_retention']):.3f} [{float(r['p1_low']):.3f},{float(r['p1_high']):.3f}] |")
 (a.output/'focused21.md').write_text('\n'.join(tab)+'\n')
if __name__=='__main__':main()
