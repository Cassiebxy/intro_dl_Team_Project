# Local interface test record

The following command was run on November 18, 2026.

```bash
person4_bart/.venv/bin/python -m unittest discover -s person4_bart/tests -v
```

All 12 tests passed. The final run followed the changes to set generation parameters explicitly and handle EOS at the generation limit.

The tests cover the following behaviors.

1. Synthetic train and dev tool groups are disjoint, and the clean identity count matches the fixture.
2. Inference files reject gold targets and extra metadata.
3. Duplicate input IDs are rejected.
4. Test pairs are rejected when loading training data.
5. Shared tool groups or identical canonical targets across splits are rejected.
6. Missing and failed outputs remain in the exact-match denominator.
7. An input SHA-256 mismatch invalidates a successful status.
8. Duplicate and unexpected output IDs are detected.
9. Empty or truncated outputs marked `ok` fail the interface check.
10. The literal audit detects a missing negation.
11. The HTML report escapes inputs and model outputs to display descriptions as text.
12. Overlength inputs and generations that hit the cap retain their IDs and explicit errors. Natural EOS at the cap counts as a normal finish. The test verifies greedy generation with a fixed cap and the inherited no-repeat constraint disabled.

The final MPS run records integration evidence in `summary.json`, `reload_check.json`, and `diagnostic_rewrites.jsonl`. The unit tests verify interface behavior. The integration run recorded one case of over-deletion.
