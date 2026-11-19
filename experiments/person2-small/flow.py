"""Build the local normalizer package and run a bounded FLAN-T5-small smoke test."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import sys

PILOT = Path(__file__).resolve().parents[1] / 'normalizer-flan-t5-small-pilot-20261105'
sys.path.insert(0, str(PILOT))
from pilot import CUES, DEV_CUE, PREFIX, write_rows


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def build(out):
    source = PILOT / 'first-train' / 'split_manifest.jsonl'
    manifest = read(source)
    pairs = defaultdict(list)
    groups, cases, texts = {}, {}, {}
    for row in manifest:
        old_group = row['source_group']
        group = str(128 if old_group == 131 else old_group)
        split = 'dev' if old_group in (128, 131) else row['split']
        clean = row['target']
        tool_id = 'tool_' + digest(json.dumps([row['tool'], clean], ensure_ascii=False))
        row.update(source_tool_id=tool_id, source_group_id=group, split=split)
        row['pilot_source_group'] = row.pop('source_group')
        for registry, keys in ((groups, [group]), (cases, row['source_cases']), (texts, [clean])):
            for key in keys:
                if registry.setdefault(key, split) != split:
                    raise ValueError(f'Cross-split key: {key}')
        variants = [('clean', None, 'none', clean),
                    ('suffix_1', CUES[0], 'priority', f'{clean} {CUES[0]}'),
                    ('prefix_2', CUES[1], 'effectiveness', f'{CUES[1]} {clean}'),
                    ('suffix_3', CUES[2], 'mixed', f'{clean} {CUES[2]}')]
        if split != 'train':
            variants.append(('unseen_wording', DEV_CUE, 'priority', f'{DEV_CUE} {clean}'))
        for label, cue, family, description in variants:
            desc_id = 'desc_' + digest(description)
            pairs[split].append(dict(example_id='pair_' + digest(f'{tool_id}:{label}:{desc_id}'),
                                     source_tool_id=tool_id, source_group_id=group,
                                     source_case_ids=row['source_cases'], split=split, variant=label,
                                     cue_id='none' if cue is None else 'cue_' + digest(cue),
                                     cue_family=family, description_id=desc_id,
                                     input_description=description, target_description=clean))
    all_pairs = sum(pairs.values(), [])
    if len({r['example_id'] for r in all_pairs}) != len(all_pairs):
        raise ValueError('Duplicate example ID')
    input_splits = {}
    for row in all_pairs:
        if input_splits.setdefault(row['description_id'], row['split']) != row['split']:
            raise ValueError('Identical normalizer input crosses splits')
    old_train = read(PILOT / 'first-train' / 'train.jsonl')
    old_ids = {c for r in old_train for c in r['source_cases']}
    overlap = {split: sorted(old_ids & {c for r in pairs[split] for c in r['source_case_ids']})
               for split in ('dev', 'test')}
    out.mkdir(parents=True, exist_ok=False)
    write_rows(out / 'split_manifest.jsonl', manifest)
    for split in ('train', 'dev', 'test'):
        rows = pairs[split]
        write_rows(out / f'pairs_{split}.jsonl', rows)
        projected = {r['description_id']: dict(description_id=r['description_id'],
                                               input_description=r['input_description']) for r in rows}
        write_rows(out / f'normalizer_inputs_{split}.jsonl', list(projected.values()))
    audit = dict(group_counts=Counter(groups.values()),
                 pair_counts={s: len(rows) for s, rows in pairs.items()},
                 old_train_case_overlap=overlap,
                 split_decision='Group 131 joined 128 in dev as a conservative near-duplicate precaution.',
                 generalization_scope='The same wording probe is used in dev and test. Test holds out tool groups.',
                 hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.jsonl'))})
    (out / 'manifest.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2), flush=True)


def smoke(data, out):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, set_seed

    set_seed(42)
    torch.set_num_threads(4)
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    base = PILOT / 'model'
    tokenizer = AutoTokenizer.from_pretrained(base, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(base, local_files_only=True).to(device)
    rng = random.Random(42)
    train = rng.sample(read(data / 'pairs_train.jsonl'), 8)
    dev = rng.sample(read(data / 'pairs_dev.jsonl'), 8)
    out.mkdir(parents=True, exist_ok=False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)

    def batch_loss(rows):
        inputs = tokenizer([PREFIX + r['input_description'] for r in rows],
                           padding=True, return_tensors='pt').to(device)
        labels = tokenizer([r['target_description'] for r in rows],
                           padding=True, return_tensors='pt').input_ids.to(device)
        labels[labels == tokenizer.pad_token_id] = -100
        return model(**inputs, labels=labels).loss

    def generate(model):
        model.eval()
        results = []
        with torch.inference_mode():
            for row in dev:
                inputs = tokenizer(PREFIX + row['input_description'],
                                   return_tensors='pt').to(device)
                count = inputs.input_ids.shape[-1]
                limit = min(256, max(64, 2 * count))
                output = model.generate(**inputs, max_new_tokens=limit, do_sample=False)[0, 1:].tolist()
                ended = tokenizer.eos_token_id in output
                results.append(dict(description_id=row['description_id'], run_id=out.name,
                                    input_sha256=digest(row['input_description']),
                                    normalized_description=tokenizer.decode(output, skip_special_tokens=True),
                                    status='ok', error=None, input_tokens=count,
                                    output_tokens=len(output), max_new_tokens=limit,
                                    truncated=not ended and len(output) == limit))
        return results

    model.train()
    losses = []
    for i in range(0, len(train), 2):
        optimizer.zero_grad()
        loss = batch_loss(train[i:i+2])
        if not torch.isfinite(loss):
            raise ValueError('Non-finite training loss')
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    model.eval()
    with torch.inference_mode():
        dev_loss = sum(batch_loss(dev[i:i+2]).item() for i in range(0, len(dev), 2)) / 4
    before = generate(model)
    checkpoint = out / 'checkpoint'
    model.save_pretrained(checkpoint)
    tokenizer.save_pretrained(checkpoint)
    del optimizer, model
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    reloaded = AutoModelForSeq2SeqLM.from_pretrained(checkpoint, local_files_only=True).to(device)
    after = generate(reloaded)
    if before != after or len({r['description_id'] for r in after}) != len(dev):
        raise ValueError('Reloaded results differ or dev coverage is incomplete')
    write_rows(out / 'rewrites.jsonl', after)
    summary = dict(device=device, seed=42, base_revision=(base / 'revision.txt').read_text().strip(),
                   train_examples=len(train), optimizer_steps=len(losses), train_losses=losses,
                   dev_examples=len(dev), dev_loss=dev_loss, reload_matches=True,
                   truncated=sum(r['truncated'] for r in after),
                   exact_matches=sum(r['normalized_description'] == d['target_description']
                                     for r, d in zip(after, dev)),
                   prompt_prefix=PREFIX, generation_limit='min(256, max(64, 2 * input_tokens))',
                   train_example_ids=[r['example_id'] for r in train],
                   dev_example_ids=[r['example_id'] for r in dev],
                   data_manifest_sha256=hashlib.sha256((data / 'manifest.json').read_bytes()).hexdigest())
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if not k.endswith('_ids')}, indent=2), flush=True)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('data', type=Path)
    cli.add_argument('--smoke-output', type=Path)
    args = cli.parse_args()
    if not args.data.exists():
        build(args.data)
    if args.smoke_output:
        smoke(args.data, args.smoke_output)
