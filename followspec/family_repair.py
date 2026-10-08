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


def configure_variant(model,variant,rank=16,alpha=32):
    if variant not in {'fc','fc_lora','full','fc_lowrank','decoder_lora','fc_decoder_lora','head'}:raise ValueError('unknown repair variant')
    model.requires_grad_(False)
    if variant in {'fc','fc_lora','full','fc_decoder_lora'}:model.fc.requires_grad_(True)
    if variant=='head':model.lm_head.requires_grad_(True)
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


def step_batches(rows,steps,ceiling,seed):
    lengths=[len(r['input_ids'])-1 for r in rows]
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


def epoch_batches(rows,ceiling,seed):
    lengths=[len(r['input_ids'])-1 for r in rows]
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


class RepairDataset(torch.utils.data.Dataset):
    def __init__(self,rows,capture):
        self.rows=rows;self.capture=capture;self.hidden_states_dtype=torch.bfloat16
    def __len__(self):return len(self.rows)
    def __getitem__(self,i):
        from followspec.paired_data import shift_paired
        row=self.rows[i]
        raw=self.capture(torch.tensor(row['input_ids']),torch.tensor(row['loss_mask']),feature_target='base')
        data=shift_paired(raw)
        # One single-target native pass, with explicit child projected labels.
        return {k:v for k,v in data.items() if not k.startswith('base_')}


class RepairCollator:
    def __init__(self,length,hidden,taps):
        from speculators.train.data import CollateFn
        self.native=CollateFn(length,hidden,taps,dtype=torch.bfloat16)
    def __call__(self,rows):return self.native(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['target-row','drafter','data','audit','forbidden','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--variant',choices=['fc','fc_lora','full','fc_lowrank','decoder_lora','fc_decoder_lora','head'],required=True)
    p.add_argument('--steps',type=int,default=200);p.add_argument('--export-steps',nargs='+',type=int,default=[50,200])
    p.add_argument('--schedule-steps',type=int,help='shared schedule horizon for a shorter scratch control');p.add_argument('--seed',type=int,default=0);p.add_argument('--batch-tokens',type=int,default=2048)
    p.add_argument('--lr',type=float,default=2e-5);p.add_argument('--lora-rank',type=int,default=16);p.add_argument('--lora-alpha',type=int,default=32)
    p.add_argument('--scratch',action='store_true');p.add_argument('--offload-saved-tensors',action='store_true');p.add_argument('--release-grad-before-forward',action='store_true');p.add_argument('--dry-run',action='store_true')
    p.add_argument('--min-free-gb',type=float,default=0);p.add_argument('--compact-checkpoints',action='store_true');p.add_argument('--shared-export-root')
    p.add_argument('--one-epoch',action='store_true',help='derive steps and quarter/half/final exports from one complete shuffled pass')
    a=p.parse_args();target=json.loads(Path(a.target_row).read_text());rows=read(a.data);audit=json.loads(Path(a.audit).read_text())
    forbidden={prompt_hash(r.get('raw_prompt',r.get('prompt'))) for r in read(a.forbidden)}
    validate_rows(rows,forbidden,a.batch_tokens+1)
    if not audit.get('passed') or audit.get('data_sha256')!=file_hash(a.data):raise ValueError('five sample manual audit must match sealed responses')
    if any(r['generation_target']!=target['id'] or r['generation_revision']!=target['revision'] for r in rows):raise ValueError('wrong response teacher')
    if a.scratch and a.variant!='full':raise ValueError('scratch control uses full drafter')
    if a.one_epoch:
        one_epoch=epoch_batches(rows,a.batch_tokens,a.seed);a.steps=len(one_epoch)
        a.export_steps=sorted({max(1,math.ceil(a.steps*f)) for f in [.25,.5,1.]})
    if a.steps not in a.export_steps or any(x<1 or x>a.steps for x in a.export_steps):raise ValueError('invalid export budget')
    schedule_steps=a.schedule_steps or a.steps
    if schedule_steps<a.steps:raise ValueError('schedule horizon shorter than run')
    batches=step_batches(rows,a.steps,a.batch_tokens,a.seed)
    cfg=vars(a)|dict(target=target,initialization_revision=Path(a.drafter).name,schedule_horizon=schedule_steps,backend_revision=BACKEND,engine_version='0.31.0',status='pilot',code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),data_sha256=file_hash(a.data),audit_sha256=file_hash(a.audit),forbidden_sha256=file_hash(a.forbidden),n=len(rows),token_budget=sum(len(rows[i]['input_ids'])-1 for b in batches for i in b),batch_plan=batches,ttt_steps=3,ttt_step_loss_decay=1.,optimizer='adamw',weight_decay=.01,scheduler='cosine',warmup_ratio=.03,loss='native KL, answer positions, no paired or delta terms',scratch_scope='random fc/layers/head/norm; fixed family embeddings and vocabulary map' if a.scratch else None)
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
    taps=tap_layers(read_drafter_config(a.drafter,Path(a.drafter).name),base_config['num_hidden_layers'])
    conf=SpeculatorModelConfig.from_pretrained(a.drafter,local_files_only=True)
    conf.speculators_config.verifier.name_or_path=target['path'];conf.eagle_aux_hidden_state_layer_ids=taps
    conf.transformer_layer_config._attn_implementation='eager'
    model=SpeculatorModel.from_pretrained(a.drafter,config=conf,local_files_only=True,torch_dtype=torch.float32)
    if a.scratch:
        write(out/'scratch_initialization.json',initialize_scratch(model))
    proof=configure_variant(model,a.variant,a.lora_rank,a.lora_alpha);write(out/'parameters.json',proof)
    teacher=AutoModelForCausalLM.from_pretrained(target['path'],local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda').eval().requires_grad_(False)
    tokens=torch.arange(len(model.d2t))+model.d2t.cpu() if model.d2t is not None else torch.arange(base_config['vocab_size'])
    capture=OnlinePairCapture(teacher,taps,tokens,pause_check=ensure_unpaused)
    loader=torch.utils.data.DataLoader(RepairDataset(rows,capture),batch_sampler=batches,collate_fn=RepairCollator(a.batch_tokens,base_config['hidden_size'],len(taps)),num_workers=0)
    # Substitute the exact single-target projected logits (the child head can differ).
    native=model.forward
    def forward(*args,child_target_logits=None,**kwargs):
        ensure_unpaused();require_free(out,a.min_free_gb)
        h=model.verifier_lm_head.register_forward_hook(lambda _m,_a,_o:child_target_logits.detach())
        try:return native(*args,**kwargs)
        finally:h.remove()
    model.forward=forward
    def metrics_hook(_m,_args,result):
        if model.training:
            with (out/'training_metrics.jsonl').open('a') as f:f.write(json.dumps({k:float(v.detach().cpu()) for k,v in result[2].items() if v.numel()==1})+'\n')
    model.register_forward_hook(metrics_hook)
    call=dict(ttt_steps=3,ttt_step_loss_decay=1.,loss_config=resolve_loss_config('kl_div','fused'))
    trainer=Trainer(model,TrainerConfig(lr=a.lr,num_epochs=1,save_path=str(out/'checkpoints'),optimizer='adamw',weight_decay=.01,scheduler_type='cosine',scheduler_warmup_ratio=.03,scheduler_total_steps=schedule_steps,hidden_states_dtype=torch.bfloat16,train_call_kwargs=call,val_call_kwargs=call,log_freq=10),loader,None)
    serial_adamw(trainer)
    if a.release_grad_before_forward:release_grad_before_forward(trainer)
    original_step=trainer._optimizers_step;completed=0
    mutable=set(proof['trainable_names'])
    for name in list(mutable):
        if '.lora_' in name:mutable.add(name.rsplit('.',1)[0]+'.weight')
    def compact_checkpoint(label):
        from followspec.checkpoint_storage import save_trainable_checkpoint
        dest=out/'checkpoints'/str(label)
        save_trainable_checkpoint(model,dest,trainer.optimizers,dict(initialization=a.drafter,config_sha256=file_hash(out/'config.json'),step=completed),a.min_free_gb)
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
            if a.compact_checkpoints and completed<a.steps:compact_checkpoint(f'step-{completed}')
            write(dest/'repair_provenance.json',dict(config_sha256=file_hash(out/'config.json'),step=completed,variant=a.variant,elapsed_s=time.monotonic()-start,trainable=proof,export_format='native released state keys; LoRA merged'))
    trainer._optimizers_step=step
    with saved_tensor_context(a.offload_saved_tensors):trainer.run_training()
    if trainer.global_step!=a.steps or any(p.grad is not None for p in teacher.parameters()):raise ValueError('step count/frozen teacher failure')
    write(out/'results.json',dict(status='trained_pending_frozen_harness_evaluation',n=len(rows),steps=trainer.global_step,wall_s=time.monotonic()-start,max_gpu_allocated_gb=torch.cuda.max_memory_allocated()/1024**3,exports=[str(out/f'export-{i}') for i in a.export_steps]))

if __name__=='__main__':main()
