"""Independent E1 reduction of saved per-sequence counters; imports no project metrics."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def contrasts(cells):
    a,b,c,d = np.moveaxis(cells, -1, 0)
    return dict(a=a,b=b,c=c,d=d, **{
        'c-a':c-a, 'b-a':b-a, 'd-b':d-b, 'd-c':d-c, 'd-a':d-a,
        'feature': ((c-a)+(d-b))/2,
        'policy': ((b-a)+(d-c))/2,
        'interaction': d-b-c+a,
    })


def reduce_cells(cells, draws=10000, seed=0):
    cells = np.asarray(cells, dtype=np.float64)
    if cells.ndim != 2 or cells.shape[1] != 4 or not len(cells) or not np.isfinite(cells).all():
        raise ValueError('Require finite nonempty n x 4 cells ordered a,b,c,d')
    if np.any((cells < 0) | (cells > 1)):
        raise ValueError('Agreement must lie in [0,1]')
    estimates = contrasts(cells.mean(0))
    indices = np.random.default_rng(seed).integers(len(cells), size=(draws,len(cells)))
    samples = contrasts(cells[indices].mean(1))
    error = float(np.max(np.abs(samples['feature'] + samples['policy'] - samples['d-a'])))
    if error > 1e-12:
        raise AssertionError('Feature + policy != d-a in a paired resample')
    result = {key: dict(mean=float(value), ci95=np.quantile(samples[key],[.025,.975]).tolist())
              for key,value in estimates.items()}
    # Share is the ratio of macro effects in each resample, not the mean of ratios.
    valid = samples['d-a'] != 0
    shares = samples['feature'][valid] / samples['d-a'][valid]
    result['feature_share'] = dict(
        mean=float(estimates['feature']/estimates['d-a']) if estimates['d-a'] != 0 else None,
        ci95=np.quantile(shares,[.025,.975]).tolist() if len(shares) else None,
        undefined_draws=int((~valid).sum()),
        denominator_ci95=result['d-a']['ci95'],
        caution='Undefined draws omitted; near-zero denominators can make this ratio unstable.')
    result['_max_additivity_error'] = error
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    stage=args.workspace/'artifacts/P2_crossover_20261008_0348/full64'
    specs=json.loads((stage/'index.json').read_text())
    prior=json.loads((stage/'report/results.json').read_text())['results']
    args.output.mkdir(parents=True,exist_ok=False)
    results=[]; rows=[]; inputs=[]
    for spec in specs:
        if 'Tulu' in spec['model']['id']:
            continue
        raw=stage/'runs'/spec['run_id']/'per_prompt.jsonl'
        records=[json.loads(line) for line in raw.read_text().splitlines()]
        if len(records)!=64 or len({r['prompt_id'] for r in records})!=64:
            raise ValueError(f'Expected 64 distinct contexts: {raw}')
        matrices=np.asarray([r['matrix'] for r in records])
        if matrices.shape != (64,2,2):
            raise ValueError('Wrong matrix shape')
        reduced=reduce_cells(matrices.reshape(64,4))
        old=next(r for r in prior if r['model']==spec['model']['id'] and r['origin']==spec['origin'])
        for effect in ['feature','policy','interaction']:
            np.testing.assert_allclose(reduced[effect]['mean'],old['effects'][effect]['mean'],atol=1e-14)
            np.testing.assert_allclose(reduced[effect]['ci95'],old['effects'][effect]['ci95'],atol=1e-14)
        source=dict(path=str(raw.relative_to(args.workspace)),sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
        inputs.append(source)
        results.append(dict(model=spec['model']['id'],source=spec['origin'],n=64,
                            n_completion_positions=sum(r['n_tokens'] for r in records),
                            results=reduced,input=source,prior_reproduction='PASS'))
        for quantity,values in reduced.items():
            if quantity.startswith('_'):continue
            ci=values['ci95'] or [None,None]
            rows.append(dict(derivative=spec['model']['id'],text_source=spec['origin'],quantity=quantity,
                             estimate=values['mean'],ci_low=ci[0],ci_high=ci[1],n=64,
                             undefined_draws=values.get('undefined_draws',0)))
    with (args.output/'cells.csv').open('x') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (args.output/'results.json').write_text(json.dumps(dict(status='pilot',bootstrap='10000 paired sequence resamples, seed 0',
        results=results,inputs=inputs),indent=2,allow_nan=False)+'\n')
    lines=['# E1 — independent raw-cell reduction','',
        'All 12 target/source groups have 64 distinct sequences. Every saved feature, policy and interaction mean and CI reproduces the original Table-5 analysis to 1e-14.',
        '','The source code `atlas/crossover.py:factorial_effects` and saved independent reducer use:',
        '```text','a = parent taps / parent verifier; b = parent taps / child verifier',
        'c = child taps / parent verifier; d = child taps / child verifier',
        'feature = ((c-a)+(d-b))/2','policy = ((b-a)+(d-c))/2',
        'interaction = d-b-c+a','feature + policy = d-a','```','',
        'The interaction is a difference of simple effects, not an extra term to add to the averaged feature and policy effects. Additivity was checked in every resample.',
        '','Each sequence contributes its mean agreement over recorded completion positions. All four cells share the sequence bootstrap indices. CIs for every contrast and feature-share ratio come directly from its own bootstrap distribution. Ratios with near-zero denominators are unstable; zero denominators are reported as undefined, never as zero.',
        '','These are HF teacher-forced agreements, not online vLLM acceptance. Parent/child generations use the first 64 SPEED queries; public-reference uses MATH64 reference solutions and therefore changes queries as well as text source. Source-to-source differences are not controlled domain effects.',
        '','Child-source deployment contrasts (percentage points; 95% paired CIs):','',
        '| Target | Parent→child taps, parent verifier (c−a) | Parent→child taps, child verifier (d−b) | Joint change (d−a) |','|---|---:|---:|---:|']
    def fmt(v):return f"{v['mean']*100:+.2f} [{v['ci95'][0]*100:+.2f}, {v['ci95'][1]*100:+.2f}]"
    for result in results:
        if result['source']=='child':
            x=result['results'];lines.append(f"| {result['model']} | {fmt(x['c-a'])} | {fmt(x['d-b'])} | {fmt(x['d-a'])} |")
    lines.extend(['','Exact source paths and SHA-256 hashes are recorded in results.json. No cached metrics library or old reducer was imported; the original outputs were read only for the equality check.','',
                  'GPU-hours: 0.0 (CPU reanalysis of existing 12 × 64 fixed-context records).'])
    (args.output/'notes.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(groups=len(results),rows=len(rows),reproduction='PASS',output=str(args.output))))


if __name__=='__main__':main()
