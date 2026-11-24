"""CPU-only E4 step-zero exports, using the tested FIX24 loader and EDA fold."""
import argparse
import gc
import json
from pathlib import Path
import subprocess

import torch


def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    from speculators import SpeculatorModel,SpeculatorModelConfig
    from followspec.missing_embedding import fill_missing_embedding
    from followspec.family_repair import configure_variant,merged_state
    from followspec.checkpoint_storage import shared_export
    initial=a.workspace/'artifacts/P3_D50_20261009_0200/E1-official-native-v2-t0'
    target=a.workspace/'rebuttal/models/r1/6a6f4aa4197940add57724a7707d069478df56b1'
    for width in [4096,14336]:
        torch.manual_seed(0)
        config=SpeculatorModelConfig.from_pretrained(initial,local_files_only=True)
        config.speculators_config.verifier.name_or_path=str(target)
        model=SpeculatorModel.from_pretrained(initial,config=config,local_files_only=True,torch_dtype=torch.float32)
        embedding=fill_missing_embedding(model,initial,target)
        proof=configure_variant(model,'eda_private',private_width=width)
        # Match trained export precision; preserve the untouched release tensors.
        model.to(dtype=torch.bfloat16)
        dest=a.output/f'width-{width}'
        mutable={'layers.0.mlp.'+n+'.weight' for n in ['gate_proj','up_proj','down_proj']}
        shared_export(model,dest,a.workspace/'rebuttal/shared-shards',merged_state(model),mutable,350)
        report=dict(seed=0,initialization=str(initial),target=str(target),embedding=embedding,parameters=proof,
                    optimizer_steps=0,code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                    purpose='E4 untrained acceptance sanity; no training or evaluation data used')
        (dest/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(output=str(dest),parameters=proof['trainable_parameters'])),flush=True)
        del model;gc.collect()


if __name__=='__main__':main()
