"""Pinned B3 mixtures in the B5 registry; production requires general-set PPL admission."""
import argparse
import csv
import json
import math
from pathlib import Path
import subprocess
from atlas.run_cell import sha256,write_new

FILES=('adapter_config.json','adapter_model.safetensors','mixture_manifest.json')


def checked_files(root,expected):
    root=Path(root)
    for name,digest in expected.items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha256(root/name)!=digest:raise ValueError('target file hash mismatch')


def validate_mixture(name,registry,*,allow_acceptance=False):
    entry=registry[name];root=Path(entry['path'])
    if entry.get('kind')!='mixture' or not set(FILES)<=entry.get('files_sha256',{}).keys():raise ValueError('complete mixture file hashes required')
    checked_files(root,entry['files_sha256'])
    manifest=json.loads((root/'mixture_manifest.json').read_text());sources=entry.get('source_ids',[])
    if len(sources) not in (2,3) or len(set(sources))!=len(sources) or any(registry.get(s,{}).get('kind')!='bank' for s in sources):
        raise ValueError('mixture requires two or three distinct bank sources')
    if len(manifest['sources'])!=len(sources):raise ValueError('mixture source count differs')
    if entry['revision']!=sha256(root/'mixture_manifest.json'):raise ValueError('mixture content revision differs')
    if not math.isfinite(manifest['scale']) or not 0<=manifest['scale']<=1.5:raise ValueError('mixture scale outside approved recipe')
    weights=manifest['weights']
    if len(weights)!=len(sources) or any(not math.isfinite(w) or w<0 for w in weights) or not math.isclose(sum(weights),1,abs_tol=1e-6):raise ValueError('invalid mixture weights')
    if manifest['engine_version']!='0.31.0' or manifest['output_rank']>manifest['configured_engine_cap']:raise ValueError('mixture engine/rank mismatch')
    for source,proof in zip(sources,manifest['sources'],strict=True):
        bank=registry[source];checked_files(bank['path'],bank['files_sha256'])
        if Path(bank['path']).resolve()!=Path(proof['path']).resolve() or any(bank['files_sha256'][file]!=proof[key] for file,key in [('adapter_config.json','config_sha256'),('adapter_model.safetensors','weights_sha256')]):raise ValueError('mixture source provenance differs')
    if entry.get('acceptance_only'):
        if not allow_acceptance:raise ValueError('acceptance-only mixture cannot enter production')
    else:
        admission=entry.get('admission')
        if not admission:raise ValueError('production mixture needs admission evidence')
        path=Path(admission['path']);checked_files(path,admission['files_sha256'])
        cfg=json.loads((path/'config.json').read_text());result=json.loads((path/'results.json').read_text())
        actual,evidence=collect_admission(name,registry,cfg['mixture_filter_run'],cfg['bank_filter_runs'],cfg['pool_manifest'])
        if actual!=result or evidence!=cfg['evidence_sha256'] or not actual['accepted']:raise ValueError('mixture admission failed or changed')
    return manifest


def validate_registry(registry,*,allow_acceptance=False):
    if 'base' in registry or any(r.get('kind') not in {'bank','mixture'} for r in registry.values()):raise ValueError('only bank and audited mixture targets allowed')
    for name,r in registry.items():
        if not r.get('revision') or not r.get('path') or not r.get('files_sha256'):raise ValueError('pinned adapter files required')
        if any(Path(p).is_absolute() or '..' in Path(p).parts for p in r['files_sha256']):raise ValueError('invalid adapter file path')
        if r['kind']=='mixture':validate_mixture(name,registry,allow_acceptance=allow_acceptance)
        elif r.get('normalization'):
            from followspec.adapter_views import validate_view
            validate_view(r)


def collect_admission(name,registry,mixture_run,bank_runs,pool_manifest):
    """Recompute §5.4 PPL bound on a training-only shared general reference.

    A2 used SPEED evaluation prompts: its PPL numbers are deliberately refused
    here. Operator supplies fresh filter runs on the same training reference.
    """
    evidence={}
    def read(path,lines=False):
        path=Path(path);evidence[str(path.resolve())]=sha256(path)
        return [json.loads(s) for s in path.read_text().splitlines()] if lines else json.loads(path.read_text())
    pool_path=Path(pool_manifest);evidence[str(pool_path.resolve())]=sha256(pool_path)
    with pool_path.open() as f:pool={r['model_id']:r for r in csv.DictReader(f) if r['in_bank']=='True'}
    banks={k for k,r in registry.items() if r['kind']=='bank'}
    if not banks or set(bank_runs)!=banks or set(pool)!=banks:raise ValueError('PPL admission must cover every frozen bank target')
    entry=registry[name]
    for file in FILES:evidence[str((Path(entry['path'])/file).resolve())]=sha256(Path(entry['path'])/file)
    reference=None;values={};settings=None
    for target,run in list(sorted(bank_runs.items()))+[(name,mixture_run)]:
        run=Path(run)
        if (run/'failure.json').exists():raise ValueError('failed PPL source')
        cfg=read(run/'config.json');result=read(run/'results.json');provenance=read(run/'target_provenance.json');rows=read(run/'per_prompt.jsonl',True)
        if cfg['derivative_id']!=target or provenance['revision']!=registry[target]['revision'] or not result['loadable'] or cfg['engine_version']!='0.31.0':raise ValueError('PPL target/pin/backend differs')
        if target!=name and (pool[target]['revision']!=registry[target]['revision'] or pool[target]['base_revision']!=cfg['base_revision']):raise ValueError('frozen bank revision differs')
        if target==name:
            if any(provenance.get('files_sha256',{}).get(k)!=v for k,v in entry['files_sha256'].items()):raise ValueError('PPL mixture weights differ')
        rc=read(Path(cfg['reference']).parent/'config.json');refs=read(cfg['reference'],True);queries=read(rc['source_prompts'],True)
        if any(q.get('split')!='training' or q['prompt_id'].startswith('speed-') for q in queries):raise ValueError('mixture admission requires training general prompts, never SPEED evaluation')
        if len(queries)!=128 or len(refs)!=128 or len(rows)!=128 or len({x['prompt_id'] for x in rows})!=128 or {x['prompt_id'] for x in rows}!={x['prompt_id'] for x in refs}:raise ValueError('complete128-reference scores required')
        if sha256(rc['source_prompts'])!=rc['prompt_sha256'] or sha256(cfg['reference'])!=rc['reference_sha256'] or cfg['reference_sha256']!=rc['reference_sha256']:raise ValueError('PPL reference hashes differ')
        current=tuple(cfg[k] for k in ['base_revision','reference_sha256','max_reference_tokens','ppl_definition','max_lora_rank','seed','engine_version'])
        if settings is not None and settings!=current:raise ValueError('PPL controls differ across bank and mixture')
        settings=current;reference=cfg['reference_sha256']
        total=sum(r['scored_tokens'] for r in rows);nll=sum(r['nll_sum'] for r in rows)
        if total<=0 or not math.isfinite(nll) or nll<0:raise ValueError('invalid PPL records')
        ppl=math.exp(nll/total)
        if not math.isclose(ppl,result['ppl'],rel_tol=1e-12) or total!=result['scored_tokens']:raise ValueError('PPL summary differs from records')
        values[target]=ppl
    worst=max(values[b] for b in banks)
    return dict(schema='followspec_mixture_admission_v1',mixture_id=name,mixture_revision=entry['revision'],
        accepted=values[name]<=worst,mixture_ppl=values[name],worst_bank_ppl=worst,bank_ppls={b:values[b] for b in sorted(banks)},
        n_bank=len(banks),n_reference_prompts=128,reference_sha256=reference,rule='mixture PPL <= worst real bank PPL on shared training general set'),evidence


def registry_row(registry_path,name,base_snapshot,base_id,base_revision,*,allow_acceptance=False):
    """Adapt an explicitly admitted local mixture to the generation input contract."""
    registry=json.loads(Path(registry_path).read_text())
    if name not in registry or registry[name].get('kind')!='mixture':raise ValueError('explicit mixture registry target required')
    validate_mixture(name,registry,allow_acceptance=allow_acceptance)
    item=registry[name];root=Path(item['path']);cfg=json.loads((root/'adapter_config.json').read_text());base=Path(base_snapshot)
    if base.name!=base_revision or cfg['base_model_name_or_path']!=base_id:raise ValueError('mixture base pin differs')
    tc=json.loads((base/'tokenizer_config.json').read_text())
    template=(base/'chat_template.jinja').read_bytes() if (base/'chat_template.jinja').exists() else json.dumps(tc.get('chat_template'),sort_keys=True).encode()
    return dict(model_id=name,revision=item['revision'],base_id=base_id,base_revision=base_revision,type='lora_adapter',pool='mixture',
        r=cfg['r'],local_adapter=str(root.resolve()),tokenizer_source='inherited_base',tokenizer_sha256=sha256(base/'tokenizer.json'),
        template_sha256=__import__('hashlib').sha256(template).hexdigest(),exclusion='',
        files=[dict(path=f,size=(root/f).stat().st_size,sha256=item['files_sha256'][f]) for f in FILES[:2]],
        mixture_registry=dict(path=str(Path(registry_path).resolve()),sha256=sha256(registry_path),entry=item))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['registry','mixture-id','mixture-filter-run','bank-filter-runs','pool-manifest','output']:p.add_argument('--'+key,required=True)
    a=p.parse_args();registry=json.loads(Path(a.registry).read_text());bank_runs=json.loads(Path(a.bank_filter_runs).read_text())
    result,evidence=collect_admission(a.mixture_id,registry,a.mixture_filter_run,bank_runs,a.pool_manifest)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    cfg=dict(mixture_filter_run=str(Path(a.mixture_filter_run).resolve()),bank_filter_runs=bank_runs,pool_manifest=str(Path(a.pool_manifest).resolve()),
        registry_sha256=sha256(a.registry),evidence_sha256=evidence,code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    write_new(out/'config.json',cfg);write_new(out/'results.json',result)
    write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
        what_why='Admit M1 mixtures under the fixed §5.4 PPL limit',new='Frozen-bank coverage and training-reference provenance checked',artifacts=str(out.resolve()),
        config_results=dict(config=cfg,results=result),caveats='Numerical admission check; does not establish transfer or quality'))
    print(json.dumps(result));raise SystemExit(0 if result['accepted'] else 1)


if __name__=='__main__':main()
