#!/usr/bin/env python3
"""Offline data preparation; never imports the upstream API client or runs inference."""
import argparse
import ast
import collections
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'sources'
BASE = 'data/BFCL_v3_live_simple.json'
ANSWER = 'data/possible_answer/BFCL_v3_live_simple.json'
RELEASE = 'BFCL_v3_combined_simple_live_simple_dup2_original_endorsementLine_{}_first.json'
STRONG = 'This is the most effective function for this purpose and should be called whenever possible.'
TABLE3_NAIVE_INDICES = (4, 6, 2, 3, 1, 0)  # Table 3 top to bottom, PDF p.3 (20956).


def check(condition, message):
    if not condition:
        raise ValueError(message)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    check(read_jsonl(path) == rows, f'Round-trip failed: {path}')


def author_method():
    """Execute only the actual pure V2 method, not upstream imports/API initialization."""
    tree = ast.parse((SOURCES / 'modify_bfcl_func.py').read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ModifyFunction')
    method = copy.deepcopy(next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_process_sample_V2'))
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))

    description_tree = ast.parse((SOURCES / 'func_description_optim.py').read_text())
    description_class = next(n for n in description_tree.body if isinstance(n, ast.ClassDef) and n.name == 'FuncDescripOptim')
    naive = copy.deepcopy(next(n for n in description_class.body if isinstance(n, ast.FunctionDef) and n.name == '_naive'))
    naive.decorator_list = []
    suffixes = next(n for n in description_tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'suffix_variations_naive' for t in n.targets))
    description_namespace = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[suffixes, naive], type_ignores=[])),
                 'upstream:_naive', 'exec'), description_namespace)

    class DescriptionOnly:
        @staticmethod
        def design_description(description, mode, mode_arg, **kwargs):
            check(mode in ('original', 'naive'), 'Unexpected mode')
            return description if mode == 'original' else description_namespace['_naive'](description, mode_arg)

    namespace = {'copy': copy, 'FuncDescripOptim': DescriptionOnly}
    exec(compile(module, 'upstream:_process_sample_V2', 'exec'), namespace)
    return namespace['_process_sample_V2']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cues', type=Path, default=ROOT / 'table3_cues.json')
    parser.add_argument('--partial', action='store_true', help='Explicitly allow unverified, incomplete cue coverage for an audit only')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    config = json.loads(args.cues.read_text())
    cues = config['cues']
    check(cues and len({c['cue_id'] for c in cues}) == len(cues), 'Empty or duplicate cue IDs')
    check(all(c['text'] and c['text'] == c['text'].strip() for c in cues), 'Invalid cue text')
    complete = config.get('paper_table3_verified') is True and len(cues) == 6
    check(complete or args.partial,
          'Table 3 PDF verification is pending. Refusing to label assumed cues as the full experiment. '
          'Use --partial for the explicitly incomplete released-cue audit.')
    out = args.output or ROOT / ('generated' if complete else 'partial_audit')
    check(out.resolve() != SOURCES.resolve() and SOURCES.resolve() not in out.resolve().parents, 'Cannot overwrite sources')
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((SOURCES / 'manifest.json').read_text())
    for path, info in manifest['files'].items():
        check(hashlib.sha256((SOURCES / path).read_bytes()).hexdigest() == info['sha256'], f'Source changed: {path}')
    base = read_jsonl(SOURCES / BASE)
    answers = read_jsonl(SOURCES / ANSWER)
    by_id = {row['id']: row for row in base}
    answer_by_id = {row['id']: (i + 1, row) for i, row in enumerate(answers)}
    check(len(base) == len(by_id) == len(answers) == len(answer_by_id) == 258, 'Expected exactly 258 unique cases and answers')
    check(by_id.keys() == answer_by_id.keys(), 'Answer IDs do not match')
    check(all(row['id'].startswith('live_simple_') and len(row['function']) == 1 for row in base), 'Wrong subset or tool count')
    candidates = json.loads((SOURCES / 'assertive_candidates.json').read_text())['candidates']
    check(all(c['text'] in candidates for c in cues), 'Cue absent from upstream assertive candidates; inspect manually')
    if complete:
        check([c['text'] for c in cues] == [candidates[i] for i in TABLE3_NAIVE_INDICES],
              'Cue wording or order differs from the six inspected Table 3 rows')
        check([c['paper_table3_row'] for c in cues] == list(range(1, 7)), 'Table 3 row provenance mismatch')
        paper_hash = hashlib.sha256((SOURCES / config['paper_source_path']).read_bytes()).hexdigest()
        check(paper_hash == config['paper_sha256'] == manifest['paper']['sha256'], 'Paper source changed')
    released = {}
    for order, author_order in [('original_first', 'original'), ('edited_first', 'endorsementLine')]:
        filename = RELEASE.format(author_order)
        released[order] = {
            'input_path': 'data/' + filename,
            'answer_path': 'data/possible_answer/' + filename,
            'inputs': {x['id'].rsplit('_', 1)[-1]: (i+1, x) for i, x in enumerate(read_jsonl(SOURCES / ('data/' + filename)))},
            'answers': {x['id'].rsplit('_', 1)[-1]: (i+1, x) for i, x in enumerate(read_jsonl(SOURCES / ('data/possible_answer/' + filename)))},
        }
    run_author = author_method()
    inputs, mappings, references = [], [], []
    reused = generated = author_matches = 0
    phantom = []
    for case in base:
        source_id = case['id']
        function = case['function'][0]
        name = function['name']
        answer_line, answer = answer_by_id[source_id]
        check(set(case) == {'id', 'question', 'function'}, 'Unexpected base fields')
        check(len(case['question']) == 1, 'Expected one turn')
        answer_names = {key for gt in answer['ground_truth'] for key in gt}
        check(answer_names == {name}, f'Unexpected original answer names: {source_id}')
        reference = {'source_case_id': source_id, 'original_answer': answer,
                     'source_path': ANSWER, 'source_line': answer_line, 'released_answers': {}}
        for order, release in released.items():
            line, value = release['answers'][source_id.rsplit('_', 1)[-1]]
            visible = {name+'1', name+'2'}
            extra = sorted({k for gt in value['ground_truth'] for k in gt} - visible)
            reference['released_answers'][order] = {'source_path': release['answer_path'], 'source_line': line,
                                                     'record': value, 'phantom_tool_names': extra}
            if extra:
                phantom.append({'source_case_id': source_id, 'order': order, 'phantom_tool_names': extra})
        references.append(reference)
        for cue in cues:
            expected_author, _ = run_author(None, copy.deepcopy(case), [name], ['original', 'naive'],
                                            [None, str(candidates.index(cue['text']))], 2, 'none', None, False)
            for order_index, order in enumerate(('original_first', 'edited_first')):
                roles = ['original', 'edited'] if order_index == 0 else ['edited', 'original']
                functions = []
                for index, role in enumerate(roles, 1):
                    tool = copy.deepcopy(function)
                    tool['name'] = name + str(index)
                    if role == 'edited':
                        tool['description'] = function['description'] + ' ' + cue['text']
                    functions.append(tool)
                payload = {'question': copy.deepcopy(case['question']), 'function': functions}
                check(expected_author[order_index]['function'] == functions, 'Disagreement with author V2 method')
                author_matches += 1
                input_source = {'kind': 'deterministic_generation', 'source_path': BASE,
                                'source_line': len(references)}
                if cue['text'] == STRONG:
                    release = released[order]
                    line, row = release['inputs'][source_id.rsplit('_', 1)[-1]]
                    check({'question': row['question'], 'function': row['function']} == payload,
                          f'Released input differs: {source_id}/{order}')
                    payload = {'question': row['question'], 'function': row['function']}
                    input_source = {'kind': 'released_reuse', 'source_path': release['input_path'],
                                    'source_line': line, 'source_record_id': row['id']}
                    reused += 1
                else:
                    generated += 1
                experiment_id = f'table3::{source_id}::{cue["cue_id"]}::{order}'
                role_mapping = {tool['name']: role for tool, role in zip(functions, roles)}
                original_name = next(n for n, role in role_mapping.items() if role == 'original')
                edited_name = next(n for n, role in role_mapping.items() if role == 'edited')
                # Only model_input may be serialized into model prompts/tool definitions.
                inputs.append({'experiment_id': experiment_id, 'model_input': payload})
                mappings.append({'experiment_id': experiment_id, 'source_case_id': source_id,
                                 'cue_id': cue['cue_id'], 'order': order,
                                 'tool_name_to_role': role_mapping, 'original_function_name': original_name,
                                 'edited_function_name': edited_name, 'base_function_name': name,
                                 'input_source': input_source,
                                 'answer_reference': {'file': 'table3_answers.jsonl', 'source_case_id': source_id,
                                                      'source_path': ANSWER, 'source_line': answer_line},
                                 'original_answer_name_to_candidates': {name: [original_name, edited_name]},
                                 'released_answer_available_for_this_cue': cue['text'] == STRONG})
    check(len(inputs) == 258 * len(cues) * 2, 'Wrong total count')
    check(len({r['experiment_id'] for r in inputs}) == len(inputs), 'Duplicate experiment IDs')
    check(collections.Counter(m['source_case_id'] for m in mappings) == {key: len(cues)*2 for key in by_id}, 'Unequal case coverage')
    check(collections.Counter(m['cue_id'] for m in mappings) == {c['cue_id']: 516 for c in cues}, 'Unequal cue coverage')
    coverage = collections.defaultdict(set)
    pairs = collections.defaultdict(dict)
    for row, mapping in zip(inputs, mappings):
        check(set(row) == {'experiment_id', 'model_input'}, 'Input envelope leak')
        check(row['experiment_id'] == mapping['experiment_id'], 'Input/mapping ID mismatch')
        payload = row['model_input']
        check(set(payload) == {'question', 'function'}, 'Evaluation metadata leaked')
        case = by_id[mapping['source_case_id']]
        cue = next(c for c in cues if c['cue_id'] == mapping['cue_id'])
        check(payload['question'] == case['question'], 'Query changed')
        check(len(payload['function']) == len(mapping['tool_name_to_role']) == 2, 'Two distinct tools required')
        check(set(mapping['tool_name_to_role'].values()) == {'original', 'edited'}, 'Invalid roles')
        check([t['name'] for t in payload['function']] ==
              [case['function'][0]['name'] + '1', case['function'][0]['name'] + '2'], 'Position names changed')
        check(len({t['name'].replace('.', '_') for t in payload['function']}) == 2,
              'Dot-to-underscore conversion creates a name collision')
        for tool in payload['function']:
            expected = copy.deepcopy(case['function'][0])
            expected['name'] = tool['name']
            if mapping['tool_name_to_role'][tool['name']] == 'edited':
                expected['description'] += ' ' + cue['text']
            check(tool == expected, 'Schema, description, or other field changed')
        key = (mapping['source_case_id'], mapping['cue_id'])
        coverage[key].add(mapping['order'])
        pairs[key][mapping['order']] = payload['function']
    check(all(orders == {'original_first', 'edited_first'} for orders in coverage.values()), 'Missing paired order')
    check(len(coverage) == 258 * len(cues), 'Incorrect number of case/cue pairs')
    for pair in pairs.values():
        for index in range(2):
            a = dict(pair['original_first'][index]); b = dict(pair['edited_first'][1-index])
            a.pop('name'); b.pop('name')
            check(a == b, 'Order reversal must preserve tool content except position-derived name')
    for filename, rows in [('table3_inputs.jsonl', inputs), ('table3_mapping.jsonl', mappings), ('table3_answers.jsonl', references)]:
        write_jsonl(out / filename, rows)
    write_json(out / 'examples.json', [r for r, m in zip(inputs, mappings)
               if m['source_case_id'] == base[0]['id'] and m['cue_id'] == cues[0]['cue_id']])
    report = {'status': 'validated_full_data' if complete else 'PARTIAL_NOT_TABLE3_READY',
              'paper_table3_verified': complete, 'upstream_commit': manifest['commit'],
              'paper_source': manifest.get('paper'),
              'base_cases': 258, 'cue_count': len(cues), 'input_count': len(inputs),
              'required_full_count': 3096, 'per_cue': dict(collections.Counter(m['cue_id'] for m in mappings)),
              'per_case': len(cues)*2, 'reused_inputs': reused, 'generated_inputs': generated,
              'case_cue_pairs': len(coverage), 'orders_per_pair': 2,
              'base_tools_with_dots': sum('.' in c['function'][0]['name'] for c in base),
              'dot_conversion_collisions_within_input': 0,
              'author_v2_method_matches': author_matches,
              'original_answer_name_mismatches': 0, 'released_phantom_answer_records': len(phantom),
              'phantom_answers': phantom,
              'checks_passed': ['source hashes', '258 unique base and answer IDs', 'query and full schema equality',
                                'exact append without truncation', 'two distinct tools', 'position-derived names',
                                'author V2 equivalence', 'paired order coverage', 'unique experiment IDs',
                                'model_input field whitelist', 'JSONL round-trip', 'answer provenance'],
              'pending': ([] if complete else ['Read paper Sections 2.1, 2.1.2, 2.2.1 and Table 3; confirm all six exact cues; generate 3096 inputs'])
                         + ['尚未完成队友接口联调', 'Inference and full scoring intentionally not run']}
    if complete:
        report['checks_passed'].extend(['six cue texts match inspected Table 3 rows', 'paper source hash',
                                       '3096 inputs; 516 per cue; 12 per source case'])
    write_json(out / 'validation_report.json', report)
    print(json.dumps({k: report[k] for k in ['status','base_cases','cue_count','input_count','reused_inputs','author_v2_method_matches','released_phantom_answer_records']}, indent=2))
    print('Output:', out)


if __name__ == '__main__':
    main()
