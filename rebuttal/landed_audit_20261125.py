"""CPU-only scratch reduction and timing output audit, from immutable raw files."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from rebuttal.reduce_e45 import FROZEN, acceptance_contrast, reference_records, rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = a.workspace
    refs = [r for r in reference_records(root) if r['experiment'] == 'E4' and r['target'] == 0]
    scratch = []
    for run in sorted((root / 'rebuttal/runs').glob('E3b_*_step*')):
        raw = run / 'cell/per_prompt.jsonl'
        if not raw.exists():
            continue
        meta = json.loads((run / 'metrics.json').read_text())
        assert meta['exit_code'] == 0
        cfg = json.loads((run / 'cell/config.json').read_text())
        assert cfg['code_commit'] == FROZEN and cfg['engine_version'] == '0.31.0'
        assert cfg['K'] == 4 and cfg['max_new_tokens'] == 512 and cfg['batch_size'] == 8
        rr = rows(raw)
        assert len(rr) == 128
        benchmark = 'speed128' if run.name.endswith('speed128') else 'math128'
        for ref in refs:
            if ref['benchmark'] != benchmark:
                continue
            assert ref['prompt_sha256'] == cfg['prompt_sha256']
            refrows = {r['prompt_id']: r for r in rows(root / 'rebuttal/runs' / ref['run'] / 'cell/per_prompt.jsonl')}
            ordered = [refrows[i] for i in ref['subset_prompt_ids']]
            scratch.append(dict(run=run.name, reference=ref['variant'], benchmark=benchmark,
                                raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                                **acceptance_contrast({0: ordered}, {0: rr}, 4, 4)))
    timing = []
    for run in sorted((root / 'rebuttal/runs').glob('E5_*_timing_distilled_*')):
        raw = run / 'cell/timing.json'
        if not raw.exists():
            continue
        other = run.with_name(run.name.replace('_distilled_', '_none_')) / 'cell/timing.json'
        left, right = json.loads(raw.read_text()), json.loads(other.read_text())
        pass_stats = []
        for ap, bp in zip(left['passes'], right['passes']):
            am = {r['prompt_id']: r['completion_token_ids'] for r in ap['per_prompt']}
            bm = {r['prompt_id']: r['completion_token_ids'] for r in bp['per_prompt']}
            assert am.keys() == bm.keys() and len(am) == 128
            differences = []
            for q, av in am.items():
                bv = bm[q]
                if av != bv:
                    first = next((i for i, (x, y) in enumerate(zip(av, bv)) if x != y), min(len(av), len(bv)))
                    differences.append(first)
            pass_stats.append(dict(n=len(am), mismatched=len(differences),
                                   first_token_mismatches=sum(v == 0 for v in differences),
                                   median_first_difference=float(np.median(differences)) if differences else None,
                                   candidate_tokens=sum(map(len, am.values())), reference_tokens=sum(map(len, bm.values()))))
        timing.append(dict(run=run.name, comparison='distilled versus none', passes=pass_stats))
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output / 'results.json').write_text(json.dumps(dict(scratch=scratch, timing_output_audit=timing), indent=2) + '\n')


if __name__ == '__main__':
    main()
