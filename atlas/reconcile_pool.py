"""Repair pinned draft metadata, reconcile discovery, stage all bank adapters.

Preserves every previous artifact and downloads only new or incomplete snapshots.
No inference is performed. Run adapter_similarity separately after completion.
"""
import argparse
from collections import defaultdict
import copy
import json
from pathlib import Path
import random
import re
import subprocess
from atlas.curate_pool import (BASES, RELATIONS, Hub, safe_token, read_csv, write_csv,
    validate, verify_downloads, inspect_candidate, metadata, layout_exclusion,
    classify, assign_pools, stratify, stage, event, utc)


def staging_union(rows, selected):
    by_id={r['model_id']:r for r in selected}
    by_id.update({r['model_id']:r for r in rows if r['pool']=='bank' and not r['exclusion']})
    return sorted(by_id.values(),key=lambda r:r['model_id'])


def account_discovery(discovered, rows):
    ids=[r['model_id'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate candidates')
    missing=set(discovered)-set(ids)
    if missing:raise ValueError(f'missing discovered metadata: {len(missing)}')
    return len(ids)


class CachedHub(Hub):
    def file(self, model, revision, name, required=False):
        from huggingface_hub import try_to_load_from_cache, _CACHED_NO_EXIST
        cached=try_to_load_from_cache(model,name,revision=revision,cache_dir=self.cache)
        if isinstance(cached,str):return Path(cached).read_bytes()
        if cached is _CACHED_NO_EXIST:return None
        return super().file(model,revision,name,required)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',choices=BASES,required=True);p.add_argument('--previous',required=True)
    p.add_argument('--cache',required=True);p.add_argument('--output',required=True)
    p.add_argument('--existing-token',action='store_true');a=p.parse_args()
    old=Path(a.previous);out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    prior=json.loads((old/'provenance.json').read_text());base_id,cutoff=BASES[a.base]
    hub=CachedHub(a.cache,safe_token(use_existing_token=a.existing_token));bm=metadata(hub,base_id,prior['revision'])
    rows=read_csv(old/f'candidates_{a.base}.csv')
    errors=[json.loads(x) for x in (old/'errors.jsonl').read_text().splitlines()]
    discovered={r['model_id'] for r in rows}|{r['model_id'] for r in errors}
    provenance=prior|dict(previous=str(old.resolve()),code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),created_at=utc(),repair='standard layout/architecture, discovery reconciliation, all-bank staging')
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    # Re-use the pinned metadata and weights. No live HEAD changes for inspected rows.
    for r in rows:
        before=copy.deepcopy(r)
        if r['exclusion']=='author_in_bank':r['exclusion']=''
        if not r['exclusion']:
            cfg,_,_=metadata(hub,r['model_id'],r['revision'])
            reason=layout_exclusion(cfg,[x['path'] for x in r['files']])
            if not reason and r['type']!='lora_adapter':
                fields=('model_type','hidden_size','num_hidden_layers','vocab_size','num_attention_heads','num_key_value_heads','intermediate_size')
                if any(cfg.get(k)!=bm[0].get(k) for k in fields):reason='different_architecture'
            if reason:r['exclusion']=reason
            else:
                card=hub.file(r['model_id'],r['revision'],'README.md') or b''
                r['type']=classify(r['relation'].split(','),cfg,card.decode(errors='replace'),r['model_id'])
        if before!=r:event(out/'changes.jsonl',model_id=r['model_id'],previous_type=before['type'],type=r['type'],previous_exclusion=before['exclusion'],exclusion=r['exclusion'])
    # Relations are public metadata; restrict added rows to original discovered IDs.
    relations=defaultdict(set)
    for rel in RELATIONS:
        for m in hub.api.list_models(filter=f'base_model:{rel}:{base_id}'):
            if m.id in discovered:relations[m.id].add(rel)
    unresolved=[]
    for e in errors:
        revision_match=re.search(r'(?:resolve/|xet-read-token/)([a-f0-9]{40})',e['error'])
        revision=revision_match.group(1) if revision_match else None
        try:
            r=inspect_candidate(hub,e['model_id'],relations[e['model_id']],base_id,prior['revision'],bm,revision=revision)
            rows.append(r);event(out/'recovered.jsonl',model_id=r['model_id'],revision=r['revision'],exclusion=r['exclusion'])
        except Exception as exc:
            unresolved.append(e['model_id']);event(out/'errors.jsonl',model_id=e['model_id'],error_type=type(exc).__name__,error=str(exc))
    assign_pools(rows,cutoff)
    selected=stratify(rows,100);staging=staging_union(rows,selected)
    write_csv(out/f'candidates_{a.base}.csv',rows);write_csv(out/f'pool_draft_{a.base}.csv',selected)
    write_csv(out/f'staging_{a.base}.csv',staging)
    write_csv(out/f'bank_{a.base}.csv',[r for r in rows if r['pool']=='bank'])
    counts=dict(full=validate(rows),sampled=validate(selected),staging=validate(staging),discovered=len(discovered),inspected=len(rows),errors=len(unresolved))
    (out/'counts.json').write_text(json.dumps(counts,indent=2)+'\n')
    (out/'spot_checks.md').write_text('\n'.join(f'- https://huggingface.co/{r["model_id"]}/tree/{r["revision"]} — {r["type"]}, {r["pool"]}, {r["license"]}' for r in random.Random(20261005).sample(selected,10))+'\n')
    account_discovery(discovered,rows)
    old_entries={e['model_id']:e for e in map(json.loads,(old/'downloads.jsonl').read_text().splitlines()) if e.get('status')=='complete'}
    missing=[]
    for row in staging:
        try:verify_downloads([row],old/'downloads.jsonl')
        except ValueError:missing.append(row)
        else:
            e=old_entries[row['model_id']]
            event(out/'downloads.jsonl',**{k:v for k,v in e.items() if k!='time'},reused_from=str(old/'downloads.jsonl'),original_verified_at=e.get('time'))
    write_csv(out/f'download_pending_{a.base}.csv',missing)
    stage(missing,Path(a.cache),out/'downloads.jsonl',hub.token)
    verify_downloads(staging,out/'downloads.jsonl')
    (out/'staging_complete.json').write_text(json.dumps(dict(n=len(staging),sampled=len(selected),new_downloads=len(missing),at=utc()),indent=2)+'\n')

if __name__=='__main__':main()
