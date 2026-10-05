"""Report B11 acceptance from two completed B2 cells; never launches a job."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

TARGET='meta-llama/Llama-3.1-8B-Instruct'
REFERENCE='RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3'


def validate_draft(cfg):
    if cfg.get('fc_norm') is not True or cfg.get('norm_output') is not True:
        raise ValueError('EAGLE 3.1 FC normalization and post-norm must both be enabled')


def read_cell(path, expected_prompt_hash, engine_version):
    root=Path(path)
    if (root/'failure.json').exists():raise ValueError(f'failed cell: {root}')
    cfg=json.loads((root/'config.json').read_text())
    result=json.loads((root/'results.json').read_text())
    rows=[json.loads(line) for line in (root/'per_prompt.jsonl').read_text().splitlines()]
    if cfg.get('dry_run') or cfg.get('code_dirty') or result.get('synthetic'):
        raise ValueError('require completed real cells from committed code')
    for key in ('target_revision','drafter_revision','code_commit'):
        if not re.fullmatch('[a-f0-9]{40}',cfg.get(key,'')):raise ValueError(f'unpinned {key}')
    if cfg.get('target')!=TARGET or cfg.get('adapter'):raise ValueError('B11 requires the unchanged Llama base')
    if cfg.get('K')!=4 or cfg.get('method')!='eagle3':raise ValueError('B11 requires EAGLE3 at K=4')
    if cfg.get('temperature')!=0 or cfg.get('top_p')!=1:raise ValueError('greedy decoding required')
    if cfg.get('engine_version')!=engine_version or result.get('engine_version')!=engine_version:
        raise ValueError('pinned engine mismatch')
    if cfg.get('prompt_sha256')!=expected_prompt_hash:raise ValueError('SPEED prompt hash mismatch')
    if len(rows)!=128 or result.get('n')!=128 or cfg.get('n')!=128:raise ValueError('128 SPEED prompts required')
    if len({r['prompt_id'] for r in rows})!=128:raise ValueError('duplicate prompt IDs')
    vals=[r['acceptance_length'] for r in rows]
    if any(not math.isfinite(v) or not 1<=v<=5 for v in vals):raise ValueError('invalid acceptance lengths')
    if not math.isclose(sum(vals)/128,result['macro_acceptance_length'],rel_tol=0,abs_tol=1e-12):
        raise ValueError('aggregate disagrees with per-prompt records')
    if not result.get('gpu_type') or not result.get('generation_wall_s',0)>0:raise ValueError('missing real execution metadata')
    return cfg,result,{r['prompt_id']:r['acceptance_length'] for r in rows}


def compare(candidate,reference,*,expected_prompt_hash,engine_version):
    import numpy as np
    c,cr,cv=read_cell(candidate,expected_prompt_hash,engine_version)
    r,rr,rv=read_cell(reference,expected_prompt_hash,engine_version)
    validate_draft(json.loads((Path(candidate)/'drafter_config.json').read_text()))
    if r['drafter']!=REFERENCE:raise ValueError('wrong RedHatAI reference drafter')
    if not c.get('drafter_files_sha256'):raise ValueError('local trained checkpoint file hashes required')
    for key in ('target_revision','seed','max_new_tokens','batch_size','max_model_len','dtype','enable_prefix_caching'):
        if key not in c or key not in r or c[key]!=r[key]:raise ValueError(f'matched setting required: {key}')
    if cv.keys()!=rv.keys():raise ValueError('prompt IDs differ')
    diff=np.array([cv[key]-rv[key] for key in sorted(cv)])
    rng=np.random.default_rng(0)
    boot=diff[rng.integers(0,len(diff),size=(2000,len(diff)))].mean(axis=1)
    value=float(diff.mean())
    return dict(n=128,candidate_macro=cr['macro_acceptance_length'],reference_macro=rr['macro_acceptance_length'],
        difference=value,difference_ci95=np.quantile(boot,[.025,.975]).tolist(),
        uncertainty='paired prompt bootstrap, 2000 resamples, seed 0; not training-seed or repeat uncertainty',
        shortfall=max(0.,-value),baseline_met=value>=0,
        requirement='baseline met' if value>=0 else 'shortfall reported',
        source_runs=[str(Path(candidate).resolve()),str(Path(reference).resolve())],
        config_sha256={str(Path(p).resolve()):hashlib.sha256((Path(p)/'config.json').read_bytes()).hexdigest() for p in (candidate,reference)},
        engine_version=engine_version,prompt_sha256=expected_prompt_hash)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',required=True);p.add_argument('--reference',required=True)
    p.add_argument('--speed-prompts',required=True);p.add_argument('--engine-lock',required=True)
    p.add_argument('--report',required=True)
    a=p.parse_args()
    report=compare(a.candidate,a.reference,
        expected_prompt_hash=hashlib.sha256(Path(a.speed_prompts).read_bytes()).hexdigest(),
        engine_version=json.loads(Path(a.engine_lock).read_text())['vllm_version'])
    with Path(a.report).open('x') as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n')

if __name__=='__main__':main()
