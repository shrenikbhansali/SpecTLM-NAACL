"""CPU-only, restart-safe D-51 publication as already-running official jobs finish."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workspace', type=Path, required=True)
    ap.add_argument('--catalog', type=Path, required=True)
    ap.add_argument('--stage', type=Path, required=True)
    ap.add_argument('--hours', type=float, default=36)
    ap.add_argument('--poll', type=int, default=300)
    args = ap.parse_args(); ws, stage = args.workspace, args.stage
    stage.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + args.hours * 3600
    code = Path(__file__).resolve().parents[1]
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=code, text=True).strip()
    state = stage / 'published.jsonl'
    seen = {json.loads(x)['fingerprint'] for x in state.read_text().splitlines()} if state.exists() else set()
    while time.time() < deadline:
        paths = []
        for name in ['FIX24_20261009_1420', 'FIX24_official_seeds_20261009']:
            root = ws / 'artifacts' / name
            paths += list(root.glob('repair-eval/runs/*/results.json'))
            paths += list(root.glob('eval/runs/*/results.json'))
            paths += list(root.glob('FIX24-official-*/results.json'))
        signature = '\n'.join(sorted(f'{p}:{p.stat().st_size}:{p.stat().st_mtime_ns}' for p in paths))
        key = hashlib.sha256(signature.encode()).hexdigest()
        if key not in seen:
            now = datetime.datetime.now().astimezone(); stamp = now.strftime('%Y%m%d_%H%M%S')
            out = stage / ('snapshot-' + stamp)
            try:
                env = dict(os.environ, PYTHONPATH=str(code), OPENBLAS_NUM_THREADS='1')
                with (stage / (out.name + '.log')).open('x') as log:
                    subprocess.run(['python', '-m', 'paper.d51_repair_delta', '--workspace', str(ws),
                                    '--catalog', str(args.catalog), '--output', str(out)],
                                   cwd=code, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
                result = json.loads((out / 'results.json').read_text())
                (out / 'analysis-source.json').open('x').write(json.dumps(dict(code_commit=commit, fingerprint=key))+'\n')
                tex = ws / 'paper/tables' / ('D51-' + stamp)
                tex.mkdir(parents=True, exist_ok=False)
                for p in out.glob('*.tex'): shutil.copyfile(p, tex / p.name)
                (tex / 'README.md').open('x').write(f'Pilot D-51 snapshot: {out}/report.md\nCode: {commit}\nSelection: {result["selection"]}\n')
                text = (f'\n### {now.isoformat()} — codex-1 — D-51 repair-delta update\n\n'
                        f'Selection: **{result["selection"]["status"]}**; primary={result["selection"]["primary"]}. '
                        'Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. '
                        'Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. '
                        f'[Immutable report](../{out.relative_to(ws)}/report.md), '
                        f'[main rows](../{out.relative_to(ws)}/r1-main.md), '
                        f'[robustness rows](../{out.relative_to(ws)}/r1-robustness.md), '
                        f'[LaTeX](../{tex.relative_to(ws)}/README.md).\n\n'
                        + (out/'repair-delta-comparison.md').read_text() + '\n')
                if result['selection']['status'] == 'selected':
                    text += ('D-51 main focal rows now use ' + result['selection']['primary'] +
                             '; the other drafter remains a robustness comparison. This supersedes the earlier provisional production choice; '
                             'production timing and MATH-500 measurements keep their original identity.\n\n' +
                             (out/'r1-main.md').read_text() + '\n' + (out/'r1-robustness.md').read_text())
                for name in ['notes/P3.md', 'ledger/EXP-ATL-025.md', 'reports/P3-D50-consolidated-20261009.md']:
                    with (ws/name).open('a') as f: f.write(text)
                record = dict(timestamp=now.isoformat(),fingerprint=key,output=str(out),selection=result['selection'])
                with state.open('a') as f: f.write(json.dumps(record)+'\n')
                seen.add(key)
                print(json.dumps(record), flush=True)
            except Exception as exc:
                error = dict(timestamp=now.isoformat(),error=repr(exc),output=str(out))
                (stage/(out.name+'-ERROR.json')).open('x').write(json.dumps(error)+'\n')
                with (ws/'notes/P3.md').open('a') as f:
                    f.write(f'\n### {now.isoformat()} — codex-1 — D-51 report ERROR\n\n{error}; no result published.\n')
                print(json.dumps(error), flush=True)
        time.sleep(args.poll)

if __name__ == '__main__': main()
