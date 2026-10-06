"""Frozen online target pairs for the B6 raw paired-tensor contract.

One target instance owns base weights and its current PEFT adapter. No feature
shards or autograd graphs are cached. Use in the main training process with
num_workers=0, before B6's shift_paired/PairedCollator. Explicit projected
labels preserve a child's changed LM head; verifier_last_hidden_states are
the pre-final-norm states expected by the pinned native trainer.
"""
from contextlib import nullcontext,contextmanager
import threading
import torch
from atlas.generate_magpie import unpaused


def route_arm(arm,generation_target,child_id):
    if arm not in {'FS','MVD','PO-D','PO-T'}:raise ValueError('unknown training arm')
    expected='base' if arm=='PO-D' else child_id
    if generation_target!=expected:raise ValueError('response source differs from arm contract')
    return 'base' if arm in {'PO-D','PO-T'} or child_id=='base' else 'child'


class OnlinePairCapture:
    def __init__(self,model,tap_indices,draft_token_ids,*,pause_check=unpaused,projection_chunk=64):
        core=model.get_base_model() if hasattr(model,'get_base_model') else model
        n=core.config.num_hidden_layers
        if not tap_indices or len(set(tap_indices))!=len(tap_indices) or any(type(i) is not int or not 0<i<n for i in tap_indices):
            raise ValueError('explicit pre-final-norm tap indices required')
        if draft_token_ids.ndim!=1 or draft_token_ids.dtype!=torch.long or not len(draft_token_ids):
            raise ValueError('ordered draft token IDs required')
        if len(draft_token_ids.unique())!=len(draft_token_ids) or (draft_token_ids<0).any() or (draft_token_ids>=core.config.vocab_size).any():
            raise ValueError('invalid draft token IDs')
        if type(projection_chunk) is not int or projection_chunk<=0:raise ValueError('positive projection chunk required')
        self.model=model.eval().requires_grad_(False);self.core=core
        self.taps=list(tap_indices);self.tokens=draft_token_ids.detach().clone()
        self.pause_check=pause_check;self.chunk=projection_chunk;self.lock=threading.Lock()

    @contextmanager
    def _base_context(self):
        try:
            with (self.model.disable_adapter() if hasattr(self.model,'disable_adapter') else nullcontext()):
                yield
        finally:
            # PEFT restoring an adapter also re-enables its requires_grad flags.
            # This instance is an owned frozen teacher, including on exceptions.
            self.model.requires_grad_(False)

    def _forward(self,ids):
        self.pause_check();last=[]
        def norm_input(module,args):last.append(args[0].detach())
        handle=self.core.model.norm.register_forward_pre_hook(norm_input)
        try:
            # no_grad, not inference_mode: drafter backward saves these inputs.
            with torch.no_grad():
                output=self.core.model(input_ids=ids.unsqueeze(0),output_hidden_states=True,use_cache=False)
                if len(last)!=1:raise ValueError('target final norm must run exactly once')
                features=torch.cat([output.hidden_states[i][0] for i in self.taps],-1).detach()
                labels=[]
                for chunk in output.last_hidden_state.split(self.chunk,dim=1):
                    self.pause_check()
                    full=self.core.lm_head(chunk)[0]
                    labels.append(full.index_select(-1,self.tokens.to(full.device)).detach())
                return features,last[0][0],torch.cat(labels,0)
        finally:handle.remove()

    def __call__(self,input_ids,loss_mask,*,feature_target='child'):
        if input_ids.ndim!=1 or input_ids.dtype!=torch.long or len(input_ids)<2:raise ValueError('one token sequence required')
        if loss_mask.shape!=input_ids.shape or loss_mask.dtype!=torch.bool:raise ValueError('boolean assistant mask required')
        positions=loss_mask.nonzero().flatten()
        if not len(positions) or int(positions[0])<1 or not torch.equal(positions,torch.arange(int(positions[0]),len(input_ids),device=positions.device)):
            raise ValueError('one contiguous assistant response after a nonempty prompt required')
        if feature_target not in {'base','child'}:raise ValueError('invalid feature target')
        if torch.utils.data.get_worker_info() is not None:raise ValueError('online GPU capture requires num_workers=0')
        if self.model.training:raise ValueError('frozen target must stay in eval mode')
        device=next(self.model.parameters()).device;ids=input_ids.to(device);mask=loss_mask.to(device)
        with self.lock:
            with self._base_context():base=self._forward(ids)
            if feature_target=='base':child=base
            else:child=self._forward(ids)
        raw=dict(input_ids=ids,loss_mask=mask,hidden_states=child[0],base_hidden_states=base[0],
                 verifier_last_hidden_states=child[1],base_verifier_last_hidden_states=base[1],
                 child_target_logits=child[2],base_target_logits=base[2])
        if any(not torch.isfinite(v).all() for k,v in raw.items() if k not in {'input_ids','loss_mask'}):
            raise ValueError('nonfinite frozen target output')
        return raw
