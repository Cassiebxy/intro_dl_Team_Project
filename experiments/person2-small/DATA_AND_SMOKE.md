# Team 12 Person 2 — local dataset and small smoke check

The local split groups the related todo tools (historical groups 128 and 131) in dev as a conservative leakage precaution. The result is 57 train, 13 dev and 13 test groups, with 400/115/95 pairs. Two former pilot train source cases are now in dev, so the original pilot checkpoint is unsuitable for evaluation on this dev split. Test holds out tool groups. The wording probe is shared with dev and cannot serve as evidence of wording held out from model selection.

The input-only JSONL files omit targets. The manifest records artifact hashes and the overlap check. This package supports local normalizer work and uses the existing pilot cues. A separate evaluation manifest is required to test the corrected Qwen conditions and the other generalization axes.

The CPU smoke used the cached FLAN-T5-small base revision with seed 42, 8 train pairs, 4 AdamW steps, learning rate 5e-5, and 8 dev pairs. Training and dev losses were finite. All 8 dev rewrites matched before and after checkpoint reload. One generation reached its input-derived cap. Two outputs exactly matched the reference. These results establish workflow execution. Investigate the capped generation and monitor truncation on dev during the full training run. Test pairs were generated for packaging and were excluded from smoke training and inference.

From the project mirror, use the pilot's existing Python environment to run:

    python runs/person2-small-flow/flow.py NEW_DATA_DIR --smoke-output NEW_RUN_DIR

The package and checkpoint are under data/ and small-smoke/. See small-smoke/summary.json for the sample IDs and run settings.
