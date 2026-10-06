"""Owner-approved paired response prefixes; immutable originals stay on disk.

Only response suffixes are dropped. Every pair, including a zero-trim pair,
gets a log. Returned references are views, not new generation artifacts.
"""
import argparse
import json
from pathlib import Path
import subprocess
from atlas.run_cell import sha256,write_new

POLICY='paired_min_response_v1'


def trim_pair(row,cfg,peer,peer_cfg,child_id):
    from followspec.token_data import CONTROLS
    if any(cfg[k]!=peer_cfg[k] for k in CONTROLS):raise ValueError('paired generation controls differ')
    if cfg['prompt_target']!=child_id or peer_cfg['prompt_target']!=child_id:raise ValueError('paired prompt origin differs')
    if sorted([row['generation_target'],peer['generation_target']])!=sorted([child_id,'base']):
        raise ValueError('paired sources must be child and base responses')
    if any(row[k]!=peer[k] for k in ['sample_id','prompt_id','raw_prompt','prompt_sha256','prompt_token_ids','response_start','split']):
        raise ValueError('paired response context or identity differs')
    if row.get('sampling_seed')!=peer.get('sampling_seed'):raise ValueError('paired per-prompt sampling seeds differ')
    a,b=len(row['completion_token_ids']),len(peer['completion_token_ids'])
    if min(a,b)<=0:raise ValueError('empty response cannot be a training prefix')
    return dict(policy=POLICY,kept_response_tokens=min(a,b),source_response_tokens=a,
        peer_response_tokens=b,dropped_response_tokens=a-min(a,b))


def pair_runs(child_run,base_run,*,child_id,split='train'):
    from followspec.token_data import response_run
    if split not in {'train','val'}:raise ValueError('train or val split required')
    child_run=str(Path(child_run).resolve());base_run=str(Path(base_run).resolve())
    children,cc,cp=response_run(child_run);bases,bc,bp=response_run(base_run)
    if cc['derivative_id']!=child_id or bc['derivative_id']!='base':raise ValueError('wrong child/base source roles')
    indexed={r['sample_id']:(i,r) for i,r in enumerate(bases)}
    if set(indexed)!={r['sample_id'] for r in children}:raise ValueError('paired sample IDs differ')
    refs=dict(child=[],base=[]);trims=[]
    for i,row in enumerate(children):
        j,peer=indexed[row['sample_id']];view=trim_pair(row,cc,peer,bc,child_id)
        pair_id=child_id+'::'+row['sample_id']
        for name,source,index,other,other_index in [('child',child_run,i,base_run,j),('base',base_run,j,child_run,i)]:
            refs[name].append(dict(run=source,record_index=index,child_id=child_id,pair_id=pair_id,split=split,
                paired_response=dict(policy=POLICY,run=other,record_index=other_index)))
        trims.append(dict(pair_id=pair_id,source_sample_id=row['sample_id'],child_id=child_id,split=split,prompt_sha256=row['prompt_sha256'],
            context_tokens=row['response_start'],child_source=child_run,child_record_index=i,base_source=base_run,base_record_index=j,
            child_original_tokens=view['source_response_tokens'],base_original_tokens=view['peer_response_tokens'],
            kept_response_tokens=view['kept_response_tokens'],child_dropped_tokens=view['dropped_response_tokens'],
            base_dropped_tokens=view['peer_response_tokens']-view['kept_response_tokens'],policy=POLICY))
    return dict(policy=POLICY,refs=refs,trims=trims,sources={child_run:cp,base_run:bp},
        acceptance_only=cp['acceptance_only'] or bp['acceptance_only'],production_data_acceptance=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['child-run','base-run','child-id','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--split',choices=['train','val'],default='train');a=p.parse_args()
    paired=pair_runs(a.child_run,a.base_run,child_id=a.child_id,split=a.split)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    for name,refs in paired['refs'].items():write_new(out/f'{name}_refs.json',refs)
    with (out/'per_pair.jsonl').open('x') as f:
        for row in paired['trims']:f.write(json.dumps(row)+'\n')
    cfg=dict(schema='followspec_paired_response_views_v1',policy=POLICY,owner_decision='Approved paired response trimming in chat 2026-10-06',
        sources=paired['sources'],acceptance_only=paired['acceptance_only'],split=a.split,child_id=a.child_id,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_sha256=sha256(__file__),
        outputs_sha256={p.name:sha256(p) for p in out.iterdir() if p.is_file()})
    write_new(out/'config.json',cfg)
    result=dict(n_pairs=len(paired['trims']),shifted_sequence_tokens_per_side=sum(r['context_tokens']+r['kept_response_tokens']-1 for r in paired['trims']),
        assistant_loss_tokens_per_side=sum(r['kept_response_tokens'] for r in paired['trims']),
        dropped_tokens={name:sum(r[f'{name}_dropped_tokens'] for r in paired['trims']) for name in ['child','base']},
        originals_unchanged=True,production_data_acceptance=False)
    write_new(out/'results.json',result)
    write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
        what_why='Apply approved paired response matching without changing original artifacts',new='Exact prefix views and per-pair trim records',
        artifacts=str(out.resolve()),config_results=dict(config=cfg,results=result),caveats='No production recipe or full-arm budget acceptance; audit decoded prefixes before use'))
    print(json.dumps(result))


if __name__=='__main__':main()
