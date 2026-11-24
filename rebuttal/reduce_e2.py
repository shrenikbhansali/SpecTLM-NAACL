"""Independent raw-counter, seed/query-paired reduction; retain all valid outcomes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from rebuttal.baselines import raw_metric


def contrast(reference, candidate):
    seeds = sorted(set(reference) & set(candidate))
    if not seeds:
        raise ValueError('No paired training seeds')
    maps = []
    ids = None
    for seed in seeds:
        pair = []
        for rows in [reference[seed], candidate[seed]]:
            mapping = {r['prompt_id']: raw_metric(r) for r in rows}
            if len(mapping) != len(rows):
                raise ValueError('Duplicate prompt IDs')
            if ids is not None and set(mapping) != ids:
                raise ValueError('Different prompt sets')
            ids = set(mapping)
            pair.append(mapping)
        maps.append(pair)
    kept = sorted(k for k in ids if all(m[k] is not None for pair in maps for m in pair))
    if not kept:
        raise ValueError('No valid paired queries')
    # axes: seed, query, arm, metric (tau,p1)
    values = np.array([[[pair[0][k], pair[1][k]] for k in kept] for pair in maps])
    rng = np.random.default_rng(0)
    seed_draw = rng.integers(len(seeds), size=(10000, len(seeds)))
    query_draw = rng.integers(len(kept), size=(10000, len(kept)))
    sampled = values[seed_draw[:, :, None], query_draw[:, None, :]].mean(axis=(1, 2))
    mean = values.mean(axis=(0, 1))
    result = dict(seeds=seeds, n=len(kept), excluded_zero_step=len(ids)-len(kept))
    for m, metric in enumerate(['tau', 'p1']):
        for arm, label in enumerate(['reference', 'candidate']):
            result[label+'_'+metric] = float(mean[arm, m])
            result[label+'_'+metric+'_ci95'] = np.quantile(sampled[:, arm, m], [.025, .975]).tolist()
        # Difference before reduction avoids floating cancellation in constant-delta tests.
        deltas = values[:, :, 1, m] - values[:, :, 0, m]
        boot = deltas[seed_draw[:, :, None], query_draw[:, None, :]].mean(axis=(1, 2))
        result['delta_'+metric] = float(deltas.mean())
        result['delta_'+metric+'_ci95'] = np.quantile(boot, [.025, .975]).tolist()
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    groups = {}; sources = []; costs = 0.; excluded = []
    for run in sorted((a.workspace / 'rebuttal/runs').glob('E2_*')):
        if not (run / 'metrics.json').exists():
            continue
        metadata = json.loads((run / 'metrics.json').read_text())
        costs += metadata['gpu_hours']
        if metadata['exit_code'] != 0 or not (run / 'cell/per_prompt.jsonl').exists():
            continue
        config = json.loads((run / 'config.yaml').read_text())
        variant = config['variant']
        training_run = config.get('training_run', '')
        if training_run:
            if 'decoder_head_lora' in training_run:
                variant = 'decoder-head'
            elif 'whole_lora' in training_run:
                variant = {'all': 'lora-all', 'no_fc': 'lora-no_fc', 'fc_only': 'lora-fc_only'}[variant]
        elif variant in ['lora-no_fc', 'lora-fc_only'] and not run.name.endswith('_shards2'):
            excluded.append({'run': run.name, 'reason': 'INVALID-v1 duplicate physical tensor keys'})
            continue
        if config['harness_commit'] != '6da2e4265c0398ec0de5affaf23b0bd1df0be445':
            raise ValueError('Non-frozen acceptance harness')
        key = (config['target'], config['benchmark'], variant)
        seed = config['training_seed']
        if seed in groups.setdefault(key, {}):
            raise ValueError('Duplicate evaluation for same target/benchmark/variant/seed')
        path = run / 'cell/per_prompt.jsonl'
        rows = [json.loads(x) for x in path.read_text().splitlines()]
        if len(rows) != 128:
            raise ValueError('Incomplete held-out panel')
        actual = json.loads((run / 'cell/config.json').read_text())
        if actual['K'] != 4 or actual['max_new_tokens'] != 512 or actual['batch_size'] != 8:
            raise ValueError('Wrong acceptance protocol')
        groups[key][seed] = rows
        sources.append(dict(run=run.name, target=key[0], benchmark=key[1], variant=variant, seed=seed,
                            prompt_sha256=actual['prompt_sha256'], raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for target in [0, 1]:
        for bench in ['speed128', 'math128']:
            hashes = {r['prompt_sha256'] for r in sources if r['target']==target and r['benchmark']==bench}
            if len(hashes)>1:
                raise ValueError('Rendered prompt mismatch')
    results = []
    for (target, bench, variant), values in sorted(groups.items()):
        reference = groups.get((target, bench, 'interface'), {})
        if reference and set(reference) & set(values):
            results.append(dict(target=target, benchmark=bench, variant=variant,
                                reference='interface', **contrast(reference, values)))
    a.output.mkdir(parents=True, exist_ok=False)
    report = dict(results=results, sources=sources, excluded=excluded,
                  completed_gpu_hours_including_failures_and_invalid_attempts=costs,
                  method='10,000 paired seed/query bootstrap resamples; seed0; raw per-step counters only')
    (a.output / 'results.json').write_text(json.dumps(report, indent=2)+'\n')
    if results:
        with (a.output / 'results.csv').open('w') as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0]))
            writer.writeheader(); writer.writerows(results)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
