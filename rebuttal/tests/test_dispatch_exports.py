import json
from pathlib import Path
import tempfile
import unittest

from rebuttal.dispatch_exports import append_unique, completed_exports, write_immutable, evaluation


class ExportDispatchTests(unittest.TestCase):
    def test_export_requires_final_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            export = root / 'export-100'
            export.mkdir()
            (export / 'config.json').write_text('{}')
            self.assertEqual(completed_exports(root), [])
            (export / 'repair_provenance.json').write_text('{"step": 100}')
            self.assertEqual(completed_exports(root), [export])

    def test_append_is_idempotent_and_conflicting_identity_refused(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'jobs.jsonl'
            old = {'name': 'old', 'args': ['old']}
            new = {'name': 'new', 'args': ['new']}
            path.write_text(json.dumps(old) + '\n')
            self.assertEqual(append_unique(path, [new]), ['new'])
            self.assertEqual(append_unique(path, [new]), [])
            self.assertEqual([json.loads(x) for x in path.read_text().splitlines()], [old, new])
            with self.assertRaises(ValueError):
                append_unique(path, [{'name': 'new', 'args': ['changed']}])

    def test_existing_output_plan_never_rewritten(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'plan.json'
            write_immutable(p, {'x': 1})
            write_immutable(p, {'x': 1})
            with self.assertRaises(ValueError):
                write_immutable(p, {'x': 2})
            self.assertEqual(json.loads(p.read_text()), {'x': 1})

    def test_eval_keeps_frozen_generation_seed_and_prompts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stage = root / 'stage'; stage.mkdir()
            output = root / 'output'; output.mkdir()
            export = root / 'export-100'; export.mkdir()
            (export / 'config.json').write_text('{}')
            gate = root / 'gate.json'; gate.write_text('[]')
            name = 'E2_t0_interface_speed128_s0'
            plan = {'command': ['eval', '--drafter', '/old', '--drafter-revision', 'old', '--output', '/oldout', '--prompts', '/unchanged', '--seed', '0'],
                    'input_sha256': {'/old/config.json': 'old', '/unchanged': 'prompt-hash'},
                    'seed': 0, 'K': 4, 'harness_commit': '6da2e42'}
            (stage / (name + '.json')).write_text(json.dumps(plan))
            job = {'name': name, 'args': ['--tag', name, '--drafter-model', '/old', '--drafter-rev', 'old', '--plan', '/oldplan']}
            (stage / 'jobs.jsonl').write_text(json.dumps(job) + '\n')
            training = {'target': 0, 'seed': 2, 'name': 'train', 'baseline_report': str(gate), 'harness_commit': 'trained-commit', 'experiment': 'E2'}
            actual = evaluation(root, output, stage, training, export, 'all', 'speed128')
            saved = json.loads((output / (actual['name'] + '.json')).read_text())
            self.assertEqual(saved['training_seed'], 2)
            self.assertEqual(saved['seed'], 0)
            self.assertEqual(saved['harness_commit'], '6da2e42')
            self.assertEqual(saved['input_sha256']['/unchanged'], 'prompt-hash')
            self.assertEqual(saved['command'][-4:], ['--prompts', '/unchanged', '--seed', '0'])


if __name__ == '__main__':
    unittest.main()
