"""Bounded diagnostic for LoRA-vs-merged arithmetic; never substitutes B3 acceptance."""
import argparse
import json
from pathlib import Path
import subprocess
import torch
from followspec.mixture import mix,sha
from followspec.verify_mixture import ensure_unpaused,directly_merged,compare_logits,cases,write


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--launch-record',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();record=json.loads(Path(a.launch_record).read_text());argv=record['args']
    get=lambda k:argv[argv.index(k)+1]
    adapters=argv[argv.index('--adapters')+1:argv.index('--adapters')+4]
    base=get('--base');revision=get('--revision');prompts=get('--prompts');out=Path(a.output)
    ensure_unpaused();ensure_unpaused(Path.cwd());out.mkdir(parents=True,exist_ok=False)
    config=dict(base=base,revision=revision,prompt_sha256=sha(prompts),source_launch=record,n=16,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),seed=0,
        hypothesis='Separate bf16 LoRA-versus-dense execution error from factor-concatenation error',
        acceptance=False,engine='Transformers diagnostic; not a speculative decoding result')
    write(out/'config.json',config)
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from peft import PeftModel
    tokenizer=AutoTokenizer.from_pretrained(base,local_files_only=True)
    rows=[json.loads(x) for x in Path(prompts).read_text().splitlines()]
    tokens=[tokenizer(r['prompt'],return_tensors='pt') for r in rows]
    reports=[]
    for dtype in (torch.bfloat16,torch.float32):
        ensure_unpaused()
        model=AutoModelForCausalLM.from_pretrained(base,torch_dtype=dtype,local_files_only=True,attn_implementation='eager').to('cuda').eval()
        def forward(m):
            with torch.inference_mode():
                return torch.stack([m(**{k:v.to('cuda') for k,v in t.items()},use_cache=False).logits[0,-1].float().cpu() for t in tokens])
        for case in [cases(0)[0],cases(0)[4]]:
            path=adapters[0]
            if case['kind']=='random':
                path=str(out/(str(dtype).split('.')[-1]+'_mixture'))
                mix(adapters,case['weights'],case['scale'],path,max_lora_rank=32,dtype=dtype)
            peft=PeftModel.from_pretrained(model,path,autocast_adapter_dtype=False).to(dtype).eval()
            actual=forward(peft);model=peft.unload();del peft
            with directly_merged(model,adapters,case['weights'],case['scale']):reference=forward(model)
            error=compare_logits(actual,reference,atol=.125,rtol=.02)
            report=dict(dtype=str(dtype),kind=case['kind'],scale=case['scale'],weights=case['weights'],**error)
            reports.append(report);print(json.dumps(report),flush=True)
            with (out/'per_prompt.jsonl').open('a') as f:
                for row,x,y in zip(rows,actual,reference):f.write(json.dumps(dict(prompt_id=row['prompt_id'],dtype=str(dtype),kind=case['kind'],**compare_logits(x,y,atol=.125,rtol=.02)))+'\n')
        del model;torch.cuda.empty_cache()
    write(out/'results.json',dict(n=16,comparisons=reports,acceptance=False))
    write(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title='B3 merged arithmetic diagnostic',landed=__import__('datetime').date.today().isoformat(),status='pilot',
        what_why=config['hypothesis'],new='Source one-hot and random mixture compared with dense execution in bf16 and fp32',
        artifacts=str(out.resolve()),config_results=reports,caveats='Numerical diagnostic only; does not change B3 tolerance or qualify as bf16 acceptance'))

if __name__=='__main__':main()
