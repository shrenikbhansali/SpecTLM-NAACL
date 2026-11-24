"""Render independently reduced E4/E5 evidence; never infer unfinished results."""
import argparse
import json
import re
from pathlib import Path


def replace_section(text, experiment, replacement):
    pattern = r'(?ms)^## ' + re.escape(experiment) + r' — .*?(?=^## |\Z)'
    result, count = re.subn(pattern, lambda _: replacement.rstrip() + '\n\n', text)
    if count != 1:
        raise ValueError('expected one existing experiment section')
    return result


def interval(value, ci, percent=False):
    scale, digits = (100, 1) if percent else (1, 2)
    return f'{value * scale:.{digits}f} [{ci[0] * scale:.{digits}f}, {ci[1] * scale:.{digits}f}]'


def section(data, experiment, source):
    title = 'EDA baseline' if experiment == 'E4' else 'Distilled independent drafter'
    lines = [f'## {experiment} — {title}',
             'Status: partial; automatic raw-counter reduction, pending operator completion check.',
             'All acceptance cells use frozen6da2e42/vLLM0.31.0/A40, greedy, batch8, cap512. '
             'MATH is first128. Intervals are paired10,000 query/seed bootstrap95%CIs. '
             'Smoke runs are excluded. Reference rows use the identical rendered prefix of current-campaign gate cells; hashes verified.', '']
    records = [r for r in data['acceptance'] if r['experiment'] == experiment]
    new = [r for r in records if not r['variant'].startswith('reference_')]
    for target in [0, 1]:
        subset = [r for r in records if r['target'] == target]
        if not subset:
            continue
        lines += [('R1-Distill-Llama' if target == 0 else 'Nemotron') + ':', '',
                  '| Variant / seed / K | Panel | n | tau [95% CI] | p1 % [95% CI] | Train GPUh |',
                  '|---|---|---:|---|---|---:|']
        for r in subset:
            cost = f"{r['train_gpu_h']:.1f}" if 'train_gpu_h' in r else '—'
            lines.append(f"| {r['variant']} / s{r['seed']} / K{r['K']} | {r['benchmark']} | {r['n']} | "
                         f"{interval(r['tau'], r['tau_ci95'])} | {interval(r['p1'], r['p1_ci95'], True)} | {cost} |")
        lines.append('')
    pairs = [r for r in data['paired'] if r['experiment'] == experiment
             and not (r['reference'].startswith('reference_') and r['candidate'].startswith('reference_'))]
    if pairs:
        lines += ['Paired differences are candidate minus reference; no sign filtering.', '',
                  '| Target / panel | Reference | Candidate | n / seeds | Delta tau [95% CI] | Delta p1 points [95% CI] |',
                  '|---|---|---|---|---|---|']
        for r in pairs:
            lines.append(f"| {r['target']} / {r['benchmark']} | {r['reference']} | {r['candidate']} | "
                         f"{r['n']} / {len(r['seeds'])} | {interval(r['delta_tau'],r['delta_tau_ci95'])} | "
                         f"{interval(r['delta_p1'],r['delta_p1_ci95'],True)} |")
    if experiment == 'E4':
        lines += ['', 'Port: released additive singleton shared/private experts; shared FFN, fc, attention, norms and head frozen. '
                  'Private widths4096/14336; PCA128 and90th-percentile Mahalanobis are predeclared port choices. '
                  'Selected8k and random8k full-repair controls remain separate. Frozen tensor checks and FIX24 embedding proof gate production EDA evaluation.']
        if data['latency']:
            lines += ['', '| Standalone drafter | n | Median ms |', '|---|---:|---:|']
            for r in data['latency']:
                lines.append(f"| {r['drafter']} | {r['n']} | {r['median_ms']:.3f} |")
            lines.append('Standalone PyTorch first-draft forward:50warmup,1000measured CUDA-event steps, batch1, one-token context, no verifier. Not end-to-end speedup.')
    else:
        lines += ['', 'Recipe: exact full-vocabulary forward KL,15744train/256heldout repair prompts per target, '
                  'lr1e-5/2e-5 x1/3epochs. Select checkpoint by heldout tau atK4; select timing K by warm tokens/s on32heldout repair queries, separately b1/b8. '
                  'Full K2–5 acceptance sweep retained. Teacher hidden-state/head factorization is exact, not top-k; lexical IDs match and export special-token aliases preserve training IDs.']
        if data['timing']:
            lines += ['', '| Target / panel / batch | Arm | Reference | Warm token speedup [95% CI] | Panel speedup [95% CI] | Processes / warm passes |',
                      '|---|---|---|---|---|---|']
            for r in data['timing']:
                v = r['warm']
                lines.append(f"| {r['target']} / {r['benchmark']} / b{r['batch']} | {r['arm']} | {r['reference']} | "
                             f"{interval(v['token_speedup'],v['token_ci95'])} | {interval(v['panel_speedup'],v['panel_ci95'])} | 3 / 3 |")
            lines.append('Timing intervals resample process and paired prompt batch; cold/startup and output mismatches are retained in the source JSON.')
    lines += ['', f"Result status: {len(new)} completed non-reference cells in this snapshot; no unfinished outcome inferred.",
              f"GPU-hours: {data['gpu_hours_completed_including_failures'].get(experiment,0):.1f} completed, including failures; active runtime additional.",
              'Sources: ' + str(source), 'Failed runs retained: ' + json.dumps(data['failed']), '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--results', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--publish', type=Path)
    a = p.parse_args()
    data = json.loads(a.results.read_text())
    sections = {exp: section(data, exp, a.results) for exp in ['E4', 'E5']}
    with a.output.open('x') as f:
        f.write('\n'.join(sections.values()))
    if a.publish:
        text = a.publish.read_text()
        for exp, replacement in sections.items():
            text = replace_section(text, exp, replacement)
        a.publish.write_text(text)


if __name__ == '__main__':
    main()
