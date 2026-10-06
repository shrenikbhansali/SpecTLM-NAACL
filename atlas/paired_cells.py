"""Validate cell counters and compare only shared nonzero-step prompts (D32)."""
import argparse
import json
import math
from pathlib import Path
import statistics
import subprocess
from atlas.run_cell import metrics,sha256,write_new

SETTINGS=('K','seed','max_new_tokens','batch_size','max_model_len','dtype','temperature','top_p',
          'engine_version','method','max_lora_rank','gpu_memory_utilization','enable_prefix_caching')


def read_cell(path):
    root=Path(path)
    if (root/'failure.json').exists():raise ValueError('failed cell in index')
    cfg=json.loads((root/'config.json').read_text());res=json.loads((root/'results.json').read_text())
    raw=[json.loads(s) for s in (root/'per_prompt.jsonl').read_text().splitlines() if s.strip()]
    if not raw or len({r['prompt_id'] for r in raw})!=len(raw):raise ValueError('invalid prompt records')
    if 'n' in cfg and cfg['n']!=len(raw):raise ValueError('incomplete prompt records')
    values={}
    for row in raw:
        rebuilt=metrics(row['per_step_accepted'],row['per_step_drafted'],cfg['K'])
        for key,value in rebuilt.items():
            if key=='zero_step' and not value and key not in row:continue  # historical nonzero cells
            if key not in row or row[key]!=value:raise ValueError('per-prompt counters or zero-step flag not consistent')
        values[row['prompt_id']]=rebuilt['acceptance_length']
    finite=[v for v in values.values() if v is not None];nzero=len(raw)-len(finite)
    mean=statistics.mean(finite) if finite else None
    if res['n']!=len(finite) or res.get('n_total',len(raw))!=len(raw) or res.get('n_zero_step',0)!=nzero:
        raise ValueError('inconsistent aggregate counts')
    observed=res['macro_acceptance_length']
    if (mean is None and observed is not None) or (mean is not None and (observed is None or not math.isfinite(observed) or abs(observed-mean)>1e-10)):
        raise ValueError('macro not derivable from counters')
    for name,key in [('total_drafts','num_drafts'),('total_accepted_draft_tokens','num_accepted_tokens')]:
        if name in res and res[name]!=sum(r[key] for r in raw):raise ValueError('inconsistent aggregate counters')
    if cfg['engine_version']!='0.31.0' or res['engine_version']!=cfg['engine_version']:raise ValueError('mixed/unpinned engine')
    if cfg['code_dirty'] or cfg['temperature']!=0 or cfg['top_p']!=1:raise ValueError('invalid cell config')
    settings={k:cfg[k] for k in SETTINGS}
    settings.update(enable_lora=cfg.get('enable_lora',bool(cfg.get('adapter'))),use_prompt_token_ids=cfg.get('use_prompt_token_ids',False))
    return dict(config=cfg,results=res,value=mean,prompt_values=values,n_prompts=len(raw),n_valid=len(finite),n_zero_step=nzero,
                prompt_ids=sorted(values),prompt_sha256=cfg['prompt_sha256'],settings=settings)


def paired_values(left,right):
    """Two means over identical valid IDs. Empty intersections are unestimable."""
    if any(left[k]!=right[k] for k in ('prompt_sha256','prompt_ids','settings')):raise ValueError('controls not matched')
    if 'prompt_values' not in left or 'prompt_values' not in right:
        # Direct callers with historical all-valid aggregate fixtures only.
        if 'prompt_values' in left or 'prompt_values' in right or left.get('n_zero_step',0) or right.get('n_zero_step',0):
            raise ValueError('per-prompt values required for zero-step pairing')
        return dict(values=[left['value'],right['value']],n_paired=left['n_prompts'],n_excluded=0,excluded_prompt_ids=[])
    a,b=left['prompt_values'],right['prompt_values']
    if set(a)!=set(left['prompt_ids']) or set(b)!=set(right['prompt_ids']):raise ValueError('prompt map differs')
    ids=sorted(k for k in a if a[k] is not None and b[k] is not None)
    if not ids:raise ValueError('no paired nonzero-step prompts; comparison undefined')
    if any(not math.isfinite(v[k]) or v[k]<1 for v in (a,b) for k in ids):raise ValueError('invalid prompt acceptance')
    excluded=sorted(set(a)-set(ids))
    return dict(values=[statistics.mean(v[k] for k in ids) for v in (a,b)],n_paired=len(ids),n_excluded=len(excluded),excluded_prompt_ids=excluded)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',required=True);p.add_argument('--child',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    a,b=read_cell(args.parent),read_cell(args.child)
    if any(a['config'].get(k)!=b['config'].get(k) for k in ('drafter','drafter_revision','drafter_files_sha256')):raise ValueError('drafter not matched')
    result=paired_values(a,b);parent,child=result['values']
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    cfg=dict(parent=str(Path(args.parent).resolve()),child=str(Path(args.child).resolve()),policy='D32 pairwise shared nonzero-step prompts',
             engine_version='0.31.0',code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
             inputs_sha256={str(Path(root)/name):sha256(Path(root)/name) for root in (args.parent,args.child) for name in ('config.json','results.json','per_prompt.jsonl')})
    result.update(parent=parent,child=child,delta=child-parent,retention=child/parent)
    write_new(out/'config.json',cfg);write_new(out/'results.json',result)
    write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
        what_why='D32 matched-prompt cell comparison',new='Exclude zero-step observations pairwise, with counts and IDs',artifacts=str(out.resolve()),config_results=dict(config=cfg,results=result),
        caveats='Single-cell pair; no run-to-run uncertainty estimate. Operator assigns derivative and ledger ID.'))


if __name__=='__main__':main()
