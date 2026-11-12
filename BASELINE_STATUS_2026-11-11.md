# Team 12 Qwen Table 3 Baseline: Status and Reproduction Record

**Updated:** 2026-11-11
**Scope:** Qwen2.5-7B-Instruct controlled baseline only. Normalizer training is out of scope.

## 1. Current status

The corrected pipeline has passed a 16-request Delta GPU smoke test. Slurm job `23742884` completed with exit code `0:0`. Its log reports 16/16 inference requests with `status=ok`, zero inference failures, zero missing responses, and `inference_successful=true`. This verifies that model loading, generation, checkpointing, and evaluation can complete on Delta.

This is a **pipeline smoke test**, not the complete corrected baseline and not a claim that all 16 tool calls were correct. No full 7,224-request controlled experiment has been submitted or completed.

### Smoke run evidence

- GPU node: `gpua032.delta.ncsa.illinois.edu`; model: local `/scratch/bjfu/mzhao9/Qwen2.5-7B-Instruct`.
- Model load: 106.39 seconds; peak allocated GPU memory during load: 15,276,322,816 bytes (about 14.2 GiB).
- Generation: first request 71.90 seconds; the remaining 15 requests were reported between 0.71 and 1.81 seconds each.
- Slurm elapsed time: 15 minutes 51 seconds. The output does not provide enough stage timing to explain the difference between the model/generation timings and total job elapsed time; do not use this smoke alone for a full-run estimate.
- Smoke evaluation directory: `/scratch/bjfu/mzhao9/diagnostics/qwen-controlled/table3/results/qwen-controlled-smoke-v1/analysis-20261111T152634Z/`.
- Raw checkpoint: `/scratch/bjfu/mzhao9/diagnostics/qwen-controlled/table3/results/qwen-controlled-smoke-v1/raw_responses.jsonl`.

The `scontrol show job` command returned an invalid job ID because the job had already finished and left the active controller. `sacct` is the relevant source for the completed job; it reported `COMPLETED` and `0:0`.

The logs show technical inference success. Review `summary_by_condition.csv` and `per_case_structured_results.jsonl` before making any claim about tool-selection behavior or answer accuracy. The overall-correctness convention is still provisional pending TA/team confirmation.

## 2. Why the baseline was corrected

The historical baseline contained 258 BFCL `live_simple` cases × six manipulation cues × two list orders = 3,096 requests. Its generator assigned the numeric tool-name suffix from list position:

| Historical order | First tool | Second tool |
|---|---|---|
| `original_first` | Original, suffix `1` | Edited, suffix `2` |
| `edited_first` | Edited, suffix `1` | Original, suffix `2` |

Consequently, the old order comparison changed position and name suffix together. It cannot isolate a pure position effect, and the manipulated-only results cannot cleanly distinguish description preference from position/name preference. Historical results remain preserved for reproduction and clearly labeled historical comparisons; they are not pooled into the new controlled primary analysis.

## 3. Controlled experiment design

The revised generator crosses three factors independently over the same 258 cases:

| Factor | Levels |
|---|---|
| Description | Clean control; six cue conditions |
| Role order | Original first; edited first |
| Name mapping | Original receives suffix 1; edited receives suffix 1 |

Total: `7 × 2 × 2 × 258 = 7,224` requests, or 28 cells per source case. During an order swap, each role keeps its own tool name, description, and schema. The suffix assignment is independently crossed with position. In clean controls the two descriptions are identical; original/edited are identity labels for candidate comparison, not clean vs. manipulated roles.

Questions, source cases, schemas, expected-answer mapping, model checkpoint, prompt/tool protocol, and decode settings are retained. The cue is appended to the edited-role description in manipulated conditions. Input rows and mappings record condition, cue, order, role positions, suffix mapping, and a per-case seed.

Sampling settings: `do_sample=true`, temperature `0.01`, top-p `1.0`, top-k `0`, repetition penalty `1.0`, and at most 4,096 generated tokens. The model is loaded locally in BF16 on one A100. Network downloads are disabled.

### Paired seed behavior

All 28 conditions for a source case use the same SHA256-derived case seed. Transformers in the Delta environment rejected the `generator` keyword to `model.generate()`. The corrected runner instead calls `torch.manual_seed(seed)` and `torch.cuda.manual_seed_all(seed)` immediately before each generation. This gives each paired condition the same pseudorandom seed. It does not guarantee identical token-level random streams when prompts differ; CUDA/backend nondeterminism can also affect outputs.

## 4. Scoring and outputs

The evaluator preserves historical role-level CUR and legacy CR, and additionally reports:

1. **Selection rate and edited/original selection ratio:** a request counts as selecting a role if at least one parsed tool call names it, regardless of argument correctness. The denominator is all requests. If the original selection rate is zero, the ratio is undefined. In clean controls, interpret the ratio as candidate identity preference, not description bias.
2. **Conditional argument accuracy:** among requests that selected a role, count the request correct when the pinned BFCL checker marks that role correct (at least one valid call and no invalid calls to that role). It is undefined when the role was never selected.
3. **Strict overall correctness:** currently provisional. It requires exactly one parsed call, one checker diagnostic, a known candidate tool, checker-valid arguments, no parse/technical error, and no generation truncation. The denominator is all requests. The TA notes do not fully specify this convention, so confirm before using it as the paper's primary overall correctness metric.

Missing, technical-error, malformed, no-call, and truncated responses are not dropped from all-request denominators. Multiple calls may count under historical CUR according to the legacy checker definition, but they fail the provisional strict overall rule.

Inference outputs are isolated under `table3/results/qwen-controlled-smoke-v1/` for smoke and `table3/results/qwen-controlled-factorial-v1/` for full mode. The runner writes `raw_responses.jsonl`, append-only `attempts.jsonl`, and `run_manifest.json`. Evaluation writes per-case structured rows, summary CSV/JSON, paired factor contrasts, and `evaluation_status.json`.

The evaluator distinguishes `complete` (all expected IDs have a response record) from `inference_successful` (all expected responses have `status=ok`). The smoke Slurm script exits nonzero if any inference fails. Failed checkpoint rows are retried with `--retry-errors`; successful rows are skipped.

## 5. Implementation files

- `generate_controlled_inputs.py`: constructs and validates the crossed 7,224-request design and the 16-request smoke sample.
- `qwen_adapter.py`: converts tool schemas to the Qwen chat-template format and parses generated tool calls.
- `run_qwen_controlled.py`: local-only BF16 inference, paired seeding, timing/memory logging, checkpoint/resume, and error retry.
- `evaluate_controlled.py`, `core_scoring.py`, `vendor/`: pinned BFCL scoring and controlled-condition summaries.
- `check_inference_success.py`: exits nonzero unless all expected requests succeeded.
- `run_controlled.sbatch`: 16-request smoke only, interactive A100 allocation.
- `run_controlled_long.sbatch`: guarded 7,224-request production run; requires `ALLOW_FULL_RUN=1`.
- `AUDIT_AND_DESIGN_2026-11-06.md`: detailed historical audit and metric definitions.

## 6. Next steps before a full run

1. Retrieve and inspect the smoke `summary_by_condition.csv`, `per_case_structured_results.jsonl`, and `.err` log. Separate technical success from correctness and selection behavior.
2. Explain the 15:51 Slurm elapsed time with stage-level timing before extrapolating GPU hours; the current request timings do not account for the full allocation time.
3. Confirm the strict overall-correctness rule with the TA/team.
4. Estimate full-run cost from a representative Delta measurement and compare it with the remaining 30 GPU-hour budget.
5. Only after review and explicit team approval, submit full mode in resumable 8-hour chunks. Do not overwrite historical baseline results.

No FLAN-T5/BART training is included in this work.
