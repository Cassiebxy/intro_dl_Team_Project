from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
import json
import random
from train_main import train, write_rows

root = Path(__file__).resolve().parent
out = root / 'small-a3-no-identity'
out.mkdir(exist_ok=False)
def load(p):
    return [json.loads(line) for line in p.read_text().splitlines()]
a1 = root / 'small-main-20261118'
config = json.loads((a1 / 'run_config.json').read_text())
sets = {}
for split in ('train','dev'):
    rows = load(root / 'data' / f'pairs_{split}.jsonl')
    sets[split] = [dict(r, input=r['input_description'], target=r['target_description'], condition=r['variant']) for r in rows]
by_tool = defaultdict(dict)
for r in sets['train']:
    by_tool[r['source_tool_id']][r['variant']] = r
tools = sorted(by_tool)
random.Random(42).shuffle(tools)
replacement = {tool: by_tool[tool][('suffix_1','prefix_2','suffix_3')[i%3]] for i,tool in enumerate(tools)}
sets['train'] = [replacement[r['source_tool_id']] if r['variant']=='clean' else r for r in sets['train']]
assert len(sets['train']) == 400 and all(r['input'] != r['target'] for r in sets['train'])
config.update(train_exposures_per_epoch=Counter(r['variant'] for r in sets['train']), optimizer_steps=75, resampling='one additional manipulated example per tool; seeded balanced rotation')
(out/'run_config.json').write_text(json.dumps(config,indent=2))
write_rows(out/'train_exposures.jsonl', [dict(example_id=r['example_id'],variant=r['variant']) for r in sets['train']])
train(SimpleNamespace(model=root.parent/'normalizer-flan-t5-small-pilot-20261105'/'model',epochs=3,smoke=False),sets,out)
tuned = load(a1/'rewrites.jsonl')
ablation = load(out/'rewrites.jsonl')
assert len(ablation)==len(tuned)==115
summary = defaultdict(Counter)
paired=[]
for a,b in zip(tuned,ablation):
    assert a['example_id']==b['example_id']
    for name in ('all',a['variant']):
        c=summary[name]
        c.update(n=1,a1_exact=int(a['exact']),a3_exact=int(b['exact']),different_output=int(a['generated']!=b['generated']),a1_only=int(a['exact'] and not b['exact']),a3_only=int(b['exact'] and not a['exact']),a3_truncated=int(b['truncated']),a3_blank=int(not b['generated'].strip()))
    paired.append(dict(example_id=a['example_id'],variant=a['variant'],a1=a['generated'],a3=b['generated'],target=a['target']))
write_rows(out/'paired_comparison.jsonl',paired)
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
