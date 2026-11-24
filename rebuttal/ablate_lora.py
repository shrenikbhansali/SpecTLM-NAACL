"""Immutable eval-only ablations: restore exact initial weights, never subtract rounded deltas."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from safetensors import safe_open
from safetensors.torch import save_file


def weight_map(path):
    index=path/'model.safetensors.index.json'
    if index.exists():return json.loads(index.read_text())['weight_map']
    single=path/'model.safetensors'
    with safe_open(single,framework='pt') as f:return {k:single.name for k in f.keys()}


def ablate(trained,base,output,mode,adapted_keys):
    if mode not in {'no_fc','fc_only'}:raise ValueError('unknown ablation')
    trained,base,output=map(Path,[trained,base,output])
    if output.exists():raise FileExistsError(output)
    source=weight_map(trained);initial=weight_map(base)
    keys=sorted(k for k in adapted_keys if (k=='fc.weight') == (mode=='no_fc'))
    if not keys or not set(keys)<=set(source)&set(initial):raise ValueError('missing adapted/base weights')
    replacements={};proof={}
    for key in keys:
        with safe_open(base/initial[key],framework='pt') as f:old=f.get_tensor(key)
        with safe_open(trained/source[key],framework='pt') as f:new=f.get_tensor(key)
        if old.shape!=new.shape:raise ValueError('shape mismatch '+key)
        replacements[key]=old.to(new.dtype).contiguous()
        proof[key]=dict(base_dtype=str(old.dtype),export_dtype=str(new.dtype),shape=list(old.shape))
    output.mkdir(parents=True,exist_ok=False)
    # Reuse immutable source tensors without making duplicate embedding copies.
    for shard in set(source.values()):os.link(trained/shard,output/shard)
    for name in ['config.json','config.py']:
        if (trained/name).exists():shutil.copyfile(trained/name,output/name)
    name='ablation-restored.safetensors';save_file(replacements,output/name,metadata={'format':'pt'})
    mapping=source|{k:name for k in keys}
    total=0
    for key,shard in mapping.items():
        with safe_open(output/shard,framework='pt') as f:
            x=f.get_tensor(key);total+=x.numel()*x.element_size()
    (output/'model.safetensors.index.json').write_text(json.dumps({'metadata':{'total_size':total},'weight_map':mapping},indent=2)+'\n')
    (output/'ablation_provenance.json').write_text(json.dumps(dict(mode=mode,trained=str(trained.resolve()),base=str(base.resolve()),restored=proof,
        adapted_keys=sorted(adapted_keys),operation='Exact initial weights cast to trained dtype; remaining tensors hardlinked unchanged'),indent=2)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--trained',type=Path,required=True);p.add_argument('--base',type=Path,required=True)
    p.add_argument('--parameters',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['no_fc','fc_only'],required=True)
    a=p.parse_args();proof=json.loads(a.parameters.read_text())
    if proof['variant']!='whole_lora':raise ValueError('Expected whole-drafter LoRA')
    names=proof['trainable_names']
    if not all('.lora_' in n for n in names):raise ValueError('Unexpected trained parameter')
    adapted={n.rsplit('.',1)[0]+'.weight' for n in names}
    ablate(a.trained,a.base,a.output,a.mode,adapted)


if __name__=='__main__':main()
