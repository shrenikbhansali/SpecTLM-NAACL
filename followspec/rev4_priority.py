"""D56 stable pending order; preserve job identities and the single dispatcher."""
import fcntl,json,os
from ops.track_t import DISPATCH,lines
ORDER=['Y1','Y2','Y3a','Y4','Y6','Y7','Y5','Y3b','Y8','Y10']

def priority(job):
 n=job['name']
 return next((k for k,x in enumerate(ORDER) if n.startswith('REV4-'+x+'-')),20)

def promote():
 with DISPATCH.with_suffix('.publish.lock').open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX);rows=lines(DISPATCH);ordered=sorted(rows,key=priority)
  if rows==ordered:return
  tmp=DISPATCH.with_name(DISPATCH.name+f'.rev4-priority-{os.getpid()}')
  with tmp.open('x') as h:
   for r in ordered:h.write(json.dumps(r)+'\n')
  os.replace(tmp,DISPATCH)

if __name__=='__main__':promote()
