import pytest
from followspec.stress_panel import split_rows, adapter_provenance, user_text


def rows(n=70):return [dict(prompt_id=str(i),prompt='Question '+str(i),rendered_token_ids=[i+1]) for i in range(n)]


def test_fixed_split_is_order_independent_and_disjoint():
    a,b=split_rows(rows(),32,20261007)
    assert (a,b)==split_rows(list(reversed(rows())),32,20261007)
    assert len(a)==len(b)==32 and not {r['prompt_id'] for r in a}&{r['prompt_id'] for r in b}


def test_duplicate_id_content_and_short_panel_rejected():
    with pytest.raises(ValueError):split_rows(rows()+[rows()[0]],32,0)
    r=rows();r[1]['prompt']=r[0]['prompt']
    with pytest.raises(ValueError):split_rows(r,32,0)
    with pytest.raises(ValueError):split_rows(rows(63),32,0)


def test_exact_user_content_removed_from_historical_template():
    assert user_text('<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\nTest?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n')=='Test?'
    assert user_text('raw')=='raw'


def test_adapter_pin_changes_with_any_weight_bytes(tmp_path):
    import json
    (tmp_path/'adapter_config.json').write_text(json.dumps(dict(base_model_name_or_path='base',peft_type='LORA',r=8)))
    (tmp_path/'adapter_model.safetensors').write_bytes(b'fixture')
    a=adapter_provenance(tmp_path,'base')
    (tmp_path/'adapter_model.safetensors').write_bytes(b'changed')
    b=adapter_provenance(tmp_path,'base')
    assert a['revision']!=b['revision'] and len(a['revision'])==40
    with pytest.raises(ValueError):adapter_provenance(tmp_path,'wrong')
