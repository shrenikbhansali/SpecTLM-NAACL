"""Exact factorized full-vocabulary teacher distributions for E5 and E4 selection.

Stores final normalized bf16 hidden states and the unchanged bf16 LM head.
Applying the same linear map reconstructs all logits without top-k truncation.
E4 uses answer-token states; E5 uses their preceding next-token predictors.
"""
import argparse,json,time,subprocess,hashlib
from pathlib import Path
import torch
from followspec.independent_kd import read,write,jsonl
from followspec.family_repair import validate_rows,supervision_source
from followspec.train_eagle3 import ensure_unpaused
from followspec.disk_guard import require_free
from atlas.workloads import file_hash,prompt_hash
from rebuttal.kd import factor_logits,response_hidden,split_rows


def load_hidden(cache,entry):
    from safetensors import safe_open
    with safe_open(str(Path(cache)/entry['shard']),framework='pt',device='cpu') as f:return f.get_tensor(entry['key'])


def main():
    p=argparse.ArgumentParser()
    for k in ['target-row','data','forbidden','output']:p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--audit',type=Path);p.add_argument('--min-free-gb',type=float,default=350)
    p.add_argument('--smoke-samples',type=int);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();target=json.loads(a.target_row.read_text());rows=read(a.data)
    if a.smoke_samples:rows=rows[:a.smoke_samples]
    forbidden={prompt_hash(r.get('raw_prompt',r.get('prompt'))) for r in read(a.forbidden)}
    validate_rows(rows,forbidden,8192);supervision_source(target,rows,None)
    if a.audit:
        audit=json.loads(a.audit.read_text())
        if not audit.get('passed') or audit.get('data_sha256')!=file_hash(a.data):raise ValueError('data audit mismatch')
    cfg=vars(a)|{'target':target,'n':len(rows),'data_sha256':file_hash(a.data),'forbidden_sha256':file_hash(a.forbidden),
       'representation':'exact factorized full vocabulary: final normalized bf16 hidden states and frozen bf16 head',
       'projection':'F.linear bf16, log_softmax fp32; no top-k truncation',
       'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
    cfg={k:str(v) if isinstance(v,Path) else v for k,v in cfg.items()}
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    ensure_unpaused();require_free(a.output,a.min_free_gb)
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
    from transformers import AutoModelForCausalLM,PreTrainedTokenizerFast
    from safetensors.torch import save_file
    out=a.output;out.mkdir(parents=True,exist_ok=False);write(out/'config.json',cfg)
    tok=PreTrainedTokenizerFast.from_pretrained(target['path'],local_files_only=True)
    model=AutoModelForCausalLM.from_pretrained(target['path'],local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda').eval().requires_grad_(False)
    if model.lm_head.bias is not None:raise ValueError('cache currently supports bias-free teacher heads only')
    save_file({'weight':model.lm_head.weight.detach().cpu().contiguous()},out/'head.safetensors')
    tok.save_pretrained(out/'tokenizer');index=[];pending={};start=time.monotonic();audits=[];checks=[]
    def flush():
        if pending:
            ensure_unpaused();require_free(out,a.min_free_gb);save_file(pending,out/f'hidden-{(len(index)-1)//64:04d}.safetensors');pending.clear()
    with (out/'progress.jsonl').open('x') as log:
        for i,row in enumerate(rows):
            ensure_unpaused();require_free(out,a.min_free_gb)
            ids=torch.tensor([row['input_ids']],device='cuda')
            with torch.no_grad():h=model.model(input_ids=ids,use_cache=False).last_hidden_state[0]
            if not torch.isfinite(h).all():raise ValueError('nonfinite teacher states')
            stored=h.detach().cpu().contiguous();key=f'row{i}';pending[key]=stored
            entry={'index':i,'sample_id':row['sample_id'],'prompt_sha256':row['prompt_sha256'],'shard':f'hidden-{i//64:04d}.safetensors','key':key,'length':len(h),'response_start':row['response_start']};index.append(entry)
            if i<5:
                with torch.no_grad():
                    positions=range(row['response_start']-1,min(row['response_start']+2,len(h)-1))
                    reconstructed=factor_logits(stored[list(positions)].cuda(),model.lm_head.weight)
                    direct=model(input_ids=ids,use_cache=False,logits_to_keep=torch.tensor(list(positions),device='cuda')).logits[0]
                    err=(reconstructed-direct).abs().max().item()
                    if err!=0:raise ValueError('Factorized cache differs from direct full teacher logits: '+str(err))
                    checks.append({'sample_id':row['sample_id'],'positions':list(positions),'max_abs_logit_error':err,'full_vocabulary':direct.shape[-1]})
                audits.append({'sample_id':row['sample_id'],'prompt':tok.decode(row['input_ids'][:row['response_start']]),'answer':tok.decode(row['input_ids'][row['response_start']:]),'input_ids':row['input_ids'],'loss_mask':row['loss_mask'],'predictor_positions':list(range(row['response_start']-1,len(h)-1))})
            if (i+1)%64==0:flush()
            if (i+1)%16==0:
                log.write(json.dumps({'completed':i+1,'elapsed_s':time.monotonic()-start})+'\n');log.flush()
        flush()
    jsonl(out/'index.jsonl',index);write(out/'five_decoded_masks.json',audits);write(out/'factorization_checks.json',checks)
    write(out/'manifest.json',{'complete':True,'n':len(rows),'data':str(a.data),'data_sha256':file_hash(a.data),'hidden_size':model.config.hidden_size,'vocab_size':model.config.vocab_size,'dtype':'bfloat16','head_sha256':file_hash(out/'head.safetensors'),'target':target,'wall_s':time.monotonic()-start,'representation':cfg['representation']})

if __name__=='__main__':main()
