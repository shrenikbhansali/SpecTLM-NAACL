"""Advance D56 data only after exact previously inspected samples match sealing."""
import argparse,json,time
from pathlib import Path
from followspec.rev4_data import seal
from followspec.rev4_data_training import checked_audit,prepare
from followspec.rev4_train import sweep
from followspec.rev4_priority import promote
from followspec.rev2_audit_transfer import checked_samples
from followspec.rev3_x5 import publication_complete
from ops.track_t import sha,write

def transfer(review,dest):
 m=json.loads(review.read_text());assert m['manually_reviewed'] and m['reviewer']=='codex-1'
 p=Path(m['sample_path']);assert sha(p)==m['sample_sha256']
 checked_samples(json.loads(p.read_text()),json.loads((dest/'five_decoded_masks.json').read_text()))
 s=json.loads((dest/'seal.json').read_text());assert sha(dest/'per_prompt.jsonl')==s['data_sha256']
 audit=dest/'manual-audit.json'
 if audit.exists():return checked_audit(json.loads(audit.read_text()),s['data_sha256'])
 write(audit,dict(passed=True,data_sha256=s['data_sha256'],reviewer=m['reviewer'],reviewed_at=m['reviewed_at'],review_manifest=str(review),review_manifest_sha256=sha(review),sample_sha256=sha(dest/'five_decoded_masks.json'),comments=m['comments'],scope='Actual prior review, exact decoded text/IDs/mask/boundary matched after sealing; structural/eval checks applied to whole data'))

def advance(source,stage,sealed,review,code,t,experiment):
 label='thinking16k' if experiment=='Y3b' else 'math4k';dest=sealed/label
 if not (dest/'seal.json').exists():
  rows=[r for r in json.loads((source/'plan.json').read_text()) if r['target']==t]
  if not all((Path(r['run_dir'])/'results.json').exists() for r in rows):return 'generating'
  sealed.mkdir(exist_ok=True,parents=True);seal(source,dest,t)
 if not review.exists():return 'needs_manual_five_sample_review'
 transfer(review,dest)
 if experiment=='Y10':raise ValueError('Math mixed-data sealing/audit required before training; do not silently omit it')
 if not publication_complete(stage/'publish-training'):
  if stage.exists():raise ValueError('partial publication needs explicit recovery: '+str(stage))
  prepare(stage,code,sealed,t,experiment)
 return 'exports_pending' if sweep(stage,code) else 'all_evaluations_queued'

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ['source','stage','sealed','review','code']:p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--target',type=int,default=1);p.add_argument('--experiment',choices=['Y3b'],default='Y3b');a=p.parse_args()
 while True:
  state=advance(a.source,a.stage,a.sealed,a.review,a.code,a.target,a.experiment);print(state,flush=True);promote()
  if state=='all_evaluations_queued':break
  time.sleep(30)
