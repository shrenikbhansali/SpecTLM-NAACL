"""Durable operator alerts, including pre-launch refusals with no output directory."""
import argparse,datetime,hashlib,json,time,shutil
from pathlib import Path


def failures(events,since):
 return [r for r in events if r.get('t','')>=since and (r.get('event') in ['launch_failed','failed'] or (r.get('event')=='finished' and str(r.get('exit'))!='0'))]


def main():
 p=argparse.ArgumentParser();p.add_argument('--queue-log',required=True);p.add_argument('--since',required=True);p.add_argument('--output',required=True);p.add_argument('--journal',action='append',default=[]);a=p.parse_args();out=Path(a.output);out.mkdir(exist_ok=False);seen=set();last=0
 while True:
  events=[]
  for line in Path(a.queue_log).read_text().splitlines():
   try:events.append(json.loads(line))
   except json.JSONDecodeError:pass
  found=failures(events,a.since);new=[];unresolved=[]
  for r in found:
   key=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()[:20];dest=out/(key+'.json')
   if key not in seen:
    with dest.open('x') as f:json.dump(dict(alert='LAUNCH_OR_RUN_FAILED',event=r,requires_operator_acknowledgment=True),f,indent=2)
    seen.add(key);new.append(r)
   if not (out/(key+'.resolved.json')).exists():unresolved.append(r)
  stamp=datetime.datetime.now().astimezone().isoformat();free=shutil.disk_usage(out).free/1e9
  if new or time.time()-last>=3600:
   entry=f'\n### {stamp} — codex-1 — D50 launch health'+(' ALERT' if unresolved else '')+f'\nFree disk {free:.1f}GB; new failures={json.dumps(new)}; unresolved failures={json.dumps(unresolved)}. Each failure has an immutable alert file in {out}; explicit resolution records required. No failed job is silently retried or treated as running.\n'
   print(entry,flush=True)
   for journal in a.journal:
    with Path(journal).open('a') as f:f.write(entry)
   last=time.time()
  with (out/'health.jsonl').open('a') as f:f.write(json.dumps(dict(t=stamp,free_gb=free,unresolved=len(unresolved),new=len(new)))+'\n')
  time.sleep(60)

if __name__=='__main__':main()
