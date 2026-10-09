"""D-51 pilot comparison: paired repair gains relative to each initialization's reuse.

CPU analysis only. Inputs are immutable frozen-harness acceptance records. Output
is a new directory. Selection is descriptive; CIs are not selection-adjusted.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
from paper.d50_summary import raw_values, paired_summary, check_pair, invalid_path

FROZEN = '6da2e4265c0398ec0de5affaf23b0bd1df0be445'


def check_training(a, b):
    """Only initialization/operational metadata may differ in matched comparisons."""
    required = ['data_sha256', 'steps', 'seed', 'n', 'token_budget', 'variant',
                'lr', 'batch_tokens', 'ttt_steps', 'algorithm', 'one_epoch',
                'batch_plan', 'schedule_horizon']
    optional = ['schedule_steps', 'lora_rank', 'lora_alpha', 'scratch',
                'offload_saved_tensors', 'release_grad_before_forward',
                'backend_revision', 'engine_version', 'forbidden_sha256',
                'max_anchors', 'checkpoint_dflash_layers', 'continue_epoch_from']
    for k in required + optional:
        if (k in required and (k not in a or k not in b)) or a.get(k) != b.get(k):
            raise ValueError(f'matched training mismatch: {k}')
    for k in ['id', 'revision']:
        if a['target'][k] != b['target'][k]:
            raise ValueError(f'matched training mismatch: target.{k}')


def delta_comparison(official, official_reuse, production, production_reuse, draws=10000, oracle=None):
    """Same seed indices and prompt resamples across all four conditions."""
    a, b, c, d = map(lambda x: np.asarray(x, dtype=float),
                     [official, official_reuse, production, production_reuse])
    if a.ndim != 3 or a.shape != c.shape or b.shape != a.shape[1:] or d.shape != b.shape:
        raise ValueError('matched seed/query/metric shape mismatch')
    n_original = a.shape[1]
    valid = (np.isfinite(a[:, :, :2]).all(axis=(0, 2)) &
             np.isfinite(c[:, :, :2]).all(axis=(0, 2)) &
             np.isfinite(b[:, :2]).all(1) & np.isfinite(d[:, :2]).all(1))
    if oracle is not None:
        oracle = np.asarray(oracle, dtype=float)
        valid &= np.isfinite(oracle[:, :2]).all(1)
        oracle = oracle[valid]
    a, b, c, d = a[:, valid], b[valid], c[:, valid], d[valid]
    if not len(b):
        raise ValueError('no shared nonzero-step prompts')
    # The difference array preserves covariance of matched seeds and all baselines.
    diff = (a - b[None]) - (c - d[None])
    contrast = paired_summary(diff, np.zeros_like(b), draws=draws)
    return dict(n_total=n_original, n_paired=len(b), seed_count=len(a),
                official=paired_summary(a, b, oracle, draws=draws),
                production=paired_summary(c, d, oracle, draws=draws),
                official_reuse=paired_summary(b[None], b, oracle, draws=draws),
                production_reuse=paired_summary(d[None], d, oracle, draws=draws),
                difference=contrast['metrics'], bootstrap_draws=draws,
                estimand='(official repair - official reuse) - (production repair - production reuse)')


def choose_primary(records):
    wanted = {(a, w) for a in ['fc', 'full'] for w in ['speed128', 'math64']}
    ready = {(r['arm'], r['workload']): r for r in records
             if r['target'] == 0 and r['budget'] == 16000 and r['seeds'] == [0, 1, 2]}
    missing = sorted(wanted - ready.keys())
    if missing:
        return dict(status='pending', primary=None, missing=missing,
                    rule='R1 16k, 3 matched seeds, SPEED-128 primary; MATH-64 secondary')
    winners = {}
    for arm in ['fc', 'full']:
        difference = ready[arm, 'speed128']['difference']['tau']['mean']
        winners[arm] = 'official' if difference > 0 else 'production' if difference < 0 else 'tie'
    if len(set(winners.values())) != 1 or 'tie' in winners.values():
        return dict(status='mixed_variant_directions', primary=None, per_variant=winners,
                    reason='No owner rule aggregates conflicting fc/full directions or exact ties; retain both.')
    primary = winners['fc']
    return dict(status='selected', primary=primary,
                robustness='production' if primary == 'official' else 'official',
                per_variant=winners,
                rule='Larger matched 16k SPEED-128 repair delta, 3 seeds; MATH-64 secondary',
                caveat='Data-dependent descriptive selection; bootstrap CIs are not selection-adjusted.')


def write_table(out, name, headers, rows):
    with (out / (name + '.md')).open('x') as f:
        f.write('\n'.join('| ' + ' | '.join(map(str, row)) + ' |'
                          for row in [headers, ['---'] * len(headers), *rows]) + '\n')
    def esc(x):
        return str(x).replace('_', r'\_').replace('%', r'\%').replace('&', r'\&').replace('#', r'\#')
    with (out / (name + '.tex')).open('x') as f:
        f.write('\n'.join([r'\begin{tabular}{' + 'l' * len(headers) + '}'] +
                          [' & '.join(map(esc, row)) + r' \\' for row in [headers, *rows]] +
                          [r'\end{tabular}']) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workspace', type=Path, required=True)
    ap.add_argument('--catalog', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    ws, out = args.workspace, args.output
    out.mkdir(parents=True, exist_ok=False)
    hashes, cache = {}, {}
    def read(path, jsonl=False):
        p = Path(path); data = p.read_bytes(); hashes[str(p)] = hashlib.sha256(data).hexdigest()
        return [json.loads(x) for x in data.splitlines()] if jsonl else json.loads(data)
    cat = read(args.catalog)
    invalid = read(ws / 'artifacts/FIX24_20261009_1420/invalid-runs.json')
    invalid = invalid['training_directories'] + invalid['invalid_evaluation_runs']
    def load(path):
        p = Path(path)
        if invalid_path(p, invalid):
            raise ValueError(f'INVALID FIX24: {p}')
        if str(p) in cache:
            return cache[str(p)]
        c, res, rr = read(p / 'config.json'), read(p / 'results.json'), read(p / 'per_prompt.jsonl', True)
        assert c['code_commit'] == FROZEN and c['engine_version'] == '0.31.0'
        assert c['K'] == 4 and c['method'] == 'eagle3' and res['gpu_type'] == 'NVIDIA A40'
        assert c['batch_size'] == 8 and c['max_new_tokens'] == 512 and c['temperature'] == 0 and c['seed'] == 0 and c['use_prompt_token_ids']
        pp = read(c['prompts'], True)
        assert hashes[str(Path(c['prompts']))] == c['prompt_sha256']
        render = {r['prompt_id']: r['rendered_token_ids'] for r in pp}
        vals = {r['prompt_id']: raw_values(r, 4)[:3] for r in rr}
        assert len(vals) == len(rr) == c['n'] == res['n_total'] and vals.keys() == render.keys()
        assert abs(np.nanmean([v[1] for v in vals.values()]) - res['macro_acceptance_length']) < 1e-8
        cache[str(p)] = c, render, vals
        return cache[str(p)]
    # Final production checkpoints, independently verified against each training config.
    prod = {}
    for r in cat['records']:
        label, t, seed, w = r['label'], r['target'], r.get('seed'), r['workload']
        budget = None
        if t == 0 and r['campaign'] == 'D48' and label in ['generic4k-fc', 'generic4k-full']: budget = 4000
        if t == 0 and r['campaign'] == 'seeds16k' and label in ['generic16k-fc', 'generic16k-full']: budget = 16000
        if t == 1 and label.startswith('E1-production-t1-4k-'): budget = 4000
        if t == 1 and label.startswith('E7-production-t1-16k-'): budget = 16000
        if budget is None or w not in ['speed128', 'math64']: continue
        arm = label.split('-')[-1]; p = Path(r['run_dir']); c = read(p / 'config.json')
        train = Path(c['drafter']).parent; tc = read(train / 'config.json')
        if int(r['step']) != tc['steps']: continue
        assert tc['n'] == budget and tc['seed'] == seed
        key = t, budget, arm, seed, w
        if key in prod and prod[key]['run'] != str(p): raise ValueError(f'duplicate production final {key}')
        prod[key] = dict(run=str(p), train=str(train), config=tc)
    stage = ws / 'artifacts/FIX24_20261009_1420'
    seed_stage = ws / 'artifacts/FIX24_official_seeds_20261009'
    official, missing = {}, []
    for t in [0, 1]:
        for budget in [4000, 16000]:
            for arm in ['fc', 'full']:
                for seed in ([0, 1, 2] if t == 0 and budget == 16000 else [0]):
                    label = f'FIX24-official-t{t}-{budget//1000}k-{arm}'
                    train = stage / label if seed == 0 else seed_stage / f'{label}-seed{seed}'
                    if not (train / 'config.json').exists():
                        missing.append(str(train / 'config.json')); continue
                    tc = read(train / 'config.json'); step = tc['steps']
                    for w in ['speed128', 'math64']:
                        name = f'{label}-s{step}-{w}' if seed == 0 else f'{label}-seed{seed}-s{step}-{w}'
                        p = (stage / 'repair-eval/runs' if seed == 0 else seed_stage / 'eval/runs') / name
                        if not (p / 'results.json').exists() or not (train / 'results.json').exists():
                            missing.append(str(p)); continue
                        assert tc['n'] == budget and tc['seed'] == seed
                        official[t, budget, arm, seed, w] = dict(run=str(p), train=str(train), config=tc)
    d50 = ws / 'artifacts/P3_D50_20261009_0200'
    bases = {(r['target'], r['workload']): Path(r['run_dir']) for r in cat['records']
             if r['label'] == 'reused' and r['campaign'] == 'control'}
    oracles = {r['workload']: Path(r['run_dir']) for r in cat['records']
               if r['label'] == 'oracle' and r['campaign'] == 'control'}
    records, focal = [], []
    for t in [0, 1]:
        for budget in [4000, 16000]:
            for arm in ['fc', 'full']:
                for w in ['speed128', 'math64']:
                    seeds = [seed for seed in [0, 1, 2] if (t, budget, arm, seed, w) in official and (t, budget, arm, seed, w) in prod]
                    if not seeds: continue
                    paths = [d50 / f'E1-reuse/runs/D50-E1-official-t{t}-{w}', bases[t, w]]
                    bc = [load(p) for p in paths]; keys = sorted(bc[0][2])
                    check_pair(bc[0][0], bc[1][0], bc[0][1], bc[1][1])
                    arrays, provenance = [], []
                    for mapping in [official, prod]:
                        vals = []
                        for seed in seeds:
                            key = t, budget, arm, seed, w
                            check_training(official[key]['config'], prod[key]['config'])
                            r = mapping[key]; c, render, v = load(r['run'])
                            check_pair(c, bc[0][0], render, bc[0][1])
                            assert c['drafter'] == str(Path(r['train']) / f"export-{r['config']['steps']}")
                            vals.append([v[k] for k in keys]); provenance.append({k: r[k] for k in ['run', 'train']})
                        arrays.append(np.array(vals))
                    oracle_values = None
                    if t == 0:
                        oc, ore, ov = load(oracles[w]); check_pair(oc, bc[0][0], ore, bc[0][1])
                        oracle_values = [ov[k] for k in keys]
                    ss = delta_comparison(arrays[0], [bc[0][2][k] for k in keys], arrays[1], [bc[1][2][k] for k in keys], oracle=oracle_values)
                    r = dict(target=t, budget=budget, arm=arm, workload=w, seeds=seeds,
                             steps=[official[t,budget,arm,seed,w]['config']['steps'] for seed in seeds],
                             sources=provenance, reuse_paths=list(map(str, paths)), **ss)
                    records.append(r)
                    if t == 0 and budget == 16000:
                        for family in ['official', 'production']:
                            focal.append(dict(family=family, arm=arm, workload=w, seeds=seeds, statistics=ss[family]))
    selection = choose_primary(records)
    fmt = lambda v: '--' if v is None else f"{v['mean']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]"
    header = ['Target', 'Examples', 'Arm', 'Panel', 'n / seeds', 'Official repair Delta tau', 'Production repair Delta tau', 'Difference [95% CI]']
    rows = [['R1' if r['target'] == 0 else 'Nemotron', r['budget'], r['arm'], r['workload'], f"{r['n_paired']} / {len(r['seeds'])}", fmt(r['official']['delta']['tau']), fmt(r['production']['delta']['tau']), fmt(r['difference']['tau'])] for r in records]
    write_table(out, 'repair-delta-comparison', header, rows)
    header2 = ['Role', 'Drafter', 'Arm', 'Panel', 'n / seeds', 'p1 [95% CI]', 'tau [95% CI]', 'Own-reuse Delta tau [95% CI]', 'Oracle-gap recovery [95% CI]']
    main_rows, robustness = [], []
    for r in focal:
        s = r['statistics']; role = 'candidate: selection pending' if selection['primary'] is None else 'main' if r['family'] == selection['primary'] else 'robustness'
        row = [role, r['family'], r['arm'], r['workload'], f"{s['n_paired']} / {s['seeds']}", fmt(s['metrics']['p1']), fmt(s['metrics']['tau']), fmt(s['delta']['tau']), fmt(s['recovery'])]
        (robustness if role == 'robustness' else main_rows).append(row)
    # Reuse rows belong to the chosen family too; controls remain measured, never relabelled.
    for family in ['official', 'production']:
        for w in ['speed128', 'math64']:
            p = d50 / f'E1-reuse/runs/D50-E1-official-t0-{w}' if family == 'official' else bases[0,w]
            _, _, v = load(p); keys = sorted(v); values = np.array([v[k] for k in keys])
            o = np.array([load(oracles[w])[2][k] for k in keys]); ss = paired_summary(values[None], values, o)
            role = 'candidate: selection pending' if selection['primary'] is None else 'main' if family == selection['primary'] else 'robustness'
            row = [role, family, 'reuse', w, f"{ss['n_paired']} / 1", fmt(ss['metrics']['p1']), fmt(ss['metrics']['tau']), fmt(ss['delta']['tau']), fmt(ss['recovery'])]
            (robustness if role == 'robustness' else main_rows).append(row)
    write_table(out, 'r1-main', header2, main_rows)
    write_table(out, 'r1-robustness', header2, robustness)
    result = dict(status='pilot',generated=datetime.datetime.now().astimezone().isoformat(),selection=selection,records=records,focal=focal,pending=missing,input_sha256=hashes)
    (out/'results.json').open('x').write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    notice = ['# D-51: same-drafter repair gains — pilot', '',
              'Selection: ' + json.dumps(selection), '',
              'Delta tau = repaired minus the SAME drafter\'s reuse. Difference = official delta minus production delta. Positive favours official. All four conditions share exact rendered IDs, frozen6da/vLLM0.31/A40/K4. Training data SHA, tokens, steps, batch plan, seed and objective/hyperparameters match within each seed. Seed counts may differ between incomplete rows; no main choice until BOTH variants and BOTH panels have all three R1 16k seeds.', '',
              '10000 paired seed/query bootstrap draws; identical seed indices and query IDs across four conditions, shared zero-step exclusion. Only three training seeds; intervals are conditional on this selected panel and not adjusted for choosing the better drafter. SPEED-128 is the selection endpoint; MATH-64 is reported as secondary. Mixed fc/full directions retain both without inventing an aggregate selection score.', '',
              '[Repair-delta contrasts](repair-delta-comparison.md) · [Main candidates/selected](r1-main.md) · [Other drafter robustness](r1-robustness.md). Each has a LaTeX counterpart. These main/robustness tables replace the focal 16k repair and reuse rows; shared oracle, independent, n-gram and other controls remain in the existing consolidated table. Official MATH-500 and official timing are unmeasured unless explicitly supplied; production results are retained as labelled controls, not substituted. Existing consolidated baseline/ablation/timing tables retain their explicitly named initialization; switching the focal drafter does not relabel production controls or timing as official.', '',
              'The earlier corrected-official versus production ABSOLUTE-score contrasts answer a different question and do not implement D-51. This report supersedes them for drafter choice. Old FIX24-invalid repairs remain excluded. Oracle-gap fractions must use each drafter\'s own reuse denominator; a shared oracle alone does not make recovery rankings mathematically identical to delta rankings. Selection here uses Delta tau only.']
    (out/'report.md').open('x').write('\n'.join(notice)+'\n')
    print(json.dumps(dict(selection=selection,comparisons=len(records),pending=len(missing))))

if __name__ == '__main__':
    main()
