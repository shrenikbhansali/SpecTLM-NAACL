"""Paired native DFlash passes on identical sampled anchors and raw sequences.

The native backbone, anchor selection, block mask, loss and decay stay intact.
Only the normalized delta uses the child-selected top-k vocabulary, at every
native masked block position. Install before Trainer/DDP setup. This module
does not launch training and is not yet production acceptance.
"""
import math
import types
import torch
from followspec.delta import centered_delta, objective
from followspec.teacher_selection import teacher_topk, teacher_gather
from followspec.paired_data import shift_paired, validate_packed


def prepare_block_sample(raw):
    # Reuse the strict paired tensor validation, then retain the original
    # indices. Native DFlash has no EAGLE preprocessing shift (train/cli.py).
    shift_paired(raw)
    length=len(raw['input_ids'])
    return raw | dict(lengths=torch.tensor([length]),position_ids=torch.arange(length))


def align_targets(logits, indices, *, sample_from_anchor):
    if logits.ndim!=3 or indices.ndim!=1 or indices.dtype!=torch.long:
        raise ValueError('target/anchor shape mismatch')
    if not indices.numel() or bool((indices<0).any()) or bool((indices>=logits.shape[1]).any()):
        raise ValueError('target anchor index outside sequence')
    selected=indices if sample_from_anchor else (indices-1)%logits.shape[1]
    return logits[:,selected].detach()


def install_follow_spec_dflash(model,*,beta=1.,delta_lambda=.1,top_k=32,shared_verifier_head=False):
    if getattr(model,'_followspec_installed',False):raise ValueError('FollowSpec already installed')
    if type(top_k)!=int or top_k<=0:raise ValueError('positive top-k required')
    if not all(math.isfinite(x) and x>=0 for x in (beta,delta_lambda)):raise ValueError('invalid loss weights')
    if not hasattr(model,'_backbone_forward') or model.block_size<2:raise ValueError('native DFlash backbone required')
    native_forward=model.forward;native_backbone=model._backbone_forward

    def paired_forward(self,hidden_states,input_ids,document_ids,loss_mask,
                       verifier_last_hidden_states,base_hidden_states,
                       base_verifier_last_hidden_states,target_id,
                       child_target_logits=None,base_target_logits=None,**kwargs):
        if not target_id:raise ValueError('per-sample target provenance required')
        if hidden_states.shape!=base_hidden_states.shape or verifier_last_hidden_states.shape!=base_verifier_last_hidden_states.shape:
            raise ValueError('paired feature shape mismatch')
        if loss_mask.dtype!=torch.bool or loss_mask.shape!=input_ids.shape or input_ids.shape!=document_ids.shape:
            raise ValueError('aligned IDs and boolean assistant mask required')
        if input_ids.ndim!=2 or input_ids.shape[0]!=1 or input_ids.shape[1]<self.block_size:
            raise ValueError('one packed sequence at least one block long required')
        if 'ttt_steps' in kwargs:raise ValueError('DFlash uses blocks, not EAGLE unroll steps')
        validate_packed(dict(input_ids=input_ids,document_ids=document_ids,loss_mask=loss_mask),self.block_size)
        if (child_target_logits is None)!=(base_target_logits is None):raise ValueError('supply both projected target tensors')
        if not shared_verifier_head and child_target_logits is None:raise ValueError('projected target logits required')
        for logits in [child_target_logits,base_target_logits]:
            if logits is not None and (logits.ndim!=3 or logits.shape[:2]!=input_ids.shape):
                raise ValueError('projected target shape mismatch')
        captured={}
        def one_pass(kind,features,last,override):
            count=0
            def backbone(this,*args,**kw):
                nonlocal count
                count+=1
                hidden,q,p,mask,indices=native_backbone(*args,**kw)
                if override is not None:
                    projected=align_targets(override,indices,sample_from_anchor=self.config.sample_from_anchor)
                    if projected.shape!=p.shape:raise ValueError('projected target shape mismatch')
                    p=projected
                if kind=='child':
                    captured['mask']=mask.to(torch.bool);captured['indices']=indices
                    if delta_lambda:
                        if top_k>p.shape[-1]:raise ValueError('top-k exceeds draft vocabulary')
                        pc,ids=teacher_topk(p,top_k)
                        captured.update(pc=pc,ids=ids,qc=q.gather(-1,ids))
                else:
                    if not torch.equal(indices,captured['indices']) or not torch.equal(mask.to(torch.bool),captured['mask']):
                        raise ValueError('paired native anchors or masks differ')
                    if delta_lambda:
                        captured.update(p0=teacher_gather(p,captured['ids']),
                                        q0=q.detach().gather(-1,captured['ids']))
                return hidden,q,p,mask,indices
            self._backbone_forward=types.MethodType(backbone,self)
            try:
                result=native_forward(hidden_states=features.detach(),input_ids=input_ids,document_ids=document_ids,
                    loss_mask=loss_mask,verifier_last_hidden_states=last.detach(),**kwargs)
            finally:self._backbone_forward=native_backbone
            if count!=1:raise RuntimeError('native DFlash backbone call count changed')
            return result

        cpu_rng=torch.get_rng_state()
        device=hidden_states.device
        cuda_devices=[device.index if device.index is not None else torch.cuda.current_device()] if device.type=='cuda' else []
        cuda_rng=torch.cuda.get_rng_state(cuda_devices[0]) if cuda_devices else None
        tokens,lc,mc=one_pass('child',hidden_states,verifier_last_hidden_states,child_target_logits)
        # Base pass reuses the child's anchor draw; global RNG advances once.
        with torch.random.fork_rng(devices=cuda_devices):
            torch.set_rng_state(cpu_rng)
            if cuda_devices:torch.cuda.set_rng_state(cuda_rng,cuda_devices[0])
            _,lb,mb=one_pass('base',base_hidden_states,base_verifier_last_hidden_states,base_target_logits)
        delta=lc.new_zeros(());one=lc.new_ones(())
        metrics={f'child_{k}':v for k,v in mc.items()} | {f'base_{k}':v for k,v in mb.items()}
        if delta_lambda:
            args=[captured[k] for k in ['qc','q0','pc','p0']]
            delta=centered_delta(*args,captured['mask'])
            for pos in range(self.block_size):
                mask=captured['mask'][:,pos::self.block_size]
                term=centered_delta(*(v[:,pos::self.block_size] for v in args),mask)
                metrics[f'delta_position_{pos}_sum']=term.detach()
                metrics[f'delta_position_{pos}_total']=(mask.sum()>0).to(one.dtype)
        loss=objective(lc,lb,delta,beta=beta,delta_lambda=delta_lambda)
        for name,value in [('child_native',lc),('base_native',lb),('delta_loss',delta),('loss',loss)]:
            metrics[name+'_sum']=value.detach();metrics[name+'_total']=one.clone()
        return tokens,loss,metrics

    model.forward=types.MethodType(paired_forward,model)
    model._followspec_installed=True
    return model
