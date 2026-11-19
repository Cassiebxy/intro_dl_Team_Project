# Person 3: FLAN-T5-base, cue ablation, and method comparisons

Based on main commit `8cf4b2e5f9d7305d611c626d79f1c0f1ef49836f`.

**Status: implementation and CPU/data checks completed. FLAN-T5-base training and downstream Qwen inference have not run.** The editing environment has no PyTorch installation. Training and model prediction still require a smoke test on the target machine. No base weights or base scores are claimed. Existing Person 2 and Person 4 outputs are reused only for the descriptive development-set comparison.

## Experimental design

| Arm | Training examples per source description | Total exposures per epoch | Clean proportion |
| --- | --- | ---: | ---: |
| Multi-cue | One clean example and three different cue variants | 400 | 25% |
| Single-cue | One clean example and three copies of the selected cue variant | 400 | 25% |

Both arms start independently from the same pretrained FLAN-T5-base checkpoint. They use the same 100 source descriptions, three epochs, 75 optimizer updates, seed 42, learning rate 5e-5, effective batch size 16, and microbatch size 4. The default single cue is `suffix_1`; `prefix_2` and `suffix_3` are available for sensitivity runs.

“Multi-cue” means different cue templates across training examples, not multiple cues stacked in one description. The existing templates differ in wording, cue family, and insertion position. Results therefore compare these training mixtures, not a pure causal effect of cue count. Repeated exposure to one cue is also part of the single-cue treatment.

The rule baseline removes only the three exact training templates at description boundaries. Rules are fixed before evaluation and are not expanded using test targets.

The original Person 2 splits are preserved. The audit checks all manifest hashes and rejects cross-split overlap in source groups, tools, or input descriptions. Training retains Person 2's instruction prefix, AdamW defaults, example-weighted microbatch loss, and mean-of-batch-means development loss. Checkpoint selection excludes the `unseen_wording` development probes. BART uses different loss weighting; document this when interpreting comparisons.

Generation uses greedy decoding in batches of four and Person 2's input-length-based output cap. Inputs are not silently truncated. Training uses FP32 and automatically selects CUDA, MPS, or CPU. Test memory use with a smoke run before full training, especially on an 8 GB Mac.

## Setup and training

Run commands from the repository root:

```bash
python -m pip install -r experiments/person3-base/requirements.txt
python experiments/person3-base/pipeline.py audit
python -m unittest discover -s experiments/person3-base -v
```

Replace `/path/to/flan-t5-base` below with a local pretrained model directory. Alternatively, use `--model google/flan-t5-base --revision <40-character-model-commit-SHA>` to load an immutable Hub revision. Every output directory must be new to prevent overwriting evidence.

```bash
python experiments/person3-base/pipeline.py train --model /path/to/flan-t5-base --smoke --output experiments/person3-base/runs/smoke
python experiments/person3-base/pipeline.py train --model /path/to/flan-t5-base --mode multi --output experiments/person3-base/runs/base-multi
python experiments/person3-base/pipeline.py train --model /path/to/flan-t5-base --mode single --single-cue suffix_1 --output experiments/person3-base/runs/base-single
```

Training saves the selected `checkpoint/`, the most recent epoch in `last/`, optimizer state, exposure records, losses, configuration, package versions, and data/model hashes. It then reloads the selected model and generates development rewrites. The reload check compares outputs from two loads of the selected checkpoint; it does not compare an in-memory pre-save model against a reload.

**Automatic resume is not implemented.** The saved last-epoch state is recovery material, not a verified restart mechanism. Do not describe a fresh rerun as a resumed run. Smoke mode uses 16 training and eight development examples for one epoch and must not be reported as a formal experiment.

## Held-out evaluation

Use the selected checkpoint. Do not select epochs or tune settings using test results.

```bash
python experiments/person3-base/pipeline.py predict --model experiments/person3-base/runs/base-multi/checkpoint --inputs experiments/person2-small/data/normalizer_inputs_test.jsonl --output experiments/person3-base/runs/base-multi-test
python experiments/person3-base/pipeline.py score --pairs experiments/person2-small/data/pairs_test.jsonl --rewrites experiments/person3-base/runs/base-multi-test/rewrites.jsonl --method base-multi --output experiments/person3-base/runs/base-multi-test-score
```

Repeat for the single-cue model. For the shared generalization set, use `person4_bart/data/generalization_v1/normalizer_inputs_test.jsonl` as inputs and `pairs_test.jsonl` in the same directory for scoring. Use new output directories. If the team modifies models after inspecting generalization results, treat that set as diagnostic and reserve a new untouched final test set.

Run the rule baseline and score its development outputs:

```bash
python experiments/person3-base/pipeline.py predict --rule --inputs experiments/person2-small/data/normalizer_inputs_dev.jsonl --output experiments/person3-base/runs/rules-dev
python experiments/person3-base/pipeline.py score --pairs experiments/person2-small/data/pairs_dev.jsonl --rewrites experiments/person3-base/runs/rules-dev/rewrites.jsonl --method rules --output experiments/person3-base/runs/rules-dev-score
```

## Downstream Qwen handoff

```bash
python experiments/person3-base/prepare_qwen.py --pairs experiments/person2-small/data/pairs_dev.jsonl --rewrites experiments/person3-base/runs/base-multi/rewrites.jsonl --method base-multi --output experiments/person3-base/runs/qwen-base-multi-dev
python table3/controlled_baseline/run_qwen_controlled.py --input experiments/person3-base/runs/qwen-base-multi-dev/controlled_inputs.jsonl --mapping experiments/person3-base/runs/qwen-base-multi-dev/controlled_mapping.jsonl --validate-only
```

The export contains Clean, Manipulated, Normalized, and Clean-through-normalizer conditions. Both candidate descriptions are normalized; questions, tool names, schemas, order, name mapping, and seeds are preserved. Full development export produces 1,400 requests across 35 cases, both orders, and both name mappings. This differs from Person 2's 16-case subset: do not compare their aggregate downstream scores directly.

Export the same matrix for every method and use Person 1's frozen Qwen configuration and shared scorer. This script does not submit GPU work or assume archived responses can be reused. Missing, failed, empty, or truncated rewrites stop export rather than silently dropping cases. Record those failures and agree on their scoring before inference.

The final downstream table should identify method, dataset, Qwen revision/backend/decoding, cue, order, name mapping, denominator, edited-tool selection, CUR, argument correctness conditional on selection, strict response correctness, and paired transitions. Keep AutoDL and locally quantized Qwen results separate. This version exports requests; the downstream aggregation and paired comparison implementation remains to be completed with the common scoring schema.

## Text comparison and existing evidence

`score` accepts Person 2's `generated` records and the common `normalized_description` format used by Person 4. It requires exact description-ID coverage and checks input hashes where present. `compare` rejects summaries with different pairs-file hashes and generates CSV, PNG, and SVG files:

```bash
python experiments/person3-base/pipeline.py compare --summaries path/to/rules/summary.json path/to/small/summary.json path/to/base/summary.json path/to/bart/summary.json --output experiments/person3-base/runs/comparison
```

The current [development table](evidence/comparison.csv) and [figure](evidence/comparison.svg) were produced by actually running the scoring code:

| Method | Exact recovery on shared development pairs |
| --- | ---: |
| Fixed boundary-deletion rules | 92/115 |
| Published fine-tuned FLAN-T5-small | 104/115 |
| Published fine-tuned BART-base | 112/115 |
| FLAN-T5-base | Pending training |

Rules recover all 92 clean/familiar-cue inputs and none of the 23 development wording probes. These 115 rows are five variants of 23 descriptions, not 115 independent observations. This is a descriptive development comparison, not a final test ranking.

Exact recovery measures literal text matching, not all forms of semantic preservation or downstream bias mitigation. Review `review_mismatches.jsonl` for functional details retained, deleted, or altered and for cues left behind. Include both successful and failed examples in the report.

## Verification and remaining work

Completed:

- Three unit tests: shared splits and matched exposure budgets, rule-boundary behavior, and rejection of missing predictions or mismatched input hashes.
- Audit of the 400/115/95 shared train/dev/test pairs.
- Actual rule-baseline execution and rescoring of published small/BART development outputs, matching their reported totals.
- Comparison table and figure generation.
- Validation of all 1,400 exported development Qwen requests using the original runner.

Still required, in execution order:

1. Select the target machine and pin the pretrained base revision. Install dependencies and retain the resolved environment versions. The requirements file currently gives compatible ranges, not a tested lockfile.
2. Run the neural smoke test, inspect memory and generation outputs, and verify checkpoint behavior on that machine. Training/model inference have not been runtime-tested here.
3. Train multi-cue and single-cue models. Optional additional single-cue arms and seeds can measure sensitivity; do not claim stability from one seed.
4. Evaluate both selected models on shared dev, test, and generalization inputs. Review functional errors and clean-input changes manually.
5. Add untuned small and the small clean-identity ablation to the shared comparison where matching outputs exist. Current committed evidence includes only rules, trained small, and BART.
6. Freeze a common downstream evaluation matrix, run Qwen, and implement matched downstream aggregation and paired transitions. Missing inference results must stay missing.
7. Finish the cross-method tables, ablation figures, example analysis, and English methods/results section. Store checkpoint locations and configurations with the handoff.

A verified resume command and automated downstream aggregation would improve the workflow but are not implemented in this version. The code delivery is not the completed Person 3 experiment.
