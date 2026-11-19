"""Export four paired conditions for Person 1's controlled Qwen runner."""
import argparse
import copy
from pathlib import Path
from pipeline import ROOT, read, unique, rows_write, write, sha, file_hash


def prepare(args):
    pairs = read(args.pairs)
    predictions = unique(read(args.rewrites), 'description_id')
    baseline = ROOT / 'table3/controlled_baseline/generated/full_factorial_v2'
    inputs = unique(read(baseline / 'controlled_inputs.jsonl'), 'experiment_id')
    mappings = read(baseline / 'controlled_mapping.jsonl')
    cases = {c for p in pairs for c in p['source_case_ids']}
    # Infer boundary edits from evaluation PAIRS only to build manipulated requests.
    # Reference descriptions are never sent to the normalizer or downstream model.
    edits = {}
    for p in pairs:
        if p['variant'] == 'clean':
            continue
        source, target = p['input_description'], p['target_description']
        if source.endswith(' ' + target):
            edit = ('prefix', source[:-len(target)-1])
        elif source.startswith(target + ' '):
            edit = ('suffix', source[len(target)+1:])
        else:
            raise ValueError('Expected a boundary cue')
        if p['variant'] in edits and edits[p['variant']] != edit:
            raise ValueError('Inconsistent cue template')
        edits[p['variant']] = edit
    requests, output_maps = [], []
    for base in mappings:
        if base['description_condition'] != 'clean_control' or base['source_case_id'] not in cases:
            continue
        original = inputs[base['experiment_id']]['model_input']
        for variant, edit in [('clean', None), *edits.items()]:
            for normalize in (False, True):
                condition = ('clean_normalized' if normalize else 'clean_control') if edit is None else ('normalized' if normalize else 'manipulated')
                rid = '::'.join((args.method, base['source_case_id'], variant, condition, base['order'], base['name_mapping']))
                payload = copy.deepcopy(original)
                for tool in payload['function']:
                    role = base['tool_name_to_role'][tool['name']]
                    if edit and role == 'edited':
                        position, cue = edit
                        tool['description'] = (cue + ' ' + tool['description']) if position == 'prefix' else (tool['description'] + ' ' + cue)
                    if normalize:
                        text = tool['description']
                        row = predictions.get('desc_' + sha(text))
                        if row is None or row.get('input_sha256') != sha(text):
                            raise ValueError(f'Missing or mismatched rewrite: {rid}')
                        if row['status'] != 'ok' or row.get('truncated') or not row['normalized_description'].strip():
                            raise ValueError(f'Invalid rewrite; retain failure separately before inference: {rid}')
                        tool['description'] = row['normalized_description']
                for old, new in zip(original['function'], payload['function']):
                    assert {k:v for k,v in old.items() if k != 'description'} == {k:v for k,v in new.items() if k != 'description'}
                requests.append(dict(experiment_id=rid, model_input=payload))
                output_maps.append(dict(base, experiment_id=rid, description_condition=condition,
                                        cue_id=variant, normalizer_method=args.method))
    if not requests:
        raise ValueError('No matching baseline cases')
    unique(requests, 'experiment_id')
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    rows_write(out / 'controlled_inputs.jsonl', requests)
    rows_write(out / 'controlled_mapping.jsonl', output_maps)
    write(out / 'manifest.json', dict(requests=len(requests), cases=len(cases), method=args.method,
          pairs_sha256=file_hash(args.pairs), rewrites_sha256=file_hash(args.rewrites),
          status='prepared_not_run', archive_reuse=False))
    print(f'Prepared {len(requests)} requests; no Qwen inference performed.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('pairs', 'rewrites', 'method', 'output'):
        p.add_argument('--' + name, required=True)
    prepare(p.parse_args())
