import json
from pathlib import Path
import tempfile
import unittest
import torch
from safetensors.torch import save_file,load_file
from rebuttal.ablate_lora import ablate


class AblationTests(unittest.TestCase):
    def test_exact_weight_restoration_and_other_tensors_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);base=root/'base';trained=root/'trained';base.mkdir();trained.mkdir()
            old={'fc.weight':torch.ones(2,3),'layers.0.q.weight':torch.ones(2,2),'lm_head.weight':torch.ones(3,2),'embed_tokens.weight':torch.ones(5,2)}
            new={k:v+2 if k!='embed_tokens.weight' else v for k,v in old.items()}
            save_file(old,base/'model.safetensors');save_file(new,trained/'trainable.safetensors')
            (trained/'config.json').write_text('{}')
            (trained/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{k:'trainable.safetensors' for k in new}}))
            for mode,restored in [('no_fc',{'fc.weight'}),('fc_only',{'layers.0.q.weight','lm_head.weight'})]:
                out=root/mode
                ablate(trained,base,out,mode,{'fc.weight','layers.0.q.weight','lm_head.weight'})
                index=json.loads((out/'model.safetensors.index.json').read_text())['weight_map']
                self.assertEqual(set(index),set(new))
                # vLLM streams every tensor in selected shards; it does not use
                # weight_map to suppress stale duplicate keys inside a shard.
                seen=[]
                for shard in sorted(set(index.values())):
                    for key in load_file(out/shard):
                        seen.append(key)
                        self.assertEqual(index[key],shard)
                self.assertEqual(len(seen),len(set(seen)))
                self.assertEqual(set(seen),set(index))
                for key,shard in index.items():
                    actual=load_file(out/shard)[key]
                    self.assertTrue(torch.equal(actual,old[key] if key in restored else new[key]))
                self.assertTrue(torch.equal(load_file(trained/'trainable.safetensors')['fc.weight'],new['fc.weight']))
                with self.assertRaises(FileExistsError):ablate(trained,base,out,mode,{'fc.weight'})


if __name__=='__main__':unittest.main()
