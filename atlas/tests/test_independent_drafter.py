from argparse import Namespace
import pytest
from atlas.run_cell import parser, speculative_options


def args(method, mapping=False):
    return Namespace(method=method,drafter='/pinned/draft',drafter_revision='a'*40,K=4,draft_vocab_mapping=mapping)


@pytest.mark.parametrize('method',['eagle3','eagle','dflash'])
def test_existing_speculative_options_unchanged(method):
    assert speculative_options(args(method)) == dict(model='/pinned/draft',revision='a'*40,method=method,num_speculative_tokens=4)
    with pytest.raises(ValueError,match='draft_model'):speculative_options(args(method,True))


def test_independent_draft_uses_engine_vocab_mapping_only_when_requested():
    assert speculative_options(args('draft_model',True))['use_heterogeneous_vocab'] is True
    assert 'use_heterogeneous_vocab' not in speculative_options(args('draft_model'))
    a=parser().parse_args(['--target','base','--target-revision','b'*40,'--drafter','draft','--drafter-revision','a'*40,
                          '--method','draft_model','--draft-vocab-mapping','--prompts','p','--output','o'])
    assert a.method=='draft_model' and a.draft_vocab_mapping and a.K==4
