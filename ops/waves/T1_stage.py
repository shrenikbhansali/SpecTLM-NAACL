"""Track T phase 1 (D-40): download public lineage / reasoning / RL checkpoints, pinned to the commit resolved now.
Writes artifacts/T1_models_20261007/manifest.jsonl (id, revision, license tags, base_model tags, local snapshot, status). Read-only Hub use."""
import json,os,sys,time
from huggingface_hub import HfApi,snapshot_download
OUT='/home/heck2/sbhansali8/SpecTLM/artifacts/T1_models_20261007/manifest.jsonl'
MODELS=[('llama','H1','meta-llama/Llama-3.1-8B'),('llama','H1','allenai/Llama-3.1-Tulu-3-8B-SFT'),('llama','H1','allenai/Llama-3.1-Tulu-3-8B-DPO'),
 ('llama','H1','allenai/Llama-3.1-Tulu-3-8B'),('llama','H1','NousResearch/Hermes-3-Llama-3.1-8B'),('llama','H2','deepseek-ai/DeepSeek-R1-Distill-Llama-8B'),
 ('llama','H2','nvidia/Llama-3.1-Nemotron-Nano-8B-v1'),('llama','H3','luckeciano/Llama-3.1-8B-Instruct-GRPO-Base-v2_2886'),
 ('llama','H3','luckeciano/Llama-3.1-8B-Instruct-GRPO-Base-v2_4461'),('llama','H3','zztheaven/Llama-3.1-8B-Instruct-Open-R1-GRPO'),
 ('qwen3','H1','Qwen/Qwen3-8B-Base'),('qwen3','H2','deepseek-ai/DeepSeek-R1-0528-Qwen3-8B'),('qwen3','H3','shufanshen/Qwen3-8B-GRPO-DeepMath-50-steps'),
 ('qwen3','H3','shufanshen/Qwen3-8B-GRPO-DeepMath-150-steps'),('qwen3','H3','OpenLearnLM/deepseek_qwen3_8b_think_reward_grpo_step_300'),
 ('qwen3','H3','OpenLearnLM/deepseek_qwen3_8b_nothink_grpo_step_300'),('qwen3','H3','etiennebamas/qwen3-8b-classic-grpo-step-250'),
 ('qwen3','H3','tokyotech-llm/Qwen3-Swallow-8B-RL-v0.2')]
api=HfApi(); done={json.loads(l)['id'] for l in open(OUT) if '"ok"' in l} if os.path.exists(OUT) else set()
for base,h,m in MODELS:
    if m in done: continue
    rec=dict(id=m,base=base,hypothesis=h,t=time.strftime('%Y-%m-%dT%H:%M:%S'))
    try:
        info=api.model_info(m); rec['revision']=info.sha
        rec['license']=[t for t in info.tags if t.startswith('license:')]; rec['base_model']=[t for t in info.tags if t.startswith('base_model:')]
        rec['path']=snapshot_download(m,revision=info.sha,allow_patterns=['*.json','*.safetensors','tokenizer*','*.model','*.txt','*.jinja','*.py'],
                                     ignore_patterns=['original/*','*.pth'],max_workers=8)
        rec['status']='ok'
    except Exception as e:
        rec['status']='failed'; rec['error']=repr(e)[:300]
    with open(OUT,'a') as f: f.write(json.dumps(rec)+'\n')
    print(rec['status'],m,flush=True)
print('T1 STAGE DONE',flush=True)
