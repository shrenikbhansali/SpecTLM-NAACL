"""CPU contract for the installed compressed-tensors activation semantics."""
import torch
from compressed_tensors.quantization import apply_quantization_config,QuantizationConfig
from compressed_tensors.compressors import compress_module,decompress_module


def test_native_decompression_keeps_activation_quantization_enabled():
    layer=torch.nn.Linear(4,3,bias=False)
    cfg=QuantizationConfig.model_validate(dict(config_groups={'g':dict(targets=['Linear'],
        weights=dict(num_bits=8,type='int',strategy='tensor',symmetric=True),
        input_activations=dict(num_bits=8,type='int',strategy='tensor',symmetric=True))},quantization_status='frozen'))
    apply_quantization_config(layer,cfg)
    with torch.no_grad():
        layer.weight.copy_(torch.arange(12).reshape(3,4).float()/4)
        layer.weight_scale.fill_(.25);layer.input_scale.fill_(.5)
    x=torch.tensor([[.3,.7,.9,1.2]])
    expected=layer(x).detach()
    compress_module(layer);decompress_module(layer)
    actual=layer(x).detach()
    assert torch.equal(actual,expected)
    assert not torch.equal(actual,torch.nn.functional.linear(x,layer.weight))
    assert getattr(layer,'quantization_enabled',True)
