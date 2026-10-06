"""Exact PEFT LoRA mixtures with explicit engine rank-cap validation.

B=[s*w_i*c_i*B_i], A=[A_i] vertically, scaling=1. Missing modules
contribute zeros. Source tensors are never modified. No model is loaded.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import torch
from safetensors.torch import load_file,save_file

# Pinned engine source: vllm v0.31.0 vllm/config/lora.py, MaxLoRARanks.
SUPPORTED_CAPS=(1,8,16,32,64,128,256,320,512)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def patterned(pattern,module,default):
    matches=[v for k,v in pattern.items() if module==k or module.endswith('.'+k)]
    if len(matches)>1:raise ValueError('ambiguous rank/alpha pattern')
    return matches[0] if matches else default


def read(path):
    path=Path(path);cfg=json.loads((path/'adapter_config.json').read_text())
    if cfg.get('peft_type')!='LORA' or cfg.get('use_dora') or cfg.get('modules_to_save') or cfg.get('bias','none')!='none' or cfg.get('fan_in_fan_out',False):
        raise ValueError('only standard linear, bias-free LoRA adapters supported')
    if not isinstance(cfg.get('target_modules'),list):raise ValueError('target_modules must be explicit module list')
    tensors=load_file(str(path/'adapter_model.safetensors'),device='cpu');pairs={};consumed=set()
    for key,A in tensors.items():
        if not key.endswith('.lora_A.weight'):continue
        module=key[:-len('.lora_A.weight')];bk=module+'.lora_B.weight'
        B=tensors[bk];r=patterned(cfg.get('rank_pattern',{}),module,cfg['r'])
        alpha=patterned(cfg.get('alpha_pattern',{}),module,cfg['lora_alpha'])
        if A.ndim!=2 or B.ndim!=2 or A.shape[0]!=r or B.shape[1]!=r or r<=0:
            raise ValueError('invalid factor shape or rank')
        if not torch.isfinite(A).all() or not torch.isfinite(B).all() or not math.isfinite(alpha):
            raise ValueError('nonfinite factors or scaling')
        if A.dtype not in (torch.float32,torch.float16,torch.bfloat16) or B.dtype!=A.dtype:
            raise ValueError('unsupported factor dtype')
        c=alpha/(math.sqrt(r) if cfg.get('use_rslora',False) else r)
        pairs[module]=(A,B,c);consumed|={key,bk}
    if not pairs or consumed!=tensors.keys():raise ValueError('missing or unsupported adapter tensors')
    return cfg,pairs


def mix(paths,weights,scale,output,*,max_lora_rank,dtype=None):
    if len(paths)!=len(weights) or not paths:raise ValueError('one weight per adapter required')
    if not all(math.isfinite(w) and w>=0 for w in weights) or not math.isclose(sum(weights),1,abs_tol=1e-6):
        raise ValueError('weights must be finite, nonnegative and sum to one')
    if not math.isfinite(scale) or scale<0:raise ValueError('scale must be finite and nonnegative')
    if max_lora_rank not in SUPPORTED_CAPS:raise ValueError(f'unsupported engine cap; choose {SUPPORTED_CAPS}')
    sources=[read(p) for p in paths]
    bases={cfg['base_model_name_or_path'] for cfg,_ in sources}
    if len(bases)!=1:raise ValueError('source adapters must use the same base')
    ranks=[max(A.shape[0] for A,_,_ in pairs.values()) for _,pairs in sources]
    rank=sum(ranks)
    if rank>max_lora_rank:raise ValueError(f'mixture rank {rank} exceeds configured vLLM cap {max_lora_rank}')
    if dtype is None:
        dtype=sources[0][1][next(iter(sources[0][1]))][0].dtype
        for _,pairs in sources:
            for A,_,_ in pairs.values():dtype=torch.promote_types(dtype,A.dtype)
    if dtype not in (torch.float32,torch.bfloat16,torch.float16):raise ValueError('unsupported output dtype')
    modules=sorted(set().union(*(pairs.keys() for _,pairs in sources)));tensors={}
    for module in modules:
        examples=[pairs[module] for _,pairs in sources if module in pairs]
        ni,no=examples[0][0].shape[1],examples[0][1].shape[0]
        if any(A.shape[1]!=ni or B.shape[0]!=no for A,B,_ in examples):raise ValueError('incompatible module dimensions')
        Aout=torch.zeros(rank,ni,dtype=dtype);Bout=torch.zeros(no,rank,dtype=dtype);offset=0
        for weight,source_rank,(_,pairs) in zip(weights,ranks,sources):
            if module in pairs:
                A,B,c=pairs[module];r=A.shape[0]
                Aout[offset:offset+r]=A.to(dtype)
                Bout[:,offset:offset+r]=(B.double()*(scale*weight*c)).to(dtype)
            offset+=source_rank
        if not torch.isfinite(Aout).all() or not torch.isfinite(Bout).all():raise ValueError('mixture overflow')
        tensors[module+'.lora_A.weight']=Aout;tensors[module+'.lora_B.weight']=Bout
    cfg=dict(base_model_name_or_path=next(iter(bases)),peft_type='LORA',task_type='CAUSAL_LM',
        inference_mode=True,r=rank,lora_alpha=rank,use_rslora=False,use_dora=False,bias='none',
        lora_dropout=0.,fan_in_fan_out=False,target_modules=sorted({m.rsplit('.',1)[-1] for m in modules}))
    provenance=dict(formula='s * sum_i w_i c_i B_i A_i',scale=scale,weights=weights,source_ranks=ranks,
        output_rank=rank,configured_engine_cap=max_lora_rank,engine_version='0.31.0',dtype=str(dtype),
        sources=[dict(path=str(Path(p).resolve()),config_sha256=sha(Path(p)/'adapter_config.json'),
                      weights_sha256=sha(Path(p)/'adapter_model.safetensors')) for p in paths])
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    save_file(tensors,str(out/'adapter_model.safetensors'))
    (out/'adapter_config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    (out/'mixture_manifest.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return provenance


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adapters',nargs='+',required=True);p.add_argument('--weights',nargs='+',type=float,required=True)
    p.add_argument('--scale',type=float,required=True);p.add_argument('--max-lora-rank',type=int,required=True)
    p.add_argument('--dtype',choices=['float32','float16','bfloat16']);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(mix(a.adapters,a.weights,a.scale,a.output,max_lora_rank=a.max_lora_rank,
        dtype=getattr(torch,a.dtype) if a.dtype else None),indent=2))

if __name__=='__main__':main()
