"""Select detached teacher values before expanding half precision to float32.

bf16/fp16 values are exactly representable in float32. The pinned CPU/A40
acceptance checks also compare tied indices with the previous float32 top-k.
Float64 and other inputs retain the previous float32-before-selection rule.
"""
import torch


def teacher_topk(logits, k):
    source=logits.detach()
    if source.dtype not in (torch.bfloat16,torch.float16,torch.float32):source=source.float()
    values,indices=source.topk(k,dim=-1)
    return values.float(),indices


def teacher_gather(logits, indices):
    return logits.detach().gather(-1,indices).float()
