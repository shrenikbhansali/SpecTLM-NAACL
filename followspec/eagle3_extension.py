"""Add paired passes to the pinned speculators EAGLE-3 model without new weights.

The native forward and loss remain authoritative. Temporary output hooks gather
only child-selected top-k logits at each native TTT step. State-dict names and
save_pretrained are unchanged. Install before Trainer/DDP/FSDP setup.

This is a training extension, not a launch path. The operator launcher must
validate pause state, data manifests and the pinned backend before invoking it.
"""
import math
import types
import torch
from followspec.delta import centered_delta,objective


def install_follow_spec(model,*,beta=1.,delta_lambda=.1,top_k=32,shared_verifier_head=False):
    if getattr(model,'_followspec_installed',False):raise ValueError('FollowSpec already installed')
    if type(top_k)!=int or top_k<=0:raise ValueError('positive top-k required')
    if not all(math.isfinite(x) and x>=0 for x in (beta,delta_lambda)):raise ValueError('invalid loss weights')
    native_forward=model.forward

    def paired_forward(self,hidden_states,input_ids,document_ids,loss_mask,
                       verifier_last_hidden_states,base_hidden_states,
                       base_verifier_last_hidden_states,target_id,
                       child_target_logits=None,base_target_logits=None,
                       ttt_steps=3,ttt_step_loss_decay=1.,**kwargs):
        if not target_id:raise ValueError('per-sample target provenance required')
        if hidden_states.shape!=base_hidden_states.shape or verifier_last_hidden_states.shape!=base_verifier_last_hidden_states.shape:
            raise ValueError('paired features must have identical shapes and sequence alignment')
        if loss_mask.dtype!=torch.bool or loss_mask.shape!=input_ids.shape or input_ids.shape!=document_ids.shape:
            raise ValueError('aligned input IDs, document IDs and boolean assistant mask required')
        if not 0<ttt_steps<=input_ids.shape[1]:raise ValueError('unroll exceeds available sequence length')
        if not shared_verifier_head and (child_target_logits is None or base_target_logits is None):
            raise ValueError('explicit projected target logits required when verifier heads differ')
        if (child_target_logits is None)!=(base_target_logits is None):raise ValueError('supply both projected target tensors')
        child_selected=[];base_selected=[];teacher={}

        def one_pass(kind,features,last_features,override):
            counter=0
            def target_hook(module,args,output):
                if override is not None:
                    if override.shape!=output.shape:raise ValueError('projected target logit shape mismatch')
                    output=override.detach()
                if delta_lambda:
                    if kind=='child':
                        if top_k>output.shape[-1]:raise ValueError('top-k exceeds draft vocabulary')
                        values,indices=output.detach().float().topk(top_k,dim=-1)
                        teacher['child']=values;teacher['indices']=indices
                    else:teacher['base']=output.detach().float().gather(-1,teacher['indices'])
                return output
            def draft_hook(module,args,output):
                nonlocal counter
                step=counter;counter+=1
                if delta_lambda:
                    if 'indices' not in teacher:raise RuntimeError('backend called draft head before target head')
                    aligned=output[:,:-step] if step else output
                    selected=aligned.gather(-1,teacher['indices'][:,step:])
                    (child_selected if kind=='child' else base_selected).append(selected if kind=='child' else selected.detach())
            handles=[self.verifier_lm_head.register_forward_hook(target_hook),self.lm_head.register_forward_hook(draft_hook)]
            try:
                result=native_forward(hidden_states=features.detach(),input_ids=input_ids,document_ids=document_ids,
                    loss_mask=loss_mask,verifier_last_hidden_states=last_features.detach(),ttt_steps=ttt_steps,
                    ttt_step_loss_decay=ttt_step_loss_decay,**kwargs)
            finally:
                for handle in handles:handle.remove()
            if counter!=ttt_steps:raise RuntimeError('backend unroll/head call count changed')
            return result

        tokens,child_loss,child_metrics=one_pass('child',hidden_states,verifier_last_hidden_states,child_target_logits)
        _,base_loss,base_metrics=one_pass('base',base_hidden_states,base_verifier_last_hidden_states,base_target_logits)
        delta=child_loss.new_zeros(())
        metrics={f'child_{k}':v for k,v in child_metrics.items()}
        metrics.update({f'base_{k}':v for k,v in base_metrics.items()})
        one=child_loss.new_ones(())
        if delta_lambda:
            for step,(qc,q0) in enumerate(zip(child_selected,base_selected,strict=True)):
                term=centered_delta(qc,q0,teacher['child'][:,step:],teacher['base'][:,step:],loss_mask[:,step:])
                delta=delta+(ttt_step_loss_decay**step)*term
                metrics[f'delta_step_{step}_sum']=term.detach();metrics[f'delta_step_{step}_total']=one.clone()
        loss=objective(child_loss,base_loss,delta,beta=beta,delta_lambda=delta_lambda)
        for name,value in [('child_native',child_loss),('base_native',base_loss),('delta_loss',delta),('loss',loss)]:
            metrics[name+'_sum']=value.detach();metrics[name+'_total']=one.clone()
        return tokens,loss,metrics

    model.forward=types.MethodType(paired_forward,model)
    model._followspec_installed=True
    return model
