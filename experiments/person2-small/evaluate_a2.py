"""Compare the untuned FLAN-T5-small base with the saved fine-tuned dev run."""
from collections import defaultdict
import json
from pathlib import Path

from train_main import AutoModelForSeq2SeqLM, AutoTokenizer, PREFIX, torch, write_rows

root = Path(__file__).resolve().parent
a1 = root / 'small-main-20261118'
base = root.parent / 'normalizer-flan-t5-small-pilot-20261105' / 'model'
out = root / 'small-a2-untuned'
rows = [json.loads(line) for line in (a1 / 'rewrites.jsonl').read_text().splitlines()]
dev = [json.loads(line) for line in (root / 'data/pairs_dev.jsonl').read_text().splitlines()]
assert len(rows) == len(dev) == 115
assert all(all(row[k] == item[k] for k in ('example_id', 'input_description', 'target_description'))
           for row, item in zip(rows, dev))
torch.set_num_threads(4)
tokenizer = AutoTokenizer.from_pretrained(base, local_files_only=True)
reference_tokenizer = AutoTokenizer.from_pretrained(a1 / 'checkpoint', local_files_only=True)
model = AutoModelForSeq2SeqLM.from_pretrained(base, local_files_only=True).eval()
results = []
with torch.inference_mode():
    for start in range(0, len(dev), 4):
        chunk = dev[start:start + 4]
        prompts = [PREFIX + row['input_description'] for row in chunk]
        inputs = tokenizer(prompts, padding=True, return_tensors='pt')
        reference = reference_tokenizer(prompts, padding=True, return_tensors='pt')
        assert all(torch.equal(inputs[k], reference[k]) for k in inputs)
        cap = min(256, max(64, 2 * int(inputs.attention_mask.sum(dim=1).max())))
        outputs = model.generate(**inputs, max_new_tokens=cap, do_sample=False)
        assert len(outputs) == len(chunk)
        for row, ids in zip(chunk, outputs):
            decoded = tokenizer.decode(ids, skip_special_tokens=True)
            results.append(dict(row, generated=decoded, exact=decoded == row['target_description'],
                                blank=not decoded.strip(), max_new_tokens=cap,
                                truncated=tokenizer.eos_token_id not in ids.tolist() and len(ids) - 1 == cap))
counts = defaultdict(lambda: defaultdict(int))
paired = []
for tuned, untuned in zip(rows, results):
    transition = ('both_exact' if tuned['exact'] and untuned['exact'] else
                  'a1_only_exact' if tuned['exact'] else
                  'a2_only_exact' if untuned['exact'] else 'neither_exact')
    pair = dict(example_id=untuned['example_id'], group=untuned['source_group_id'],
                variant=untuned['variant'], transition=transition,
                a1_output=tuned['generated'], a2_output=untuned['generated'])
    paired.append(pair)
    for group in ('all', untuned['variant']):
        counts[group]['n'] += 1
        counts[group][transition] += 1
        counts[group]['a1_exact'] += tuned['exact']
        counts[group]['a2_exact'] += untuned['exact']
        counts[group]['a2_blank'] += untuned['blank']
        counts[group]['a2_truncated'] += untuned['truncated']
summary = dict(training_steps=0, device='cpu', base_revision=(base / 'revision.txt').read_text().strip(),
               prompt_prefix=PREFIX, batch_size=4, decoding='greedy',
               generation_limit='clamp(2 * longest tokenized input per batch, 64, 256)',
               results=counts)
out.mkdir(exist_ok=False)
write_rows(out / 'rewrites.jsonl', results)
write_rows(out / 'paired_comparison.jsonl', paired)
(out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
