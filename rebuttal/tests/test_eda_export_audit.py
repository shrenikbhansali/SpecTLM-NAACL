import unittest
import torch
from rebuttal.eda_export_audit import frozen_part


class EDAExportTests(unittest.TestCase):
    def test_shared_ffn_slices_and_ordinary_weights(self):
        old = torch.arange(12).reshape(3, 4)
        gate = torch.cat([old, old], 0)
        down = torch.cat([old, old], 1)
        self.assertTrue(torch.equal(frozen_part('layers.0.mlp.gate_proj.weight', old, gate), old))
        self.assertTrue(torch.equal(frozen_part('layers.0.mlp.down_proj.weight', old, down), old))
        self.assertTrue(torch.equal(frozen_part('fc.weight', old, old), old))
        with self.assertRaises(ValueError):
            frozen_part('fc.weight', old, gate)
