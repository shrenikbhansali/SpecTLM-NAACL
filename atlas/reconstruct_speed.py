"""Resolve official SPEED placeholders through a pinned NVIDIA source checkout.

Downloads/preparation only; no inference. Refuses to overwrite output artifacts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REVISION='36103237f6bb261386193d19c1c0966d74acec73'
SPEED_REVISION='454f88454792dfa3ccfd7ef15fff248efde44cd1'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-checkout',required=True)
    p.add_argument('--masked-parquet',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();source=Path(a.source_checkout).resolve();out=Path(a.output).resolve()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    if commit!=REVISION:raise ValueError('official reconstruction source revision mismatch')
    out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(source/'examples/specdec_bench'))
    import datasets
    from huggingface_hub import HfApi
    from specdec_bench.datasets import speed
    original=speed.load_dataset
    records=[]
    def pinned_load(path,*args,**kwargs):
        if path=='nvidia/SPEED-Bench':
            return datasets.Dataset.from_parquet(a.masked_parquet)
        if '/' in path and not path.startswith(('http://','https://')) and 'revision' not in kwargs:
            kwargs['revision']=HfApi().dataset_info(path).sha
        value=original(path,*args,**kwargs)
        record=dict(dataset=path,args=args,revision=kwargs.get('revision'),data_files=kwargs.get('data_files'),
                    fingerprint=getattr(value,'_fingerprint',None),rows=len(value))
        records.append(record)
        with (out/'source_fetches.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
        return value
    speed.load_dataset=pinned_load
    result=speed.SPEEDBench.prepare_data(out/'resolved',config_name='qualitative')
    data=datasets.Dataset.from_parquet(str(result))
    if len(data)!=880:raise ValueError('expected all 880 qualitative rows')
    if any(speed.TURNS_PLACEHOLDER in t for r in data for t in r['turns']):raise ValueError('unresolved placeholders remain')
    manifest=dict(source_revision=REVISION,speed_revision=SPEED_REVISION,masked_parquet_sha256=hashlib.sha256(Path(a.masked_parquet).read_bytes()).hexdigest(),
        resolved_parquet_sha256=hashlib.sha256(result.read_bytes()).hexdigest(),records=len(data),sources=records)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('RESOLVED',result,flush=True)

if __name__=='__main__':main()
