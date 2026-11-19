"""Matched dev evaluation using exact AutoDL request replay. Flag cache misses."""
import json, hashlib, copy, zipfile
from collections import defaultdict
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModelForSeq2SeqLM
out=Path(__file__).resolve().parent
root=out.parent
repo=Path(__file__).resolve().parents[3]
base=repo/'table3/controlled_baseline/generated/full_factorial_v2'
def lines(p):
    return [json.loads(l) for l in p.read_text().splitlines()]
manifest=lines(root/'data/split_manifest.jsonl')
cases=sorted({c for r in manifest if r['split']=='dev' for c in r['source_cases']}, key=lambda c:hashlib.sha256(c.encode()).hexdigest())[:16]
maps={r['experiment_id']:r for r in lines(base/'controlled_mapping.jsonl')}
with zipfile.ZipFile(repo/'qwen-controlled-results.zip') as z:
    def archived(filename):
        return z.read(next(n for n in z.namelist() if n.endswith('/'+filename)))
    cfg=json.loads(archived('run_manifest.json'))
    for f,k in [('controlled_inputs.jsonl','input_sha256'),('controlled_mapping.jsonl','mapping_sha256')]:
        assert hashlib.sha256((base/f).read_bytes()).hexdigest()==cfg[k]
    scores={r['experiment_id']:r for r in map(json.loads,archived('per_case_structured_results.jsonl').splitlines())}
rows=lines(base/'controlled_inputs.jsonl')
def key(m,p):
    return (m['source_case_id'],m['order'],m['name_mapping'],m['seed'],json.dumps(p,sort_keys=True,ensure_ascii=False))
cache={key(maps[r['experiment_id']],r['model_input']):r['experiment_id'] for r in rows}
subset=[r for r in rows if (m:=maps[r['experiment_id']])['source_case_id'] in cases and m['description_condition'] in ('clean_control','table3_cue_1') and m['name_mapping']=='original_suffix1']
assert len(subset)==64
texts=sorted({t['description'] for r in subset for t in r['model_input']['function']})
torch.set_num_threads(4)
ck=root/'small-a3-no-identity/checkpoint'
tok=AutoTokenizer.from_pretrained(ck,local_files_only=True)
model=AutoModelForSeq2SeqLM.from_pretrained(ck,local_files_only=True).eval()
rewrites={}
for i in range(0,len(texts),4):
    chunk=texts[i:i+4]
    x=tok(['Remove promotional language. Preserve all functional details: '+t for t in chunk],padding=True,return_tensors='pt')
    cap=min(256,max(64,2*int(x.attention_mask.sum(1).max())))
    with torch.inference_mode(): y=model.generate(**x,max_new_tokens=cap,do_sample=False)
    rewrites.update(zip(chunk,tok.batch_decode(y,skip_special_tokens=True)))
results=[]
for r in subset:
    m=maps[r['experiment_id']]
    label='clean' if m['description_condition']=='clean_control' else 'manipulated'
    for norm in [False,True]:
        p=copy.deepcopy(r['model_input'])
        if norm:
            for t in p['function']: t['description']=rewrites[t['description']]
        rid=cache.get(key(m,p))
        results.append(dict(case=m['source_case_id'],order=m['order'],condition=label+('_norm' if norm else ''),source_id=r['experiment_id'],matched_id=rid,score=scores[rid] if rid else None,model_input=p))
(out/'requests_and_scores.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results))
(out/'rewrites.json').write_text(json.dumps(rewrites,ensure_ascii=False,indent=2))
for label in ('clean','manipulated','manipulated_norm','clean_norm'):
 for order in ('original_first','edited_first'):
    s=[r['score'] for r in results if r['condition']==label and r['order']==order and r['score']]
    print(label,order,len(s),[sum(v[k] for v in s) for k in ('selected_edited','selected_original','edited_cur_correct','original_cur_correct','strict_overall_correct')])
