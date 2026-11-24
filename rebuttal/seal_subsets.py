"""Use already inspected examples only after proving they belong to each new subset."""
import argparse
import json
import time
from pathlib import Path


def reviewed_members(rows, reviewed):
    known = {r['sample_id']: r for r in reviewed}
    if len(known) != len(reviewed):
        raise ValueError('duplicate reviewed identities')
    matches = []
    for row in rows:
        if row['sample_id'] in known:
            if row != known[row['sample_id']]:
                raise ValueError('reviewed member changed')
            matches.append(row)
    if len(matches) < 5:
        raise ValueError('fewer than five inspected members: additional manual review required')
    return matches[:5]


def main():
    from atlas.workloads import file_hash, prompt_hash
    from followspec.family_repair import validate_rows, supervision_source
    from followspec.independent_kd import read
    from rebuttal.dispatch_exports import write_immutable
    from followspec.rev2_data_analysis import describe
    p = argparse.ArgumentParser()
    for name in ['selection', 'review', 'target-row', 'forbidden']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--wait', action='store_true')
    a = p.parse_args()
    approval = json.loads((a.review / 'inspection.json').read_text())
    if not approval['inspected'] or any(file_hash(a.review / k) != v for k, v in approval['sha256'].items()):
        raise ValueError('missing or changed inspection evidence')
    reviewed = json.loads((a.review / 'rows.json').read_text())
    decoded = {r['sample_id']: r for r in json.loads((a.review / 'decoded.json').read_text())}
    if set(decoded) != {r['sample_id'] for r in reviewed} or not all(r['mask_correct'] for r in decoded.values()):
        raise ValueError('decoded/mask evidence incomplete')
    while not (a.selection / 'results.json').exists():
        if not a.wait:
            raise ValueError('selection incomplete')
        time.sleep(20)
    forbidden = {prompt_hash(r.get('raw_prompt', r.get('prompt'))) for r in read(a.forbidden)}
    target = json.loads(a.target_row.read_text())
    for subset in ['selected', 'random']:
        source = a.selection / subset / 'per_prompt.jsonl'
        rows = read(source)
        if len(rows) != 8000:
            raise ValueError('incorrect subset size')
        five = reviewed_members(rows, reviewed)
        validate_rows(rows, forbidden, 8192)
        supervision_source(target, rows, None)
        proof = dict(passed=True, data_sha256=file_hash(source), n=len(rows), reviewer='codex-1',
                     inspection_sha256=file_hash(a.review / 'inspection.json'),
                     five_sample_ids=[r['sample_id'] for r in five],
                     rule='first five subset members present in the already inspected fixed seed904 random24 sample; exact row identity proved; no approval if fewer than five',
                     scope='tokenization, masks, provenance and leakage; not a correctness certification of target answers',
                     quality_filter_applied=False)
        write_immutable(a.selection / subset / 'five_decoded_masks.json', [decoded[r['sample_id']] for r in five])
        write_immutable(a.selection / subset / 'quality-report.json', describe(rows))
        write_immutable(a.selection / subset / 'manual-audit.json', proof)
        print(json.dumps(proof), flush=True)


if __name__ == '__main__':
    main()
