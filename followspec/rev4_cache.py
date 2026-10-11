"""D47 finished-launch vLLM compile-cache reclamation, manifest before removal."""
import argparse,json,shutil,time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from ops.track_t import WS,write

def eligible(cache,root):
 return cache.name=='vllm_cache' and cache.parent.parent==root and not cache.is_symlink() and not cache.parent.is_symlink() and cache.is_dir() and (cache.parent/'exit_code').is_file()

def sweep(root,out):
 paths=[c for c in root.glob('*/vllm_cache') if eligible(c,root)];out.mkdir(exist_ok=False,parents=True)
 write(out/'manifest.json',dict(authorization='D47/D56; finished-launch regenerable compile caches only',paths=[dict(path=str(p),exit_code=(p.parent/'exit_code').read_text().strip()) for p in paths],free_before_gb=shutil.disk_usage(root).free/1e9))
 def rm(p):
  if not eligible(p,root):return dict(path=str(p),status='skipped_recheck')
  shutil.rmtree(p);return dict(path=str(p),status='removed_compile_cache')
 with ThreadPoolExecutor(max_workers=8) as pool, (out/'actions.jsonl').open('x') as f:
  for r in pool.map(rm,paths):f.write(json.dumps(r)+'\n');f.flush()
 write(out/'results.json',dict(paths=len(paths),free_after_gb=shutil.disk_usage(root).free/1e9))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--trigger-gb',type=float,default=380);p.add_argument('--watch',action='store_true');a=p.parse_args();a.output.mkdir(exist_ok=False)
 while True:
  free=shutil.disk_usage(WS/'artifacts').free/1e9
  if free<a.trigger_gb:
   out=a.output/datetime.now().strftime('%Y%m%d_%H%M%S_%f');sweep(WS/'artifacts',out);print('MANIFESTED CACHE RECLAMATION',out,flush=True)
  if not a.watch:break
  time.sleep(60)
