import copy
import tempfile
import unittest
from pathlib import Path

from person4_bart import SCHEMA_VERSION
from person4_bart.core import audit, inference_rows, load_inputs, load_pairs, save_report, text_hash, validate_splits, write_jsonl
from person4_bart.make_synthetic import DEV, TRAIN, build


def output(row, text="kept", status="ok", error=None, truncated=False):
    return {"schema_version": SCHEMA_VERSION, "run_id": "test", "description_id": row["description_id"],
            "input_sha256": text_hash(row["input_description"]), "normalized_description": text,
            "status": status, "error": error, "input_tokens": 8, "output_tokens": 3, "truncated": truncated}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_fixtures_have_disjoint_tool_groups_and_identity_pairs(self):
        train, dev = build("train", TRAIN), build("dev", DEV)
        info = validate_splits(train, dev)
        self.assertEqual((info["train_examples"], info["dev_examples"]), (32, 16))
        self.assertEqual(sum(r["variant"] == "clean_identity" for r in train), 8)
        self.assertTrue(all(r["source_group_id"].startswith("toy_") for r in train + dev))

    def test_gold_never_enters_inference_file(self):
        path = self.path / "input.jsonl"
        write_jsonl(path, [{"description_id": "a", "input_description": "text", "target_description": "gold"}])
        with self.assertRaisesRegex(ValueError, "keep gold/metadata separate"):
            load_inputs(path)

    def test_duplicate_input_ids_are_rejected(self):
        row = {"description_id": "a", "input_description": "text"}
        path = self.path / "input.jsonl"
        write_jsonl(path, [row, row])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            load_inputs(path)

    def test_test_pairs_cannot_be_loaded_as_training(self):
        row = build("train", TRAIN)[0]
        row["split"] = "test"
        path = self.path / "pairs.jsonl"
        write_jsonl(path, [row])
        with self.assertRaisesRegex(ValueError, "expected split train"):
            load_pairs(path, "train")

    def test_group_and_exact_target_leakage_are_rejected(self):
        train, dev = build("train", TRAIN), build("dev", DEV)
        dev[0]["source_group_id"] = train[0]["source_group_id"]
        with self.assertRaisesRegex(ValueError, "Source groups overlap"):
            validate_splits(train, dev)
        dev = build("dev", DEV)
        dev[0]["target_description"] = train[0]["target_description"]
        with self.assertRaisesRegex(ValueError, "canonical targets overlap"):
            validate_splits(train, dev)

    def test_missing_and_error_rows_remain_in_metric_denominator(self):
        pairs = build("dev", DEV)[:3]
        inputs = inference_rows(pairs)
        outputs = [output(inputs[0], pairs[0]["target_description"]),
                   output(inputs[1], pairs[1]["target_description"], status="error", error="failed")]
        metrics, details = audit(inputs, outputs, pairs)
        self.assertEqual(metrics["n_expected"], 3)
        self.assertAlmostEqual(metrics["exact_match_rate"], 1 / 3)
        self.assertEqual(metrics["missing_ids"], [pairs[2]["description_id"]])
        self.assertEqual(metrics["error_or_missing_n"], 2)

    def test_hash_mismatch_invalidates_success(self):
        row = {"description_id": "a", "input_description": "text"}
        wrong = output(row)
        wrong["input_sha256"] = "wrong"
        metrics, _ = audit([row], [wrong])
        self.assertFalse(metrics["contract_valid"])
        self.assertEqual(metrics["ok_n"], 0)

    def test_duplicates_and_unexpected_output_ids_are_detected(self):
        row = {"description_id": "a", "input_description": "text"}
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            audit([row], [output(row), output(row)])
        extra = {"description_id": "b", "input_description": "other"}
        metrics, _ = audit([row], [output(row), output(extra)])
        self.assertEqual(metrics["extra_ids"], ["b"])
        self.assertFalse(metrics["contract_valid"])

    def test_truncation_and_empty_success_are_contract_errors(self):
        row = {"description_id": "a", "input_description": "text"}
        for result in [output(row, truncated=True), output(row, text="")]:
            metrics, _ = audit([row], [result])
            self.assertFalse(metrics["contract_valid"])
            self.assertEqual(metrics["ok_n"], 0)

    def test_preservation_check_does_not_call_missing_negation_correct(self):
        pairs = build("dev", DEV)[:1]
        inputs = inference_rows(pairs)
        text = pairs[0]["target_description"].replace("does not support refunds", "supports refunds")
        metrics, details = audit(inputs, [output(inputs[0], text)], pairs)
        self.assertEqual(metrics["protected_span_pass_rate"], 0)
        self.assertIn("does not support refunds", details[0]["missing_protected_spans"])

    def test_report_escapes_untrusted_description_markup(self):
        row = {"description_id": "a", "input_description": "<script>alert('x')</script>"}
        metrics, details = audit([row], [output(row, text="<img src=x onerror=alert(1)>")])
        save_report(self.path / "report", metrics, details)
        document = (self.path / "report/rewrite_report.html").read_text()
        self.assertNotIn("<script>", document)
        self.assertNotIn("<img src=", document)
        self.assertIn("&lt;script&gt;", document)


class GenerationTests(unittest.TestCase):
    def test_generation_caps_and_input_overflow_preserve_ids(self):
        import torch
        from types import SimpleNamespace
        from person4_bart.model import generate

        class Encoded(dict):
            def to(self, device):
                return self

        class Tokenizer:
            eos_token_id, pad_token_id, bos_token_id = 2, 1, 0

            def __call__(self, text, **kwargs):
                if isinstance(text, str):
                    return {"input_ids": [5] * len(text.split())}
                return Encoded(input_ids=torch.ones((len(text), 3), dtype=torch.long))

            def decode(self, ids, **kwargs):
                return "kept"

        class Model:
            config = SimpleNamespace(max_position_embeddings=1024)

            def eval(self):
                return self

            def generate(self, input_ids, **kwargs):
                self.settings = kwargs
                return torch.tensor([[2, 5, 6, 7]] * len(input_ids))

        rows = [{"description_id": "a", "input_description": "short"},
                {"description_id": "b", "input_description": "this input is too long for limit"}]
        model = Model()
        outputs = generate(model, Tokenizer(), rows, run_id="test", device="cpu", max_input_tokens=3, max_new_tokens=3)
        self.assertEqual([r["description_id"] for r in outputs], ["a", "b"])
        self.assertEqual(outputs[0]["error"], "generation_limit_reached")
        self.assertTrue(outputs[0]["truncated"])
        self.assertIn("input_too_long", outputs[1]["error"])
        self.assertFalse(outputs[1]["input_truncated"])
        self.assertEqual(model.settings["max_new_tokens"], 3)
        self.assertFalse(model.settings["do_sample"])
        self.assertEqual(model.settings["no_repeat_ngram_size"], 0)
        self.assertFalse(model.settings["early_stopping"])
        # A natural EOS exactly on the configured last token is a normal finish.
        model.generate = lambda input_ids, **kwargs: torch.tensor([[2, 5, 6, 2]] * len(input_ids))
        normal = generate(model, Tokenizer(), rows[:1], run_id="test", device="cpu", max_input_tokens=3, max_new_tokens=3)
        self.assertEqual(normal[0]["status"], "ok")
        self.assertFalse(normal[0]["truncated"])


if __name__ == "__main__":
    unittest.main()
