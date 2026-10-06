"""Render training queries once for matched child/base response controls."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from atlas.run_cell import sha256,write_new
from atlas.filter_pool import resolve_target
from atlas.generate_magpie import verify_inputs
from atlas.workloads import prompt_hash


def render_rows(rows,tokenizer):
    if not rows or len({r['prompt_id'] for r in rows})!=len(rows):raise ValueError('unique nonempty query set required')
    result=[]
    for r in rows:
        if r.get('split')!='training' or r.get('format')=='chat_template_rendered':raise ValueError('raw training queries required')
        text=tokenizer.apply_chat_template([{'role':'user','content':r['prompt']}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
        ids=tokenizer.encode(text,add_special_tokens=False)
        if not ids:raise ValueError('empty chat rendering')
        result.append(dict(prompt_id=r['prompt_id'],raw_prompt_sha256=prompt_hash(r['prompt']),rendered_text=text,rendered_token_ids=ids))
    return result


def write_bundle(output,rows,metadata):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    with (out/'prompts.jsonl').open('x') as f:
        for row in rows:f.write(json.dumps(row)+'\n')
    write_new(out/'config.json',metadata|dict(schema='followspec_rendered_training_v1',n=len(rows),rendered_sha256=sha256(out/'prompts.jsonl')))


def load_bundle(path,rows,*,prompt_target,base_tokenizer_sha256,prompt_sha256):
    path=Path(path);cfg=json.loads((path.parent/'config.json').read_text())
    if cfg.get('schema')!='followspec_rendered_training_v1' or cfg['rendered_sha256']!=sha256(path):raise ValueError('rendered bundle changed')
    if cfg['prompt_target_id']!=prompt_target or cfg['tokenizer_sha256']!=base_tokenizer_sha256 or cfg['prompt_sha256']!=prompt_sha256:
        raise ValueError('wrong prompt origin, vocabulary or raw query source')
    rendered=[json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    if len(rendered)!=len(rows) or cfg['n']!=len(rows):raise ValueError('rendered query count mismatch')
    for r,s in zip(rows,rendered,strict=True):
        if r['prompt_id']!=s['prompt_id'] or prompt_hash(r['prompt'])!=s['raw_prompt_sha256']:raise ValueError('rendered query identity mismatch')
        if not s['rendered_token_ids'] or any(type(i) is not int or i<0 for i in s['rendered_token_ids']):raise ValueError('invalid rendered token IDs')
    return [{'prompt_token_ids':r['rendered_token_ids']} for r in rendered]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['base-snapshot','base-id','base-revision','tokenizer','tokenizer-revision','prompts','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--derivative-id',default='base');p.add_argument('--pool');p.add_argument('--downloads');p.add_argument('--filter-run')
    a=p.parse_args();a.adapter=None;a.adapter_revision=None
    for path,rev in [(a.base_snapshot,a.base_revision),(a.tokenizer,a.tokenizer_revision)]:
        if not re.fullmatch('[a-f0-9]{40}',rev) or Path(path).name!=rev:raise ValueError('pinned local snapshot required')
    _,_,row=resolve_target(a);meta=dict(prompt_target_id=a.derivative_id,prompt_target_revision=row['revision'])
    if a.derivative_id!='base':
        if row['pool']!='bank' or row['type']!='lora_adapter':raise ValueError('only accepted bank prompt origins allowed')
        if not a.filter_run:raise ValueError('A2 proof required')
        root=Path(a.filter_run);cfg=json.loads((root/'config.json').read_text());provenance=json.loads((root/'target_provenance.json').read_text())
        if cfg['derivative_id']!=a.derivative_id or provenance['revision']!=row['revision'] or not json.loads((root/'results.json').read_text()).get('accepted'):
            raise ValueError('wrong or rejected A2 prompt origin')
        verify_inputs(row,None,a.tokenizer,a.tokenizer_revision)
        meta['filter_results_sha256']=sha256(root/'results.json')
    elif a.tokenizer!=a.base_snapshot:raise ValueError('base origin needs base tokenizer')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(a.tokenizer,local_files_only=True,trust_remote_code=False)
    rows=[json.loads(s) for s in Path(a.prompts).read_text().splitlines() if s.strip()]
    if any(r.get('derivative_id') and r['derivative_id']!=a.derivative_id for r in rows):raise ValueError('wrong Magpie query origin')
    rendered=render_rows(rows,tokenizer)
    meta.update(prompt_sha256=sha256(a.prompts),tokenizer=a.tokenizer,tokenizer_revision=a.tokenizer_revision,
        tokenizer_sha256=sha256(Path(a.tokenizer)/'tokenizer.json'),
        template_sha256=__import__('hashlib').sha256(json.dumps(tokenizer.chat_template,sort_keys=True).encode()).hexdigest(),
        acceptance_only=any(r.get('acceptance_only',False) for r in rows),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    write_bundle(a.output,rendered,meta)
    print(json.dumps(meta|dict(n=len(rows))))


if __name__=='__main__':main()
