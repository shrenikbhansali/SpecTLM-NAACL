"""Task-quality diagnostics for D-39; separate from unchanged acceptance metrics."""
import json
import os
import re
import secrets
import signal
import subprocess
import numpy as np


def math_answer(text):
    # Same answer rule as the historical tlm_sd.quality GSM8K scorer.
    pattern=r'[-+]?(?:\d[\d,]*\.?\d*|\.\d+)'
    matches=re.findall(pattern,text.rsplit('####',1)[-1] if '####' in text else text)
    if not matches:return None
    value=matches[0] if '####' in text else matches[-1]
    number=float(value.replace(',',''))
    return str(int(number)) if number.is_integer() else f'{number:.10g}'


def code_pass(code,tests):
    fenced=re.search(r'```(?:python)?\s*(.*?)```',code,re.I|re.S)
    code=fenced.group(1).strip() if fenced else code.strip()
    nonce=secrets.token_hex(24)
    worker='''import sys,json,resource
resource.setrlimit(resource.RLIMIT_CPU,(2,2))
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,1024**2))
resource.setrlimit(resource.RLIMIT_NPROC,(16,16))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
code,tests,nonce=json.load(sys.stdin)
namespace={}
try:
    exec(compile(code,'candidate','exec'),namespace)
    for test in tests:exec(compile(test,'test','exec'),namespace)
except BaseException:
    sys.exit(1)
print(nonce,flush=True)
'''
    cmd=['bwrap','--unshare-all','--die-with-parent','--cap-drop','ALL',
         '--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64',
         '--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir','/tmp',
         '/usr/bin/python3.11','-I','-c',worker]
    # Bounded output file avoids memory growth from generated print loops.
    import tempfile
    with tempfile.TemporaryFile() as log:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.DEVNULL,start_new_session=True,env={"PATH":"/usr/bin:/bin"})
        try:process.communicate(json.dumps([code,tests,nonce]).encode(),timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.communicate();return dict(passed=False,reason='timeout')
        log.seek(0);output=log.read(1024**2)
    return dict(passed=process.returncode==0 and nonce.encode() in output.splitlines(),returncode=process.returncode)


def compare(prompts,parent,child):
    ids=[r['prompt_id'] for r in prompts]
    if not prompts or len(set(ids))!=len(ids) or ids!=[r['prompt_id'] for r in parent] or ids!=[r['prompt_id'] for r in child]:
        raise ValueError('quality prompt alignment differs')
    domain=prompts[0]['domain'];details=[]
    if domain not in ('math','code') or any(r['domain']!=domain for r in prompts):raise ValueError('unsupported quality domain')
    for r,p,c in zip(prompts,parent,child):
        if domain=='math':
            ref=math_answer(r['reference'])
            if ref is None:raise ValueError('missing reference answer')
            a=float(math_answer(p['completion'])==ref);b=float(math_answer(c['completion'])==ref)
        else:
            if not code_pass(r['reference'],r['tests'])['passed']:raise ValueError('reference code fails sandbox; inspect test setup before using quality')
            a=float(code_pass(p['completion'],r['tests'])['passed']);b=float(code_pass(c['completion'],r['tests'])['passed'])
        details.append(dict(prompt_id=r['prompt_id'],parent=a,child=b))
    delta=np.array([r['child']-r['parent'] for r in details]);rng=np.random.default_rng(20261007)
    interval=np.quantile(delta[rng.integers(0,len(delta),size=(10000,len(delta)))].mean(1),[.025,.975]).tolist()
    return dict(domain=domain,metric='exact_match' if domain=='math' else 'pass_at_1_visible_MBPP_tests',n=len(details),
        parent_score=float(np.mean([r['parent'] for r in details])),child_score=float(np.mean([r['child'] for r in details])),
        delta=float(delta.mean()),delta_ci95_paired_prompts=interval,per_prompt=details,
        caveat='Small fixed development subset; uncertainty conditional on this trained target. Historical prompt includes MBPP visible tests.')
