import json
from pathlib import Path
import tempfile
import unittest
from rebuttal.budget_guard import usage, is_target_process


class BudgetTests(unittest.TestCase):
    def test_finished_and_live_time_both_count(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a=root/'E2_done'; a.mkdir(); (a/'metrics.json').write_text('{"gpu_hours": 2}')
            b=root/'E2_running'; b.mkdir(); (b/'cmd.txt').write_text('cmd')
            import os
            os.utime(b/'cmd.txt', (1000,1000))
            other=root/'E4_done';other.mkdir();(other/'metrics.json').write_text('{"gpu_hours": 99}')
            self.assertEqual(usage(root,'E2_',now=4600),3)

    def test_exact_module_output_and_uid_only(self):
        args=['python','-m','followspec.family_repair','--output','/run/cell']
        self.assertTrue(is_target_process(args,100,100,{'/run/cell'}))
        self.assertFalse(is_target_process(args,101,100,{'/run/cell'}))
        self.assertFalse(is_target_process(args,100,100,{'/different'}))
        self.assertFalse(is_target_process(['python','-c',' '.join(args)],100,100,{'/run/cell'}))


if __name__ == '__main__':unittest.main()
