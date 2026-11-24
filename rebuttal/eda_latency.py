"""A40 batch-one standalone EDA/released first-draft latency, no verifier."""
import argparse,json,time,statistics
from pathlib import Path
import torch
from followspec.independent_kd import write
from followspec.missing_embedding import fill_missing_embedding
from followspec.train_eagle3 import ensure_unpaused

def main():
 p=argparse.ArgumentParser();p.add_argument('--drafters',nargs='+',required=True);p.add_argument('--target',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();ensure_unpaused()
 if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
 from speculators import SpeculatorModel,SpeculatorModelConfig
 out=a.output;out.mkdir(parents=True,exist_ok=False);write(out/'config.json',vars(a)|{'output':str(a.output),'n':1000,'warmup':50,'batch':1,'context_tokens':1,'protocol':'standalone single-token first-draft forward; no existing KV context; includes fc, embedding, decoder, norm, head; excludes verifier and tokenizer'})
 results=[]
 for path in a.drafters:
  cfg=SpeculatorModelConfig.from_pretrained(path,local_files_only=True);cfg.speculators_config.verifier.name_or_path=a.target
  model=SpeculatorModel.from_pretrained(path,config=cfg,local_files_only=True,torch_dtype=torch.bfloat16);fill_missing_embedding(model,path,a.target);model.to('cuda').eval().requires_grad_(False)
  torch.manual_seed(0);hidden=torch.randn(1,1,model.fc.in_features,device='cuda',dtype=torch.bfloat16);ids=torch.tensor([[42]],device='cuda');docs=torch.zeros_like(ids)
  samples=[]
  with torch.no_grad():
   for i in range(1050):
    ensure_unpaused();start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True);start.record()
    result=model(hidden_states=hidden,input_ids=ids,document_ids=docs,ttt_steps=1);end.record();end.synchronize()
    if i>=50:samples.append(start.elapsed_time(end))
  results.append({'drafter':path,'n':len(samples),'median_ms':statistics.median(samples),'mean_ms':statistics.mean(samples),'samples_ms':samples})
  del model,result;torch.cuda.empty_cache()
 write(out/'results.json',{'status':'measured_standalone_not_end_to_end','records':results})
if __name__=='__main__':main()
