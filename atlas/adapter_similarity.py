"""Exact flattened BA cosine via small factor contractions, without dense BA."""
import argparse
import csv
import json
import math
from pathlib import Path


def load_factors(path):
    from safetensors.torch import load_file
    cfg=json.loads((Path(path)/'adapter_config.json').read_text())
    if cfg.get('use_dora') or cfg.get('modules_to_save') or cfg.get('bias','none')!='none':
        raise ValueError('Similarity currently requires pure LoRA updates')
    tensors=load_file(str(Path(path)/'adapter_model.safetensors'),device='cpu')
    pairs={}
    def pattern_value(patterns,module,default):
        matches=[value for key,value in patterns.items() if module==key or module.endswith('.'+key)]
        if len(matches)>1: raise ValueError('Ambiguous adapter pattern')
        return matches[0] if matches else default
    for key,A in tensors.items():
        if not key.endswith('.lora_A.weight'): continue
        module=key[:-len('.lora_A.weight')]
        B=tensors[module+'.lora_B.weight']
        rank=pattern_value(cfg.get('rank_pattern',{}),module,cfg['r'])
        alpha=pattern_value(cfg.get('alpha_pattern',{}),module,cfg['lora_alpha'])
        if A.shape[0]!=rank or B.shape[1]!=rank: raise ValueError('rank/config mismatch')
        scale=alpha/(math.sqrt(rank) if cfg.get('use_rslora',False) else rank)
        pairs[module]=(B.double(),A.double(),scale)
    if not pairs: raise ValueError('No standard LoRA factors')
    return pairs


def inner(a,b):
    result=0.
    for key in a.keys() & b.keys():
        B,A,s=a[key];D,C,t=b[key]
        if B.shape[0]!=D.shape[0] or A.shape[1]!=C.shape[1]: raise ValueError('incompatible modules')
        result += float(((B.double().T@D.double())*(A.double()@C.double().T)).sum())*s*t
    return result


def cosine_updates(a,b):
    aa,bb=inner(a,a),inner(b,b)
    if aa<=0 or bb<=0:return None
    return max(-1.,min(1.,inner(a,b)/math.sqrt(aa*bb)))


def main():
    from atlas.curate_pool import read_csv,verify_downloads
    p=argparse.ArgumentParser();p.add_argument('--pool',required=True);p.add_argument('--downloads',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();rows=[r for r in read_csv(args.pool) if r['type']=='lora_adapter']
    verify_downloads(rows,args.downloads)
    entries={e['model_id']:e for e in map(json.loads,Path(args.downloads).read_text().splitlines()) if e.get('status')=='complete'}
    with Path(args.output).open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['model_a','model_b','revision_a','revision_b','cosine','threshold','flag'])
        writer.writeheader()
        for i,a in enumerate(rows):
            factors_a=load_factors(entries[a['model_id']]['path'])
            for b in rows[i+1:]:
                cosine=cosine_updates(factors_a,load_factors(entries[b['model_id']]['path']))
                threshold=0.95 if a['pool']==b['pool']=='bank' else 0.9 if {a['pool'],b['pool']}=={'bank','test'} else None
                flag='undefined_zero_update' if cosine is None else 'above_threshold' if threshold and cosine>threshold else ''
                writer.writerow(dict(model_a=a['model_id'],model_b=b['model_id'],revision_a=a['revision'],revision_b=b['revision'],cosine=cosine,threshold=threshold,flag=flag));f.flush()

if __name__=='__main__':main()
