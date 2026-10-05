"""Create a new environment; never modify an existing one. No GPU execution."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

p=argparse.ArgumentParser();p.add_argument('--prefix',required=True);p.add_argument('--lock-output',required=True)
a=p.parse_args();dest=Path(a.prefix).resolve();lock=Path(a.lock_output).resolve()
if dest.exists() or lock.exists(): raise SystemExit('Refusing to overwrite environment or lock directory')
release=json.load(urllib.request.urlopen('https://pypi.org/pypi/vllm/json',timeout=30))
version=release['info']['version']
if tuple(map(int,version.split('.')[:2])) < (0,20): raise SystemExit('No acceptable stable release')
lock.mkdir(parents=True)
(lock/'engine.json').write_text(json.dumps({'vllm_version':version,'source':'https://pypi.org/pypi/vllm/json','python':sys.version,'release_files':[{k:f[k] for k in ('filename','digests','url')} for f in release['urls']]},indent=2)+'\n')
subprocess.run([sys.executable,'-m','venv',str(dest)],check=True)
python=str(dest/'bin/python')
pip_env={k:v for k,v in os.environ.items() if not k.startswith('PIP_')}
pip_env['PIP_CONFIG_FILE']=os.devnull
subprocess.run([python,'-m','pip','install','--index-url','https://pypi.org/simple','--no-cache-dir',f'vllm=={version}','pytest'],check=True,env=pip_env)
subprocess.run([python,'-m','pip','check'],check=True)
with (lock/'requirements.freeze.txt').open('x') as out:
 subprocess.run([python,'-m','pip','freeze','--all'],stdout=out,check=True)
with (lock/'installed.json').open('x') as out:
 subprocess.run([python,'-m','pip','inspect'],stdout=out,check=True)
print('ENVIRONMENT_READY',dest,flush=True)
