"""Offline D-32 pairing for raw census counters; generation defaults are untouched.

The caller supplies the pinned harness's metric function. Keep prompt-macro and
pooled-step first-position acceptance distinct, and remove both sides of a pair
when either side has no speculative steps.
"""


def _indexed(rows, k, metrics_fn):
    indexed = {}
    for row in rows:
        ident = row['prompt_id']
        if ident in indexed:
            raise ValueError(f'duplicate prompt ID: {ident}')
        metric = metrics_fn(row['per_step_accepted'], row['per_step_drafted'], k)
        indexed[ident] = dict(
            p1=metric['per_position_conditional_acceptance'][0],
            tau=metric['acceptance_length'],
            length=len(row['completion_token_ids']),
            steps=metric['num_drafts'],
            first_accepted=metric['per_position_accepted'][0],
            first_opportunities=metric['per_position_opportunities'][0],
        )
    return indexed


def _aggregate(rows):
    return dict(
        macro_p1=sum(r['p1'] for r in rows) / len(rows),
        pooled_p1=sum(r['first_accepted'] for r in rows)
        / sum(r['first_opportunities'] for r in rows),
        tau=sum(r['tau'] for r in rows) / len(rows),
        length=sum(r['length'] for r in rows) / len(rows),
    )


def paired_acceptance(base, child, k, metrics_fn):
    """Return paired records and explicitly named acceptance estimands."""
    a, c = _indexed(base, k, metrics_fn), _indexed(child, k, metrics_fn)
    if not a or a.keys() != c.keys():
        raise ValueError('nonempty, identical prompt-ID sets are required')
    ids = sorted(i for i in a if a[i]['steps'] and c[i]['steps'])
    excluded = sorted(set(a) - set(ids))
    paired = [dict(prompt_id=i, A00=a[i], A10=c[i]) for i in ids]
    parent = _aggregate([a[i] for i in ids]) if ids else None
    target = _aggregate([c[i] for i in ids]) if ids else None
    retention = ({key: target[key] / value if value else None
                  for key, value in parent.items()} if ids else None)
    return dict(n_total=len(a), n_paired=len(ids), ids=ids,
                excluded_ids=excluded, paired=paired,
                A00=parent, A10=target, retention=retention)
