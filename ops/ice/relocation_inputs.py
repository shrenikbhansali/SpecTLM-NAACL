"""Inventory all sealed M3 data and runtime files for copy-only ICE relocation.

Run on heck before rsync. Snapshot symlinks must be copied with rsync -L so their
bytes, rather than links into an uncopied HF blob cache, reach the destination.
"""
import argparse
import json
from pathlib import Path
from atlas.relocation import digest, Relocation
from followspec.production_pipeline import checked_stage,read


def training_inputs(finalized):
    root,cfg=checked_stage(finalized)
    if cfg['stage']!='finalize':raise ValueError('sealed finalized training corpus required')
    files={root/'stage_files.json'}|{root/n for n in read(root/'stage_files.json')}
    spec=cfg['spec'];files.add(Path(spec['code_repo'])/'atlas/env/requirements.lock')
    def directory(path):
        found={p for p in Path(path).rglob('*') if p.is_file() and '.cache' not in p.parts}
        if not found:raise ValueError(f'missing or empty model directory: {path}')
        files.update(found)
    for key in ('base_snapshot','drafter_snapshot'):directory(spec[key])
    for arm in ('FS','MVD','PO-D','PO-T'):
        m=read(root/arm/'manifest.json');audit=m['sample_mask_audit'];p=Path(audit['path'])
        if digest(p)!=audit['sha256']:raise ValueError('decoded mask audit changed')
        files.add(p)
        for source,proof in m.get('sources',{}).items():
            for name,h in proof['files_sha256'].items():
                p=Path(source)/name
                if digest(p)!=h:raise ValueError('response source changed')
                files.add(p)
        for entry in m.get('registry',{}).values():
            directory(entry['path'])
            for name,h in entry['files_sha256'].items():
                if digest(Path(entry['path'])/name)!=h:raise ValueError('adapter input changed')
    return files


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--finalized',nargs='+',required=True);p.add_argument('--workspace',required=True)
    p.add_argument('--destination',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();root=Path(a.workspace).resolve();files=set()
    for stage in a.finalized:files.update(training_inputs(stage))
    for f in files:
        if not f.is_relative_to(root):raise ValueError(f'input outside source workspace: {f}; use atlas.relocation with explicit additional prefix')
    manifest=dict(version=1,prefixes=[dict(source=str(root),destination=str(Path(a.destination)))],files_sha256={str(f):digest(f) for f in sorted(files)})
    Relocation(manifest)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    (out/'files.txt').write_text(''.join(str(f.relative_to(root))+'\n' for f in sorted(files)))
    (out/'relocation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result=dict(n_files=len(files),n_bytes=sum(f.stat().st_size for f in files),relocation_sha256=digest(out/'relocation.json'),submitted=False)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
