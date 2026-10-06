"""D-27 method data planning. Pure planning functions never launch GPU jobs."""
import argparse
import hashlib
import json
import random
from itertools import accumulate, combinations
from pathlib import Path

from atlas.workloads import prompt_hash

ARMS = ('FS', 'MVD', 'PO-D', 'PO-T')


def sample_candidates(registry, *, seed, max_lora_rank):
    """Freeze both rounds before any PPL scores; uniform width and source subset.

    Rank-infeasible subsets are rejected before sampling, not after seeing PPL.
    Widths remain equiprobable among the feasible widths, recorded in the plan.
    """
    if max_lora_rank not in (8, 16, 32, 64, 128, 256, 320, 512):
        raise ValueError('unsupported engine rank cap')
    names = sorted(k for k, v in registry.items() if v['kind'] == 'bank')
    options = {n: [list(c) for c in combinations(names, n)
                   if sum(registry[k]['rank'] for k in c) <= max_lora_rank] for n in (2, 3)}
    if not all(options.values()):
        raise ValueError('rank cap must allow both two- and three-source mixtures')
    rng = random.Random(seed); result = []
    for i in range(60):
        sources = rng.choice(options[rng.choice([2, 3])])
        gamma = [rng.gammavariate(.5, 1.) for _ in sources]
        result.append(dict(id=f'm1-r{i // 30 + 1}-{i % 30:02}', round=i // 30 + 1,
                           source_ids=sources, weights=[g / sum(gamma) for g in gamma],
                           scale=rng.uniform(0, 1.5), seed=seed, alpha=.5,
                           max_lora_rank=max_lora_rank))
    return result


def admission_selection(candidate_ids, results):
    if len(candidate_ids) != 60 or len(set(candidate_ids)) != 60:
        raise ValueError('exactly two preregistered rounds required')
    if set(results) not in (set(candidate_ids[:30]), set(candidate_ids)):
        raise ValueError('complete round required; missing results are not rejections')
    if any(type(v) is not bool for v in results.values()):
        raise ValueError('explicit admission booleans required')
    selected = [k for k in candidate_ids if results.get(k)][:30]
    next_round = 2 if len(selected) < 30 and len(results) == 30 else None
    return dict(admitted=selected, ready=20 <= len(selected) <= 30 and next_round is None,
                next_round=next_round, n_passed=sum(results.values()))


def checked_queries(rows, label, forbidden=()):
    ids = set(); hashes = set(); blocked = set(forbidden)
    for r in rows:
        h = prompt_hash(r['prompt'])
        if r.get('split') != 'training' or r.get('acceptance_only') or r['prompt_id'].startswith('speed-'):
            raise ValueError(f'{label}: production training queries required')
        if r['prompt_id'] in ids or h in hashes:
            raise ValueError(f'{label}: duplicate prompt')
        if h in blocked:
            raise ValueError(f'{label}: forbidden/validation overlap')
        ids.add(r['prompt_id']); hashes.add(h)
    if not rows:
        raise ValueError(f'{label}: empty queries')
    return hashes


def allocate_queries(registry, general, magpie, validation, *, seed, forbidden):
    """Parent and child general pools are disjoint; general queries are shared
    across child targets. Each target has no repeated query. Validation is an
    explicit operator input, globally disjoint from all training queries.
    """
    bank = sorted(k for k, v in registry.items() if v['kind'] == 'bank')
    mixtures = sorted(k for k, v in registry.items() if v['kind'] == 'mixture')
    if len(bank) != 33 or not 20 <= len(mixtures) <= 30:
        raise ValueError('D-27 requires 33 bank and 20–30 admitted mixtures')
    targets = sorted(bank + mixtures)
    if set(magpie) != set(targets):
        raise ValueError('Magpie inputs must cover all admitted targets')
    blocked = {prompt_hash(q['prompt']) for q in forbidden}
    val_hashes = checked_queries(validation, 'validation', blocked)
    checked_queries(general, 'general', blocked | val_hashes)
    for k in targets:
        checked_queries(magpie[k], 'Magpie '+k, blocked | val_hashes)
        if len(magpie[k]) < 500:
            raise ValueError('Magpie requires 500 queries per target')
        if any(q.get('derivative_id', k) != k for q in magpie[k]):
            raise ValueError('wrong Magpie origin')
    # Nearest D-27 integer, dropping at most one final query to permit exact halves.
    rounded = round(33000 / len(targets)); per_fs = rounded - rounded % 2
    child_counts = {'FS': per_fs * len(targets), 'MVD': 33000}
    # Keep only complete six-child/two-parent blocks at final tail matching.
    parent_counts = {a: n // 3 for a, n in child_counts.items()}
    parent_n = max(parent_counts.values())
    pool = list(general); random.Random(seed).shuffle(pool)
    if len(pool) < parent_n + 500:
        raise ValueError('general pool too small for disjoint parent/child partition')
    parent = pool[:parent_n]; child_pool = pool[parent_n:]
    child_hashes = {prompt_hash(q['prompt']) for q in child_pool}
    parent_hashes = {prompt_hash(q['prompt']) for q in parent}
    # A Magpie query overlapping the chosen parent set would violate parent isolation.
    if any(prompt_hash(q['prompt']) in parent_hashes for rows in magpie.values() for q in rows):
        raise ValueError('Magpie/parent general overlap')
    assigned = {}; arm_ids = {'FS': {}, 'MVD': {}}
    for target in targets:
        rng = random.Random(f'{seed}/{target}')
        own_hashes = {prompt_hash(m['prompt']) for m in magpie[target]}
        available = [q for q in child_pool if prompt_hash(q['prompt']) not in own_hashes]
        need = 500 if target in bank else per_fs // 2
        if len(available) < need:
            raise ValueError('not enough disjoint child general queries')
        selected = rng.sample(available, need)
        own = list(magpie[target]); rng.shuffle(own)
        rows = []
        for m, g in zip(own[:need], selected, strict=True):
            rows.extend([m | dict(kind='magpie', role='child'), g | dict(kind='general', role='child')])
        checked_queries(rows, target, blocked | val_hashes | parent_hashes)
        arm_ids['FS'][target] = [q['prompt_id'] for q in rows[:per_fs]]
        if target in bank:
            arm_ids['MVD'][target] = [q['prompt_id'] for q in rows]
        assigned[target] = rows + [q | dict(kind='general', role='validation') for q in validation]
    assigned['base'] = [q | dict(kind='general', role='parent') for q in parent] + [
        q | dict(kind='general', role='validation') for q in validation]
    return dict(schema='followspec_D27_queries_v1', queries=assigned, arm_ids=arm_ids,
                parent_ids={a: [q['prompt_id'] for q in parent[:n]] for a, n in parent_counts.items()},
                validation=validation, seed=seed,
                counts=dict(fs_per_target=per_fs, fs_rounded_per_target=rounded,
                            per_target_tail_drop=rounded-per_fs, child=child_counts, parent=parent_counts),
                policy='Seeded parent/child general partition; general shared across targets; no within-target duplicates',
                child_general_pool_hashes=sorted(child_hashes), parent_general_hashes=sorted(parent_hashes))


def match_tails(lengths, *, batch_check, allowed_ends=None):
    """Largest shared prefix budget whose native steps match for every seed.

    No token edits, reordering, replacement or resampling. `allowed_ends` can
    restrict boundaries to preserve 50:50 child composition and 25% parent.
    """
    if set(lengths) != set(ARMS) or not lengths['FS'] == lengths['PO-D'] == lengths['PO-T']:
        raise ValueError('paired lengths must match')
    if any(not values or any(type(n) is not int or n <= 0 or n > 8192 for n in values) for values in lengths.values()):
        raise ValueError('invalid lengths or native truncation required')
    sums = {}
    for arm in ('FS', 'MVD'):
        ends = set(allowed_ends[arm]) if allowed_ends else set(range(1, len(lengths[arm])+1))
        sums[arm] = {total: i for i, total in enumerate(accumulate(lengths[arm]), 1) if i in ends}
    attempts = []
    for budget in sorted(sums['FS'].keys() & sums['MVD'].keys(), reverse=True):
        kept = {a: sums['MVD' if a == 'MVD' else 'FS'][budget] for a in ARMS}
        try:
            report = batch_check({a: lengths[a][:kept[a]] for a in ARMS})
        except ValueError as exc:
            attempts.append(dict(token_budget=budget, kept=kept, error=str(exc))); continue
        return dict(token_budget=budget, kept=kept, audit=report, attempts=attempts,
                    dropped_indices={a: list(range(kept[a], len(lengths[a]))) for a in ARMS})
    raise ValueError('no nonempty matched prefix with equal native steps; no resampling permitted; '+json.dumps(attempts))


def launcher_job(spec, name, task, prompts, command, *, python=None):
    py = python or spec['python']
    args = ['--task', task, '--base', 'llama', '--drafter', 'method-data', '--k', '0',
            '--seed', str(spec['seed']), '--no-resolve', '--tag', name,
            '--prompts', str(prompts), '--engine-lock', str(Path(spec['code_repo'])/'atlas/env/requirements.lock'),
            '--python', py, '--code-repo', spec['code_repo'], '--config-name', 'launcher.json',
            '--target', spec['base_id'], '--target-rev', spec['base_revision']]
    for value in ('HF_HUB_OFFLINE=1', 'OMP_NUM_THREADS=4', 'MKL_NUM_THREADS=4', 'VLLM_CACHE_ROOT={out_dir}/vllm_cache'):
        args += ['--env', value]
    return dict(name=name, args=args+['--', py, '-u', *map(str, command)])


def validate_spec(spec):
    import re
    required = ('code_repo','python','base_id','base_revision','base_snapshot','drafter_snapshot',
                'drafter_revision','pool_manifest','staging_manifest','downloads','artifacts_root',
                'general_prompts','forbidden_files','seed','max_lora_rank')
    if any(k not in spec for k in required):
        raise ValueError('missing production specification fields')
    for key in ('base_revision', 'drafter_revision'):
        if not re.fullmatch('[a-f0-9]{40}', spec[key]):raise ValueError('model revisions must be SHA pins')
    for key, rev in [('base_snapshot','base_revision'),('drafter_snapshot','drafter_revision')]:
        if Path(spec[key]).name != spec[rev]:raise ValueError('snapshot revision mismatch')
    if spec['base_id'] != 'meta-llama/Llama-3.1-8B-Instruct':raise ValueError('D-27 is Llama only')
    if type(spec['seed']) is not int or not spec['forbidden_files']:raise ValueError('seed and evaluation exclusions required')
    if spec['max_lora_rank'] not in (128,256,320,512):raise ValueError('rank cap must support frozen bank mixtures')
    return spec


def main():
    from followspec.production_pipeline import main as run
    run()


if __name__ == '__main__':main()
