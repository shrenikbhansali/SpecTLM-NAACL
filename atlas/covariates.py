"""Offline paired covariates on identical derivative-generated token sequences.

Generation belongs to the pinned B2 engine. Offline feature passes use an
explicitly recorded Transformers backend; they are never atlas AL measurements.
"""
import argparse
from collections import defaultdict
from datetime import date
import importlib.metadata
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
import torch
from atlas.run_cell import ensure_unpaused,sha256,local_files,write_new


def tap_layers(config,n):
    layers=config.get('eagle_aux_hidden_state_layer_ids')
    if not layers:layers=config.get('eagle_config',{}).get('layer_ids')
    if not layers:layers=[2,n//2,n-3]
    if not layers or any(type(i) is not int or not 0<i<n for i in layers):raise ValueError('invalid EAGLE3 taps')
    return sorted(set(layers))


def draft_mask(t2d,d2t):
    if t2d.dtype!=torch.bool or t2d.ndim!=1 or d2t.ndim!=1:raise ValueError('invalid draft vocabulary mapping')
    expected=torch.arange(len(d2t))+d2t.cpu()
    if not torch.equal(t2d.cpu().nonzero().flatten(),expected):raise ValueError('inconsistent t2d/d2t mapping')
    return t2d.cpu()


def compare_tokens(base_logits,child_logits,base_features,child_features,vocab_mask):
    if base_logits.shape!=child_logits.shape or base_logits.ndim!=2 or not len(base_logits):raise ValueError('logit shape mismatch')
    if base_logits.shape[-1]!=len(vocab_mask) or vocab_mask.dtype!=torch.bool:raise ValueError('vocab mismatch')
    b,c=base_logits.float().log_softmax(-1),child_logits.float().log_softmax(-1)
    if not torch.isfinite(b).all() or not torch.isfinite(c).all():raise ValueError('nonfinite logits')
    kl=(c.exp()*(c-b)).sum(-1)
    if kl.min() < -1e-5:raise ValueError('negative KL beyond floating-point error')
    mask=vocab_mask.to(b.device);outside_b=b.exp()[:,~mask].sum(-1);outside_c=c.exp()[:,~mask].sum(-1)
    features={}
    if base_features.keys()!=child_features.keys():raise ValueError('tap mismatch')
    for layer in base_features:
        x,y=base_features[layer].double(),child_features[layer].double()
        if x.shape!=y.shape or len(x)!=len(b):raise ValueError('feature shape mismatch')
        nx=x.norm(dim=-1);ny=y.norm(dim=-1)
        if (nx==0).any() or (ny==0).any():raise ValueError('undefined zero-norm feature displacement')
        relative=(y-x).norm(dim=-1)/nx
        # Algebraically 1-cosine; exactly zero for identical normalized vectors.
        cosine=.5*((y/ny[:,None]-x/nx[:,None])**2).sum(-1)
        features[str(layer)]=dict(relative_l2=float(relative.mean()),cosine_displacement=float(cosine.mean()))
    return dict(n_tokens=len(b),kl_child_base=float(kl.clamp_min(0).mean()),features=features,
        outside_vocab_mass_base=float(outside_b.mean()),outside_vocab_mass_child=float(outside_c.mean()),
        outside_vocab_mass_shift=float((outside_c-outside_b).mean()))


def square_norm(t):
    return sum(float(chunk.float().square().sum(dtype=torch.float64)) for chunk in t.detach().reshape(-1).split(4*1024**2))


def norm_groups(base,delta_squares):
    totals=defaultdict(lambda:[0.,0.,0])
    if set(delta_squares)-set(base):raise ValueError('update module absent from base')
    for name,weight in base.items():
        if not name.endswith('.weight'):continue
        kind=name.split('.')[-2];den=square_norm(weight);num=delta_squares.get(name,0.)
        totals[kind][0]+=num;totals[kind][1]+=den;totals[kind][2]+=1
    if any(d==0 for _,d,_ in totals.values()):raise ValueError('zero-norm weight group')
    return {k:dict(relative_norm=math.sqrt(n/d),delta_squared_norm=n,base_squared_norm=d,modules=count) for k,(n,d,count) in sorted(totals.items())}


def relative_weight_groups(base,updates):return norm_groups(base,{k:square_norm(v) for k,v in updates.items()})


def template_identity(base,child=None,adapter=False):
    def template(path):
        root=Path(path)
        if (root/'chat_template.jinja').is_file():return (root/'chat_template.jinja').read_text()
        if (root/'tokenizer_config.json').is_file():return json.loads((root/'tokenizer_config.json').read_text()).get('chat_template')
        return None
    b=template(base);c=template(child) if child else b
    inherited=bool(adapter and child and not any((Path(child)/name).exists() for name in ('chat_template.jinja','tokenizer_config.json')))
    if inherited:c=b
    digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    return dict(changed=b!=c,base_sha256=digest(b),child_sha256=digest(c),child_inherits_base=inherited)


def adapter_norms(base,adapter):
    from atlas.adapter_similarity import load_factors,inner
    factors=load_factors(adapter);squares={}
    for module,triple in factors.items():
        name=module.removeprefix('base_model.model.')+'.weight'
        squares[name]=inner({module:triple},{module:triple})
    return norm_groups(base,squares)


def load_sequences(path,smoke):
    path=Path(path);cfg=json.loads((path.parent/'config.json').read_text())
    if cfg['sequences_sha256']!=sha256(path) or cfg['generation_engine']!='0.31.0':raise ValueError('sequence provenance mismatch')
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    if cfg.get('n')!=len(rows):raise ValueError('sequence count differs from manifest')
    if (smoke and not 1<=len(rows)<=10) or (not smoke and len(rows)!=64):raise ValueError('need64 own queries, or explicit <=10 acceptance smoke')
    if not smoke and (cfg['acceptance_only'] or cfg['workload']!='own'):raise ValueError('production requires real own-workload sequences')
    if len({r['prompt_id'] for r in rows})!=len(rows):raise ValueError('duplicate prompt IDs')
    for r in rows:
        if not 1<=r['response_start']<len(r['input_ids']):raise ValueError('missing response')
        if len(r['input_ids'])>4096:raise ValueError('sequence too long; no silent truncation')
        if any(type(i) is not int or i<0 for i in r['input_ids']):raise ValueError('invalid input token')
        expected=[0]*r['response_start']+[1]*(len(r['input_ids'])-r['response_start'])
        if r.get('assistant_mask')!=expected:raise ValueError('assistant mask differs from saved generation boundary')
    return rows,cfg


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',required=True);p.add_argument('--base-revision',required=True)
    p.add_argument('--child');p.add_argument('--adapter');p.add_argument('--derivative-id',required=True);p.add_argument('--derivative-revision',required=True)
    p.add_argument('--drafter',required=True);p.add_argument('--drafter-revision',required=True);p.add_argument('--sequences',required=True)
    p.add_argument('--output',required=True);p.add_argument('--acceptance-smoke',action='store_true');p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    import re
    for rev in (a.base_revision,a.drafter_revision):
        if not re.fullmatch('[a-f0-9]{40}',rev):raise ValueError('pin base/drafter')
    if Path(a.base).name!=a.base_revision or Path(a.drafter).name!=a.drafter_revision:raise ValueError('snapshot revision mismatch')
    if bool(a.child)+bool(a.adapter)>1:raise ValueError('choose child snapshot or adapter')
    if a.child and (not re.fullmatch('[a-f0-9]{40}',a.derivative_revision) or Path(a.child).name!=a.derivative_revision):raise ValueError('pin child snapshot')
    if not a.child and not a.adapter and a.derivative_id!='base':raise ValueError('missing derivative weights')
    rows,source=load_sequences(a.sequences,a.acceptance_smoke)
    if a.derivative_id!='base' and (source['derivative_id']!=a.derivative_id or source['derivative_revision']!=a.derivative_revision):raise ValueError('sequences from another derivative')
    bc=json.loads((Path(a.base)/'config.json').read_text());dc=json.loads((Path(a.drafter)/'config.json').read_text());taps=tap_layers(dc,bc['num_hidden_layers'])
    template=template_identity(a.base,a.child or a.adapter,adapter=bool(a.adapter))
    config=vars(a)|dict(source=source,template=template,tap_indices=taps,tap_semantics='HF hidden_states indices (embedding-inclusive), pre-final-norm',
        tap_default_source='vLLM0.31.0 SupportsEagle3.get_eagle3_default_aux_hidden_state_layers: (2,n//2,n-3)',
        offline_backend={k:importlib.metadata.version(k) for k in ('torch','transformers','peft')},
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_sha256=sha256(__file__),
        dtype='bfloat16',attention='eager',seed=0,K=source.get('K'),prompt_sha256=source['prompt_sha256'],
        averaging='token-weighted over generated-token prediction positions; features average per-token displacement',
        absolute_mass_caveat='outside-vocabulary absolute mass need not vanish for base/self; its shift must vanish')
    if a.dry_run:print(json.dumps(config,indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd())
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit code before real acceptance')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
    torch.manual_seed(0)
    from transformers import AutoModelForCausalLM
    from safetensors import safe_open
    from peft import PeftModel
    with safe_open(str(Path(a.drafter)/'model.safetensors'),framework='pt',device='cpu') as mapping:
        mask=draft_mask(mapping.get_tensor('t2d'),mapping.get_tensor('d2t'))
    config['drafter_config_sha256']=sha256(Path(a.drafter)/'config.json')
    config['gpu_type']=torch.cuda.get_device_name(0)
    if 'A40' not in config['gpu_type']:raise ValueError('covariates require assigned A40')
    if a.adapter:config['adapter_files_sha256']=local_files(a.adapter)
    write_new(out/'config.json',config)
    try:
        base=AutoModelForCausalLM.from_pretrained(a.base,torch_dtype=torch.bfloat16,local_files_only=True,trust_remote_code=False,attn_implementation='eager').to('cuda').eval()
        weights=dict(base.named_parameters());child=None
        if a.adapter:
            weight_result=adapter_norms(weights,a.adapter)
            child=PeftModel.from_pretrained(base,a.adapter,autocast_adapter_dtype=False).eval()
        elif a.child:
            from atlas.quantized_targets import load_child
            child,backend=load_child(a.child)
            write_new(out/'child_backend.json',backend)
            cw=dict(child.named_parameters())
            if set(weights)-set(cw):raise ValueError('full-weight parameter names differ')
            # Native CT retains scale metadata parameters; only actual base model
            # weights enter the norm. Packed layouts must be expanded by the loader.
            if any(cw[k].shape!=v.shape for k,v in weights.items()):raise ValueError('unexpanded quantized weight shape')
            weight_result=norm_groups(weights,{k:square_norm(cw[k].float()-v.float()) for k,v in weights.items()})
        else:weight_result=norm_groups(weights,{})
        write_new(out/'weight_covariates.json',weight_result)
        def capture(model,row):
            ids=torch.tensor([row['input_ids']],device='cuda');start=row['response_start']-1;end=ids.shape[1]-1
            core=model.get_base_model() if hasattr(model,'get_base_model') else model
            with torch.inference_mode():
                output=core.model(input_ids=ids,output_hidden_states=True,use_cache=False)
                # Compute logits only at prediction positions for generated tokens.
                logits=core.lm_head(output.last_hidden_state[:,start:end])[0].float().cpu()
                feats={i:output.hidden_states[i][0,start:end].float().cpu() for i in taps}
            return logits,feats
        records=[]
        with (out/'per_prompt.jsonl').open('x') as f:
            for row in rows:
                ensure_unpaused()
                if a.adapter:
                    with child.disable_adapter():bl,bh=capture(child,row)
                else:bl,bh=capture(base,row)
                cl,ch=capture(child or base,row)
                report=dict(prompt_id=row['prompt_id'],source_run_id=source['source_run_id'],**compare_tokens(bl,cl,bh,ch,mask))
                f.write(json.dumps(report)+'\n');f.flush();records.append(report)
        n=sum(r['n_tokens'] for r in records)
        mean=lambda key:sum(r[key]*r['n_tokens'] for r in records)/n
        result={k:mean(k) for k in ('kl_child_base','outside_vocab_mass_base','outside_vocab_mass_child','outside_vocab_mass_shift')}
        result['features']={str(i):{key:sum(r['features'][str(i)][key]*r['n_tokens'] for r in records)/n for key in ('relative_l2','cosine_displacement')} for i in taps}
        result.update(n_prompts=len(records),n_tokens=n,weight_covariates=weight_result,lm_head_relative_change=weight_result['lm_head']['relative_norm'],
            chat_template_changed=template['changed'],wall_s=time.perf_counter()-started,
            uncertainty='per-prompt records retained; this single bounded diagnostic does not estimate run-to-run noise')
        write_new(out/'results.json',result)
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=str(date.today()),status='pilot',
            what_why='Paired offline covariates on derivative-generated sequences',new='Pinned tap/vocabulary mappings; explicit source generation provenance',
            artifacts=str(out.resolve()),config_results=dict(config=config,results=result),caveats='Offline Transformers feature pass, not an atlas acceptance cell. Operator review required.'))
    except Exception as e:
        write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise

if __name__=='__main__':main()
