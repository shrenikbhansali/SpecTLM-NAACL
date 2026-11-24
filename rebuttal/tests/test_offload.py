import copy
import unittest
import torch

from rebuttal.offload import pack_tensor, unpack_tensor, stride_preserving_offload


class OffloadTests(unittest.TestCase):
    def test_padded_transposed_and_expanded_views_preserve_layout(self):
        tensors=[torch.randn(8,344)[:,:343],torch.randn(2,3,4).transpose(1,2),
                 torch.randn(1,5).expand(3,5),torch.randn(9,7)[2:8,1:6]]
        for x in tensors:
            y=unpack_tensor(pack_tensor(x))
            self.assertTrue(torch.equal(x,y));self.assertEqual(x.stride(),y.stride())
            self.assertEqual(x.storage_offset(),y.storage_offset());self.assertEqual(x.dtype,y.dtype)

    def test_compiled_backward_layout_contract(self):
        class Checked(torch.autograd.Function):
            @staticmethod
            def forward(ctx,x):
                view=x[:,:7];ctx.stride=view.stride();ctx.save_for_backward(view)
                return view.square().sum()
            @staticmethod
            def backward(ctx,grad):
                x,=ctx.saved_tensors
                assert x.stride()==ctx.stride
                result=torch.zeros(x.shape[0],8);result[:,:7]=2*x*grad
                return result
        x=torch.randn(3,8,requires_grad=True)
        with stride_preserving_offload():loss=Checked.apply(x)
        loss.backward();expected=torch.zeros_like(x);expected[:,:7]=2*x.detach()[:,:7]
        self.assertTrue(torch.equal(x.grad,expected))

    def test_multistep_loss_gradient_and_optimizer_equal(self):
        torch.manual_seed(0);a=torch.nn.Linear(7,4);b=copy.deepcopy(a)
        opts=[torch.optim.AdamW(m.parameters(),lr=.001) for m in [a,b]]
        for _ in range(3):
            x=torch.randn(8,14)[:,::2]
            for model,opt in zip([a,b],opts):
                opt.zero_grad()
                if model is b:
                    with stride_preserving_offload():loss=model(x).T.square().sum()
                else:loss=model(x).T.square().sum()
                loss.backward();opt.step()
            for p,q in zip(a.parameters(),b.parameters()):
                self.assertTrue(torch.equal(p,q));self.assertTrue(torch.equal(p.grad,q.grad))
                for key in opts[0].state[p]:self.assertTrue(torch.equal(opts[0].state[p][key],opts[1].state[q][key]))


if __name__=='__main__':unittest.main()
