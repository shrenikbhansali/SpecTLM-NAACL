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


def load_presets(*,family='llama',algorithm='eagle3'):
    if family not in {'llama','qwen3'}:raise ValueError('unsupported EAGLE family')
    if algorithm not in {'eagle3','dflash'} or (algorithm=='dflash' and family!='llama'):raise ValueError('unsupported training algorithm/family')
    arms={name:json.loads((Path(__file__).with_name('configs')/(name+'.json')).read_text()) for name in EXPECTED}
    if family=='qwen3':
        for cfg in arms.values():cfg['initialization']='RedHatAI/Qwen3-8B-speculator.eagle3'
    if algorithm=='dflash':
        for cfg in arms.values():
            cfg.update(algorithm='dflash',initialization='z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat',
                       block_size=10,max_anchors=512,gamma=4.,per_position_loss_weight='fixed-exp-decay')
            del cfg['ttt_steps'];del cfg['ttt_step_loss_decay']
    return arms


def validate_eagle_family(family,base_config,drafter_config):
    expected={'llama':'LlamaForCausalLM','qwen3':'Qwen3ForCausalLM'}
    if family not in expected or base_config.get('model_type')!=family:raise ValueError('target family differs')
    spec=drafter_config.get('speculators_config',{})
    if spec.get('algorithm')!='eagle3' or expected[family] not in spec.get('verifier',{}).get('architectures',[]):
        raise ValueError('drafter verifier family differs')


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
    p.add_argument('--family',choices=['llama','qwen3'],default='llama')
    p.add_argument('--algorithm',choices=['eagle3','dflash'],default='eagle3')
    a=p.parse_args();arms=load_presets(family=a.family,algorithm=a.algorithm) if not a.configs else {c['arm']:c for c in [json.loads(Path(p).read_text()) for p in a.configs]}
    print(json.dumps(check_matched(arms),indent=2))

if __name__=='__main__':main()
