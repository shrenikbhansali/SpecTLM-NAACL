"""Bounded real-target FIX-3 acceptance; no drafter checkpoint is trained."""
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import subprocess
import time
import torch
from safetensors import safe_open
from transformers import AutoModelForCausalLM,AutoTokenizer
from peft import PeftModel
from atlas.run_cell import sha256,write_new
from atlas.generate_magpie import unpaused,validate_hardware
from followspec.online_capture import OnlinePairCapture,route_arm


def read(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['base-cell','child-cell','drafter','output']:p.add_argument('--'+name,required=True)
    a=p.parse_args();unpaused()
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit first')
    validate_hardware(torch.cuda.get_device_name(0),True)
    bc=json.loads((Path(a.base_cell)/'config.json').read_text());cc=json.loads((Path(a.child_cell)/'config.json').read_text())
    if any(c['engine_version']!='0.31.0' or not c['acceptance_only'] for c in [bc,cc]):raise ValueError('bounded pinned generation required')
    if bc['prompt_sha256']!=cc['prompt_sha256']:raise ValueError('different training queries')
    base_rows=read(Path(a.base_cell)/'per_prompt.jsonl');child_rows=read(Path(a.child_cell)/'per_prompt.jsonl')
    if len(base_rows)!=5 or len(child_rows)!=5:raise ValueError('exactly five samples required')
    for directory in [a.base_cell,a.child_cell]:
        if (Path(directory)/'failure.json').exists() or not (Path(directory)/'results.json').exists():raise ValueError('incomplete generation')
    with safe_open(str(Path(a.drafter)/'model.safetensors'),framework='pt',device='cpu') as f:d2t=f.get_tensor('d2t')
    tokens=torch.arange(len(d2t))+d2t
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    cfg=dict(acceptance_only=True,base=bc['target'],base_revision=bc['base_revision'],adapter=cc['adapter'],adapter_revision=cc['derivative_revision'],
        drafter=a.drafter,drafter_revision=Path(a.drafter).name,code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256=sha256(__file__),online_source_sha256=sha256(Path(__file__).parents[1]/'online_capture.py'),
        source_configs_sha256={s:sha256(Path(s)/'config.json') for s in [a.base_cell,a.child_cell]},
        source_records_sha256={s:sha256(Path(s)/'per_prompt.jsonl') for s in [a.base_cell,a.child_cell]},
        prompt_sha256=cc['prompt_sha256'],seed=101,K=None,engine_version='0.31.0 generation; offline Transformers target',
        gpu_type=torch.cuda.get_device_name(0),dtype='bfloat16',taps=[2,16,29],feature_tolerance=dict(atol=0,rtol=0),
        scope='FIX-3 feature-provider acceptance, not B6 overfit or final B5 arm budgets')
    write_new(out/'config.json',cfg);start=time.perf_counter();torch.manual_seed(101)
    try:
        target=AutoModelForCausalLM.from_pretrained(bc['target'],local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda')
        model=PeftModel.from_pretrained(target,cc['adapter'],autocast_adapter_dtype=False)
        capture=OnlinePairCapture(model,cfg['taps'],tokens)
        parameter_ids={k:id(v) for k,v in model.named_parameters()}
        tokenizer=AutoTokenizer.from_pretrained(bc['target'],local_files_only=True)
        reports=[];audits=[];arm_counts={}
        def fresh(raw,base):
            seen=[];handle=target.model.norm.register_forward_pre_hook(lambda m,args:seen.append(args[0].detach()))
            try:
                with (model.disable_adapter() if base else nullcontext()),torch.no_grad():
                    output=target.model(input_ids=raw['input_ids'][None],output_hidden_states=True,use_cache=False)
                    features=torch.cat([output.hidden_states[i][0] for i in cfg['taps']],-1)
                return features,seen[0][0]
            finally:handle.remove()
        with (out/'per_prompt.jsonl').open('x') as record:
            for index,row in enumerate(child_rows):
                ids=torch.tensor(row['input_ids']);mask=torch.tensor(row['loss_mask']);raw=capture(ids,mask)
                displacement=float((raw['hidden_states'].float()-raw['base_hidden_states'].float()).norm())
                assert displacement>0
                if index<3:
                    for base in [False,True]:
                        features,last=fresh(raw,base);prefix='base_' if base else ''
                        torch.testing.assert_close(features,raw[prefix+'hidden_states'],atol=0,rtol=0)
                        torch.testing.assert_close(last,raw[prefix+'verifier_last_hidden_states'],atol=0,rtol=0)
                # Test a consuming drafter layer's autograd, without training a checkpoint.
                head=torch.nn.Linear(raw['hidden_states'].shape[-1],1,bias=False,device='cuda',dtype=torch.bfloat16)
                head(raw['hidden_states']).float().square().mean().backward()
                assert head.weight.grad is not None and torch.isfinite(head.weight.grad).all()
                assert all(p.grad is None for p in model.parameters())
                for arm in ['FS','MVD','PO-T']:
                    routing=route_arm(arm,row['generation_target'],row['generation_target'])
                    arm_counts[arm]=arm_counts.get(arm,0)+int(mask.sum())
                    audits.append(dict(arm=arm,sample_id=row['sample_id'],feature_target=routing,
                        decoded_prompt=tokenizer.decode(ids[:row['response_start']]),decoded_answer=tokenizer.decode(ids[row['response_start']:]),
                        response_start=row['response_start'],loss_mask=row['loss_mask'],tokens=len(ids),assistant_tokens=int(mask.sum())))
                report=dict(sample_id=row['sample_id'],feature_difference_l2=displacement,assistant_tokens=int(mask.sum()),
                    fresh_pass_exact=index<3,target_gradients=False,drafter_layer_backward=True)
                record.write(json.dumps(report)+'\n');record.flush();reports.append(report);del raw,head
            for row in base_rows:
                ids=torch.tensor(row['input_ids']);mask=torch.tensor(row['loss_mask']);raw=capture(ids,mask,feature_target=route_arm('PO-D','base',cc['derivative_id']))
                assert torch.equal(raw['hidden_states'],raw['base_hidden_states'])
                assert torch.equal(raw['child_target_logits'],raw['base_target_logits'])
                arm_counts['PO-D']=arm_counts.get('PO-D',0)+int(mask.sum())
                audits.append(dict(arm='PO-D',sample_id=row['sample_id'],feature_target='base',decoded_prompt=tokenizer.decode(ids[:row['response_start']]),
                    decoded_answer=tokenizer.decode(ids[row['response_start']:]),response_start=row['response_start'],loss_mask=row['loss_mask'],
                    tokens=len(ids),assistant_tokens=int(mask.sum())))
                del raw
        # Actual zero update through PEFT, in memory only. Restore all B factors.
        factors=[m.weight for module in model.modules() if hasattr(module,'lora_B') for m in module.lora_B.values()]
        assert factors;copies=[p.detach().clone() for p in factors]
        try:
            with torch.no_grad():
                for p in factors:p.zero_()
            for row in child_rows[:3]:
                raw=capture(torch.tensor(row['input_ids']),torch.tensor(row['loss_mask']))
                for key in ['hidden_states','verifier_last_hidden_states']:
                    assert torch.equal(raw[key],raw['base_'+key])
                assert torch.equal(raw['child_target_logits'],raw['base_target_logits'])
        finally:
            with torch.no_grad():
                for p,original in zip(factors,copies,strict=True):p.copy_(original)
        assert parameter_ids=={k:id(v) for k,v in model.named_parameters()}
        assert not target.model.norm._forward_pre_hooks
        with (out/'decoded_mask_audit.jsonl').open('x') as f:
            for r in audits:f.write(json.dumps(r)+'\n')
        result=dict(passed=True,n_child=5,n_base=5,fresh_pair_checks=3,zero_update_exact_checks=3,
            one_target_weight_copy=True,target_gradients=False,arm_assistant_tokens=arm_counts,
            full_arm_budget_matching='pending B5; these tiny differing response lengths are reported, not called matched',
            feature_shards_written=0,max_gpu_allocated_gb=torch.cuda.max_memory_allocated()/1024**3,wall_s=time.perf_counter()-start,
            source_response_runs=[a.base_cell,a.child_cell],records=reports)
        write_new(out/'results.json',result)
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
            what_why='Online paired target provider acceptance on an A40',new='One frozen target, exact paired prefixes, no feature shards',
            artifacts=str(out.resolve()),config_results=dict(config=cfg,results=result),caveats=cfg['scope']))
        print(json.dumps(result))
    except Exception as e:write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
