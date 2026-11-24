import datetime
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from rebuttal.run_recorded import seconds_until_deadline, check_baseline_gate, run_command


class RunRecordedTests(unittest.TestCase):
    def test_deadline_is_absolute_and_requires_timezone(self):
        now=datetime.datetime(2026,11,28,16,59,tzinfo=datetime.timezone.utc)
        self.assertEqual(seconds_until_deadline('2026-11-28T12:00:00-05:00',now),60)
        with self.assertRaises(ValueError):seconds_until_deadline('2026-11-28T12:00:00',now)
        with self.assertRaises(ValueError):seconds_until_deadline('2026-11-28T11:58:00-05:00',now)
        self.assertIsNone(seconds_until_deadline(None,now))

    def test_gate_requires_all_matching_target_cells(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'gate.json'
            rows=[dict(target=0,arm=a,benchmark=b,status='pass')
                  for a in ('reuse','full','dedicated') for b in ('speed128','math500')]
            path.write_text(json.dumps(rows))
            plan=dict(requires_baseline_pass=True,target=0,baseline_report=str(path))
            check_baseline_gate(plan)
            rows.pop();path.write_text(json.dumps(rows))
            with self.assertRaises(ValueError):check_baseline_gate(plan)
            with self.assertRaises(ValueError):check_baseline_gate(dict(requires_baseline_pass=True,target=0))
            check_baseline_gate({})

    def test_timeout_stops_child_and_records_deadline(self):
        with tempfile.TemporaryFile(mode='w+') as log:
            code,reason=run_command([sys.executable,'-c','import time;time.sleep(30)'],'.',log,timeout=.1)
            self.assertNotEqual(code,0);self.assertEqual(reason,'deadline')
            code,reason=run_command([sys.executable,'-c','print("ok")'],'.',log,timeout=3)
            self.assertEqual(code,0);self.assertIsNone(reason)


if __name__=='__main__':unittest.main()
