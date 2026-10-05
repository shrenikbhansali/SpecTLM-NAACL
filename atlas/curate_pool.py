"""Curate draft pools without loading models; stage pinned Hub files separately.

No generation, training, or inference is performed. All outputs are append-only or
created exclusively. Authentication is anonymous unless a verified read token is
explicitly requested. The owner-authorized write-capable token is read-only in this tool. Run `python -m atlas.curate_pool --help`.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import random
import re
import shutil

BASES = {'llama': ('meta-llama/Llama-3.1-8B-Instruct', '2025-07-01'),
         'qwen3': ('Qwen/Qwen3-8B', '2026-01-01')}
RELATIONS = ('adapter', 'finetune', 'merge', 'quantized')
LICENSES = {'apache-2.0', 'mit', 'bsd-2-clause', 'bsd-3-clause', 'llama3.1',
            'cc-by-4.0', 'cc-by-sa-4.0', 'cc-by-nc-4.0', 'cc-by-nc-sa-4.0',
            'cc0-1.0', 'wtfpl', 'unlicense'}
FIELDS = ('model_id', 'revision', 'base_id', 'relation', 'created_at', 'author',
          'license', 'downloads', 'gated', 'file_formats', 'size_bytes', 'r',
          'lora_alpha', 'use_rslora', 'target_modules', 'type',
          'tokenizer_identical', 'template_changed', 'pool', 'exclusion', 'files',
          'tokenizer_sha256', 'template_sha256', 'tokenizer_source', 'base_revision')
JSON_FIELDS = {'file_formats', 'target_modules', 'files', 'gated', 'tokenizer_identical',
               'template_changed', 'use_rslora'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def event(path, **kwargs):
    with Path(path).open('a') as f:
        f.write(json.dumps({'time': utc(), **kwargs}, sort_keys=True) + '\n')
    print(json.dumps(kwargs, sort_keys=True), flush=True)


def assign_pools(rows, cutoff):
    cut = datetime.fromisoformat(cutoff).replace(tzinfo=timezone.utc)
    for r in rows:
        created = datetime.fromisoformat(r['created_at'].replace('Z', '+00:00'))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        r['pool'] = ('excluded' if r['exclusion'] else
                     'bank' if created < cut and r['type'] == 'lora_adapter' else
                     'precutoff_atlas' if created < cut else 'test')
    authors = {r['author'] for r in rows if r['pool'] == 'bank'}
    for r in rows:
        if r['pool'] == 'test' and r['author'] in authors:
            r['pool'], r['exclusion'] = 'excluded', 'author_in_bank'
    return rows


def stratify(rows, count):
    groups = defaultdict(list)
    for row in rows:
        if not row['exclusion']:
            groups[row['type']].append(row)
    for group in groups.values():
        group.sort(key=lambda r: (-int(r['downloads']), r['model_id']))
    result = []
    while len(result) < count:
        added = False
        for key in sorted(groups):
            if groups[key] and len(result) < count:
                result.append(groups[key].pop(0)); added = True
        if not added:
            break
    return result


def validate(rows):
    seen = set()
    for r in rows:
        missing = set(FIELDS) - r.keys()
        if missing:
            raise ValueError(f'missing fields: {sorted(missing)}')
        if r['model_id'] in seen:
            raise ValueError(f'duplicate ID: {r["model_id"]}')
        seen.add(r['model_id'])
        if not re.fullmatch('[0-9a-f]{40}', r['revision']):
            raise ValueError(f'unpinned revision: {r["model_id"]}')
        if not r['author'] or not r['created_at']:
            raise ValueError('missing author or creation date')
        if not r['exclusion'] and (r['license'] not in LICENSES or
                                   r['tokenizer_identical'] is not True):
            raise ValueError('unverified license/tokenizer in eligible row')
    bank = {r['author'] for r in rows if r['pool'] == 'bank'}
    test = {r['author'] for r in rows if r['pool'] == 'test'}
    if bank & test:
        raise ValueError('author overlap between pools')
    return {key: dict(sorted(Counter(str(r[key]) for r in rows).items()))
            for key in ('pool', 'type')}


def write_csv(path, rows, fields=FIELDS):
    with Path(path).open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict, bool))
                             or v is None else v for k, v in row.items()})


def read_csv(path):
    with Path(path).open() as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for key in JSON_FIELDS:
            if r.get(key):
                r[key] = json.loads(r[key])
        for key in ('size_bytes', 'downloads'):
            r[key] = int(r[key])
    return rows


def verify_downloads(rows, log):
    entries = {}
    if Path(log).exists():
        for line in Path(log).read_text().splitlines():
            e = json.loads(line)
            if e.get('status') == 'complete':
                entries[e['model_id']] = e
    for r in rows:
        e = entries.get(r['model_id'])
        if not e or e['revision'] != r['revision']:
            raise ValueError(f'missing or wrong revision: {r["model_id"]}')
        root = Path(e['path'])
        for spec in r['files']:
            path = root / spec['path']
            if not path.is_file() or path.stat().st_size != spec['size']:
                raise ValueError(f'missing file/size mismatch: {path}')
    return len(rows)


def safe_token(use_read_token=False, use_existing_token=False):
    if not use_read_token and not use_existing_token:
        return False
    from huggingface_hub import HfApi, get_token
    token = get_token()
    if not token or (not use_existing_token and HfApi(token=token).whoami()['auth']['accessToken']['role'] != 'read'):
        raise ValueError('A verified read-only HF token is required; no token value is logged')
    return token


class Hub:
    def __init__(self, cache, token=False):
        from huggingface_hub import HfApi
        self.api, self.cache, self.token = HfApi(token=token), str(cache), token

    def file(self, model, revision, name, required=False):
        from huggingface_hub import hf_hub_download
        from huggingface_hub.errors import EntryNotFoundError
        try:
            path = hf_hub_download(model, name, revision=revision,
                                   cache_dir=self.cache, token=self.token)
            return Path(path).read_bytes()
        except EntryNotFoundError:
            if required:
                raise
            return None

    def meta(self, model, revision=None):
        return self.api.model_info(model, revision=revision, files_metadata=True)


def metadata(hub, model, revision):
    config_raw = hub.file(model, revision, 'config.json')
    tok = hub.file(model, revision, 'tokenizer.json')
    tc = hub.file(model, revision, 'tokenizer_config.json')
    jinja = hub.file(model, revision, 'chat_template.jinja')
    cfg = json.loads(config_raw) if config_raw else {}
    tokcfg = json.loads(tc) if tc else {}
    template = jinja or json.dumps(tokcfg.get('chat_template'), sort_keys=True).encode()
    return cfg, tok, template


def classify(relations, cfg, card, model_id):
    if 'adapter' in relations:
        return 'lora_adapter'
    quant = cfg.get('quantization_config', {})
    method = str(quant.get('quant_method', '')).lower()
    if method in {'fp8', 'fbgemm_fp8'} or (method == 'compressed-tensors' and
                                         'float' in json.dumps(quant).lower()):
        return 'quantized_fp8'
    if method in {'awq', 'gptq'}:
        return 'quantized_' + method
    if 'abliterat' in (card + model_id).lower():
        return 'abliterated'
    if re.search(r'\b(RL|GRPO|PPO|DPO)\b', card, re.I):
        return 'rl_tuned'
    if 'merge' in relations:
        return 'merge'
    if 'finetune' in relations:
        return 'full_finetune'
    return 'other'


def inspect_candidate(hub, model_id, relations, base_id, base_revision, base_meta):
    info = hub.meta(model_id)
    files = [{'path': s.rfilename, 'size': s.size, 'blob_id': s.blob_id,
              'sha256': s.lfs.sha256 if s.lfs else None} for s in info.siblings]
    card_data = info.card_data.to_dict() if info.card_data else {}
    license = card_data.get('license', '')
    if not isinstance(license, str):
        license = json.dumps(license)
    r = dict.fromkeys(FIELDS, '')
    r.update(model_id=model_id, revision=info.sha, base_id=base_id,
             base_revision=base_revision, relation=','.join(sorted(relations)),
             created_at=info.created_at.isoformat(), author=model_id.split('/')[0],
             license=license, downloads=info.downloads or 0, gated=info.gated,
             file_formats=sorted({Path(s['path']).suffix.lstrip('.') for s in files}),
             size_bytes=sum(s['size'] or 0 for s in files), files=files,
             tokenizer_identical=False, template_changed=None, type='other')
    if license not in LICENSES:
        r['exclusion'] = 'unknown_or_unreviewed_license'; return r
    weights = [s for s in files if s['path'].endswith(('.safetensors', '.bin'))]
    if not weights:
        r['exclusion'] = 'no_standard_weights'; return r
    cfg, tok, template = metadata(hub, model_id, info.sha)
    ac_raw = hub.file(model_id, info.sha, 'adapter_config.json')
    ac = json.loads(ac_raw) if ac_raw else {}
    if ac:
        if ac.get('peft_type') != 'LORA' or ac.get('base_model_name_or_path') != base_id:
            r['exclusion'] = 'wrong_adapter_type_or_base'; return r
        if ac.get('use_dora') or ac.get('modules_to_save'):
            r['exclusion'] = 'nonstandard_adapter'; return r
        for key in ('r', 'lora_alpha', 'target_modules'):
            r[key] = ac.get(key)
        r['use_rslora'] = ac.get('use_rslora', False)
        if tok is None:
            tok = base_meta[1]; r['tokenizer_source'] = 'inherited_base'
        if not hub.file(model_id, info.sha, 'tokenizer_config.json') and not hub.file(model_id, info.sha, 'chat_template.jinja'):
            template = base_meta[2]
    else:
        if any(cfg.get(k) != base_meta[0].get(k) for k in
               ('model_type', 'hidden_size', 'num_hidden_layers', 'vocab_size')):
            r['exclusion'] = 'different_architecture'; return r
    if tok is None or base_meta[1] is None:
        r['exclusion'] = 'missing_tokenizer'; return r
    r['tokenizer_source'] = r['tokenizer_source'] or 'repository'
    r['tokenizer_sha256'], r['template_sha256'] = digest(tok), digest(template)
    r['tokenizer_identical'] = digest(tok) == digest(base_meta[1])
    r['template_changed'] = digest(template) != digest(base_meta[2])
    if not r['tokenizer_identical']:
        r['exclusion'] = 'nonidentical_tokenizer'
    card = hub.file(model_id, info.sha, 'README.md') or b''
    r['type'] = classify(relations, cfg, card.decode(errors='replace'), model_id)
    if 'adapter' in relations and not ac:
        r['exclusion'] = 'missing_adapter_config'
    # Stage the standard HF weights and their configs, not extra GGUF/MLX formats.
    r['files'] = [s for s in files if '/' not in s['path'] and
                  (s['path'].endswith(('.safetensors', '.json', '.jinja', '.model', '.txt', '.md'))
                   or s['path'].startswith('LICENSE'))]
    if not any(s['path'].endswith('.safetensors') for s in r['files']):
        r['files'] += [s for s in weights if '/' not in s['path']]
    if not any(s['path'].endswith(('.bin', '.safetensors')) for s in r['files']):
        r['exclusion'] = 'no_root_standard_weights'
    if any(s['size'] is None for s in r['files']):
        r['exclusion'] = 'unknown_file_size'
    r['size_bytes'] = sum(s['size'] or 0 for s in r['files'])
    return r


def curate(args):
    out = Path(args.output); out.mkdir(parents=True, exist_ok=False)
    hub = Hub(out/'hub', safe_token(args.read_token, args.existing_token))
    base_id, cutoff = BASES[args.base]
    info = hub.meta(base_id)
    bm = metadata(hub, base_id, info.sha)
    if bm[1] is None:
        raise ValueError('Cannot curate without a verified base tokenizer')
    (out/'provenance.json').write_text(json.dumps(dict(base_id=base_id,
        revision=info.sha, cutoff=cutoff, cutoff_status='pending_owner_D04',
        source='https://huggingface.co/docs/hub/models-cards#specifying-a-base-model',
        created_at=utc(), base_tokenizer_sha256=digest(bm[1]), sample_size=args.count),indent=2))
    candidates = defaultdict(set)
    for relation in RELATIONS:
        for m in hub.api.list_models(filter=f'base_model:{relation}:{base_id}', sort='downloads', direction=-1):
            candidates[m.id].add(relation)
        event(out/'progress.jsonl', stage='listed', relation=relation, count=len(candidates))
    rows = []
    for i, (model, relations) in enumerate(sorted(candidates.items())):
        try:
            row = inspect_candidate(hub, model, relations, base_id, info.sha, bm)
            rows.append(row)
            event(out/'metadata.jsonl', **row)
        except Exception as e:
            # Preserve failures for retry; incomplete discovery must never pass acceptance.
            event(out/'errors.jsonl', model_id=model, error_type=type(e).__name__, error=str(e))
        if i % 25 == 0:
            event(out/'progress.jsonl', stage='inspected', count=i+1, total=len(candidates))
    assign_pools(rows, cutoff)
    counts = validate(rows)
    selected = stratify(rows, args.count)
    write_csv(out/f'candidates_{args.base}.csv', rows)
    write_csv(out/f'pool_draft_{args.base}.csv', selected)
    (out/'counts.json').write_text(json.dumps(dict(full=counts, sampled=validate(selected),
        discovered=len(candidates), inspected=len(rows), errors=len(candidates)-len(rows)),indent=2))
    spots = random.Random(20261005).sample(selected,min(10,len(selected)))
    (out/'spot_checks.md').write_text('\n'.join(f'- https://huggingface.co/{r["model_id"]}/tree/{r["revision"]} — {r["type"]}, {r["pool"]}, {r["license"]}' for r in spots)+'\n')
    if args.download:
        stage(selected, out/'hub', out/'downloads.jsonl', hub.token)


def stage(rows, cache, log, token=False):
    from huggingface_hub import snapshot_download
    priority = lambda r: (0 if r['type']=='lora_adapter' else 1 if r['type'].startswith('quantized') else 2, r['model_id'])
    Path(cache).mkdir(parents=True, exist_ok=True)
    total = 0
    for r in sorted(rows, key=priority):
        try:
            needed = r['size_bytes']
            if shutil.disk_usage(cache).free < needed + 20*1024**3:
                raise OSError('Insufficient disk space, preserving 20 GiB reserve')
            event(log, status='started', model_id=r['model_id'], revision=r['revision'], expected_bytes=needed)
            path = snapshot_download(r['model_id'], revision=r['revision'], token=token,
                                     cache_dir=str(cache), allow_patterns=[f['path'] for f in r['files']], max_workers=4)
            for spec in r['files']:
                p = Path(path)/spec['path']
                if not p.is_file() or p.stat().st_size != spec['size']:
                    raise ValueError(f'File size mismatch: {p}')
                sha = hashlib.sha256() if spec.get('sha256') else hashlib.sha1()
                if not spec.get('sha256'):
                    sha.update(f'blob {p.stat().st_size}\0'.encode())
                with p.open('rb') as f:
                    for chunk in iter(lambda:f.read(8*1024**2), b''):
                        sha.update(chunk)
                expected = spec.get('sha256') or spec.get('blob_id')
                if expected and sha.hexdigest() != expected:
                    raise ValueError(f'Content hash mismatch: {p}')
            total += needed
            event(log, status='complete', model_id=r['model_id'], revision=r['revision'], path=path,
                  size_bytes=needed, total_verified_bytes=total)
        except Exception as e:
            event(log, status='failed', model_id=r['model_id'], revision=r['revision'],
                  error_type=type(e).__name__, error=str(e))
    verify_downloads(rows, log)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command', required=True)
    c=sub.add_parser('curate'); c.add_argument('--base',choices=BASES,required=True)
    c.add_argument('--output',required=True); c.add_argument('--count',type=int,default=100)
    c.add_argument('--existing-token', action='store_true', help='Owner authorized existing credential for reads only'); c.add_argument('--download',action='store_true'); c.add_argument('--read-token',action='store_true')
    d=sub.add_parser('download'); d.add_argument('--pool',required=True)
    d.add_argument('--cache',required=True); d.add_argument('--log',required=True)
    d.add_argument('--read-token',action='store_true'); d.add_argument('--existing-token', action='store_true')
    v=sub.add_parser('verify'); v.add_argument('--pool',required=True); v.add_argument('--log',required=True)
    args=p.parse_args()
    if args.command=='curate': curate(args)
    elif args.command=='download': stage(read_csv(args.pool),Path(args.cache),Path(args.log),safe_token(args.read_token, args.existing_token))
    else:
        rows=read_csv(args.pool); print(validate(rows)); print('verified downloads',verify_downloads(rows,args.log))

if __name__=='__main__': main()
