import json
import subprocess
import sys
import pytest
from atlas.run_cell import engine_prompts, lora_enabled


def test_historical_text_path_and_explicit_exact_token_path():
    rows=[dict(prompt_id='p',prompt='<BOS>chat',rendered_token_ids=[128000,128006,42])]
    assert engine_prompts(rows,False)==['<BOS>chat']
    assert engine_prompts(rows,True)==[{'prompt_token_ids':[128000,128006,42]}]
    assert rows[0]['rendered_token_ids']==[128000,128006,42]


@pytest.mark.parametrize('ids',[None,[],[True],[1.5],[-1],'1,2'])
def test_bad_ids_fail_before_engine(ids):
    with pytest.raises(ValueError,match='token_ids'):engine_prompts([dict(prompt='x',rendered_token_ids=ids)],True)


def test_lora_default_is_unchanged_and_control_is_explicit():
    assert lora_enabled(None,False) is False
    assert lora_enabled('/adapter',False) is True
    assert lora_enabled(None,True) is True
    assert lora_enabled('/adapter',True) is True


def test_dry_run_records_effective_controls_without_loading_gpu(tmp_path):
    p=tmp_path/'prompts.jsonl';p.write_text(json.dumps(dict(prompt_id='p',prompt='already rendered',rendered_token_ids=[128000,42]))+'\n')
    args=[sys.executable,'-m','atlas.run_cell','--target','base/model','--target-revision','a'*40,'--drafter','org/draft',
          '--drafter-revision','b'*40,'--method','eagle3','--prompts',str(p),'--output',str(tmp_path/'unused'),'--dry-run']
    default=subprocess.run(args,text=True,capture_output=True);assert default.returncode==0,default.stderr
    assert json.loads(default.stdout)['config']['enable_lora'] is False
    result=subprocess.run(args+['--use-prompt-token-ids','--enable-lora'],text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    cfg=json.loads(result.stdout)['config'];assert cfg['enable_lora'] and cfg['use_prompt_token_ids']
    assert not (tmp_path/'unused').exists()


def test_raw_query_token_ids_cannot_be_mistaken_for_rendered_context():
    with pytest.raises(ValueError,match='rendered_token_ids'):
        engine_prompts([dict(prompt='<BOS>chat',token_ids=[42])],True)


def test_rendered_ids_are_explicit_and_leave_raw_tokens_unchanged():
    from atlas.workloads import render_evaluation
    class Tokenizer:
        def apply_chat_template(self,messages,**kwargs):return '<BOS>'+messages[0]['content']+'<ASSISTANT>'
        def encode(self,text,add_special_tokens):
            assert not add_special_tokens and text=='<BOS>query<ASSISTANT>'
            return [128000,42,128006]
    row=dict(prompt_id='p',prompt='query',token_ids=[42])
    old=render_evaluation([row],Tokenizer(),'llama')[0]
    assert old['token_ids']==[42] and 'rendered_token_ids' not in old
    new=render_evaluation([row],Tokenizer(),'llama',capture_token_ids=True)[0]
    assert new['token_ids']==[42] and new['rendered_token_ids']==[128000,42,128006]
    assert engine_prompts([new],True)==[{'prompt_token_ids':[128000,42,128006]}]
