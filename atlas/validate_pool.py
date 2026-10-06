"""Read-only B1 acceptance checks on immutable draft artifacts."""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
from atlas.curate_pool import read_csv,validate,verify_downloads


def validate_similarities(staging,pairs):
    adapters={r['model_id']:r for r in staging if r['type']=='lora_adapter'}
    expected={frozenset(p) for p in itertools.combinations(adapters,2)};seen=set();flagged=0;undefined=0
    for r in pairs:
        key=frozenset((r['model_a'],r['model_b']))
        if key not in expected or key in seen:raise ValueError('unexpected/duplicate adapter pair')
        seen.add(key);a,b=(adapters[r[q]] for q in ('model_a','model_b'))
        if r['revision_a']!=a['revision'] or r['revision_b']!=b['revision']:raise ValueError('pair revision mismatch')
        threshold=.95 if a['pool']==b['pool']=='bank' else .9 if {a['pool'],b['pool']}=={'bank','test'} else None
        if (float(r['threshold']) if r['threshold'] else None)!=threshold:raise ValueError('wrong similarity threshold')
        if r['cosine']=='':flag='undefined_zero_update';undefined+=1
        else:
            c=float(r['cosine'])
            if not math.isfinite(c) or not -1<=c<=1:raise ValueError('invalid cosine')
            flag='above_threshold' if threshold is not None and c>threshold else ''
        if r['flag']!=flag:raise ValueError('incorrect pair flag')
        flagged+=flag=='above_threshold'
    if seen!=expected:raise ValueError('missing adapter pairs')
    return dict(adapters=len(adapters),pairs=len(pairs),above_threshold=flagged,undefined_zero_update=undefined)


def check(root,base):
    root=Path(root);counts=json.loads((root/'counts.json').read_text());report={}
    for role,prefix in [('full','candidates'),('sampled','pool_draft'),('staging','staging')]:
        rows=read_csv(root/f'{prefix}_{base}.csv');actual=validate(rows)
        if actual!=counts[role] or any(sum(group.values())!=len(rows) for group in actual.values()):raise ValueError('counts mismatch')
        report[role]=dict(n=len(rows),counts=actual)
    full=read_csv(root/f'candidates_{base}.csv');sample=read_csv(root/f'pool_draft_{base}.csv');staging=read_csv(root/f'staging_{base}.csv')
    if len(sample)!=100 or counts['errors']!=0 or counts['discovered']!=len(full) or counts['inspected']!=len(full):raise ValueError('incomplete discovery/sample')
    by_id={r['model_id']:r for r in full}
    if any(r!=by_id[r['model_id']] or r['exclusion'] for r in staging):raise ValueError('ineligible or inconsistent staging row')
    expected={r['model_id'] for r in sample}|{r['model_id'] for r in full if r['pool']=='bank'}
    if {r['model_id'] for r in staging}!=expected:raise ValueError('sample/bank staging mismatch')
    report['staged_files_verified']=verify_downloads(staging,root/'downloads.jsonl')
    with (root/'similarity.csv').open() as f:report['similarity']=validate_similarities(staging,list(csv.DictReader(f)))
    report['manifest_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob('*.csv'))}
    report.update(passed=True,draft_cutoffs_pending_owner=True,loadability_coherence='operator A2 / FIX-1; not asserted by B1')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',choices=['llama','qwen3'],required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    report=check(a.input,a.base)
    with Path(a.output).open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
