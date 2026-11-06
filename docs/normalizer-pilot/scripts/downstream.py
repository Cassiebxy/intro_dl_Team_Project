import copy
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from transformers import AutoTokenizer
from table3_baseline.core import read_jsonl, write_jsonl, upstream_prompt, sha256
from table3_baseline.runner import dump, output_budget, run

BASE = Path(os.environ['TABLE3_BASELINE_RUN'])
PILOT = Path(os.environ['NORMALIZER_PILOT_RUN'])
ROOT = PILOT / 'qwen-four-conditions'
CONDITIONS = ['clean', 'manipulated', 'normalized', 'clean_normalized']


def prepare():
    ROOT.mkdir(exist_ok=True)
    if (ROOT / 'protocol.json').exists():
        return
    protocol = json.loads((BASE / 'protocol.json').read_text())
    tokenizer = AutoTokenizer.from_pretrained(protocol['model_path'], local_files_only=True)
    source = {r['case_id']: r for r in read_jsonl(BASE / 'requests.jsonl')
              if r['cue_id'] == 1 and r['order'] == 'original_first'}
    rewrites = [json.loads(line) for line in (PILOT / 'first-train/rewrites.jsonl').read_text().splitlines()]
    clean = {r['tool']: r for r in rewrites if r['condition'] == 'clean'}
    # Key by exact target too, since a tool name may have translated descriptions.
    clean = {(r['tool'], r['target']): r for r in rewrites if r['condition'] == 'clean'}
    rows, prompts = [], []
    for edited in [r for r in rewrites if r['condition'] == 'unseen_wording']:
        case = source[edited['source_cases'][0]]
        original = clean[(edited['tool'], edited['target'])]
        assert case['function'][0]['description'].strip() == edited['target']
        for condition in CONDITIONS:
            for order in ['original_first', 'edited_first']:
                row = copy.deepcopy(case)
                row['id'] = f"{row['case_id']}__{condition}__{order}"
                row['condition'] = condition
                row['source_group'] = edited['source_group']
                row['order'] = order
                descriptions = {
                    'clean': (edited['target'], edited['target']),
                    'manipulated': (edited['target'], edited['input']),
                    'normalized': (original['generated'], edited['generated']),
                    'clean_normalized': (original['generated'], original['generated']),
                }[condition]
                for tool, description in zip(row['function'], descriptions):
                    tool['description'] = description
                if order == 'edited_first':
                    row['function'].reverse()
                prompt = upstream_prompt(row, protocol['upstream_path'])
                row['prompt_tokens'] = len(tokenizer.encode(prompt, add_special_tokens=True))
                row['max_new_tokens'] = output_budget(row['prompt_tokens'], protocol['context'])
                rows.append(row)
                prompts.append(dict(id=row['id'], text=prompt))
    write_jsonl(ROOT / 'requests.jsonl', rows)
    write_jsonl(ROOT / 'prompts.jsonl', prompts)
    write_jsonl(ROOT / 'expected.jsonl', [dict(id=r['id'], roles=r['roles'], ground_truth=r['expected']) for r in rows])
    smoke_cases = sorted({r['case_id'] for r in rows})[:2]
    write_jsonl(ROOT / 'smoke_requests.jsonl', [r for r in rows if r['case_id'] in smoke_cases])
    protocol['input_hashes'] = {name: sha256(ROOT / name) for name in
        ['requests.jsonl', 'prompts.jsonl', 'expected.jsonl', 'smoke_requests.jsonl']}
    protocol.update(request_count=len(rows), case_ids=sorted({r['case_id'] for r in rows}),
                    experiment='four conditions; fixed role-name mapping; one unseen assertive paraphrase',
                    normalizer_sha256=sha256(PILOT / 'first-train/checkpoint/model.safetensors'),
                    normalizer_outputs_sha256=sha256(PILOT / 'first-train/rewrites.jsonl'))
    dump(ROOT / 'protocol.json', protocol)


def summarize():
    mapping = {r['id']: r for r in read_jsonl(ROOT / 'requests.jsonl')}
    groups = defaultdict(list)
    for score in read_jsonl(ROOT / 'full/scores.jsonl'):
        row = mapping[score['id']]
        groups[(row['condition'], row['order'])].append((row, score))
    result = []
    for (condition, order), pairs in groups.items():
        n = len(pairs)
        item = dict(condition=condition, order=order, n=n,
                    cr=sum(s['cr'] for _, s in pairs)/n,
                    rec=sum(len(s['calls']) == 1 and len(s['diagnostics']) == 1
                            and s['diagnostics'][0]['valid'] for _, s in pairs)/n,
                    parse_failures=sum(s['status'] == 'parse_error' for _, s in pairs))
        for role in ['original', 'edited']:
            selected = sum(any(r['roles'][role] in call for call in s['calls']) for r, s in pairs)
            correct = sum(s[role+'_correct'] for _, s in pairs)
            item[role+'_sr'] = selected/n
            item[role+'_aac'] = correct/selected if selected else None
            item[role+'_cur'] = correct/n
        item['selection_ratio'] = item['edited_sr']/item['original_sr'] if item['original_sr'] else None
        result.append(item)
    with (ROOT / 'metrics_by_condition_order.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=result[0])
        writer.writeheader()
        writer.writerows(result)
    dump(ROOT / 'metrics.json', result)
    print(json.dumps(result, indent=2), flush=True)


prepare()
if sys.argv[-1] == 'prepare':
    print(ROOT)
else:
    run(ROOT, 'smoke')
    run(ROOT, 'full')
    summarize()
