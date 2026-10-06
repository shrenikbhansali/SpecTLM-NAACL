"""CPU-only audit of exact native batching; never changes data or presets."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ARMS = {'FS', 'MVD', 'PO-D', 'PO-T'}


def inspect_splits(arms):
    seen = {}
    for manifest in arms.values():
        for row in manifest['samples']:
            split = row['split']
            if split not in {'train', 'val'}:
                raise ValueError('invalid split')
            if seen.setdefault(row['prompt_sha256'], split) != split:
                raise ValueError('cross-arm training/validation prompt overlap')
    return {split: sum(s == split for s in seen.values()) for split in ['train', 'val']}


def inspect_batches(lengths_by_arm, *, factory, batch_max_length, seeds, epochs, replicas):
    if set(lengths_by_arm) != ARMS:
        raise ValueError('all four arms required')
    if not seeds or len(set(seeds)) != len(seeds) or epochs < 1 or replicas < 1:
        raise ValueError('nonempty distinct seeds and positive epochs/replicas required')
    for lengths in lengths_by_arm.values():
        if not lengths or any(type(n) is not int or not 0 < n <= batch_max_length for n in lengths):
            raise ValueError('nonempty positive lengths required; native truncation forbidden')
    budgets = {sum(v) for v in lengths_by_arm.values()}
    if len(budgets) != 1:
        raise ValueError('actual token budgets differ')
    records = []; step_counts = {}
    for seed in seeds:
        for arm, lengths in lengths_by_arm.items():
            steps = 0
            for epoch in range(epochs):
                seen = []; rank_steps = []
                for rank in range(replicas):
                    sampler = factory(batch_max_length=batch_max_length, lengths=lengths,
                                      num_replicas=replicas, rank=rank, seed=seed)
                    sampler.set_epoch(epoch)
                    batches = [[int(i) for i in batch] for batch in sampler]
                    rank_steps.append(len(batches))
                    for step, batch in enumerate(batches):
                        if not batch or any(i < 0 or i >= len(lengths) for i in batch):
                            raise ValueError('invalid or empty native batch')
                        tokens = sum(lengths[i] for i in batch)
                        if tokens > batch_max_length:
                            raise ValueError('native batch exceeds capacity')
                        seen.extend(batch)
                        records.append(dict(arm=arm, seed=seed, epoch=epoch, rank=rank, step=step,
                                            sample_indices=batch, shifted_tokens=tokens))
                if sorted(seen) != list(range(len(lengths))):
                    raise ValueError(f'{arm} seed{seed} epoch{epoch}: sampler dropped or duplicated samples')
                if len(set(rank_steps)) != 1:
                    raise ValueError('native rank optimizer steps differ')
                steps += rank_steps[0]
            step_counts[f'{arm}:{seed}'] = steps
    if len(set(step_counts.values())) != 1:
        raise ValueError('native optimizer steps differ across arms/seeds: '+json.dumps(step_counts))
    return dict(token_budget=next(iter(budgets)), optimizer_steps=next(iter(step_counts.values())),
                step_counts=step_counts, batches=records)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifests', nargs=4, required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--replicas', type=int, default=1)
    p.add_argument('--acceptance-smoke', action='store_true')
    a = p.parse_args()
    from atlas.run_cell import sha256, write_new
    from followspec.configs import load_presets, check_matched
    from followspec.token_data import OnlineResponseDataset, validate_arm_set
    from followspec.train_eagle3 import BACKEND
    from speculators.version import git_commit
    from speculators.train.distributed_batch_sampler import MultipackDistributedBatchSamplerV2
    if git_commit != BACKEND:
        raise ValueError('wrong native sampler source revision')
    manifests = [json.loads(Path(path).read_text()) for path in a.manifests]
    if len({m['arm'] for m in manifests}) != 4:
        raise ValueError('four distinct arm manifests required')
    arms = {m['arm']: m for m in manifests}
    cfgs = load_presets(); check_matched(cfgs); cfg = cfgs['FS']
    matched = validate_arm_set(arms); split_counts = inspect_splits(arms)
    if a.acceptance_smoke and any(len(m['samples']) > 64 or not m['acceptance_only'] for m in manifests):
        raise ValueError('bounded acceptance requires <=64 acceptance-only samples per arm')
    lengths = {}
    for arm, m in arms.items():
        ds = OnlineResponseDataset(m, split='train', bank=None, shift=lambda r:r,
                                   allow_acceptance=a.acceptance_smoke)
        lengths[arm] = ds.approx_lengths
        if sum(ds.approx_lengths) != m['token_budget']:
            raise ValueError('manifest budget differs from actual response views')
    out = Path(a.output); out.mkdir(parents=True, exist_ok=False)
    config = vars(a) | dict(code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                           manifest_sha256={path:sha256(path) for path in a.manifests},
                           backend_revision=BACKEND, seeds=cfg['seeds'], epochs=cfg['epochs'],
                           batch_max_length=cfg['total_seq_len'], models_loaded=False)
    write_new(out/'config.json',config)
    try:
        report = inspect_batches(lengths, factory=MultipackDistributedBatchSamplerV2,
                                 batch_max_length=cfg['total_seq_len'], seeds=cfg['seeds'],
                                 epochs=cfg['epochs'], replicas=a.replicas)
        with (out/'per_batch.jsonl').open('x') as f:
            for row in report.pop('batches'): f.write(json.dumps(row)+'\n')
        result = report | dict(passed=True, matched=matched, split_prompt_counts=split_counts,
                               production_ready=False, per_batch_sha256=sha256(out/'per_batch.jsonl'),
                               caveat='Batch audit only; recipe quotas, mixture admission, masks, features and capacity remain required')
        write_new(out/'results.json',result)
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,
            landed=__import__('datetime').date.today().isoformat(),status='pilot',
            what_why='Verify matched actual tokens, full sample coverage and native optimizer steps before training',
            new='CPU-only pinned sampler audit across every arm and seed',artifacts=str(out.resolve()),
            config_results=dict(config=config,results=result),caveats=result['caveat']))
        print(json.dumps(result))
    except Exception as e:
        write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__ == '__main__': main()
