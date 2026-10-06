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
