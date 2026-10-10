"""D-45 single-target EAGLE repair using the pinned native online-capture trainer.

This opt-in entry point does not modify the earlier FollowSpec recipe. All variants
share response records, batches, optimizer and loss. Only trainable parameter scope
changes. Local exports merge LoRA and preserve the released state-dict layout.
"""
import argparse,json,math,random,subprocess,time
from pathlib import Path
import torch
from followspec.independent_kd import read,write,jsonl,answer_labels
from followspec.train_eagle3 import BACKEND,ensure_unpaused
from atlas.workloads import file_hash,prompt_hash
from followspec.disk_guard import require_free

class RepairLinear(torch.nn.Module):
    def __init__(self,base,rank,alpha):
        super().__init__();self.base=base;self.scale=alpha/rank
        self.lora_A=torch.nn.Parameter(base.weight.new_empty(rank,base.in_features))
        self.lora_B=torch.nn.Parameter(base.weight.new_zeros(base.out_features,rank))
        torch.nn.init.kaiming_uniform_(self.lora_A,a=math.sqrt(5))
    def forward(self,x):
        return self.base(x)+torch.nn.functional.linear(torch.nn.functional.linear(x,self.lora_A),self.lora_B)*self.scale


def configure_variant(model,variant,rank=16,alpha=32,algorithm="eagle3"):
    if variant not in {'fc','fc_lora','full','fc_lowrank','decoder_lora','fc_decoder_lora','head','decoder_dense','decoder_qo'}:raise ValueError('unknown repair variant')
    model.requires_grad_(False)
    if variant in {'fc','fc_lora','full','fc_decoder_lora'}:model.fc.requires_grad_(True)
    if variant=='head':model.lm_head.requires_grad_(True)
    if variant=='decoder_dense':model.layers.requires_grad_(True)
    if variant=='decoder_qo':
        found=[]
        for name,module in model.named_modules():
            if name.startswith('layers.') and isinstance(module,torch.nn.Linear) and name.rsplit('.',1)[-1] in {'q_proj','o_proj'}:
                module.requires_grad_(True);found.append(name)
        if not found:raise ValueError('no decoder q/o projections')
    if variant=='fc_lowrank':
        if rank<1:raise ValueError('positive LoRA rank required')
        model.fc=RepairLinear(model.fc,rank,alpha)
    if variant=='full':
        for name,module in model.named_children():
            if name not in {'embed_tokens','verifier_lm_head','verifier_norm'}:module.requires_grad_(True)
    if variant in {'fc_lora','decoder_lora','fc_decoder_lora'}:
        if rank<1:raise ValueError('positive LoRA rank required')
        found=[]
        for name,module in list(model.named_modules()):
            if name.startswith('layers.') and isinstance(module,torch.nn.Linear) and name.rsplit('.',1)[-1] in ({'q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'} if variant=='fc_lora' else {'q_proj','v_proj','gate_proj','up_proj','down_proj'}):
                parent,leaf=name.rsplit('.',1);model.get_submodule(parent)._modules[leaf]=RepairLinear(module,rank,alpha);found.append(name)
        if not found:raise ValueError('no drafter layer projections found')
    if algorithm=='dflash' and not model.use_draft_vocab:model.lm_head.requires_grad_(False)
    names=[n for n,p in model.named_parameters() if p.requires_grad]
    return dict(variant=variant,rank=rank if 'lora' in variant or variant=='fc_lowrank' else None,alpha=alpha if 'lora' in variant or variant=='fc_lowrank' else None,trainable_names=names,trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),frozen_parameters=sum(p.numel() for p in model.parameters() if not p.requires_grad))


def merged_state(model):
    state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    for name,module in model.named_modules():
        if not isinstance(module,RepairLinear):continue
        state[name+'.weight']=state.pop(name+'.base.weight')+state.pop(name+'.lora_B')@state.pop(name+'.lora_A')*module.scale
        if name+'.base.bias' in state:state[name+'.bias']=state.pop(name+'.base.bias')
    return state


def initialize_scratch(model):
    """HF 5.x marks loaded tensors initialized; explicitly clear that guard."""
    changed=0
    for name,module in model.named_children():
        if name in {'embed_tokens','verifier_norm','verifier_lm_head'}:continue
        before={n:p.detach().clone() for n,p in module.named_parameters()}
        for p in list(module.parameters())+list(module.buffers()):
            if hasattr(p,'_is_hf_initialized'):p._is_hf_initialized=False
        module.apply(model._init_weights)
        changed+=sum(not torch.equal(p,before[n]) for n,p in module.named_parameters())
    if not changed:raise ValueError('scratch initialization changed no parameters')
    return dict(changed_parameters=changed,scope='fc/layers/head/norm; fixed embeddings and vocabulary mapping')


def step_batches(rows,steps,ceiling,seed,shift=1):
    lengths=[len(r['input_ids'])-shift for r in rows]
    if not rows or min(lengths)<1 or max(lengths)>ceiling:raise ValueError('invalid lengths; no truncation')
    if steps<1:raise ValueError('positive steps required')
    rng=random.Random(seed);batches=[]
    while len(batches)<steps:
        indices=list(range(len(rows)));rng.shuffle(indices);batch=[];length=0
        for i in indices:
            if batch and length+lengths[i]>ceiling:
                batches.append(batch);batch=[];length=0
            batch.append(i);length+=lengths[i]
        if batch:batches.append(batch)
    return batches[:steps]


def epoch_batches(rows,ceiling,seed,shift=1):
    lengths=[len(r['input_ids'])-shift for r in rows]
    if not rows or min(lengths)<1 or max(lengths)>ceiling:raise ValueError('invalid lengths; no truncation')
    indices=list(range(len(rows)));random.Random(seed).shuffle(indices)
    batches=[];batch=[];length=0
    for i in indices:
        if batch and length+lengths[i]>ceiling:batches.append(batch);batch=[];length=0
        batch.append(i);length+=lengths[i]
    if batch:batches.append(batch)
    return batches


def validate_rows(rows,forbidden,max_length):
    if len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('duplicate training samples')
    if len({r['prompt_sha256'] for r in rows})!=len(rows):raise ValueError('duplicate training prompts')
    for r in rows:
        answer_labels(r,max_length)
        if prompt_hash(r['raw_prompt'])!=r['prompt_sha256'] or r['prompt_sha256'] in forbidden:raise ValueError('evaluation overlap or prompt hash mismatch')


def supervision_source(target, rows, alternate):
    """Keep response provenance fixed while explicitly intervening on HF supervision."""
    if any(r['generation_target']!=target['id'] or r['generation_revision']!=target['revision'] for r in rows):
        raise ValueError('wrong response teacher')
    source=target if alternate is None else alternate
    if any(not source.get(k) for k in ['id','revision','path']):
        raise ValueError('supervision source requires pinned id/revision/path')
    return source


class RepairDataset(torch.utils.data.Dataset):
    def __init__(self,rows,capture,algorithm="eagle3"):
        self.rows=rows;self.capture=capture;self.algorithm=algorithm;self.hidden_states_dtype=torch.bfloat16
    def __len__(self):return len(self.rows)
    def __getitem__(self,i):
        from followspec.paired_data import shift_paired
        row=self.rows[i]
        raw=self.capture(torch.tensor(row['input_ids']),torch.tensor(row['loss_mask']),feature_target='base')
        if self.algorithm=='dflash':
            from followspec.dflash_extension import prepare_block_sample
            data=prepare_block_sample(raw)
        else:data=shift_paired(raw)
        # One single-target native pass, with explicit child projected labels.
        return {k:v for k,v in data.items() if not k.startswith('base_')}


class RepairCollator:
    def __init__(self,length,hidden,taps):
        from speculators.train.data import CollateFn
        self.native=CollateFn(length,hidden,taps,dtype=torch.bfloat16)
    def __call__(self,rows):return self.native(rows)


def epoch_export_steps(steps, fractions=None):
    fractions = [.25, .5, 1.] if fractions is None else fractions
    if steps < 1 or not fractions or any(not math.isfinite(f) or not 0 < f <= 1 for f in fractions) or 1. not in fractions:
        raise ValueError('epoch export fractions must be finite, in (0, 1], and include 1')
    return sorted({max(1, math.ceil(steps * f)) for f in fractions})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['target-row','drafter','data','audit','forbidden','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--variant',choices=['fc','fc_lora','full','fc_lowrank','decoder_lora','fc_decoder_lora','head','decoder_dense','decoder_qo'],required=True)
    p.add_argument('--supervision-row',help='REV1 fixed-text control: alternate pinned teacher for taps and soft labels; response provenance and initialization stay unchanged')
    p.add_argument('--steps',type=int,default=200);p.add_argument('--export-steps',nargs='+',type=int,default=[50,200])
    p.add_argument('--schedule-steps',type=int,help='shared schedule horizon for a shorter scratch control');p.add_argument('--seed',type=int,default=0);p.add_argument('--batch-tokens',type=int,default=2048)
    p.add_argument('--lr',type=float,default=2e-5);p.add_argument('--lora-rank',type=int,default=16);p.add_argument('--lora-alpha',type=int,default=32)
    p.add_argument('--scratch',action='store_true');p.add_argument('--offload-saved-tensors',action='store_true');p.add_argument('--release-grad-before-forward',action='store_true');p.add_argument('--dry-run',action='store_true')
    p.add_argument('--min-free-gb',type=float,default=0);p.add_argument('--compact-checkpoints',action='store_true');p.add_argument('--shared-export-root')
    p.add_argument('--one-epoch',action='store_true',help='derive steps and quarter/half/final exports from one complete shuffled pass')
    p.add_argument('--epoch-export-fractions',nargs='+',type=float,help='explicit export fractions for --one-epoch; default remains .25 .5 1')
    p.add_argument('--algorithm',choices=['eagle3','dflash'],default='eagle3');p.add_argument('--max-anchors',type=int,default=64)
    p.add_argument('--checkpoint-dflash-layers',action='store_true')
    p.add_argument('--ttt-steps',type=int,default=3,choices=[3,4],help='D50 explicit native EAGLE unroll depth; default unchanged')
    p.add_argument('--probe-batches',type=int,default=0,help='FIX24 diagnostic: frozen step-zero forwards only, no optimizer or exports')
    p.add_argument('--continue-epoch-from',help='D50 continue one epoch from a completed compact run, restoring named optimizer state')
    a=p.parse_args();target=json.loads(Path(a.target_row).read_text());rows=read(a.data);audit=json.loads(Path(a.audit).read_text())
    forbidden={prompt_hash(r.get('raw_prompt',r.get('prompt'))) for r in read(a.forbidden)}
    validate_rows(rows,forbidden,a.batch_tokens+(a.algorithm=='eagle3'))
    shift=int(a.algorithm=='eagle3')
    if a.algorithm=='dflash' and (a.variant not in {'fc','full'} or a.scratch):raise ValueError('D48 DFlash fc/full warm-start only')
    if not audit.get('passed') or audit.get('data_sha256')!=file_hash(a.data):raise ValueError('five sample manual audit must match sealed responses')
    supervision=supervision_source(target,rows,json.loads(Path(a.supervision_row).read_text()) if a.supervision_row else None)
    if a.supervision_row:
        if a.algorithm!='eagle3' or a.continue_epoch_from:raise ValueError('alternate supervision supports fresh EAGLE repair only')
        child_cfg=json.loads((Path(target['path'])/'config.json').read_text())
        parent_cfg=json.loads((Path(supervision['path'])/'config.json').read_text())
        if any(child_cfg[k]!=parent_cfg[k] for k in ['hidden_size','vocab_size','num_hidden_layers']):raise ValueError('incompatible supervision architecture')
        from transformers import AutoTokenizer
        child_tok=AutoTokenizer.from_pretrained(target['path'],local_files_only=True)
        parent_tok=AutoTokenizer.from_pretrained(supervision['path'],local_files_only=True)
        if child_tok.get_vocab()!=parent_tok.get_vocab():raise ValueError('alternate supervision requires identical token-id vocabulary')
    if a.scratch and a.variant!='full':raise ValueError('scratch control uses full drafter')
    previous=None;resume_step=0
    if a.continue_epoch_from:
        from followspec.repair_continuation import continuation_batches
        if not a.one_epoch or a.scratch or a.algorithm!='eagle3':raise ValueError('continuation requires one-epoch Eagle warm-start')
        prior=Path(a.continue_epoch_from);previous=json.loads((prior/'config.json').read_text());prior_result=json.loads((prior/'results.json').read_text())
        if previous['data_sha256']!=file_hash(a.data) or previous['seed']!=a.seed or previous['variant']!=a.variant or previous['ttt_steps']!=a.ttt_steps:raise ValueError('continuation recipe mismatch')
        if previous['lr']!=a.lr or previous['batch_tokens']!=a.batch_tokens or previous['drafter']!=a.drafter or previous['target']!=target:raise ValueError('continuation controls mismatch')
        resume_step=previous['steps'];checkpoint=prior/f'checkpoints/epoch-0-step-{resume_step}'
        for f in ['trainable.safetensors','optimizer_state_dict.pt','scheduler_state_dict.pt','trainable_checkpoint.json']:
            if not (checkpoint/f).exists():raise ValueError('missing final continuation state: '+f)
        epoch_index=previous.get('completed_epochs',1);one_epoch=continuation_batches(rows,a.batch_tokens,a.seed,epoch_index);a.steps=len(one_epoch);a.export_steps=epoch_export_steps(a.steps,a.epoch_export_fractions)
    elif a.one_epoch:
        one_epoch=epoch_batches(rows,a.batch_tokens,a.seed,shift=shift);a.steps=len(one_epoch)
        a.export_steps=epoch_export_steps(a.steps,a.epoch_export_fractions)
    elif a.epoch_export_fractions is not None:
        raise ValueError('--epoch-export-fractions requires --one-epoch')
    if a.steps not in a.export_steps or any(x<1 or x>a.steps for x in a.export_steps):raise ValueError('invalid export budget')
    schedule_steps=a.schedule_steps or a.steps
    if schedule_steps<a.steps:raise ValueError('schedule horizon shorter than run')
    batches=one_epoch if previous else step_batches(rows,a.steps,a.batch_tokens,a.seed,shift=shift)
    cfg=vars(a)|dict(target=target,initialization_revision=Path(a.drafter).name,schedule_horizon=schedule_steps,backend_revision=BACKEND,engine_version='0.31.0',status='pilot',code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),data_sha256=file_hash(a.data),audit_sha256=file_hash(a.audit),forbidden_sha256=file_hash(a.forbidden),n=len(rows),token_budget=sum(len(rows[i]['input_ids'])-shift for b in batches for i in b),batch_plan=batches,ttt_steps=a.ttt_steps,ttt_step_loss_decay=1.,optimizer='adamw',weight_decay=.01,scheduler='cosine',warmup_ratio=.03,loss='native KL, answer positions, no paired or delta terms',scratch_scope='random fc/layers/head/norm; fixed family embeddings and vocabulary map' if a.scratch else None)
    if a.algorithm=='dflash':cfg.update(ttt_steps=None,ttt_step_loss_decay=None,loss='native DFlash fused KL; gamma4 fixed-exp-decay; answer positions',max_anchors=a.max_anchors)
    if a.supervision_row:cfg.update(supervision=supervision,supervision_row_sha256=file_hash(a.supervision_row),control='Derivative text and initialization fixed; alternate model supplies both taps and soft labels')
    if previous:cfg.update(schedule_horizon=resume_step+a.steps,resume_source=str(prior),resume_source_config_sha256=file_hash(prior/'config.json'),resume_checkpoint=str(checkpoint),resume_global_step=resume_step,completed_epochs=epoch_index+1,continuation_schedule='Restore AdamW moments; extend cosine total horizon to prior+new steps, no replay. First epoch retains original shorter schedule; not equivalent to uninterrupted two-epoch training.',rng_policy='Prior checkpoint lacks RNG state; deterministic seed reset at continuation, next epoch data order matches native shuffle stream',cumulative_token_budget=previous['token_budget']+cfg['token_budget'])
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd());require_free(a.output,a.min_free_gb)
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
    from speculators.version import git_commit
    if git_commit!=BACKEND:raise ValueError('wrong native backend')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit source first')
    from speculators import SpeculatorModel,SpeculatorModelConfig
    from speculators.losses import resolve_loss_config
    from speculators.train.trainer import Trainer,TrainerConfig
    from transformers import AutoModelForCausalLM
    from atlas.covariates import tap_layers
    from atlas.run_cell import read_drafter_config
    from followspec.online_capture import OnlinePairCapture
    from followspec.training_memory import saved_tensor_context,release_grad_before_forward,serial_adamw
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write(out/'config.json',cfg)
    torch.manual_seed(a.seed);start=time.monotonic()
    base_config=json.loads((Path(target['path'])/'config.json').read_text())
    if a.algorithm=='dflash':
        from followspec.dflash_loader import load_released_dflash
        model=load_released_dflash(a.drafter,target['path'],attention='eager',device='cpu');taps=list(model.target_layer_ids)
    else:
        taps=tap_layers(read_drafter_config(a.drafter,Path(a.drafter).name),base_config['num_hidden_layers'])
        conf=SpeculatorModelConfig.from_pretrained(a.drafter,local_files_only=True)
        conf.speculators_config.verifier.name_or_path=target['path'];conf.eagle_aux_hidden_state_layer_ids=taps
        conf.transformer_layer_config._attn_implementation='eager'
        model=SpeculatorModel.from_pretrained(a.drafter,config=conf,local_files_only=True,torch_dtype=torch.float32)
        from followspec.missing_embedding import fill_missing_embedding
        if a.probe_batches:
            from followspec.missing_embedding import state_hashes
            before_embedding_fill=state_hashes(model)
        write(out/'embedding_source.json',fill_missing_embedding(model,a.drafter,target['path']))
        if a.probe_batches:write(out/'loaded_state.json',dict(legacy=before_embedding_fill,fixed=state_hashes(model)))
    if a.scratch:
        write(out/'scratch_initialization.json',initialize_scratch(model))
    proof=configure_variant(model,a.variant,a.lora_rank,a.lora_alpha,algorithm=a.algorithm)
    if previous:
        from safetensors.torch import load_file
        state=load_file(checkpoint/'trainable.safetensors');expected={n for n,p in model.named_parameters() if p.requires_grad}
        if set(state)!=expected:raise ValueError('continuation trainable scope mismatch')
        model.load_state_dict(state,strict=False)
    write(out/'parameters.json',proof)
    teacher=AutoModelForCausalLM.from_pretrained(supervision['path'],local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda').eval().requires_grad_(False)
    tokens=torch.arange(len(model.d2t))+model.d2t.cpu() if model.d2t is not None else torch.arange(base_config['vocab_size'])
    capture=OnlinePairCapture(teacher,taps,tokens,pause_check=ensure_unpaused)
    loader=torch.utils.data.DataLoader(RepairDataset(rows,capture,a.algorithm),batch_sampler=batches,collate_fn=RepairCollator(a.batch_tokens,base_config['hidden_size'],len(taps)),num_workers=0)
    # Substitute the exact single-target projected logits (the child head can differ).
    native=model.forward
    def forward(*args,child_target_logits=None,**kwargs):
        ensure_unpaused();require_free(out,a.min_free_gb)
        if a.algorithm=='dflash':
            from followspec.dflash_extension import align_targets
            backbone=model._backbone_forward
            def projected(*ba,**bk):
                hidden,q,p,mask,indices=backbone(*ba,**bk)
                return hidden,q,align_targets(child_target_logits,indices,sample_from_anchor=model.config.sample_from_anchor),mask,indices
            model._backbone_forward=projected
            try:return native(*args,**kwargs)
            finally:model._backbone_forward=backbone
        h=model.verifier_lm_head.register_forward_hook(lambda _m,_a,_o:child_target_logits.detach())
        try:return native(*args,**kwargs)
        finally:h.remove()
    model.forward=forward
    def metrics_hook(_m,_args,result):
        if model.training:
            with (out/'training_metrics.jsonl').open('a') as f:f.write(json.dumps({k:float(v.detach().cpu()) for k,v in result[2].items() if v.numel()==1})+'\n')
    model.register_forward_hook(metrics_hook)
    call=dict(ttt_steps=a.ttt_steps,ttt_step_loss_decay=1.,loss_config=resolve_loss_config('kl_div','fused'))
    if a.algorithm=='dflash':call=dict(max_anchors=a.max_anchors,gamma=4.,per_position_loss_weight='fixed-exp-decay',loss_config=resolve_loss_config('kl_div','fused'))
    if a.checkpoint_dflash_layers:
        if a.algorithm!='dflash':raise ValueError('layer checkpointing is DFlash only')
        from followspec.training_memory import checkpoint_dflash_layers
        checkpoint_dflash_layers(model)
    trainer=Trainer(model,TrainerConfig(lr=a.lr,num_epochs=1,save_path=str(out/'checkpoints'),optimizer='adamw',weight_decay=.01,scheduler_type='cosine',scheduler_warmup_ratio=.03,scheduler_total_steps=schedule_steps,hidden_states_dtype=torch.bfloat16,train_call_kwargs=call,val_call_kwargs=call,log_freq=10),loader,None)
    if previous:
        from followspec.repair_continuation import restore_optimizer_by_name
        from transformers import get_cosine_schedule_with_warmup
        restore_optimizer_by_name(model,trainer.optimizers,torch.load(checkpoint/'optimizer_state_dict.pt',map_location='cpu',weights_only=True))
        total=resume_step+a.steps;warmup=int(total*.03);trainer.schedulers=[]
        for opt in trainer.optimizers:
            for group in opt.param_groups:group['initial_lr']=a.lr
            trainer.schedulers.append(get_cosine_schedule_with_warmup(opt,warmup,total,last_epoch=resume_step-1))
        write(out/'continuation.json',dict(resume_step=resume_step,additional_steps=a.steps,total_horizon=total,first_lr=[g['lr'] for o in trainer.optimizers for g in o.param_groups],prior_scheduler_state_sha256=file_hash(checkpoint/'scheduler_state_dict.pt'),optimizer_sha256=file_hash(checkpoint/'optimizer_state_dict.pt')))
    serial_adamw(trainer)
    if a.release_grad_before_forward:release_grad_before_forward(trainer)
    if a.probe_batches:
        if a.probe_batches<1:raise ValueError('positive probe count required')
        from followspec.missing_embedding import probe_batches
        with saved_tensor_context(a.offload_saved_tensors):records=probe_batches(model,loader,call,a.probe_batches)
        write(out/'results.json',dict(status='step_zero_diagnostic_no_training',metrics=records,n_batches=len(records),optimizer_steps=0,wall_s=time.monotonic()-start))
        return
    original_step=trainer._optimizers_step;completed=0
    mutable=set(proof['trainable_names'])
    for name in list(mutable):
        if '.lora_' in name:mutable.add(name.rsplit('.',1)[0]+'.weight')
    def compact_checkpoint(label, save_optimizer=True):
        from followspec.checkpoint_storage import save_trainable_checkpoint
        dest=out/'checkpoints'/str(label)
        save_trainable_checkpoint(model,dest,trainer.optimizers,dict(initialization=a.drafter,config_sha256=file_hash(out/'config.json'),step=completed),a.min_free_gb,save_optimizer=save_optimizer)
        if trainer.schedulers:torch.save([x.state_dict() for x in trainer.schedulers],dest/'scheduler_state_dict.pt')
    if a.compact_checkpoints:
        # The native trainer otherwise writes another full model at epoch end.
        # New flag replaces persistence only; forward/loss/optimizer are unchanged.
        trainer.maybe_save_checkpoint=lambda epoch,local_step=0:compact_checkpoint(f'epoch-{epoch}-step-{completed}')

    def step():
        nonlocal completed
        if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in model.parameters()):raise ValueError('nonfinite drafter gradient')
        original_step();completed+=1
        if completed in a.export_steps:
            dest=out/f'export-{completed}'
            require_free(out,a.min_free_gb)
            if a.shared_export_root:
                from followspec.checkpoint_storage import shared_export
                shared_export(model,dest,a.shared_export_root,merged_state(model),mutable,a.min_free_gb)
            else:
                dest.mkdir(exist_ok=False);model.save_pretrained(dest,state_dict=merged_state(model),safe_serialization=True)
            if a.compact_checkpoints and completed<a.steps:compact_checkpoint(f'step-{completed}',save_optimizer=False)
            write(dest/'repair_provenance.json',dict(config_sha256=file_hash(out/'config.json'),step=completed,variant=a.variant,elapsed_s=time.monotonic()-start,trainable=proof,export_format='native released state keys; LoRA merged'))
    trainer._optimizers_step=step
    with saved_tensor_context(a.offload_saved_tensors):trainer.run_training()
    if trainer.global_step!=a.steps or any(p.grad is not None for p in teacher.parameters()):raise ValueError('step count/frozen teacher failure')
    write(out/'results.json',dict(status='trained_pending_frozen_harness_evaluation',n=len(rows),steps=trainer.global_step,wall_s=time.monotonic()-start,max_gpu_allocated_gb=torch.cuda.max_memory_allocated()/1024**3,exports=[str(out/f'export-{i}') for i in a.export_steps]))

if __name__=='__main__':main()
