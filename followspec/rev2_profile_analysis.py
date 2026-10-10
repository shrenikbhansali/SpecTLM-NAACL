"""D54 E16 measured synchronized steps and exact serialization accounting."""
import argparse, hashlib, json, struct
from pathlib import Path
import numpy as np
from followspec.rev2_training_analysis import matched_training


def summarize_steps(rows):
    if len(rows)!=200 or [r['step'] for r in rows]!=list(range(1,201)):
        raise ValueError('exactly200 sequential measured steps required')
    times=np.array([r['wall_s'] for r in rows],float)
    if not np.isfinite(times).all() or (times<=0).any():raise ValueError('invalid timing')
    steady=times[10:]
    return dict(n_steps=200,steady_steps=190,all_steps_mean_s=float(times.mean()),
                steady_mean_s=float(steady.mean()),steady_median_s=float(np.median(steady)),
                steady_p10_p90_s=np.quantile(steady,[.1,.9]).tolist(),
                peak_allocated_bytes=max(r['peak_allocated_bytes'] for r in rows),
                peak_reserved_bytes=max(r['peak_reserved_bytes'] for r in rows))


def header(path):
    with path.open('rb') as f:
        n=struct.unpack('<Q',f.read(8))[0]
        return json.loads(f.read(n))


def tensor_bytes(h):
    sizes={'F32':4,'F16':2,'BF16':2,'I64':8,'BOOL':1,'I32':4,'U8':1}
    return sum(int(np.prod(v['shape']))*sizes[v['dtype']] for k,v in h.items() if k!='__metadata__')


def storage(root):
    records=[];seen=set();logical=0;unique=0
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        s=p.stat();logical+=s.st_size;key=(s.st_dev,s.st_ino)
        if key not in seen:unique+=s.st_size;seen.add(key)
        r=dict(path=str(p.relative_to(root)),file_bytes=s.st_size,nlink=s.st_nlink)
        if p.suffix=='.safetensors':r['tensor_bytes']=tensor_bytes(header(p))
        records.append(r)
    return dict(logical_file_bytes=logical,unique_inode_file_bytes=unique,files=records)


def analyze(stage,out):
    out.mkdir(exist_ok=False);records=[];pending=[];anchor=None
    for row in json.loads((stage/'plan.json').read_text()):
        if row['experiment']!='E16':continue
        root=Path(row['run_dir'])
        if not (root/'results.json').exists():pending.append(row['name']);continue
        c=json.loads((root/'config.json').read_text());r=json.loads((root/'results.json').read_text());proof=json.loads((root/'parameters.json').read_text())
        if anchor is None:anchor=c
        matched_training(anchor,c)
        assert r['steps']==200 and c['steps']==200
        profile=root/'step_profile.jsonl';stats=summarize_steps([json.loads(x) for x in profile.read_text().splitlines()]);stats['profile_sha256']=hashlib.sha256(profile.read_bytes()).hexdigest()
        exports=[Path(p) for p in r['exports']];assert len(exports)==1
        export=exports[0];trainable=export/'trainable.safetensors'
        n=proof['trainable_parameters'] if 'trainable_parameters' in proof else proof.get('trainable',proof.get('trainable_count'))
        records.append(dict(arm=row['arm'],source=str(root),seed=c['seed'],trainable_parameters=n,trainable_proof=proof,
                            step_profile=stats,whole_run_s=r['wall_s'],export=storage(export),
                            mutable_export_bytes=trainable.stat().st_size,
                            mutable_export_tensor_bytes=tensor_bytes(header(trainable)),
                            checkpoints=storage(root/'checkpoints')))
    (out/'results.json').write_text(json.dumps(dict(status='pilot',records=records,pending=pending,scope='single200step process per arm; first10steps excluded only from steady statistics; step quantiles are not uncertainty across repeated training; target capture included; export time excluded'),indent=2))
    text=['# E16 training resources — pilot','', 'Matched first200 batches, target capture included. Steady timing uses steps11–200; intervals below are within-run10th–90th percentiles, not repeated-run CIs. File sizes reflect actual exports (fp32), not hypothetical bf16 storage. Shared shards count once per unique inode within each export; mutable bytes are the additional merged weights.','', '| Arm | Steps | Mean all / steady s | Steady p10–p90 s | Peak allocated / reserved GiB | Mutable export MB | Compact checkpoints MB |','|---|---:|---|---|---|---:|---:|']
    for r in records:
        s=r['step_profile'];text.append(f"| {r['arm']} |200|{s['all_steps_mean_s']:.3f} / {s['steady_mean_s']:.3f}|{s['steady_p10_p90_s'][0]:.3f}–{s['steady_p10_p90_s'][1]:.3f}|{s['peak_allocated_bytes']/2**30:.2f} / {s['peak_reserved_bytes']/2**30:.2f}|{r['mutable_export_bytes']/1e6:.3f}|{r['checkpoints']['unique_inode_file_bytes']/1e6:.3f}|")
    text+=['',f'Pending: {len(pending)}.'];(out/'report.md').write_text('\n'.join(text)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.stage,a.output)
