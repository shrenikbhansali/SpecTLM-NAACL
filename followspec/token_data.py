"""Audited response references and online features; no persistent feature shards.

Assembly reports actual token counts. It never trims, repeats or resamples data
to make a budget pass. A mismatched arm set is an error, not an inferred recipe.
"""
import argparse
import json
import math
from pathlib import Path
import torch
from torch.utils.data import Dataset
from atlas.run_cell import sha256,write_new
from atlas.workloads import prompt_hash
from followspec.online_capture import route_arm

CONTROLS=('engine_version','base_revision','seed','temperature','top_p','max_new_tokens','max_lora_rank','batch_size','gpu_type')


def response_run(path):
    path=Path(path).resolve()
    if (path/'failure.json').exists():raise ValueError('failed response source')
    cfg=json.loads((path/'config.json').read_text());result=json.loads((path/'results.json').read_text())
    rows=[json.loads(s) for s in (path/'per_prompt.jsonl').read_text().splitlines() if s.strip()]
    if cfg.get('schema')!='followspec_response_tokens_v1' or cfg['engine_version']!='0.31.0':raise ValueError('wrong response schema/engine')
    if len(rows)!=result['n'] or len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('response count/identity mismatch')
    for r in rows:
        ids=r['input_ids'];start=r['response_start']
        if not 1<=start<len(ids) or any(type(i) is not int or i<0 for i in ids):raise ValueError('invalid response sequence')
        if r['loss_mask']!=[False]*start+[True]*(len(ids)-start) or any(type(v) is not bool for v in r['loss_mask']):raise ValueError('wrong assistant mask')
        if r['prompt_token_ids']!=ids[:start] or r['completion_token_ids']!=ids[start:]:raise ValueError('saved token boundary differs')
        if r['split']!='train' or r['prompt_sha256']!=prompt_hash(r['raw_prompt']):raise ValueError('wrong query split/hash')
        if r['generation_target']!=cfg['derivative_id'] or r['generation_revision']!=cfg['derivative_revision']:raise ValueError('wrong response target')
    if sum(sum(r['loss_mask']) for r in rows)!=result['assistant_tokens']:raise ValueError('assistant token total mismatch')
    provenance=dict(path=str(path),files_sha256={f:sha256(path/f) for f in ['config.json','results.json','per_prompt.jsonl']},
        controls={k:cfg[k] for k in CONTROLS},acceptance_only=cfg['acceptance_only'])
    return rows,cfg,provenance


def build_manifest(arm,refs,*,registry,base_revision,initialization_revision,forbidden_hashes=(),allow_acceptance=False):
    if arm not in {'FS','MVD','PO-D','PO-T'} or not refs:raise ValueError('nonempty known arm required')
    if any(r.get('kind')!='bank' for r in registry.values()):raise ValueError('only audited bank targets supported; mixtures remain B3-blocked')
    sources={};loaded={};samples=[];ids=set();splits={};forbidden=set(forbidden_hashes)
    for ref in refs:
        source=str(Path(ref['run']).resolve());child=ref['child_id']
        if child!='base' and child not in registry:raise ValueError('non-bank target in data')
        if ref['split'] not in {'train','val'} or ref['pair_id'] in ids:raise ValueError('duplicate pair ID or invalid split')
        ids.add(ref['pair_id'])
        if source not in loaded:
            loaded[source]=response_run(source);sources[source]=loaded[source][2]
        rows,cfg,_=loaded[source]
        if cfg['base_revision']!=base_revision:raise ValueError('source base revision mismatch')
        if type(ref['record_index']) is not int or not 0<=ref['record_index']<len(rows):raise ValueError('invalid response record index')
        r=rows[ref['record_index']]
        if (cfg['acceptance_only'] or r['acceptance_only']) and not allow_acceptance:raise ValueError('acceptance data cannot enter production')
        if r['prompt_sha256'] in forbidden:raise ValueError('evaluation query in training data')
        prior=splits.setdefault(r['prompt_sha256'],ref['split'])
        if prior!=ref['split']:raise ValueError('training/validation prompt overlap')
        feature=route_arm(arm,r['generation_target'],child)
        if r['generation_target']!='base' and r['generation_revision']!=registry[child]['revision']:raise ValueError('bank revision mismatch')
        if cfg['prompt_target']!=child:raise ValueError('response context origin differs from logical child')
        samples.append(dict(sample_id=ref['pair_id'],source=source,record_index=ref['record_index'],split=ref['split'],
            child_id=child,feature_target=feature,prompt_sha256=r['prompt_sha256'],length=len(r['input_ids']),
            assistant_tokens=sum(r['loss_mask']),context_token_ids=r['prompt_token_ids']))
    train=[r for r in samples if r['split']=='train']
    return dict(schema='followspec_online_tokens_v1',arm=arm,registry=registry,sources=sources,samples=samples,
        base_revision=base_revision,initialization_revision=initialization_revision,forbidden_prompt_hashes=sorted(forbidden),
        acceptance_only=any(s['acceptance_only'] for s in sources.values()),data_acceptance_passed=False,
        token_budget=sum(r['length']-1 for r in train),token_budget_unit='shifted sequence tokens',
        assistant_loss_tokens=sum(r['assistant_tokens'] for r in train),optimizer_steps=None,
        parent_sample_share=sum(r['child_id']=='base' for r in train)/len(train) if train else None,
        status='assembled_pending_matched_budget_and_native_trainer_acceptance')


def validate_arm_set(arms):
    if set(arms)!={'FS','MVD','PO-D','PO-T'}:raise ValueError('all four arms required')
    if any(m['arm']!=name for name,m in arms.items()):raise ValueError('arm identity mismatch')
    for key in ['base_revision','initialization_revision','token_budget','token_budget_unit']:
        if len({m[key] for m in arms.values()})!=1:raise ValueError('token budget or common initialization differs: '+key)
    if not arms['FS']['token_budget']:raise ValueError('empty training budget')
    reference=next(iter(arms['FS']['sources'].values()))['controls']
    for m in arms.values():
        for source in m['sources'].values():
            if any(source['controls'][k]!=reference[k] for k in CONTROLS if k!='seed'):
                raise ValueError('unmatched generation engine, hardware or sampling controls')
    indexed={name:{r['sample_id']:r for r in m['samples']} for name,m in arms.items()}
    if not indexed['FS'].keys()==indexed['PO-T'].keys()==indexed['PO-D'].keys():raise ValueError('unmatched FS/PO-T/PO-D pairs')
    for key,a in indexed['FS'].items():
        t=indexed['PO-T'][key];d=indexed['PO-D'][key]
        if (a['source'],a['record_index'])!=(t['source'],t['record_index']):raise ValueError('PO-T must reuse exact FS response records')
        for other in [t,d]:
            if any(a[k]!=other[k] for k in ['child_id','split','prompt_sha256','context_token_ids']):raise ValueError('unmatched response context or split')
            ac=arms['FS']['sources'][a['source']]['controls'];oc=arms['PO-T' if other is t else 'PO-D']['sources'][other['source']]['controls']
            if ac!=oc:raise ValueError('response controls differ')
    return dict(matched=True,shifted_sequence_tokens=arms['FS']['token_budget'],
        assistant_loss_tokens={k:m['assistant_loss_tokens'] for k,m in arms.items()},
        parent_sample_share={k:m['parent_sample_share'] for k,m in arms.items()},
        optimizer_steps='must be resolved and checked by native batch sampler before training',
        full_recipe='sample quotas, parent share, mixture acceptance and owner settings remain separate launch requirements')


class OnlineResponseDataset(Dataset):
    def __init__(self,manifest,*,split,bank,shift,noise_std=0.,allow_acceptance=False):
        if manifest.get('schema')!='followspec_online_tokens_v1':raise ValueError('wrong token manifest schema')
        if manifest['acceptance_only'] and not allow_acceptance:raise ValueError('acceptance-only dataset')
        if not math.isfinite(noise_std) or noise_std<0:raise ValueError('invalid shared noise')
        self.manifest=manifest;self.bank=bank;self.shift=shift;self.noise_std=noise_std;self.loaded={};self.stats={}
        for source,proof in manifest['sources'].items():
            for name,digest in proof['files_sha256'].items():
                if sha256(Path(source)/name)!=digest:raise ValueError('response source changed')
                self.stats[str(Path(source)/name)]=(Path(source)/name).stat()
            self.loaded[source]=response_run(source)[0]
        self.rows=[r for r in manifest['samples'] if r['split']==split]
        if not self.rows:raise ValueError('empty requested split')
        for item in self.rows:
            r=self.loaded[item['source']][item['record_index']]
            expected=route_arm(manifest['arm'],r['generation_target'],item['child_id'])
            if item['feature_target']!=expected or item['length']!=len(r['input_ids']) or item['prompt_sha256']!=r['prompt_sha256']:
                raise ValueError('manifest entry differs from source')
        self.approx_lengths=[r['length']-1 for r in self.rows];self.hidden_states_dtype=torch.bfloat16

    def __len__(self):return len(self.rows)

    def __getitem__(self,index):
        item=self.rows[index]
        for name in self.manifest['sources'][item['source']]['files_sha256']:
            path=Path(item['source'])/name;old=self.stats[str(path)];now=path.stat()
            if (old.st_size,old.st_mtime_ns)!=(now.st_size,now.st_mtime_ns):raise ValueError('response source changed during epoch')
        r=self.loaded[item['source']][item['record_index']]
        raw=self.bank.capture(item['child_id'],torch.tensor(r['input_ids'],dtype=torch.long),torch.tensor(r['loss_mask'],dtype=torch.bool),feature_target=item['feature_target'])
        if self.noise_std:
            noise=2*(torch.rand_like(raw['hidden_states'])-.5)*self.noise_std
            raw['hidden_states']=raw['hidden_states']+noise;raw['base_hidden_states']=raw['base_hidden_states']+noise
        return dict(tensors=self.shift(raw),target_id=item['child_id'],sample_id=item['sample_id'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();plan=json.loads(Path(a.plan).read_text());manifest=build_manifest(**plan)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write_new(out/'manifest.json',manifest)
    cfg=dict(plan=str(Path(a.plan).resolve()),plan_sha256=sha256(a.plan),source_sha256=sha256(__file__),
        code_commit=__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip())
    write_new(out/'config.json',cfg)
    write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
        what_why='Audited response-token arm manifest',new='Online feature references with exact measured token counts',artifacts=str(out.resolve()),
        config_results=dict(config=cfg,token_budget=manifest['token_budget'],assistant_loss_tokens=manifest['assistant_loss_tokens']),
        caveats='No training acceptance claim; matched arm budgets and native sampler steps must pass before launch'))
    print(json.dumps({k:manifest[k] for k in ['arm','token_budget','assistant_loss_tokens','parent_sample_share','status']}))


if __name__=='__main__':main()
