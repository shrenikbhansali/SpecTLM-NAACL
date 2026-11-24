"""Seal completed data only when its first five rows match a prior human/agent review.

This waits for generation completion; it never substitutes an automated quality
check for reading the decoded examples. The reviewed snapshot must already exist.
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def validate_review(rows, reviewed):
    if len(reviewed) != 5 or len(rows) < 5 or rows[:5] != reviewed:
        raise ValueError('completed data differs from the five inspected rows')


def main():
    from atlas.workloads import file_hash, prompt_hash
    from followspec.family_repair import validate_rows, supervision_source
    from followspec.independent_kd import read
    from rebuttal.dispatch_exports import write_immutable
    p = argparse.ArgumentParser()
    for name in ['source', 'reviewed', 'decoded-review', 'target-row', 'forbidden']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--expected-n', type=int, required=True)
    p.add_argument('--wait', action='store_true')
    a = p.parse_args()
    reviewed = json.loads(a.reviewed.read_text())
    decoded = json.loads(a.decoded_review.read_text())
    if len(decoded) != 5 or not all(r['mask_correct'] for r in decoded):
        raise ValueError('missing decoded-string/mask review')
    if [r['sample_id'] for r in decoded] != [r['sample_id'] for r in reviewed]:
        raise ValueError('review identities differ')
    complete = a.source.parent / 'results.json'
    while not complete.exists():
        if not a.wait:
            raise ValueError('generation not complete')
        metrics = a.source.parent.parent / 'metrics.json'
        if metrics.exists() and json.loads(metrics.read_text()).get('exit_code') != 0:
            raise RuntimeError('generation failed; inspected partial data not sealed')
        time.sleep(20)
    rows = read(a.source)
    validate_review(rows, reviewed)
    if len(rows) != a.expected_n:
        raise ValueError('incorrect final sample count')
    blocked = {prompt_hash(r.get('raw_prompt', r.get('prompt'))) for r in read(a.forbidden)}
    validate_rows(rows, blocked, 8192)
    supervision_source(json.loads(a.target_row.read_text()), rows, None)
    report = dict(passed=True, n=len(rows), data_sha256=file_hash(a.source),
                  reviewer='codex-1', reviewed_rows_sha256=file_hash(a.reviewed),
                  decoded_review_sha256=file_hash(a.decoded_review),
                  forbidden_sha256=file_hash(a.forbidden),
                  timestamp=datetime.now(ZoneInfo('America/New_York')).isoformat(),
                  proof='first five rows identical to previously inspected decoded strings and masks; all final rows pass provenance and mask checks')
    dest = a.source.parent / 'manual-audit.json'
    if dest.exists():
        existing = json.loads(dest.read_text())
        if existing.get('data_sha256') != report['data_sha256'] or not existing.get('passed'):
            raise ValueError('existing audit disagrees')
    else:
        write_immutable(dest, report)
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
