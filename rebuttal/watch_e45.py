"""CPU-only updates from completed E4/E5 runs; never launches GPU work."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--publish', action='store_true')
    p.add_argument('--once', action='store_true')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    with (a.output / 'watch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = None
        while True:
            files = sorted((a.workspace / 'rebuttal/runs').glob('E[45]*/metrics.json'))
            signature = hashlib.sha256(b''.join(str(f).encode() + f.read_bytes() for f in files)).hexdigest()
            if signature != previous:
                now = datetime.datetime.now().astimezone()
                dest = a.output / now.strftime('%Y%m%d_%H%M%S_%f')
                commands = [[sys.executable, '-m', 'rebuttal.reduce_e45', '--workspace', str(a.workspace), '--output', str(dest)],
                            [sys.executable, '-m', 'rebuttal.report_e45', '--results', str(dest / 'results.json'), '--output', str(dest / 'report.md')]]
                if a.publish:
                    commands[1] += ['--publish', str(a.workspace / 'rebuttal/RESULTS.md')]
                try:
                    for cmd in commands:
                        subprocess.run(cmd, check=True)
                except Exception as error:
                    with (a.output / 'alerts.jsonl').open('a') as alerts:
                        alerts.write(json.dumps({'timestamp': now.isoformat(), 'signature': signature, 'error': str(error), 'path': str(dest)}) + '\n')
                    print('ANALYSIS FAILED', error, flush=True)
                else:
                    tmp = a.output / 'latest.tmp'
                    tmp.write_text(json.dumps({'timestamp': now.isoformat(), 'path': str(dest), 'signature': signature}) + '\n')
                    os.replace(tmp, a.output / 'latest.json')
                    print('REDUCED', dest, flush=True)
                previous = signature  # Retain the failed snapshot; retry on the next completed run.
            if a.once:
                return
            time.sleep(60)


if __name__ == '__main__':
    main()
