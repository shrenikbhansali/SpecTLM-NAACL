"""D56 uncentered least-squares / orthogonal per-tap maps folded into fc."""
import argparse,json,time,subprocess
from pathlib import Path
import torch
from atlas.run_cell import ensure_unpaused,sha256,write_new
from followspec.disk_guard import require_free

def fit_maps(gram,cross):
 if gram.shape!=cross.shape or gram.ndim!=2 or gram.shape[0]!=gram.shape[1]:raise ValueError('square paired moments required')
 if not torch.isfinite(gram).all() or not torch.isfinite(cross).all():raise ValueError('nonfinite fit moments')
 ls=torch.linalg.pinv(gram,hermitian=True,rtol=1e-10)@cross
 u,s,vh=torch.linalg.svd(cross,full_matrices=False);orthogonal=u@vh
 return ls,orthogonal

def fold_maps(weight,maps):
 width=maps[0].shape[0]
 if weight.shape[1]!=width*len(maps) or any(a.shape!=(width,width) for a in maps):raise ValueError('tap layout mismatch')
 return torch.cat([weight[:,k*width:(k+1)*width]@a.to(weight).T for k,a in enumerate(maps)],1)

def main():
 p=argparse.ArgumentParser();
 for key in ['parent','child','drafter','data','audit','forbidden','output']:p.add_argument('--'+key,required=True)
 p.add_argument('--count',type=int,default=4000);p.add_argument('--min-free-gb',type=float,default=350);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
 from followspec.family_repair import validate_rows
 from atlas.workloads import prompt_hash
 from ops.track_t import lines
 allrows=lines(Path(a.data));rows=allrows[:a.count];assert len(rows)==a.count
 validate_rows(rows,{prompt_hash(r.get('raw_prompt',r.get('prompt'))) for r in lines(Path(a.forbidden))},4097)
 audit=json.loads(Path(a.audit).read_text());assert audit['passed'] and audit['data_sha256']==sha256(a.data)
 cfg=vars(a)|dict(n=len(rows),data_sha256=sha256(a.data),audit_sha256=sha256(a.audit),forbidden_sha256=sha256(a.forbidden),code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),fit='uncentered Xchild A=Yparent; fp64 moments; pinv Gram rtol1e-10; Procrustes U@Vh; fc block W@A.T',positions='same assistant-prediction feature positions as native repair: response_start-2:-2',seed=0)
 if a.dry_run:print(json.dumps(cfg));return
 ensure_unpaused();require_free(a.output,a.min_free_gb);assert 'A40' in torch.cuda.get_device_name(0)
 from transformers import AutoModelForCausalLM
 from speculators import SpeculatorModel,SpeculatorModelConfig
 from followspec.missing_embedding import fill_missing_embedding
 from followspec.checkpoint_storage import shared_export
 from atlas.covariates import tap_layers
 from safetensors.torch import save_file
 out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write_new(out/'config.json',cfg);start=time.monotonic();torch.manual_seed(0);torch.set_num_threads(8)
 teachers=[AutoModelForCausalLM.from_pretrained(x,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda').eval().requires_grad_(False) for x in [a.parent,a.child]]
 taps=tap_layers(json.loads((Path(a.drafter)/'config.json').read_text()),teachers[0].config.num_hidden_layers);width=teachers[0].config.hidden_size
 gram=torch.zeros((len(taps),width,width),device='cuda',dtype=torch.float64);cross=torch.zeros_like(gram);tokens=0
 with (out/'progress.jsonl').open('x') as f,torch.no_grad():
  for n,row in enumerate(rows,1):
   ensure_unpaused();require_free(out,a.min_free_gb);ids=torch.tensor(row['input_ids'],device='cuda').unsqueeze(0);feats=[]
   for model in teachers:
    h=model.model(input_ids=ids,output_hidden_states=True,use_cache=False).hidden_states
    feats.append(torch.stack([h[k][0,row['response_start']-2:-2].double() for k in taps]));del h
   parent,child=feats;gram.add_(torch.bmm(child.transpose(1,2),child));cross.add_(torch.bmm(child.transpose(1,2),parent));tokens+=child.shape[1]
   if n%20==0:f.write(json.dumps(dict(n=n,tokens=tokens,elapsed_s=time.monotonic()-start))+'\n');f.flush()
   del feats,parent,child
 gram=gram.cpu();cross=cross.cpu();del teachers,model,ids;torch.cuda.empty_cache();maps={'ls':[],'procrustes':[]}
 for g,c in zip(gram,cross,strict=True):
  ls,op=fit_maps(g,c);maps['ls'].append(ls);maps['procrustes'].append(op)
 save_file({f'{name}.tap{k}':m.float().contiguous() for name,ms in maps.items() for k,m in enumerate(ms)},out/'maps.safetensors')
 conf=SpeculatorModelConfig.from_pretrained(a.drafter,local_files_only=True);conf.speculators_config.verifier.name_or_path=a.child;conf.eagle_aux_hidden_state_layer_ids=taps;conf.transformer_layer_config._attn_implementation='eager'
 draft=SpeculatorModel.from_pretrained(a.drafter,config=conf,local_files_only=True,torch_dtype=torch.float32);write_new(out/'embedding_source.json',fill_missing_embedding(draft,a.drafter,a.child));weight=draft.fc.weight.detach().clone();exports={}
 for name,ms in maps.items():
  with torch.no_grad():draft.fc.weight.copy_(fold_maps(weight,ms))
  dest=out/('export-'+name);shared_export(draft,dest,out.parent/'shared-shards',draft.state_dict(),{'fc.weight'},a.min_free_gb);write_new(dest/'repair_provenance.json',dict(kind='training-free '+name,changed_keys=['fc.weight'],config_sha256=sha256(out/'config.json'),maps_sha256=sha256(out/'maps.safetensors')));exports[name]=str(dest)
 write_new(out/'results.json',dict(n=len(rows),n_tokens=tokens,taps=taps,exports=exports,wall_s=time.monotonic()-start,max_gpu_allocated_gb=torch.cuda.max_memory_allocated()/2**30))
if __name__=='__main__':main()
