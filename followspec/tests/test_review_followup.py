import copy
from followspec.review_followup import replace, long_cell, capacity_cell


def template():
    return dict(name='old', args=['--tag','old','--prompts','oldprompts','--note','old','--code-repo','frozen','--','python','-m','atlas.run_cell','--prompts','oldprompts','--max-new-tokens','512','--max-model-len','4096','--output','oldout'])


def test_long_cell_retains_engine_and_explicit_pairing():
    old=template(); saved=copy.deepcopy(old)
    j=long_cell(old,'new','panel','out',8192)
    assert old==saved
    a=j['args']; i=a.index('--')
    assert a[a.index('--code-repo')+1]=='frozen'
    assert a[a.index('--max-new-tokens')+1]=='8192'
    assert a[:i][a[:i].index('--prompts')+1]=='panel'
    assert a[i+1:][a[i+1:].index('--prompts')+1]=='panel'
    assert a[a.index('--output')+1]=='out'


def test_replace_variable_argument_list():
    a=['--steps','300','--export-steps','50','150','300','--offload']
    replace(a,'--export-steps',['300'])
    assert a==['--steps','300','--export-steps','300','--offload']


def test_capacity_parameter_matches():
    assert 75*(12288+4096)==16*76800
    assert abs(655*76800-4096*12288)/(4096*12288)<.001
