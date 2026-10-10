"""Portable, provenance-linked export of already verified P1/FIX23 census evidence."""
import argparse,csv,hashlib,json
from pathlib import Path

def main(root,out):
    out.mkdir(parents=True,exist_ok=False)
    sources=['artifacts/FIX23_census_20261008_1640/results.json','artifacts/P1_typed_20261008_1515/analysis-v3/results.json','artifacts/P1_typed_20261008_1515/typed-v2.json']
    hist,focused,cards=[json.loads((root/s).read_text()) for s in sources]
    bymodel={r['model']:r for r in cards}
    records=[]
    for population,data in [('historical174',hist),('focused25_including_controls',focused)]:
        for r in data['records']:
            c=bymodel[r['model']];p1=r['retention'].get('macro_p1',r['retention'].get('p1'))
            records.append(dict(population=population,model=r['model'],revision=r['revision'],family=r.get('base') or ('qwen' if 'qwen' in r['model'].lower() else 'llama'),method=r['method'],workload=r['workload'],n=r['n'],lineage=r['lineage'],history='+'.join(r['history']),quality=r.get('quality','historical'),p1_retention=p1['mean'],p1_low=p1['ci95'][0],p1_high=p1['ci95'][1],tau_retention=r['retention']['tau']['mean'],length_retention=r['retention']['length']['mean'],card_url=c['card_url'],card_sha256=c['card_sha256'],evidence=json.dumps(c['evidence']),source=json.dumps(r.get('run_dirs',r.get('sources')))))
    with (out/'per-model.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    (out/'card-inventory.json').write_text(json.dumps(cards,indent=2))
    (out/'groups.json').write_text(json.dumps(dict(historical=hist['classes'],focused=focused['classes']),indent=2))
    lines=['# Archived 174-checkpoint census: family/workload/lineage/history composition','',
           'Previously verified FIX23 estimates, not newly fitted numbers. Hierarchical checkpoint/prompt bootstrap intervals. Focused SPEED study is separate in groups.json; controls and composite histories remain labeled.','',
           '| Family | Workload | Lineage | History | Drafter | Checkpoints | Prompt pairs | p1 retention [95% CI] |','|---|---|---|---|---|---:|---:|---|']
    for r in hist['classes']:
        v=r['macro_p1_retention'];lines.append(f"| {r['base']} | {r['workload']} | {r['lineage']} | {r['history']} | {r['method']} | {r['n_checkpoints']} | {r['n_prompt_pairs']} | {v['mean']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] |")
    (out/'census-groups.md').write_text('\n'.join(lines)+'\n')
    (out/'provenance.json').write_text(json.dumps(dict(source_hashes={s:hashlib.sha256((root/s).read_bytes()).hexdigest() for s in sources},historical_counts=hist['counts'],focused_counts=focused['counts'],exported_rows=len(records)),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.root,a.output)
