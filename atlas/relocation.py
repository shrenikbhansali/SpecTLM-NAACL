"""Opt-in verified views of copied sealed inputs; never rewrite their bytes.

SPECTLM_RELOCATION names a sidecar made on the source site, and
SPECTLM_RELOCATION_SHA256 pins that sidecar. File hashes always cover raw bytes.
The view changes absolute metadata paths, never prompt/response text or tokens.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

_CONTENT_FIELDS = {'prompt','completion','reference','text','content','messages',
    'instruction','response','tests','code','rendered_text','question','answer','solution','problem','context','rendered_token_ids','prompt_token_ids',
    'completion_token_ids','input_ids','labels','loss_mask'}
_CACHE = {}


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def absolute(value):
    if not isinstance(value,str) or not Path(value).is_absolute():raise ValueError('absolute relocation path required')
    if '..' in Path(value).parts:raise ValueError('relocation path traversal')
    return str(Path(value))


class Relocation:
    def __init__(self,config):
        if config.get('version')!=1:raise ValueError('unknown relocation version')
        self.prefixes=[(absolute(p['source']),absolute(p['destination'])) for p in config['prefixes']]
        if not self.prefixes or len({a for a,b in self.prefixes})!=len(self.prefixes):raise ValueError('duplicate or missing source prefix')
        if any(a==b for a,b in self.prefixes):raise ValueError('relocation source and destination must differ')
        for old,_ in self.prefixes:
            for _,new in self.prefixes:
                if old==new or old.startswith(new+'/') or new.startswith(old+'/'):
                    raise ValueError('source and destination prefixes overlap')
        self.prefixes.sort(key=lambda p:len(p[0]),reverse=True)
        self.files={absolute(p):h for p,h in config['files_sha256'].items()}
        if not self.files or any(not re.fullmatch('[a-f0-9]{64}',h) for h in self.files.values()):raise ValueError('complete file hashes required')
        self.mapped={}
        for source,h in self.files.items():
            dest=self.path(source)
            if dest==source:raise ValueError('file outside relocation prefixes')
            if dest in self.mapped:raise ValueError('relocation destination collision')
            self.mapped[dest]=h

    @classmethod
    def from_file(cls,path):return cls(json.loads(Path(path).read_text()))

    def path(self,value):
        for old,new in self.prefixes:
            if value==old or value.startswith(old+'/'):
                absolute(value)
                return new+value[len(old):]
        return value

    def verify(self):
        for path,h in self.mapped.items():
            if not Path(path).is_file():raise ValueError(f'relocated input missing: {path}')
            if digest(path)!=h:raise ValueError(f'relocated input changed: {path}')
        return len(self.mapped)

    def view(self,value):
        if isinstance(value,str):return self.path(value)
        if isinstance(value,list):return [self.view(v) for v in value]
        if isinstance(value,dict):
            result={}
            for k,v in value.items():
                key=self.path(k)
                if key in result:raise ValueError('relocation metadata key collision')
                result[key]=v if k in _CONTENT_FIELDS else self.view(v)
            return result
        return value


def active():
    path=os.environ.get('SPECTLM_RELOCATION')
    if not path:return None
    expected=os.environ.get('SPECTLM_RELOCATION_SHA256')
    raw=Path(path).read_bytes()
    if not expected or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('relocation manifest changed or hash pin missing')
    key=(str(Path(path).resolve()),expected)
    if key not in _CACHE:
        r=Relocation(json.loads(raw));r.verify();_CACHE[key]=r
    return _CACHE[key]


def relocate_path(path):
    r=active();return Path(r.path(str(path))) if r else Path(path)


def _read(path):
    r=active();p=(Path(r.path(str(path))) if r else Path(path)).absolute()
    raw=p.read_bytes()
    if r and str(p) in r.mapped and hashlib.sha256(raw).hexdigest()!=r.mapped[str(p)]:raise ValueError(f'relocated input changed: {p}')
    return raw,r


def read_json(path):
    raw,r=_read(path);obj=json.loads(raw);return r.view(obj) if r else obj


def read_jsonl(path):
    raw,r=_read(path);rows=[json.loads(s) for s in raw.decode().splitlines() if s.strip()]
    return r.view(rows) if r else rows


def environment():
    if not os.environ.get('SPECTLM_RELOCATION'):return []
    active()
    return [f'{key}={os.environ[key]}' for key in ('SPECTLM_RELOCATION','SPECTLM_RELOCATION_SHA256')]


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('inventory');a.add_argument('--prefix',nargs=2,action='append',required=True,metavar=('SOURCE','DESTINATION'))
    a.add_argument('--include',nargs='+',required=True);a.add_argument('--output',required=True)
    a=sub.add_parser('verify');a.add_argument('--manifest',required=True)
    a=p.parse_args()
    if a.mode=='verify':print('verified',Relocation.from_file(a.manifest).verify(),'files');return
    files={}
    for item in a.include:
        path=Path(item).absolute()
        if not path.exists():raise ValueError(f'input missing: {path}')
        for f in ([path] if path.is_file() else sorted(path.rglob('*'))):
            if f.is_file() and '.git' not in f.parts:files[str(f)]=digest(f)
    obj=dict(version=1,prefixes=[dict(source=s,destination=d) for s,d in a.prefix],files_sha256=files)
    Relocation(obj)  # schema, boundaries and destination collisions, before writing
    with Path(a.output).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
    print('SPECTLM_RELOCATION_SHA256='+digest(a.output))


if __name__=='__main__':main()
