import json
from pathlib import Path
import pytest
from atlas.run_cell import sha256
from followspec.render_inputs import render_rows,load_bundle,write_bundle


class Tokenizer:
    def apply_chat_template(self,messages,**kwargs):
        assert kwargs['enable_thinking'] is False and kwargs['add_generation_prompt']
        return '<child>'+messages[0]['content']+'</user><assistant>'
    def encode(self,text,add_special_tokens):
        assert not add_special_tokens
        return list(text.encode())


def test_shared_training_context_is_identical_for_parent_and_child(tmp_path):
    rows=[dict(prompt_id='p',prompt='A training question?',split='training')]
    source=tmp_path/'raw.jsonl';source.write_text(json.dumps(rows[0])+'\n')
    result=render_rows(rows,Tokenizer())
    meta=dict(prompt_target_id='bank-child',tokenizer_sha256='vocab',prompt_sha256=sha256(source))
    out=tmp_path/'bundle';write_bundle(out,result,meta)
    a=load_bundle(out/'prompts.jsonl',rows,prompt_target='bank-child',base_tokenizer_sha256='vocab',prompt_sha256=sha256(source))
    b=load_bundle(out/'prompts.jsonl',rows,prompt_target='bank-child',base_tokenizer_sha256='vocab',prompt_sha256=sha256(source))
    assert a==b==[{'prompt_token_ids':Tokenizer().encode('<child>A training question?</user><assistant>',False)}]
    with pytest.raises(ValueError):load_bundle(out/'prompts.jsonl',rows,prompt_target='base',base_tokenizer_sha256='vocab',prompt_sha256=sha256(source))
    with pytest.raises(ValueError):load_bundle(out/'prompts.jsonl',rows,prompt_target='bank-child',base_tokenizer_sha256='different',prompt_sha256=sha256(source))
    (out/'prompts.jsonl').write_text('{}\n')
    with pytest.raises(ValueError):load_bundle(out/'prompts.jsonl',rows,prompt_target='bank-child',base_tokenizer_sha256='vocab',prompt_sha256=sha256(source))


def test_evaluation_or_already_rendered_queries_cannot_be_training_contexts():
    with pytest.raises(ValueError):render_rows([dict(prompt_id='p',prompt='x',split='evaluation')],Tokenizer())
    with pytest.raises(ValueError):render_rows([dict(prompt_id='p',prompt='x',split='training',format='chat_template_rendered')],Tokenizer())
