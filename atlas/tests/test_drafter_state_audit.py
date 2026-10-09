import torch
from atlas.drafter_state_audit import tensor_fingerprint


def test_fingerprint_covers_values_shape_and_dtype():
    x = torch.arange(6, dtype=torch.bfloat16).reshape(2, 3)
    assert tensor_fingerprint(x) == tensor_fingerprint(x.clone())
    assert tensor_fingerprint(x) != tensor_fingerprint(x + 1)
    assert tensor_fingerprint(x) != tensor_fingerprint(x.reshape(3, 2))
    assert tensor_fingerprint(x) != tensor_fingerprint(x.float())
