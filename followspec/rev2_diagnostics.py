"""D54 CPU evidence: same-prefix OOV contrasts and pinned-engine tree feasibility."""
import argparse,ast,hashlib,json
from pathlib import Path
import numpy as np
from followspec.rev2_analysis import paired_seed_query
from ops.track_t import WS,write

def collect(out):
    out.mkdir(exist_ok=False);p=WS/'artifacts/P2_crossover_20261008_0348/full64/report/results.json';source=json.loads(p.read_text());records=[]
    for r in source['results']:
        raw=Path(r['source']['run_dir'])/'per_prompt.jsonl';rows=[json.loads(l) for l in raw.read_text().splitlines()]
        x=np.array([[np.mean(q['teachers'][0]['oov']) for q in rows]]);y=np.array([[np.mean(q['teachers'][1]['oov']) for q in rows]])
        records.append(dict(model=r['model'],origin=r['origin'],oov=paired_seed_query(x,y),source=str(raw),sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),effects=r['effects']))
    write(out/'diagnostics.json',records)
    text=['# A4b: parent versus child draft-vocabulary OOV on identical prefixes','', '64 sequences per origin; paired10,000 query draws. Positive difference means child OOV is greater. HF teacher-forced diagnostic; no online acceptance claim.','', '| Model | Origin | Parent OOV | Child OOV | Child−parent [95% CI] |','|---|---|---:|---:|---|']
    for r in records:
        q=r['oov'];d=q['delta'];text.append(f"| {r['model']} | {r['origin']} | {100*q['reference']['mean']:.2f}% | {100*q['arm']['mean']:.2f}% | {100*d['mean']:+.2f}pp [{100*d['ci95'][0]:+.2f}, {100*d['ci95'][1]:+.2f}] |")
    (out/'oov.md').write_text('\n'.join(text)+'\n')
    root=WS/'.venv-atlas-031-clean/lib/python3.11/site-packages/vllm';config=root/'config/speculative.py';s=config.read_text();tree=ast.parse(s)
    fields=[n.target.id for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='SpeculativeConfig' for n in c.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name)]
    files={}
    for rel in ['config/speculative.py','v1/spec_decode/eagle.py','v1/spec_decode/llm_base_proposer.py','v1/sample/rejection_sampler.py']:
        p=root/rel;content=p.read_text();files[rel]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),tree_mentions=[dict(line=i,text=l) for i,l in enumerate(content.splitlines(),1) if 'tree' in l.lower()])
    assert not any('tree' in k and not k.startswith('suffix_') for k in fields)
    write(out/'E18-feasibility.json',dict(status='infeasible_in_pinned_engine',engine='0.31.0',config_fields=fields,sources=files,reason='No EAGLE static-token-tree configuration/proposer/verification path exposed; proposer retains future-tree FIXME. Suffix trees are lookup-method internals. No dependency or frozen-engine modifications.'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();collect(a.output)
