"""Rebuttal E5: full 1B fine-tuning with exact full-vocabulary forward KL."""
import argparse,json,random,subprocess,time
from pathlib import Path
import torch
from followspec.independent_kd import read,write,jsonl
from followspec.train_eagle3 import ensure_unpaused
from followspec.disk_guard import require_free
from atlas.workloads import file_hash
from rebuttal.kd import full_kl,response_hidden,split_rows,pack_by_responses
from rebuttal.teacher_cache import load_hidden


def main():
    p=argparse.ArgumentParser()
    for k in ['cache','model','output']:p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--lr',type=float,choices=[1e-5,2e-5],required=True);p.add_argument('--epochs',type=int,choices=[1,3],required=True)
    p.add_argument('--seed',type=int,default=0);p.add_argument('--heldout',type=int,default=256)
    p.add_argument('--batch-response-tokens',type=int,default=2048);p.add_argument('--projection-chunk',type=int,default=128)
    p.add_argument('--min-free-gb',type=float,default=350);p.add_argument('--smoke-steps',type=int);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();manifest=json.loads((a.cache/'manifest.json').read_text());rows=read(manifest['data']);index=read(a.cache/'index.jsonl')
    if file_hash(manifest['data'])!=manifest['data_sha256'] or len(index)!=len(rows):raise ValueError('changed/incomplete teacher cache')
    train,validation=split_rows(rows,a.heldout,a.seed);batches=pack_by_responses(rows,train,a.batch_response_tokens,a.epochs,a.seed)
    if a.smoke_steps:batches=batches[:a.smoke_steps]
    cfg={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()}
    cfg.update(teacher=manifest['target'],teacher_manifest_sha256=file_hash(a.cache/'manifest.json'),data_sha256=manifest['data_sha256'],n_train=len(train),n_validation=len(validation),steps=len(batches),train_indices=train,validation_indices=validation,optimizer='AdamW',weight_decay=.01,schedule='cosine with 3% warmup',objective='full-vocabulary forward KL at all answer positions; exact factorized teacher cache',commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    ensure_unpaused();require_free(a.output,a.min_free_gb)
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
    from transformers import AutoModelForCausalLM,PreTrainedTokenizerFast,get_cosine_schedule_with_warmup
    from safetensors.torch import load_file
    out=a.output;out.mkdir(parents=True,exist_ok=False);write(out/'config.json',cfg)
    teacher_tok=PreTrainedTokenizerFast.from_pretrained(a.cache/'tokenizer',local_files_only=True)
    student_tok=PreTrainedTokenizerFast.from_pretrained(a.model,local_files_only=True)
    from followspec.family_repair import supervision_vocabulary
    aliases=supervision_vocabulary(teacher_tok.get_vocab(),student_tok.get_vocab(),128000)
    write(out/'tokenizer_alignment.json',{'lexical_ids_identical':True,'special_aliases':aliases,'training_ids':'teacher token IDs retained; special-ID aliases explicitly logged','export_tokenizer':'teacher special-token aliases at identical IDs; lexical vocabulary unchanged; exports retain the same IDs used for KL'})
    random.seed(a.seed);torch.manual_seed(a.seed);start=time.monotonic()
    model=AutoModelForCausalLM.from_pretrained(a.model,local_files_only=True,torch_dtype=torch.float32,attn_implementation='sdpa').to('cuda')
    model.config.use_cache=False;model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.train()
    head=load_file(a.cache/'head.safetensors')['weight'].to('cuda');head.requires_grad_(False)
    if model.get_output_embeddings().weight.shape[0]!=head.shape[0]:raise ValueError('full vocabulary support mismatch')
    optimizer=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=.01,foreach=False)
    scheduler=get_cosine_schedule_with_warmup(optimizer,int(.03*len(batches)),len(batches))
    write(out/'five_decoded_masks.json',[{'sample_id':rows[i]['sample_id'],'prompt':teacher_tok.decode(rows[i]['input_ids'][:rows[i]['response_start']]),'answer':teacher_tok.decode(rows[i]['input_ids'][rows[i]['response_start']:]),'input_ids':rows[i]['input_ids'],'loss_mask':rows[i]['loss_mask']} for i in train[:5]])
    torch.cuda.reset_peak_memory_stats()
    with (out/'steps.jsonl').open('x') as log:
        for step,batch in enumerate(batches,1):
            ensure_unpaused();require_free(out,a.min_free_gb);optimizer.zero_grad(set_to_none=True);total_tokens=sum(len(rows[i]['input_ids'])-rows[i]['response_start'] for i in batch);total_loss=0.;step_start=time.monotonic()
            for i in batch:
                row=rows[i];ids=torch.tensor([row['input_ids']],device='cuda');teacher_hidden=response_hidden(load_hidden(a.cache,index[i]),row).cuda()
                with torch.autocast('cuda',dtype=torch.bfloat16):
                    h=model.model(input_ids=ids,use_cache=False).last_hidden_state[0]
                    loss=full_kl(response_hidden(h,row),model.get_output_embeddings().weight,teacher_hidden,head,a.projection_chunk)
                    weighted=loss*(len(teacher_hidden)/total_tokens)
                if not torch.isfinite(weighted):raise ValueError('nonfinite KL')
                weighted.backward();total_loss+=float(weighted.detach())
                del h,loss,weighted,teacher_hidden
            # Native repair uses gradient clipping at one; keep it here too.
            norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            if not torch.isfinite(norm):raise ValueError('nonfinite gradient')
            optimizer.step();scheduler.step();torch.cuda.synchronize()
            log.write(json.dumps({'step':step,'loss':total_loss,'answer_tokens':total_tokens,'step_s':time.monotonic()-step_start,'elapsed_s':time.monotonic()-start,'lr':scheduler.get_last_lr()[0],'grad_norm':float(norm),'peak_allocated_gib':torch.cuda.max_memory_allocated()/2**30})+'\n');log.flush()
    require_free(out,a.min_free_gb);model.eval();model.config.use_cache=True
    for key in ['bos_token_id','eos_token_id','pad_token_id']:
        value=getattr(teacher_tok,key,None)
        setattr(model.config,key,value);setattr(model.generation_config,key,value)
    dest=out/'export';model.to(dtype=torch.bfloat16).save_pretrained(dest,safe_serialization=True);teacher_tok.save_pretrained(dest)
    write(dest/'distillation_provenance.json',{'config_sha256':file_hash(out/'config.json'),'steps':len(batches),'trainable_parameters':sum(p.numel() for p in model.parameters()),'wall_s':time.monotonic()-start,'status':'smoke_only' if a.smoke_steps else 'trained_pending_heldout_selection','teacher_cache':str(a.cache)})
    write(out/'results.json',{'status':'smoke_only' if a.smoke_steps else 'trained_pending_heldout_selection','export':str(dest),'steps':len(batches),'wall_s':time.monotonic()-start,'peak_allocated_gib':torch.cuda.max_memory_allocated()/2**30})
if __name__=='__main__':main()
