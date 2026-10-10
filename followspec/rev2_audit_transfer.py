"""Carry a completed manual sample review onto sealed identical samples only.

This cannot create a review. It requires a manually written reviewed manifest
and byte-hashed, already inspected sample files, then checks decoded text, exact
IDs, mask and boundary against the sealer's output before recording data hash.
"""
import argparse,json,time
from pathlib import Path
from ops.track_t import sha,write
FIELDS=['prompt','answer','input_ids','response_start','loss_mask','mask_valid']

def checked_samples(reviewed,sealed):
    if len(reviewed)!=len(sealed) or len(reviewed) not in [5,10]:raise ValueError('sample count differs')
    for a,b in zip(reviewed,sealed,strict=True):
        if not a['mask_valid'] or not b['mask_valid']:raise ValueError('invalid reviewed mask')
        for k in FIELDS:
            if a[k]!=b[k]:raise ValueError('sealed sample was not inspected: '+k)
    return True

def transfer(manifest,root):
    m=json.loads(manifest.read_text());assert m['manually_reviewed'] and m['reviewer']=='codex-1'
    remaining=[]
    for r in m['datasets']:
        dest=root/f"sealed-t{r['target']}"/r['label'];audit=dest/'manual-audit.json'
        if audit.exists():continue
        samples=dest/'five_decoded_masks.json';seal=dest/'seal.json'
        if not samples.exists() or not seal.exists():remaining.append(str(dest));continue
        expected=[]
        for source in r['reviewed_samples']:
            p=Path(source['path']);assert sha(p)==source['sha256'];expected+=json.loads(p.read_text())
        checked_samples(expected,json.loads(samples.read_text()));s=json.loads(seal.read_text());data=dest/'per_prompt.jsonl';assert s['data_sha256']==sha(data)
        write(audit,dict(passed=True,data_sha256=s['data_sha256'],reviewer=m['reviewer'],reviewed_at=m['reviewed_at'],review_manifest=str(manifest),review_manifest_sha256=sha(manifest),sample_sha256=sha(samples),comments=r['comments'],scope='Manual decoded text/mask review occurred before sealing; exact inspected text, token IDs, boundary and mask revalidated against sealed samples. Whole-dataset structural/eval-exclusion checks performed by sealer.'))
        print('TRANSFERRED MANUAL REVIEW',str(audit),flush=True)
    return remaining

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--watch',action='store_true');a=p.parse_args()
    while True:
        pending=transfer(a.manifest,a.root)
        if not pending or not a.watch:break
        print('waiting for sealed identical samples',pending,flush=True);time.sleep(30)
