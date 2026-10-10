"""Keep D54 prerequisite data ahead of long timing without restarting the queue."""
import fcntl,json,os
from ops.track_t import DISPATCH,lines

def priority(j):
    n=j['name']
    if not n.startswith('REV2-'):return 20
    if '-data-' in n:return 0
    if any(n.endswith('-'+w) for w in ['speed128','math64','math500','math32-512','math32-2048','math32-8192']) or '-E14-' in n:return 1
    if '-E9-' in n or '-E12-' in n:return 2
    if '-E8-' in n:return 3
    if '-E10a-' in n:return 4
    if '-E10b-' in n:return 5
    return 10

def promote():
    with DISPATCH.with_suffix('.publish.lock').open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX);rows=lines(DISPATCH);ordered=sorted(rows,key=priority)
        if rows==ordered:return
        tmp=DISPATCH.with_name(DISPATCH.name+f'.priority-{os.getpid()}')
        with tmp.open('x') as h:
            for r in ordered:h.write(json.dumps(r)+'\n')
        os.replace(tmp,DISPATCH)
if __name__=='__main__':promote()
