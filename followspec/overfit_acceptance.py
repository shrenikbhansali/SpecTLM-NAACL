"""B6 acceptance only: native training on exactly64 bounded bank responses.

Three fixed epochs, native8192 batching and the starting FS optimizer/loss.
The before/after probe reuses training data to test overfitting, not held-out
generalization. This command cannot consume production data or launch a sweep.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
from atlas.run_cell import sha256,write_new
from followspec.train_eagle3 import BACKEND,ensure_unpaused


def validate_corpus(rows):
    if len(rows)!=64 or len({r['sample_id'] for r in rows})!=64 or len({r['prompt_sha256'] for r in rows})!=64:
        raise ValueError('exactly64 distinct training responses required')
    if any(not r['acceptance_only'] or r['split']!='train' or not 1<=len(r['completion_token_ids'])<=64 for r in rows):
        raise ValueError('bounded acceptance-only training responses required')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['base','drafter','registry','responses','sample-audit','output']:p.add_argument('--'+key,required=True)
    a=p.parse_args();ensure_unpaused();ensure_unpaused(Path.cwd())
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit first')
    from followspec.token_data import response_run,build_manifest,OnlineResponseDataset
    rows,source,_=response_run(a.responses);validate_corpus(rows)
    audit=json.loads(Path(a.sample_audit).read_text())
    if audit.get('responses_sha256')!=sha256(Path(a.responses)/'per_prompt.jsonl') or audit.get('sample_ids')!=[r['sample_id'] for r in rows[:5]] or not audit.get('decoded_and_masks_inspected'):
        raise ValueError('five decoded samples and masks must be inspected first')
    if source['base_revision']!=Path(a.base).name:raise ValueError('base snapshot mismatch')
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForCausalLM
    from speculators import SpeculatorModel,SpeculatorModelConfig
    from speculators.version import git_commit
    from speculators.losses import resolve_loss_config
    from speculators.train.trainer import Trainer,TrainerConfig
    from speculators.train.distributed_batch_sampler import MultipackDistributedBatchSamplerV2
    from atlas.covariates import tap_layers
    from followspec.configs import load_presets
    from followspec.online_bank import FrozenAdapterBank
    from followspec.paired_data import PairedCollator,shift_paired
    from followspec.eagle3_extension import install_follow_spec
    if git_commit!=BACKEND:raise ValueError('wrong native backend')
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('D-19 acceptance requires A40')
    cfg=load_presets()['FS'];epochs=3;seed=0
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();torch.manual_seed(seed)
    config=vars(a)|dict(acceptance_only=True,n=64,epochs=epochs,seed=seed,K=None,training_config=cfg,
        base_revision=Path(a.base).name,initialization_revision=Path(a.drafter).name,backend_revision=BACKEND,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        gpu_type=torch.cuda.get_device_name(0),response_config_sha256=sha256(Path(a.responses)/'config.json'),
        response_records_sha256=sha256(Path(a.responses)/'per_prompt.jsonl'),registry_sha256=sha256(a.registry),
        sample_audit_sha256=sha256(a.sample_audit),generation_engine='0.31.0',
        versions={n:importlib.metadata.version(n) for n in ['torch','transformers','speculators','peft']},
        loss_implementation='fused',drafter_attention='simple_flex_attention',target_attention='eager',
        probe='same64 training responses, fixed sampler order, no noise; not held-out evaluation',
        scope='B6 overfit and native checkpoint acceptance; does not resolve production B5 budgets or owner defaults')
    write_new(out/'config.json',config)
    try:
        registry=json.loads(Path(a.registry).read_text())
        refs=[dict(run=a.responses,record_index=i,child_id=r['generation_target'],pair_id=r['sample_id'],split='train') for i,r in enumerate(rows)]
        manifest=build_manifest('FS',refs,registry=registry,base_revision=Path(a.base).name,
            initialization_revision=Path(a.drafter).name,allow_acceptance=True)
        write_new(out/'manifest.json',manifest)
        target=AutoModelForCausalLM.from_pretrained(a.base,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda')
        model_cfg=SpeculatorModelConfig.from_pretrained(a.drafter,local_files_only=True)
        model_cfg.speculators_config.verifier.name_or_path=a.base
        model_cfg.eagle_aux_hidden_state_layer_ids=tap_layers(json.loads((Path(a.drafter)/'config.json').read_text()),target.config.num_hidden_layers)
        model_cfg.transformer_layer_config._attn_implementation='simple_flex_attention'
        model=SpeculatorModel.from_pretrained(a.drafter,config=model_cfg,local_files_only=True,torch_dtype=torch.float32)
        bank=FrozenAdapterBank(target,registry,model_cfg.eagle_aux_hidden_state_layer_ids,
            torch.arange(len(model.d2t))+model.d2t.cpu(),pause_check=ensure_unpaused)
        install_follow_spec(model,beta=cfg['beta'],delta_lambda=cfg['delta_lambda'],top_k=cfg['top_k'],shared_verifier_head=False)
        keys=set(model.state_dict());initial_fc=model.fc.weight.detach().clone()
        def capture_metrics(module,args,result):
            if not torch.isfinite(result[1]):raise ValueError('nonfinite native loss')
            terms={k:float(v.detach().cpu()) for k,v in result[2].items() if getattr(v,'numel',lambda:0)()==1}
            with (out/'metrics.jsonl').open('a') as f:f.write(json.dumps(dict(training=module.training,terms=terms),allow_nan=False)+'\n')
        model.register_forward_pre_hook(lambda *_:ensure_unpaused())
        model.register_forward_hook(capture_metrics)
        def loader(noise):
            ds=OnlineResponseDataset(manifest,split='train',bank=bank,shift=shift_paired,noise_std=noise,allow_acceptance=True)
            if max(ds.approx_lengths)>cfg['total_seq_len']:raise ValueError('no sample truncation allowed')
            sampler=MultipackDistributedBatchSamplerV2(cfg['total_seq_len'],ds.approx_lengths,1,0,seed=seed)
            if sorted(int(i) for batch in sampler for i in batch)!=list(range(64)):raise ValueError('sampler dropped or duplicated samples')
            return DataLoader(ds,batch_sampler=sampler,collate_fn=PairedCollator(cfg['total_seq_len'],target.config.hidden_size,3,cfg['ttt_steps']),num_workers=0)
        train=loader(cfg['noise_std']);probe=loader(0.)
        call=dict(ttt_steps=cfg['ttt_steps'],ttt_step_loss_decay=cfg['ttt_step_loss_decay'],loss_config=resolve_loss_config('kl_div','fused'))
        steps=epochs*len(train)
        native_cfg=TrainerConfig(lr=cfg['lr'],num_epochs=epochs,save_path=str(out/'checkpoints'),optimizer=cfg['optimizer'],
            weight_decay=cfg['weight_decay'],scheduler_type=cfg['scheduler'],scheduler_warmup_ratio=cfg['warmup_ratio'],
            scheduler_total_steps=steps,hidden_states_dtype=torch.bfloat16,train_call_kwargs=call,resume_from_checkpoint=False)
        trainer=Trainer(model,native_cfg,train,None)
        def evaluate():
            model.eval();values=[]
            with torch.no_grad():
                for batch in probe:
                    batch={k:v.to('cuda') if isinstance(v,torch.Tensor) else v for k,v in batch.items()}
                    with torch.autocast('cuda',dtype=torch.bfloat16):_,loss,_=model(**batch,**call)
                    values.append(float(loss))
            return dict(mean_batch_loss=sum(values)/len(values),batch_losses=values)
        before=evaluate();write_new(out/'before.json',before)
        trainer.run_training()
        after=evaluate();write_new(out/'after.json',after)
        assert after['mean_batch_loss']<before['mean_batch_loss'],'loss did not fall on the fixed64 training probe'
        assert trainer.global_step==steps
        assert all(p.grad is None and not p.requires_grad for p in bank.model.parameters())
        grads=[p.grad for p in model.parameters() if p.grad is not None]
        assert grads and all(torch.isfinite(g).all() for g in grads)
        assert not torch.equal(initial_fc,model.fc.weight.detach().cpu()),'drafter weights did not update'
        assert set(model.state_dict())==keys
        checkpoint=out/'checkpoints'/str(epochs-1)
        assert (checkpoint/'config.json').is_file() and (checkpoint/'model.safetensors').is_file()
        with (out/'per_prompt.jsonl').open('x') as f:
            for r in rows:f.write(json.dumps(dict(sample_id=r['sample_id'],prompt_sha256=r['prompt_sha256'],assistant_tokens=sum(r['loss_mask']),shifted_tokens=len(r['input_ids'])-1))+'\n')
        result=dict(passed=True,n=64,epochs=epochs,optimizer_steps=steps,shifted_tokens=manifest['token_budget'],
            before=before,after=after,loss_decrease=before['mean_batch_loss']-after['mean_batch_loss'],
            frozen_teacher=True,finite_drafter_gradients=True,checkpoint=str(checkpoint.resolve()),
            checkpoint_sha256={p.name:sha256(p) for p in checkpoint.iterdir() if p.suffix in {'.safetensors','.json'}},
            max_gpu_allocated_gb=torch.cuda.max_memory_allocated()/1024**3,wall_s=time.perf_counter()-start,B2_acceptance='pending')
        write_new(out/'results.json',result)
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
            what_why='B6 native64-sample overfit acceptance',new='Online paired frozen bank targets, normalized delta, native Trainer and export',
            artifacts=str(out.resolve()),config_results=dict(config=config,results=result),caveats=config['scope']+'; n=1 acceptance seed, no inferential uncertainty'))
        print(json.dumps(result))
    except BaseException as e:write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
