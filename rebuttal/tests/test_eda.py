import unittest
import torch
from rebuttal.eda import SharedPrivateMLP, fold_mlp, install_eda


class MLP(torch.nn.Module):
    def __init__(self,width=7):
        super().__init__()
        self.gate_proj=torch.nn.Linear(4,width,bias=False)
        self.up_proj=torch.nn.Linear(4,width,bias=False)
        self.down_proj=torch.nn.Linear(width,4,bias=False)
    def forward(self,x):return self.down_proj(torch.nn.functional.silu(self.gate_proj(x))*self.up_proj(x))


class EDATests(unittest.TestCase):
    def test_fold_matches_two_experts_and_input_gradient(self):
        model=SharedPrivateMLP(MLP().double(),private_width=3).double()
        x=torch.randn(2,5,4,dtype=torch.double,requires_grad=True)
        expected=model(x);folded=fold_mlp(model);actual=folded(x)
        torch.testing.assert_close(actual,expected,atol=1e-12,rtol=1e-12)
        a=torch.autograd.grad(actual.square().sum(),x,retain_graph=True)[0]
        b=torch.autograd.grad(expected.square().sum(),x)[0]
        torch.testing.assert_close(a,b,atol=1e-12,rtol=1e-12)
        self.assertEqual(folded.gate_proj.out_features,10)

    def test_single_expert_code_gates_cancel_and_shared_stays_frozen(self):
        model=SharedPrivateMLP(MLP(),private_width=3)
        x=torch.randn(2,4);before=model(x).detach()
        with torch.no_grad():
            model.shared_gate.weight.fill_(100.)
            model.private_gate.weight.fill_(-100.)
        torch.testing.assert_close(before,model(x))
        model(x).square().sum().backward()
        self.assertTrue(all(p.grad is None for p in model.shared.parameters()))
        self.assertTrue(all(p.grad is not None for p in model.private.parameters()))
        self.assertEqual(model.shared_gate.weight.grad.abs().sum().item(),0)
        self.assertEqual(model.private_gate.weight.grad.abs().sum().item(),0)

    def test_only_new_expert_and_routers_train(self):
        model=torch.nn.Module();model.fc=torch.nn.Linear(12,4)
        layer=torch.nn.Module();layer.mlp=MLP();layer.attn=torch.nn.Linear(4,4)
        model.layers=torch.nn.ModuleList([layer]);model.lm_head=torch.nn.Linear(4,11)
        proof=install_eda(model,3)
        self.assertEqual(proof['trainable_parameters'],3*4*3+2*4)
        self.assertEqual(proof['added_parameters'],proof['trainable_parameters'])
        self.assertFalse(model.fc.weight.requires_grad)
        self.assertFalse(model.lm_head.weight.requires_grad)

    def test_native_merged_export_has_only_standard_mlp_keys(self):
        from followspec.family_repair import configure_variant,merged_state
        from types import SimpleNamespace
        model=torch.nn.Module();layer=torch.nn.Module();layer.mlp=MLP()
        model.layers=torch.nn.ModuleList([layer]);model.fc=torch.nn.Linear(12,4)
        model.config=SimpleNamespace(transformer_layer_config=SimpleNamespace(intermediate_size=7))
        configure_variant(model,'eda_private',private_width=3)
        x=torch.randn(2,4);expected=model.layers[0].mlp(x)
        state=merged_state(model)
        self.assertEqual(set(state),{'fc.weight','fc.bias'}|{f'layers.0.mlp.{n}.weight' for n in ['gate_proj','up_proj','down_proj']})
        model.layers[0].mlp=MLP(10);model.load_state_dict(state)
        torch.testing.assert_close(model.layers[0].mlp(x),expected)
        self.assertEqual(model.config.transformer_layer_config.intermediate_size,10)


if __name__=='__main__':unittest.main()
