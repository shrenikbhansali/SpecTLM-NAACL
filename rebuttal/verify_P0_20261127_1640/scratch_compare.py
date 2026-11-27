"""Post-export paired comparison against the reproduced seed-0 warm repair."""
import json
from pathlib import Path
from rebuttal.reduce_e45 import acceptance_contrast, rows, sha

ROOT = Path('/home/heck2/sbhansali8/ReFit')
out = []
for panel in ['speed128', 'math128']:
    names = [f'E3b_t0_scratch20ep_s0_gcc13_all_step92175_{panel}',
             'BASELINE_t0_full_' + ('speed128' if panel == 'speed128' else 'math500') + '_s0_cachefix1']
    cells = [ROOT/'rebuttal/runs'/name/'cell' for name in names]
    configs = [json.loads((cell/'config.json').read_text()) for cell in cells]
    for key in ['target', 'target_revision', 'engine_version', 'K', 'temperature',
                'max_new_tokens', 'batch_size', 'use_prompt_token_ids']:
        assert configs[0][key] == configs[1][key], key
    prompts = [rows(Path(c['prompts'])) for c in configs]
    assert len(prompts[0]) == 128
    for a, b in zip(prompts[0], prompts[1][:128], strict=True):
        assert a['prompt_id'] == b['prompt_id']
        assert a['rendered_token_ids'] == b['rendered_token_ids']
    raw = [rows(cell/'per_prompt.jsonl') for cell in cells]
    ids = {r['prompt_id'] for r in raw[0]}
    paired = [r for r in raw[1] if r['prompt_id'] in ids]
    assert len(ids) == len(paired) == 128
    out.append({'panel': panel, 'reference': names[0], 'candidate': names[1],
                'raw_sha256': [sha(cell/'per_prompt.jsonl') for cell in cells],
                'scope': 'one training seed; warm16k vs scratch64k five-epoch continuous schedule; not data/compute matched',
                **acceptance_contrast({0: raw[0]}, {0: paired}, 4, 4)})
destination = ROOT/'rebuttal/verify_P0_20261127_1640/scratch-vs-warm.json'
with destination.open('x') as f:
    json.dump(out, f, indent=2)
    f.write('\n')
for r in out:
    print(r['panel'], r['reference_tau'], r['candidate_tau'], r['delta_tau'], r['delta_tau_ci95'])
