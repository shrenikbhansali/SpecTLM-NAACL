"""B3 real-model acceptance driver. Dry runs never load a model or create outputs.

Run logits and vllm phases in separate processes/environments. Numeric tolerances
are required inputs because MASTER does not prescribe numerical bf16 limits.
"""
import argparse
from contextlib import contextmanager
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import torch
from followspec.mixture import mix,read,sha

ROOT=Path(__file__).resolve().parents[1]


def ensure_unpaused(start=ROOT):
    for parent in (Path(start).resolve(),*Path(start).resolve().parents):
        for relative in ('EXPERIMENTS_PAUSED.json','tlm-spec-maintenance/EXPERIMENTS_PAUSED.json'):
            marker=parent/relative
            if marker.exists():raise RuntimeError(f'Experiments paused: {marker}')


def cases(seed):
    result=[dict(name=f'onehot_{i}',kind='onehot',source=i,weights=[int(i==j) for j in range(3)],scale=1.) for i in range(3)]
    result.append(dict(name='zero',kind='zero',weights=[1/3]*3,scale=0.))
    g=torch.Generator().manual_seed(seed)
    for i,s in enumerate((.5,1.,1.5)):
        w=torch.rand(3,generator=g,dtype=torch.float64);w/=w.sum()
        result.append(dict(name=f'random_{i}',kind='random',weights=w.tolist(),scale=s))
    return result


def compare_logits(actual,reference,*,atol,rtol):
    if actual.shape!=reference.shape or not torch.isfinite(actual).all() or not torch.isfinite(reference).all():
        raise ValueError('invalid comparison logits')
    diff=(actual.double()-reference.double()).abs()
    denom=reference.double().abs().clamp_min(torch.finfo(torch.float64).eps)
    return dict(max_absolute_difference=diff.max().item(),max_relative_difference=(diff/denom).max().item(),
        passed=bool(torch.all(diff<=atol+rtol*reference.double().abs())),atol=atol,rtol=rtol)


@contextmanager
def directly_merged(model,adapters,weights,scale):
    """Build dense updates independently from original factors, restore exact bits."""
    sources=[read(path)[1] for path in adapters]
    modules=sorted(set().union(*(s.keys() for s in sources)))
    saved={}
    try:
        with torch.no_grad():
            for name in modules:
                if not name.startswith('base_model.model.'):raise ValueError('unexpected PEFT module prefix')
                layer=model.get_submodule(name.removeprefix('base_model.model.'))
                saved[name]=(layer,layer.weight.detach().cpu().clone())
                delta=torch.zeros_like(layer.weight,dtype=torch.float32)
                for factors,w in zip(sources,weights):
                    if name in factors:
                        A,B,c=factors[name]
                        delta.add_(B.to(delta.device,dtype=torch.float32)@A.to(delta.device,dtype=torch.float32),alpha=scale*w*c)
                layer.weight.copy_((layer.weight.float()+delta).to(layer.weight.dtype))
        yield model
    finally:
        with torch.no_grad():
            for layer,original in saved.values():layer.weight.copy_(original.to(layer.weight.device))


def write(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def logits_phase(a,rows,out):
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from peft import PeftModel
    ensure_unpaused();torch.manual_seed(a.seed)
    tokenizer=AutoTokenizer.from_pretrained(a.base,revision=a.revision,trust_remote_code=False)
    tokens=[tokenizer(r['prompt'],return_tensors='pt') for r in rows]
    if any(x['input_ids'].shape[1]>a.max_model_len for x in tokens):raise ValueError('prompt exceeds max length; no silent truncation')
    model=AutoModelForCausalLM.from_pretrained(a.base,revision=a.revision,torch_dtype=torch.bfloat16,
        trust_remote_code=False,attn_implementation='eager').to('cuda').eval()
    def forward(current):
        result=[]
        with torch.inference_mode():
            for encoded in tokens:
                ensure_unpaused()
                result.append(current(**{k:v.to('cuda') for k,v in encoded.items()},use_cache=False).logits[0,-1].float().cpu())
        return torch.stack(result)
    baseline=forward(model);reports=[]
    for case in cases(a.seed):
        ensure_unpaused();adapter=out/case['name']
        mix(a.adapters,case['weights'],case['scale'],adapter,max_lora_rank=a.max_lora_rank,dtype=torch.bfloat16)
        peft=PeftModel.from_pretrained(model,str(adapter),autocast_adapter_dtype=False).eval()
        actual=forward(peft);model=peft.unload();del peft
        if case['kind']=='zero':reference=baseline
        elif case['kind']=='onehot':
            peft=PeftModel.from_pretrained(model,a.adapters[case['source']],autocast_adapter_dtype=False).eval()
            reference=forward(peft);model=peft.unload();del peft
        else:
            with directly_merged(model,a.adapters,case['weights'],case['scale']):reference=forward(model)
        check=compare_logits(actual,reference,atol=a.atol,rtol=a.rtol)
        report=case|check;reports.append(report)
        write(out/(case['name']+'_results.json'),report)
        with (out/'per_prompt.jsonl').open('a') as f:
            for row,x,y in zip(rows,actual,reference):
                f.write(json.dumps(dict(case=case['name'],prompt_id=row['prompt_id'],**compare_logits(x,y,atol=a.atol,rtol=a.rtol)))+'\n')
    return dict(n=16,logit_scope='next-token full vocabulary at final prompt position',cases=reports,
                gpu_type=torch.cuda.get_device_name(0),passed=all(r['passed'] for r in reports))


def vllm_phase(a,rows,out):
    if importlib.metadata.version('vllm')!='0.31.0':raise RuntimeError('B3 requires pinned vLLM 0.31.0')
    from vllm import LLM,SamplingParams
    from vllm.lora.request import LoRARequest
    case=cases(a.seed)[5];adapter=out/'mixture'
    mix(a.adapters,case['weights'],case['scale'],adapter,max_lora_rank=a.max_lora_rank,dtype=torch.bfloat16)
    ensure_unpaused()
    llm=LLM(model=a.base,revision=a.revision,tokenizer_revision=a.revision,dtype='bfloat16',
        trust_remote_code=False,enable_lora=True,max_loras=1,max_lora_rank=a.max_lora_rank,
        max_model_len=a.max_model_len,gpu_memory_utilization=a.gpu_memory_utilization,seed=a.seed)
    ensure_unpaused()
    results=llm.generate([r['prompt'] for r in rows],SamplingParams(temperature=0.,max_tokens=4,seed=a.seed),
        lora_request=LoRARequest('B3_mixture',1,str(adapter)),use_tqdm=False)
    if len(results)!=16 or any(not r.outputs or not r.outputs[0].token_ids for r in results):
        raise RuntimeError('multi-LoRA generation did not return 16 nonempty completions')
    with (out/'per_prompt.jsonl').open('x') as f:
        for row,result in zip(rows,results):
            f.write(json.dumps(dict(prompt_id=row['prompt_id'],token_ids=list(result.outputs[0].token_ids),text=result.outputs[0].text))+'\n')
    return dict(n=16,passed=True,engine_version='0.31.0',gpu_type=torch.cuda.get_device_name(0),generated_tokens=sum(len(r.outputs[0].token_ids) for r in results))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase',choices=['logits','vllm'],required=True)
    p.add_argument('--base',required=True);p.add_argument('--revision',required=True)
    p.add_argument('--adapters',nargs=3,required=True);p.add_argument('--prompts',required=True)
    p.add_argument('--max-lora-rank',type=int,required=True);p.add_argument('--seed',type=int,default=0)
    p.add_argument('--atol',type=float,required=True);p.add_argument('--rtol',type=float,required=True)
    p.add_argument('--max-model-len',type=int,default=4096);p.add_argument('--gpu-memory-utilization',type=float,default=.75)
    p.add_argument('--output',required=True);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    if not re.fullmatch('[a-f0-9]{40}',a.revision):raise ValueError('pin base revision')
    if not 0<=a.atol<1 or not 0<=a.rtol<1:raise ValueError('explicit finite numerical tolerances required')
    rows=[json.loads(x) for x in Path(a.prompts).read_text().splitlines() if x.strip()]
    if len(rows)!=16 or len({r['prompt_id'] for r in rows})!=16 or any(not r['prompt'].strip() for r in rows):
        raise ValueError('exactly 16 unique prompts required')
    cfg=vars(a).copy();cfg.update(prompt_sha256=sha(a.prompts),cases=cases(a.seed),K=None,
        source_sha256=sha(__file__),engine_version='0.31.0',dtype='bfloat16',
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        adapters_sha256=[dict(config=sha(Path(path)/'adapter_config.json'),weights=sha(Path(path)/'adapter_model.safetensors')) for path in a.adapters])
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd())
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip():
        raise RuntimeError('commit tracked changes before acceptance')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    cfg['versions']={name:importlib.metadata.version(name) for name in ('torch','transformers','safetensors')}
    if a.phase=='logits':cfg['versions']['peft']=importlib.metadata.version('peft')
    write(out/'config.json',cfg)
    try:
        result=logits_phase(a,rows,out) if a.phase=='logits' else vllm_phase(a,rows,out)
        write(out/'results.json',result)
        write(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title='B3 acceptance '+a.phase,status='pilot',
            landed=__import__('datetime').date.today().isoformat(),what_why='Verify LoRA mixture implementation',new='Exact factor concatenation',
            artifacts=str(out.resolve()),config_results=result,caveats='Numerical verification; not an atlas acceptance-length result'))
        if not result['passed']:raise RuntimeError('numerical checks failed; inspect preserved reports')
    except BaseException as e:
        write(out/'failure.json',dict(error_type=type(e).__name__,error=str(e)));raise

if __name__=='__main__':main()
