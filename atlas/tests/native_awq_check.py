"""Bounded A40 comparison against pinned vLLM's actual AWQ dequantizer."""
import json
import importlib.metadata
import torch
from atlas.quantized_targets import unpack_awq
from vllm.model_executor.layers.quantization.awq_triton import awq_dequantize_triton

assert importlib.metadata.version('vllm')=='0.31.0'
torch.manual_seed(81)
q=torch.randint(-(2**31),2**31-1,(64,16),dtype=torch.int32,device='cuda')
z=torch.randint(-(2**31),2**31-1,(2,16),dtype=torch.int32,device='cuda')
s=(torch.rand((2,128),device='cuda')*.1).half()
reference=awq_dequantize_triton(q,s,z).T
actual=unpack_awq(q,z,s,32).half()
error=float((reference-actual).abs().max())
assert torch.equal(reference,actual)
print(json.dumps(dict(passed=True,shape=list(actual.shape),max_absolute_error=error,engine='0.31.0')))
