"""D50 diagnostic of effective vLLM-loaded weights. No acceptance measurement."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path


def tensor_fingerprint(tensor):
    value = tensor.detach().cpu().contiguous()
    import torch
    return dict(shape=list(value.shape), dtype=str(value.dtype),
                sha256=hashlib.sha256(value.view(torch.uint8).numpy().tobytes()).hexdigest())


def inspect_worker(worker):
    runner = worker.model_runner
    drafter = runner.drafter.model
    config = drafter.config.to_dict()
    # Record concrete submodule attributes as well as HF config: embedding
    # sharing, fused loader mappings, tap semantics and positional settings.
    modules = {}
    for name, module in drafter.named_modules():
        record = {'class': type(module).__module__ + '.' + type(module).__name__}
        for attr in ['eps', 'variance_epsilon', 'head_size', 'rotary_dim',
                     'base', 'is_neox_style', 'scaling_factor', 'norm_before_fc',
                     'norm_output', 'use_aux_hidden_state', 'target_hidden_size',
                     'num_heads', 'num_kv_heads', 'scale']:
            value = getattr(module, attr, None)
            if isinstance(value, (str, int, float, bool)):
                record[attr] = value
        modules[name] = record
    return dict(weights={name: tensor_fingerprint(value)
                         for name, value in drafter.state_dict().items()},
                # Nonpersistent RoPE caches vary in allocated length; config,
                # base and rotary dimension are captured above.
                modules=modules, config=config,
                taps=list(runner.get_model().model.aux_hidden_state_layers))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-config', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--min-free-gb', type=float, default=250.)
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    cfg = json.loads(Path(a.source_config).read_text())
    if cfg['engine_version'] != '0.31.0' or cfg['method'] != 'eagle3':
        raise ValueError('Pinned EAGLE3 config required')
    if a.dry_run:
        print(json.dumps(vars(a) | dict(scope=__doc__)))
        return
    from followspec.disk_guard import require_free
    from atlas.run_cell import ensure_unpaused
    ensure_unpaused(); require_free(a.output, a.min_free_gb)
    import torch
    from vllm import LLM
    if importlib.metadata.version('vllm') != '0.31.0' or 'A40' not in torch.cuda.get_device_name(0):
        raise ValueError('Pinned vLLM and A40 required')
    out = Path(a.output); out.mkdir(parents=True, exist_ok=False)
    (out/'config.json').open('x').write(json.dumps(cfg | dict(diagnostic='loaded drafter state, no acceptance', source_config=a.source_config), indent=2)+'\n')
    llm = LLM(model=cfg['target'], revision=cfg['target_revision'],
              tokenizer_revision=cfg['target_revision'], dtype=cfg['dtype'],
              trust_remote_code=False, seed=0, disable_log_stats=False,
              enable_prefix_caching=False, max_model_len=cfg['max_model_len'],
              gpu_memory_utilization=cfg['gpu_memory_utilization'],
              enable_lora=False, max_lora_rank=64,
              per_request_spec_decode_metrics='detailed',
              speculative_config=dict(model=cfg['drafter'], revision=cfg['drafter_revision'],
                                      method='eagle3', num_speculative_tokens=4))
    values = llm.collective_rpc(inspect_worker)
    (out/'loaded-state.json').open('x').write(json.dumps(values, indent=2)+'\n')
    (out/'results.json').open('x').write(json.dumps(dict(status='diagnostic_complete', workers=len(values)))+'\n')


if __name__ == '__main__':
    main()
