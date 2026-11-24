"""Independent EDA step-zero sanity versus the exact reproduced reused drafter."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from rebuttal.reduce_e2 import contrast


def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.workspace
    base=root/'rebuttal/runs/BASELINE_t0_reuse_speed128_s0_exactfamily/cell'
    def read(p):return [json.loads(x) for x in p.read_text().splitlines()]
    original=json.loads((base/'config.json').read_text());rows=[]
    for width in [4096,14336]:
        run=root/f'rebuttal/runs/E4_t0_eda-width{width}_step0_speed128_s0'
        if not (run/'metrics.json').exists():continue
        metadata=json.loads((run/'metrics.json').read_text())
        if metadata['exit_code']!=0:raise ValueError('Failed EDA sanity run')
        config=json.loads((run/'cell/config.json').read_text())
        for key in ['prompt_sha256','K','seed','max_new_tokens','batch_size','engine_version','target_revision','code_commit']:
            if config[key]!=original[key]:raise ValueError('Unmatched '+key)
        raw=run/'cell/per_prompt.jsonl'
        result=contrast({0:read(base/'per_prompt.jsonl')},{0:read(raw)})
        if result['n']!=128:raise ValueError('Incomplete panel')
        proof=json.loads((root/f'rebuttal/E4/step0_exports_20261124/width-{width}/preparation.json').read_text())
        result.update(width=width,trainable_params=proof['parameters']['trainable_parameters'],
                      gpu_h=metadata['gpu_hours'],run=str(run),raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
        rows.append(result)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    if rows:
        with (a.output/'results.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
