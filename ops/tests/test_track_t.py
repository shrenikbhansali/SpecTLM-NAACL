import copy
import pytest
from ops.track_t import validate_render, build_jobs, conditional_counts


class Tokenizer:
    bos_token_id = 1
    def encode(self, text, add_special_tokens=False): return [1, 4]
    def decode(self, ids, **kwargs): return 'rendered'


def test_render_rejects_missing_duplicate_and_changed_tokens():
    raw = [{'prompt_id': 'a', 'prompt': 'raw'}]
    rows = [{'prompt_id': 'a', 'raw_prompt': 'raw', 'prompt': 'rendered', 'rendered_token_ids': [1, 4]}]
    assert validate_render(rows, raw, Tokenizer(), 10)['n'] == 1
    for key, val in [('rendered_token_ids', [1, 1, 4]), ('raw_prompt', 'other'), ('prompt_id', 'b')]:
        bad = copy.deepcopy(rows); bad[0][key] = val
        with pytest.raises(ValueError): validate_render(bad, raw, Tokenizer(), 10)
    with pytest.raises(ValueError): validate_render(rows * 2, raw, Tokenizer(), 10)
    with pytest.raises(ValueError): validate_render(rows, raw, Tokenizer(), 4)


def test_72_cells_are_paired_native_k_and_safe(tmp_path):
    models = [dict(id=f'model-{i}', base='llama' if i < 10 else 'qwen3', revision='a'*40,
                   path=f'/snapshots/{i}', hypothesis='H1', license=[]) for i in range(18)]
    index = {r['id']: {'rendered': '/prompts/'+r['id']} for r in models}
    jobs, records = build_jobs(models, index, tmp_path)
    assert len(jobs) == len(records) == len({j['name'] for j in jobs}) == 72
    for i in range(0, 72, 2):
        a, b = records[i:i+2]
        assert a['cell'] == 'A00' and b['cell'] == 'A10'
        assert a['prompt_file'] == b['prompt_file'] and a['K'] == b['K']
        assert a['K'] == (4 if a['method'] == 'eagle3' else 10 if a['base'] == 'llama' else 16)
        assert a['argv'][a['argv'].index('--target')+1] != b['argv'][b['argv'].index('--target')+1]
    for j in jobs:
        assert set(j['allowed_nodes']) == {'heck-srv1','heck-srv3'}
        assert '--use-prompt-token-ids' in j['args'] and '--enable-lora' not in j['args']
        assert 'VLLM_CACHE_ROOT={out_dir}/vllm_cache' in j['args']


def test_conditional_denominator_accounts_for_short_proposals():
    assert conditional_counts([0, 1, 2], [1, 1, 3], 3) == ([2, 1, 0], [3, 1, 1])
    with pytest.raises(ValueError): conditional_counts([3], [2], 3)
