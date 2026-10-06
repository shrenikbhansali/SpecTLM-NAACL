"""Optional memory lifetime fix for the pinned native Trainer (no accumulation).

The native loop clears old gradients after the next forward. Clearing them
also before that forward lowers its peak without changing loss, backward,
clipping, optimizer state or step order. Evaluation keeps last-step gradients.
Install only on the pinned Trainer, not on a gradient-accumulating loop.
"""
import torch


def release_grad_before_forward(trainer):
    def clear_previous_step(module, _args):
        if module.training and torch.is_grad_enabled():
            trainer._optimizers_zero_grad()
    return trainer.model.register_forward_pre_hook(clear_previous_step)


def saved_tensor_context(enabled=False):
    """Move autograd's saved tensors to pinned CPU storage without arithmetic changes."""
    from contextlib import nullcontext
    return torch.autograd.graph.save_on_cpu(pin_memory=True) if enabled else nullcontext()


def checkpoint_dflash_layers(model):
    """Use native cache-free DFlash layers with kwargs-safe checkpointing."""
    if model.config.speculators_config.algorithm!='dflash':
        raise ValueError('layer checkpointing is restricted to native DFlash; Eagle has mutable caches')
    if not model.supports_gradient_checkpointing:raise ValueError('backend does not support checkpointing')
    # Native DFlash passes both trainable hidden inputs by keyword. Reentrant
    # checkpointing cannot track those inputs and would silently lose gradients.
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})


def serial_adamw(trainer):
    """Avoid AdamW's all-parameter foreach temporaries with unchanged updates."""
    if not trainer.optimizers or any(not isinstance(opt,torch.optim.AdamW) for opt in trainer.optimizers):
        raise ValueError('serial AdamW requires the native AdamW optimizer')
    if any(group.get('fused') for opt in trainer.optimizers for group in opt.param_groups):
        raise ValueError('cannot change a fused optimizer implementation')
    for opt in trainer.optimizers:
        opt.defaults['foreach']=False
        for group in opt.param_groups:group['foreach']=False
