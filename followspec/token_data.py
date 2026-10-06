"""Audited response references and online features; no persistent feature shards.

Assembly reports actual token counts. Explicit paired response views use the
owner-approved shorter response prefix while preserving full prompts and sources.
No repeated/resampled records or inferred total-budget matching are added.
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
from followspec.paired_responses import POLICY,trim_pair
from followspec.mixture_targets import validate_mixture

CONTROLS=('engine_version','base_revision','seed','temperature','top_p','max_new_tokens','max_lora_rank','batch_size','gpu_type')


def response_run(path):
    path=Path(path).resolve()
    if (path/'failure.json').exists():raise ValueError('failed response source')
    cfg=json.loads((path/'config.json').read_text());result=json.loads((path/'results.json').read_text())
    rows=[json.loads(s) for s in (path/'per_prompt.jsonl').read_text().splitlines() if s.strip()]
    if cfg.get('schema')!='followspec_response_tokens_v1' or cfg['engine_version']!='0.31.0':raise ValueError('wrong response schema/engine')
    if len(rows)!=result['n'] or len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('response count/identity mismatch')
    for r in rows:
        if type(r['acceptance_only']) is not bool or r['acceptance_only']!=cfg['acceptance_only']:raise ValueError('source acceptance scope mismatch')
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
    if any(r.get('kind') not in {'bank','mixture'} for r in registry.values()):raise ValueError('only audited bank and mixture targets supported')
    for name,entry in registry.items():
        if entry['kind']=='mixture':validate_mixture(name,registry,allow_acceptance=allow_acceptance)
    sources={};loaded={};samples=[];ids=set();splits={};forbidden=set(forbidden_hashes)
    def load(source):
        if source not in loaded:
            loaded[source]=response_run(source);sources[source]=loaded[source][2]
        return loaded[source]
    for ref in refs:
        source=str(Path(ref['run']).resolve());child=ref['child_id']
        if child!='base' and child not in registry:raise ValueError('target absent from audited registry')
        if child!='base' and arm=='MVD' and registry[child]['kind']!='bank':raise ValueError('MVD requires bank-only targets')
        if ref['split'] not in {'train','val'} or ref['pair_id'] in ids:raise ValueError('duplicate pair ID or invalid split')
        ids.add(ref['pair_id'])
        rows,cfg,_=load(source)
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
        view=None
        if 'paired_response' in ref:
            peer_ref=ref['paired_response']
            if peer_ref.get('policy')!=POLICY:raise ValueError('unapproved response-view policy')
            peer_source=str(Path(peer_ref['run']).resolve());peer_rows,peer_cfg,_=load(peer_source)
            j=peer_ref['record_index']
            if type(j) is not int or not 0<=j<len(peer_rows):raise ValueError('invalid paired response record index')
            peer=peer_rows[j]
            if (peer_cfg['acceptance_only'] or peer['acceptance_only']) and not allow_acceptance:raise ValueError('acceptance peer cannot enter production')
            if peer_cfg['base_revision']!=base_revision:raise ValueError('peer base revision mismatch')
            for original in [r,peer]:
                expected=base_revision if original['generation_target']=='base' else registry[child]['revision']
                if original['generation_revision']!=expected:raise ValueError('paired target revision mismatch')
            view=trim_pair(r,cfg,peer,peer_cfg,child)|dict(peer_source=peer_source,peer_record_index=j)
        kept=view['kept_response_tokens'] if view else len(r['completion_token_ids'])
        samples.append(dict(sample_id=ref['pair_id'],source=source,record_index=ref['record_index'],split=ref['split'],
            child_id=child,feature_target=feature,prompt_sha256=r['prompt_sha256'],length=r['response_start']+kept,
            assistant_tokens=kept,context_token_ids=r['prompt_token_ids']))
        if view is not None:samples[-1]['response_view']=view
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
    return _validate_arms(arms)


def validate_paired_arms(arms):
    """Validate a paired subset without claiming the bank-only MVD is matched."""
    if set(arms)!={'FS','PO-D','PO-T'}:raise ValueError('exactly three paired arms required')
    return _validate_arms(arms)


def _validate_arms(arms):
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
        if a.get('response_view')!=t.get('response_view'):raise ValueError('PO-T must reuse exact FS response view')
        av,dv=a.get('response_view'),d.get('response_view')
        if bool(av)!=bool(dv):raise ValueError('paired response views must be used on both sides')
        if av and ((av['peer_source'],av['peer_record_index'])!=(d['source'],d['record_index']) or
                   (dv['peer_source'],dv['peer_record_index'])!=(a['source'],a['record_index']) or
                   av['kept_response_tokens']!=dv['kept_response_tokens']):raise ValueError('wrong reciprocal response view')
        for other in [t,d]:
            if any(a[k]!=other[k] for k in ['child_id','split','prompt_sha256','context_token_ids','length','assistant_tokens']):raise ValueError('unmatched response context or split')
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
            self.loaded[source]=response_run(source)
        self.rows=[r for r in manifest['samples'] if r['split']==split]
        if not self.rows:raise ValueError('empty requested split')
        for item in self.rows:
            r=self._view(item)
            expected=route_arm(manifest['arm'],r['generation_target'],item['child_id'])
            if item['feature_target']!=expected or item['length']!=len(r['input_ids']) or item['prompt_sha256']!=r['prompt_sha256'] or item['assistant_tokens']!=sum(r['loss_mask']) or item['context_token_ids']!=r['prompt_token_ids']:
                raise ValueError('manifest entry differs from source')
        self.approx_lengths=[r['length']-1 for r in self.rows];self.hidden_states_dtype=torch.bfloat16

    def _view(self,item):
        rows,cfg,_=self.loaded[item['source']];r=rows[item['record_index']]
        view=item.get('response_view')
        if view is None:return r
        peer_rows,peer_cfg,_=self.loaded[view['peer_source']];peer=peer_rows[view['peer_record_index']]
        expected=trim_pair(r,cfg,peer,peer_cfg,item['child_id'])|dict(peer_source=view['peer_source'],peer_record_index=view['peer_record_index'])
        if view!=expected:raise ValueError('response view differs from immutable paired sources')
        end=r['response_start']+view['kept_response_tokens']
        return r|dict(input_ids=r['input_ids'][:end],loss_mask=r['loss_mask'][:end],completion_token_ids=r['input_ids'][r['response_start']:end])

    def __len__(self):return len(self.rows)

    def __getitem__(self,index):
        item=self.rows[index]
        sources={item['source']}
        if item.get('response_view'):sources.add(item['response_view']['peer_source'])
        for source in sources:
            for name in self.manifest['sources'][source]['files_sha256']:
                path=Path(source)/name;old=self.stats[str(path)];now=path.stat()
                if (old.st_size,old.st_mtime_ns)!=(now.st_size,now.st_mtime_ns):raise ValueError('response source changed during epoch')
        r=self._view(item)
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
