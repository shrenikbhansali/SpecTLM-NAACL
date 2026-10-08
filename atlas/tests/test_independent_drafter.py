"""I1 opt-in method: exercise the actual harness with a fake engine."""
import json
import sys
import types

import pytest

from atlas import run_cell


@pytest.mark.parametrize('method', ['draft_model', 'eagle3', 'eagle', 'dflash'])
def test_method_forwarded_without_changing_decoding(tmp_path, monkeypatch, method):
    prompts = tmp_path / 'prompts.jsonl'
    prompts.write_text(json.dumps(dict(prompt_id='p', prompt='hello', rendered_token_ids=[1, 2])) + '\n')
    out = tmp_path / 'cell'
    captured = {}

    class LLM:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def generate(self, batch, sampling, **kwargs):
            assert batch == [{'prompt_token_ids': [1, 2]}]
            assert sampling == dict(temperature=0., top_p=1., max_tokens=512, seed=0)
            counters = dict(per_step_accepted=[0, 2, 4], per_step_drafted=[4, 4, 4],
                            histogram=[1, 0, 1, 0, 1], num_spec_tokens=4, num_draft_tokens=12)
            completion = types.SimpleNamespace(text='answer', token_ids=[3], spec_decode_metrics=counters)
            return [types.SimpleNamespace(prompt_token_ids=[1, 2], outputs=[completion])]

    monkeypatch.setitem(sys.modules, 'vllm', types.SimpleNamespace(LLM=LLM, SamplingParams=lambda **kw: kw))
    monkeypatch.setitem(sys.modules, 'torch', types.SimpleNamespace(cuda=types.SimpleNamespace(get_device_name=lambda _: 'test GPU')))
    monkeypatch.setattr(run_cell.importlib.metadata, 'version', lambda _: '0.31.0')
    monkeypatch.setattr(run_cell.subprocess, 'check_output', lambda cmd, **kw: '' if 'status' in cmd else 'c' * 40)
    monkeypatch.setattr(run_cell, 'read_drafter_config', lambda *a: {'model_type': 'llama'})
    monkeypatch.setattr(run_cell, 'ensure_unpaused', lambda *a: None)
    monkeypatch.setattr(sys, 'argv', ['run_cell', '--target', 'org/target', '--target-revision', 'a' * 40,
        '--drafter', 'org/draft', '--drafter-revision', 'b' * 40, '--method', method,
        '--prompts', str(prompts), '--output', str(out), '--use-prompt-token-ids', '--enable-lora'])
    run_cell.main()
    assert captured['speculative_config'] == dict(model='org/draft', revision='b' * 40,
                                                  method=method, num_speculative_tokens=4)
    assert captured['enable_lora'] is True
    assert captured['per_request_spec_decode_metrics'] == 'detailed'
    assert captured['enable_prefix_caching'] is False
    config = json.loads((out / 'config.json').read_text())
    assert (config['method'], config['drafter_revision'], config['K'], config['batch_size']) == (method, 'b' * 40, 4, 1)
    result = json.loads((out / 'results.json').read_text())
    assert result['macro_acceptance_length'] == 3
    row = json.loads((out / 'per_prompt.jsonl').read_text())
    assert row['per_position_conditional_acceptance'] == [2/3, 1., .5, 1.]
    assert row['accepted_lengths'] == [1, 3, 5]


def test_unknown_method_rejected():
    with pytest.raises(SystemExit):
        run_cell.parser().parse_args(['--method', 'made_up'])
