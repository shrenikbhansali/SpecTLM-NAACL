import unittest
import torch
from followspec.family_repair import configure_variant, merged_state, step_batches, multi_epoch_batches


class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.fc=torch.nn.Linear(6,2,bias=False)
        self.layers=torch.nn.ModuleList([torch.nn.ModuleDict({'q_proj':torch.nn.Linear(2,2,bias=False)})])
        self.lm_head=torch.nn.Linear(2,3,bias=False)
        self.embed_tokens=torch.nn.Embedding(3,2)

    def forward(self,x):return self.lm_head(self.layers[0]['q_proj'](self.fc(x)))


class TrainingExtensionTests(unittest.TestCase):
    def test_decoder_head_lora_freezes_interface_and_merges(self):
        model=Tiny();before={k:v.clone() for k,v in model.state_dict().items()};x=torch.randn(2,6)
        original=model(x).detach();proof=configure_variant(model,'decoder_head_lora',2,4)
        self.assertFalse(model.fc.weight.requires_grad)
        self.assertEqual(proof['trainable_parameters'],2*(2+2+2+3))
        self.assertTrue(all(n.startswith(('layers.','lm_head.')) and '.lora_' in n for n in proof['trainable_names']))
        torch.testing.assert_close(model(x),original)
        for name,p in model.named_parameters():
            if 'lora_B' in name:p.data.normal_()
        restored=Tiny();restored.load_state_dict(merged_state(model))
        torch.testing.assert_close(restored(x),model(x))
        self.assertTrue(torch.equal(restored.fc.weight,before['fc.weight']))

    def test_epochs_preserve_native_order_and_complete_samples(self):
        rows=[{'input_ids':list(range(n))} for n in [4,8,6,7,10,8,3]]
        batches,ends=multi_epoch_batches(rows,4,16,0)
        self.assertEqual(batches,step_batches(rows,len(batches),16,0))
        self.assertEqual(len(ends),4)
        start=0
        for end in ends:
            self.assertEqual(sorted(i for b in batches[start:end] for i in b),list(range(len(rows))))
            self.assertTrue(all(sum(len(rows[i]['input_ids'])-1 for i in b)<=16 for b in batches[start:end]))
            start=end
        self.assertEqual(ends[-1],len(batches))

    def test_bad_epoch_count_and_truncation_rejected(self):
        for epochs,ceiling in [(0,16),(2,1)]:
            with self.assertRaises(ValueError):multi_epoch_batches([{'input_ids':[1,2,3]}],epochs,ceiling,0)


if __name__=='__main__':unittest.main()
