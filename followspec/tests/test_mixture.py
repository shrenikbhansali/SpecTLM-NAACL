import json
import pytest
import torch
from safetensors.torch import load_file,save_file
from followspec.mixture import mix


def sources(tmp_path):
    g=torch.Generator().manual_seed(4);paths=[];updates=[]
    for i,(rank,alpha,rs,modules) in enumerate([(2,4,False,['q_proj']), (3,6,True,['q_proj','v_proj']), (1,2,False,['v_proj'])]):
        root=tmp_path/str(i);root.mkdir();paths.append(root)
        cfg=dict(base_model_name_or_path='base',peft_type='LORA',task_type='CAUSAL_LM',r=rank,lora_alpha=alpha,use_rslora=rs,target_modules=modules,bias='none')
        (root/'adapter_config.json').write_text(json.dumps(cfg))
        tensors={};update={}
        for module in modules:
            key='base_model.model.layers.0.'+module
            A=torch.randn(rank,6,generator=g);B=torch.randn(5,rank,generator=g)
            tensors[key+'.lora_A.weight']=A;tensors[key+'.lora_B.weight']=B
            update[key]=(alpha/(rank**0.5 if rs else rank))*B@A
        save_file(tensors,str(root/'adapter_model.safetensors'));updates.append(update)
    return paths,updates


def dense(path):
    t=load_file(str(path/'adapter_model.safetensors'))
    return {key[:-len('.lora_A.weight')]:t[key.replace('.lora_A.','.lora_B.')]@A for key,A in t.items() if '.lora_A.' in key}


def test_one_hot_zero_and_saved_scaling(tmp_path):
    paths,updates=sources(tmp_path)
    for i in range(3):
        out=tmp_path/f'one{i}';mix(paths,[int(j==i) for j in range(3)],1,out,max_lora_rank=8)
        for module,matrix in dense(out).items():
            torch.testing.assert_close(matrix,updates[i].get(module,torch.zeros_like(matrix)),atol=1e-6,rtol=1e-5)
        cfg=json.loads((out/'adapter_config.json').read_text())
        assert cfg['lora_alpha']==cfg['r']==6
        assert cfg['use_rslora'] is False
    out=tmp_path/'zero';mix(paths,[.2,.3,.5],0,out,max_lora_rank=8)
    assert all(torch.count_nonzero(x)==0 for x in dense(out).values())


@pytest.mark.parametrize('scale',[.5,1.,1.5])
def test_random_mixtures_projection_matches_direct_merge_on_16_inputs(tmp_path,scale):
    paths,updates=sources(tmp_path)
    w=torch.softmax(torch.randn(3,generator=torch.Generator().manual_seed(int(scale*10))),dim=0).tolist()
    out=tmp_path/'mixed';mix(paths,w,scale,out,max_lora_rank=8)
    x=torch.randn(16,6,generator=torch.Generator().manual_seed(9))
    for module,matrix in dense(out).items():
        direct=sum(scale*weight*u.get(module,torch.zeros_like(matrix)) for weight,u in zip(w,updates))
        torch.testing.assert_close(x@matrix.T,x@direct.T,atol=5e-6,rtol=1e-5)


def test_cap_and_no_overwrite(tmp_path):
    paths,_=sources(tmp_path)
    with pytest.raises(ValueError,match='cap'): mix(paths,[.2,.3,.5],1,tmp_path/'too_big',max_lora_rank=1)
    assert not (tmp_path/'too_big').exists()
    with pytest.raises(FileExistsError):mix(paths,[.2,.3,.5],1,paths[0],max_lora_rank=8)


def test_invalid_weights_and_base(tmp_path):
    paths,_=sources(tmp_path)
    for weights in ([1,1,1],[-1,1,1],[float('nan'),0,1]):
        with pytest.raises(ValueError):mix(paths,weights,1,tmp_path/'bad',max_lora_rank=8)
    cfg=json.loads((paths[0]/'adapter_config.json').read_text());cfg['base_model_name_or_path']='other'
    (paths[0]/'adapter_config.json').write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='base'):mix(paths,[.2,.3,.5],1,tmp_path/'bad',max_lora_rank=8)


def test_mixed_dtypes_and_rank_patterns(tmp_path):
    paths,_=sources(tmp_path)
    t=load_file(str(paths[1]/'adapter_model.safetensors'))
    for key in t: t[key]=t[key].to(torch.bfloat16)
    save_file(t,str(paths[1]/'adapter_model.safetensors'))
    cfg=json.loads((paths[1]/'adapter_config.json').read_text())
    cfg['alpha_pattern']={'q_proj':9};(paths[1]/'adapter_config.json').write_text(json.dumps(cfg))
    out=tmp_path/'mixed';mix(paths,[0,1,0],1,out,max_lora_rank=8)
    for module,update in dense(out).items():
        alpha=9 if module.endswith('q_proj') else 6
        expected=alpha/(3**0.5)*t[module+'.lora_B.weight'].float()@t[module+'.lora_A.weight'].float()
        torch.testing.assert_close(update,expected,atol=2e-6,rtol=1e-5)
