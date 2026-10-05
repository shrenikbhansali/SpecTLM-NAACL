"""Matched arm presets and config-difference contract (MASTER §§5.4–5.5)."""
import argparse
import json
from pathlib import Path

EXPECTED={
 'FS':dict(targets='bank_and_mixtures',responses='child',features='child',labels='child',delta_lambda=.1,mixtures=True),
 'MVD':dict(targets='bank',responses='child',features='child',labels='child',delta_lambda=0.,mixtures=False),
 'PO-D':dict(targets='parent',responses='parent',features='parent',labels='parent',delta_lambda=0.,mixtures=True),
 'PO-T':dict(targets='parent',responses='fs_child_text',features='parent',labels='parent',delta_lambda=0.,mixtures=True),
}
ALLOWED={'arm',*next(iter(EXPECTED.values())).keys()}


def load_presets():
    return {name:json.loads((Path(__file__).with_name('configs')/(name+'.json')).read_text()) for name in EXPECTED}


def check_matched(arms):
    if set(arms)!=set(EXPECTED):raise ValueError('exactly FS, MVD, PO-D, PO-T required')
    keys=set(arms['FS'])
    if any(set(v)!=keys for v in arms.values()):raise ValueError('config schema mismatch')
    for name,cfg in arms.items():
        if cfg['arm']!=name:raise ValueError('arm identity mismatch')
        for key,value in EXPECTED[name].items():
            if cfg[key]!=value:raise ValueError(f'{name}: wrong intended field {key}')
    differences={}
    for key in sorted(keys):
        values={name:cfg[key] for name,cfg in arms.items()}
        if len({json.dumps(v,sort_keys=True) for v in values.values()})>1:
            if key not in ALLOWED:raise ValueError(f'unintended arm difference: {key}')
            differences[key]=values
    return differences


def main():
    p=argparse.ArgumentParser();p.add_argument('--configs',nargs=4)
    a=p.parse_args();arms=load_presets() if not a.configs else {c['arm']:c for c in [json.loads(Path(p).read_text()) for p in a.configs]}
    print(json.dumps(check_matched(arms),indent=2))

if __name__=='__main__':main()
