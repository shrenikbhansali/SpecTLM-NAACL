"""Bounded real PEFT adapter-switch test for the online B5 loader."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import torch
from safetensors import safe_open
from transformers import AutoModelForCausalLM,AutoTokenizer
from atlas.run_cell import sha256,write_new
from atlas.generate_magpie import unpaused
from atlas.covariates import tap_layers
from followspec.online_bank import FrozenAdapterBank


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['base','drafter','registry','responses','output']:p.add_argument('--'+key,required=True)
    a=p.parse_args();unpaused()
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 check required')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit source first')
    registry=json.loads(Path(a.registry).read_text());assert len(registry)==2
    rows=[json.loads(s) for s in Path(a.responses).read_text().splitlines()];assert len(rows)==5
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    cfg=dict(base=a.base,base_revision=Path(a.base).name,drafter=a.drafter,drafter_revision=Path(a.drafter).name,
        registry=registry,registry_sha256=sha256(a.registry),responses=a.responses,response_sha256=sha256(a.responses),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),acceptance_only=True,
        generation_engine='0.31.0',gpu_type=torch.cuda.get_device_name(0),seed=0,K=None)
    write_new(out/'config.json',cfg)
    try:
        torch.manual_seed(0)
        model=AutoModelForCausalLM.from_pretrained(a.base,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda')
        before_embed=model.model.embed_tokens.weight
        with safe_open(str(Path(a.drafter)/'model.safetensors'),framework='pt',device='cpu') as f:d2t=f.get_tensor('d2t')
        taps=tap_layers(json.loads((Path(a.drafter)/'config.json').read_text()),model.config.num_hidden_layers)
        bank=FrozenAdapterBank(model,registry,taps,torch.arange(len(d2t))+d2t)
        ids=torch.tensor(rows[0]['input_ids']);mask=torch.tensor(rows[0]['loss_mask'])
        reference=bank.capture('base',ids,mask);base_features=reference['hidden_states'].cpu();base_labels=reference['child_target_logits'].cpu();del reference
        names=list(registry);observed=[];first=None
        for name in [names[0],names[1],names[0]]:
            unpaused();raw=bank.capture(name,ids,mask)
            assert bank.base is model and bank.resident_adapters==1
            assert model.model.embed_tokens.weight is before_embed
            assert torch.equal(raw['base_hidden_states'].cpu(),base_features)
            assert torch.equal(raw['base_target_logits'].cpu(),base_labels)
            assert not torch.equal(raw['hidden_states'].cpu(),base_features)
            if first is None:first=raw['hidden_states'].cpu()
            elif len(observed)==2:assert torch.equal(first,raw['hidden_states'].cpu())
            observed.append(dict(target=name,resident_adapters=bank.resident_adapters,base_exact=True,child_nonzero=True))
            del raw
        base_again=bank.capture('base',ids,mask)
        assert torch.equal(base_again['hidden_states'].cpu(),base_features)
        assert torch.equal(base_again['child_target_logits'].cpu(),base_labels)
        assert all(not x.requires_grad and x.grad is None for x in bank.model.parameters())
        tok=AutoTokenizer.from_pretrained(a.base,local_files_only=True)
        with (out/'decoded_mask_audit.jsonl').open('x') as f:
            for r in rows:
                assert r['loss_mask']==[False]*r['response_start']+[True]*(len(r['input_ids'])-r['response_start'])
                f.write(json.dumps(dict(sample_id=r['sample_id'],decoded_prompt=tok.decode(r['prompt_token_ids']),
                    decoded_answer=tok.decode(r['completion_token_ids']),loss_mask=r['loss_mask'],response_start=r['response_start']))+'\n')
        with (out/'per_prompt.jsonl').open('x') as f:
            for r in observed:f.write(json.dumps(r)+'\n')
        result=dict(passed=True,n_adapters=2,n_switch_sequence=3,reloaded_child_exact=True,base_exact_after_all_switches=True,
            one_target_weight_copy=True,max_resident_adapters=1,wall_s=time.perf_counter()-start,
            max_gpu_allocated_gb=torch.cuda.max_memory_allocated()/1024**3,scope='loader acceptance only; no training')
        write_new(out/'results.json',result)
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
            what_why='Bounded bank adapter switching for online training targets',new='Pinned PEFT unload/reload preserves base and child features',
            artifacts=str(out.resolve()),config_results=dict(config=cfg,results=result),caveats=result['scope']))
        print(json.dumps(result))
    except Exception as e:write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
