"""Observe native EAGLE3 teacher-forced unroll with explicit sequence alignment.

The scorer anchors at generated (bonus) tokens and excludes predictions beyond
saved answers. Deeper positions remain teacher-forced diagnostics, not native
acceptance lengths. Native model loading and ten-derivative validation are
separate acceptance requirements.
"""
import torch


def capture_eagle_unroll(model,features,input_ids,steps):
    if input_ids.ndim!=2 or input_ids.shape[0]!=1 or features.ndim!=3 or features.shape[:2]!=input_ids.shape:
        raise ValueError('one aligned feature/token sequence required')
    if type(steps) is not int or not 0<steps<input_ids.shape[1]:raise ValueError('invalid unroll length')
    if not torch.isfinite(features).all():raise ValueError('nonfinite native features')
    if model.training:raise ValueError('offline drafter must be in eval mode')
    captured=[]
    def head_hook(module,args,output):
        if output.ndim!=3 or output.shape[:2]!=(1,input_ids.shape[1]-1):raise ValueError('native head shape changed')
        captured.append(output[0].detach().float().cpu())
    handle=model.lm_head.register_forward_hook(head_hook)
    try:
        with torch.inference_mode():
            model(hidden_states=features[:,:-1],input_ids=input_ids[:,1:],
                  document_ids=torch.zeros_like(input_ids[:,1:]),ttt_steps=steps)
    finally:handle.remove()
    if len(captured)!=steps:raise ValueError('native head/unroll count changed')
    return captured


def align_eagle_step(target_logits,draft_logits,response_start,step):
    if target_logits.ndim!=2 or draft_logits.ndim!=2 or len(draft_logits)!=len(target_logits)-1:
        raise ValueError('native target/draft alignment mismatch')
    length=len(target_logits)
    if type(step) is not int or not 0<=step<length-1 or not 1<=response_start<length:raise ValueError('invalid sequence boundary/step')
    # Native slot0 consumes x1 and featuresH0, predicting x2. At depthd it
    # predicts x(2+d), whose target distribution is given by logitsH(1+d).
    anchors=torch.arange(max(1,response_start),length-1-step,device=target_logits.device)
    if not len(anchors):raise ValueError('no answer positions remain at this depth')
    return target_logits[anchors+step],draft_logits[(anchors-1).to(draft_logits.device)],anchors


def expanded_logprobs(logits,d2t,vocab_size):
    if logits.ndim!=2 or d2t.ndim!=1 or logits.shape[1]!=len(d2t) or d2t.dtype!=torch.long:
        raise ValueError('draft-vocabulary shape/type mismatch')
    mapped=torch.arange(len(d2t),device=d2t.device)+d2t
    if len(mapped.unique())!=len(mapped) or (mapped<0).any() or (mapped>=vocab_size).any():raise ValueError('invalid draft-vocabulary offsets')
    if not torch.isfinite(logits).all():raise ValueError('nonfinite draft logits')
    result=torch.full((len(logits),vocab_size),-torch.inf,device=logits.device,dtype=torch.float32)
    result[:,mapped.to(logits.device)]=logits.float().log_softmax(-1)
    return result
