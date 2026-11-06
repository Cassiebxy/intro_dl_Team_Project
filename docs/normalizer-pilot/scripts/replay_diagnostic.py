import json, os, pathlib, torch, hashlib
from transformers import AutoTokenizer,AutoModelForCausalLM,GenerationConfig
p = pathlib.Path(os.environ['NORMALIZER_PILOT_RUN']) / 'qwen-four-conditions'
protocol=json.loads((p/'protocol.json').read_text());tok=AutoTokenizer.from_pretrained(protocol['model_path'],local_files_only=True)
prompts={r['id']:r['text'] for r in map(json.loads,(p/'prompts.jsonl').read_text().splitlines())}
gen=GenerationConfig.from_dict(json.loads((p/'full/generation_config.json').read_text()))
out=p/'diagnostic_replay_original_limit.jsonl'
for attention in ['sdpa']:
 model=AutoModelForCausalLM.from_pretrained(protocol['model_path'],local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation=attention).to('mps').eval()
 for cid in ['live_simple_188-113-0','live_simple_70-34-0','live_simple_67-31-0']:
  rid=cid+'__clean__original_first';seed=int(hashlib.sha256(rid.encode()).hexdigest()[:8],16)%(2**31)
  torch.manual_seed(seed);torch.mps.manual_seed(seed);inputs=tok(prompts[rid],return_tensors='pt',add_special_tokens=True).to('mps')
  with torch.inference_mode(): result=model.generate(**inputs,generation_config=gen,max_new_tokens=4096)
  ids=result[0,inputs.input_ids.shape[1]:].tolist();row=dict(id=rid,attention=attention,seed=seed,token_count=len(ids),text=tok.decode(ids,skip_special_tokens=True))
  with out.open('a') as f:f.write(json.dumps(row)+'\n')
  print(json.dumps(row),flush=True)
 del model
 import gc
 gc.collect();torch.mps.empty_cache()
