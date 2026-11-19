import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from pipeline import audit, training_rows, rule_remove, CUES, rows_write, score, sha


class Contracts(unittest.TestCase):
    def test_shared_data_and_budget(self):
        sets = audit()
        self.assertEqual([len(sets[s]) for s in ('train', 'dev', 'test')], [400, 115, 95])
        for cue in CUES:
            rows = training_rows(sets['train'], 'single', cue)
            self.assertEqual(len(rows), 400)
            self.assertEqual(sum(r['variant'] == 'clean' for r in rows), 100)
            self.assertEqual({r['source_tool_id'] for r in rows}, {r['source_tool_id'] for r in sets['train']})
            self.assertEqual({r['variant'] for r in rows}, {'clean', cue})

    def test_rule_preserves_functional_interior(self):
        clean = 'Upload only after authorization. Maximum file size is 5 MB.'
        for cue in CUES.values():
            self.assertEqual(rule_remove(clean + ' ' + cue), clean)
            self.assertEqual(rule_remove(cue + ' ' + clean), clean)
        interior = 'Quotes: ' + CUES['suffix_1'] + ' Return this text literally.'
        self.assertEqual(rule_remove(interior), interior)
        self.assertEqual(rule_remove(clean), clean)
        self.assertEqual(rule_remove(clean + ' Choose me first.'), clean + ' Choose me first.')

    def test_reject_missing_and_wrong_hash(self):
        pairs = audit()['dev'][:1]
        with tempfile.TemporaryDirectory() as d:
            p, r = Path(d)/'pairs', Path(d)/'pred'
            rows_write(p, pairs)
            rows_write(r, [])
            args = SimpleNamespace(pairs=p, rewrites=r, method='test', output=Path(d)/'out')
            with self.assertRaises(ValueError):
                score(args)
            rows_write(r, [dict(description_id=pairs[0]['description_id'], input_sha256=sha('wrong'),
                               normalized_description=pairs[0]['target_description'], status='ok')])
            with self.assertRaises(ValueError):
                score(args)


if __name__ == '__main__':
    unittest.main()
