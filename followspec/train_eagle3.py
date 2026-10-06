"""Operator-only paired EAGLE-3 training entry point; dry-run never loads models.

Requires resolved matched configs and audited B5 data. Native B6 acceptance
passed; production data and research-decision prerequisites remain enforced.
"""
import argparse
from contextlib import contextmanager
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
from followspec.configs import check_matched
from followspec.paired_data import file_sha

ROOT=Path(__file__).resolve().parents[1]
BACKEND='261a82dd44ca05ff73006938c0614111bb2dd2b7'


def ensure_unpaused(start=ROOT):
    for root in (Path(start).resolve(),*Path(start).resolve().parents):
        for relative in ('EXPERIMENTS_PAUSED.json','tlm-spec-maintenance/EXPERIMENTS_PAUSED.json'):
            if (root/relative).exists():raise RuntimeError(f'Experiments paused: {root/relative}')


def validate_training_layout(config,manifest):
    algorithm=config.get('algorithm','eagle3')
    if algorithm not in {'eagle3','dflash'}:raise ValueError('unsupported training algorithm')
    if algorithm=='dflash' and manifest.get('schema')!='followspec_online_tokens_v1':raise ValueError('DFlash requires audited online raw data')
    layout,unit=('dflash_raw','raw sequence tokens') if algorithm=='dflash' else ('eagle_shift','shifted sequence tokens')
    if manifest.get('sequence_layout','eagle_shift')!=layout or manifest.get('token_budget_unit','shifted sequence tokens')!=unit:
        raise ValueError('training algorithm and data layout differ')


def resolve_plan(config,manifest,seed):
    if config.get('backend_revision')!=BACKEND:raise ValueError('wrong backend revision')
    for key in ('initialization_revision','token_budget','optimizer_steps'):
        if not config.get(key):raise ValueError(f'resolved {key} required; no inferred research settings')
    if not re.fullmatch('[a-f0-9]{40}',config['initialization_revision']):raise ValueError('initialization must be pinned')
    if seed not in config['seeds']:raise ValueError('seed not in matched preset')
    if manifest.get('schema') not in {'followspec_paired_features_v1','followspec_online_tokens_v1'} or manifest.get('arm')!=config['arm']:
        raise ValueError('wrong data schema or arm')
    for key in ('token_budget','optimizer_steps','initialization_revision'):
        if manifest.get(key)!=config[key]:raise ValueError(f'data/config {key} mismatch')
    validate_training_layout(config,manifest)
    return dict(training_config=config,seed=seed,backend_revision=BACKEND,
                evaluation_engine_version='0.31.0',dry_run=True,
                feature_capture='online' if manifest['schema']=='followspec_online_tokens_v1' else 'offline')


def write(path,data):
    with Path(path).open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')


@contextmanager
def owned_output(out,rank,barrier):
    """Write failures only after this launch has acquired its output directory."""
    owned=False
    try:
        if rank==0:
            out.mkdir(parents=True,exist_ok=False)
            owned=True
        barrier()
        owned=True  # Other ranks join only after rank zero created this run.
        yield
    except BaseException as error:
        if owned and out.is_dir() and not (out/f'failure.rank{rank}.json').exists():
            write(out/f'failure.rank{rank}.json',dict(error_type=type(error).__name__,error=str(error)))
        raise


def run(a,plan,manifest):
    ensure_unpaused();ensure_unpaused(Path.cwd())
    from speculators.version import git_commit
    if git_commit!=BACKEND:raise RuntimeError('installed speculators source differs from lock')
    import torch
    from torch.utils.data import DataLoader
    from speculators import SpeculatorModel,SpeculatorModelConfig
    from speculators.losses import resolve_loss_config
    from speculators.train.distributed import maybe_setup_distributed,maybe_destroy_distributed,get_dp_rank,get_dp_size,get_rank,get_local_rank
    from speculators.train.distributed_batch_sampler import MultipackDistributedBatchSamplerV2
    from speculators.train.trainer import Trainer,TrainerConfig
    from followspec.eagle3_extension import install_follow_spec
    from followspec.paired_data import PairedFeatureDataset,PairedCollator,shift_paired
    from atlas.generate_magpie import validate_hardware
    cfg=plan['training_config']
    algorithm=cfg.get('algorithm','eagle3')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip():
        raise RuntimeError('commit tracked source before launching')
    if not manifest.get('data_acceptance_passed') or not manifest.get('sample_mask_audit'):
        raise ValueError('B5 feature and decoded mask acceptance required')
    if manifest.get('acceptance_only'):raise ValueError('production trainer refuses acceptance-only corpora')
    if not Path(a.base_snapshot).is_dir() or not re.fullmatch('[a-f0-9]{40}',manifest.get('base_revision','')) or Path(a.base_snapshot).name!=manifest['base_revision']:
        raise ValueError('pinned local base snapshot required')
    out=Path(a.output).resolve()
    maybe_setup_distributed()
    rank=get_rank()
    try:
        validate_hardware(torch.cuda.get_device_name(get_local_rank()),False,a.allow_a40_production)
        def barrier():
            if torch.distributed.is_initialized():torch.distributed.barrier()
        with owned_output(out,rank,barrier):
            torch.manual_seed(a.seed)
            plan.update(dry_run=False,code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                data_manifest_sha256=file_sha(a.manifest),base_revision=manifest['base_revision'],
                base_snapshot_files_sha256={str(p.relative_to(a.base_snapshot)):file_sha(p) for p in Path(a.base_snapshot).rglob('*') if p.is_file() and '.cache' not in p.parts},
                versions={name:importlib.metadata.version(name) for name in ('speculators','torch','transformers','hs-connectors','peft')},
                world_size=get_dp_size(),gpu_type=torch.cuda.get_device_name(get_local_rank()),
                allow_a40_production=a.allow_a40_production,drafter_snapshot=a.drafter_snapshot,
                target_attention='eager',torch_compile_disable=os.environ.get('TORCH_COMPILE_DISABLE'),
                loss_implementation='fused',data_loader_workers=0)
            if rank==0:write(out/'config.json',plan)
            ensure_unpaused()
            initialization=a.drafter_snapshot or cfg['initialization']
            if a.drafter_snapshot and Path(a.drafter_snapshot).name!=cfg['initialization_revision']:raise ValueError('drafter snapshot pin mismatch')
            from atlas.run_cell import read_drafter_config
            from atlas.covariates import tap_layers
            base_config=json.loads((Path(a.base_snapshot)/'config.json').read_text())
            if algorithm=='dflash':
                from followspec.dflash_loader import load_released_dflash
                from followspec.dflash_extension import install_follow_spec_dflash,prepare_block_sample
                if not a.drafter_snapshot:raise ValueError('DFlash requires a pinned local released snapshot')
                model=load_released_dflash(initialization,a.base_snapshot,device='cpu')
                if model.block_size!=cfg['block_size']:raise ValueError('released DFlash block size differs from config')
                model_cfg=model.config;taps=list(model.target_layer_ids);shift=prepare_block_sample;span=model.block_size
                install=install_follow_spec_dflash
            else:
                model_cfg=SpeculatorModelConfig.from_pretrained(initialization,revision=cfg['initialization_revision'])
                model_cfg.speculators_config.verifier.name_or_path=str(Path(a.base_snapshot).resolve())
                taps=tap_layers(read_drafter_config(initialization,cfg['initialization_revision']),base_config['num_hidden_layers'])
                model_cfg.eagle_aux_hidden_state_layer_ids=taps
                model=SpeculatorModel.from_pretrained(initialization,revision=cfg['initialization_revision'],config=model_cfg,torch_dtype=torch.float32)
                shift=shift_paired;span=cfg['ttt_steps'];install=install_follow_spec
            install(model,beta=cfg['beta'],delta_lambda=cfg['delta_lambda'],top_k=cfg['top_k'],
                shared_verifier_head=manifest.get('shared_verifier_head',False))
            model.register_forward_pre_hook(lambda *_:ensure_unpaused())
            def record_metrics(module,args,result):
                metrics={k:float(v.detach().cpu()) for k,v in result[2].items() if getattr(v,'numel',lambda:0)()==1}
                with (out/f'training_metrics.rank{rank}.jsonl').open('a') as f:f.write(json.dumps(metrics,allow_nan=False)+'\n')
            model.register_forward_hook(record_metrics)
            bank=None
            if plan['feature_capture']=='online':
                from transformers import AutoModelForCausalLM
                from followspec.online_bank import FrozenAdapterBank
                from followspec.token_data import OnlineResponseDataset
                target=AutoModelForCausalLM.from_pretrained(a.base_snapshot,local_files_only=True,trust_remote_code=False,
                    torch_dtype=torch.bfloat16,attn_implementation='eager').to(get_local_rank())
                tokens=torch.arange(len(model.d2t))+model.d2t.cpu() if model.d2t is not None else torch.arange(base_config['vocab_size'])
                bank=FrozenAdapterBank(target,manifest['registry'],taps,tokens,pause_check=ensure_unpaused)
            loaders={}
            for split in ('train','val'):
                if bank is not None:
                    ds=OnlineResponseDataset(manifest,split=split,bank=bank,shift=shift,noise_std=cfg['noise_std'] if split=='train' else 0.)
                else:
                    ds=PairedFeatureDataset(a.manifest,split=split,allowed_targets=manifest['allowed_targets'],
                        forbidden_hashes=set(manifest['forbidden_prompt_hashes']),noise_std=cfg['noise_std'] if split=='train' else 0.)
                sampler=MultipackDistributedBatchSamplerV2(batch_max_length=cfg['total_seq_len'],lengths=ds.approx_lengths,
                    num_replicas=get_dp_size(),rank=get_dp_rank(),seed=a.seed)
                collate=PairedCollator(cfg['total_seq_len'],model.config.transformer_layer_config.hidden_size,
                    len(taps),span)
                loaders[split]=DataLoader(ds,batch_sampler=sampler,collate_fn=collate,num_workers=0)
                if split=='train':
                    if sum(ds.approx_lengths)!=cfg['token_budget']:raise ValueError('actual training token count mismatch')
                    if len(loaders[split])*cfg['epochs']!=cfg['optimizer_steps']:raise ValueError('actual optimizer step count mismatch')
                    if rank==0:
                        with (out/'per_prompt.jsonl').open('x') as f:
                            for row in ds.rows:f.write(json.dumps(row)+'\n')
            call=(dict(max_anchors=cfg['max_anchors'],gamma=cfg['gamma'],per_position_loss_weight=cfg['per_position_loss_weight'])
                  if algorithm=='dflash' else dict(ttt_steps=cfg['ttt_steps'],ttt_step_loss_decay=cfg['ttt_step_loss_decay']))
            call['loss_config']=resolve_loss_config('kl_div','fused')
            trainer_cfg=TrainerConfig(lr=cfg['lr'],num_epochs=cfg['epochs'],save_path=str(out/'checkpoints'),
                optimizer=cfg['optimizer'],weight_decay=cfg['weight_decay'],scheduler_type=cfg['scheduler'],
                scheduler_warmup_ratio=cfg['warmup_ratio'],scheduler_total_steps=cfg['optimizer_steps'],
                hidden_states_dtype=torch.bfloat16,train_call_kwargs=call,val_call_kwargs=call,resume_from_checkpoint=False)
            trainer=Trainer(model,trainer_cfg,loaders['train'],loaders['val'])
            ensure_unpaused();trainer.run_training()
            if rank==0:
                result=dict(status='trained_pending_vllm_acceptance',n=len(loaders['train'].dataset),token_budget=cfg['token_budget'],
                            optimizer_steps=trainer.global_step,checkpoints=str(out/'checkpoints'),B2_acceptance='pending')
                write(out/'results.json',result)
                write(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=f"{cfg['arm']} EAGLE-3 seed {a.seed}",
                    landed=__import__('datetime').date.today().isoformat(),status='pilot',what_why='Matched FollowSpec training arm',
                    new='Paired native distillation and normalized centered delta',artifacts=str(out),config_results=result,
                    caveats='Operator must validate exported checkpoint and held-out cells; no research conclusion'))
    finally:maybe_destroy_distributed()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--configs',nargs=4,required=True);p.add_argument('--arm',choices=['FS','MVD','PO-D','PO-T'],required=True)
    p.add_argument('--manifest',required=True);p.add_argument('--base-snapshot',required=True)
    p.add_argument('--drafter-snapshot',help='local snapshot matching the preset initialization revision')
    p.add_argument('--allow-a40-production',action='store_true',help='owner decision D-19; retain matched training defaults')
    p.add_argument('--seed',type=int,required=True);p.add_argument('--output',required=True);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();arms={c['arm']:c for c in [json.loads(Path(path).read_text()) for path in a.configs]}
    check_matched(arms);manifest=json.loads(Path(a.manifest).read_text())
    plan=resolve_plan(arms[a.arm],manifest,a.seed)
    if a.dry_run:print(json.dumps(plan,indent=2));return
    run(a,plan,manifest)

if __name__=='__main__':main()
