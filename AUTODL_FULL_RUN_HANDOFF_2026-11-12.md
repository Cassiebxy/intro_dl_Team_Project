# Qwen Controlled Table 3 Baseline: AutoDL Run Handoff

**Prepared:** 2026-11-12  
**Scope:** Review of `qwen-controlled-results.zip`, the AutoDL run artifacts, and a reproducible context packet for teammates/ChatGPT.

## Executive status

The submitted archive contains a structurally complete 7,224-request run and matching evaluation outputs. The manifest input and mapping SHA-256 hashes exactly match the repository's `full_factorial_v2` inputs. The evaluation was independently rerun locally with the repository's evaluator and pinned BFCL checker: all 67 summary rows matched the archived summary with zero field differences.

The run is technically complete: 7,224/7,224 unique response IDs, all `status=ok`, no inference errors, no missing IDs, and all generation `finish_reason=stop`. This verifies run completeness and scoring reproducibility. It does **not** establish that the experiment matches the originally planned NCSA A100 setup: this run used an NVIDIA GeForce RTX 4090 on AutoDL, and the model revision is recorded as `null`. Report the actual hardware and checkpoint provenance; do not describe it as an A100 run.

## 1. Archive and artifact locations

The user supplied `qwen-controlled-results.zip`. It contains:

```text
table3/results/qwen-controlled-autodl-full-v1/
  run_manifest.json
  attempts.jsonl
  raw_responses.jsonl
  run.lock
table3/results/qwen-controlled-autodl-evaluation-v1/
  per_case_structured_results.jsonl
  summary_by_condition.csv
  summary_by_condition.json
  paired_factor_contrasts.csv
  paired_factor_contrasts.json
  evaluation_status.json
```

`run.lock` is a leftover lock file and is not a result. The archive itself was about 1.35 MB compressed. The result files should be preserved as the run artifact; do not replace the historical baseline directory.

## 2. Experiment design and input verification

The controlled factorial crosses:

- Description state: clean control + six assertive cues (7 levels).
- Presentation order: original-role first or edited-role first (2 levels).
- Tool-name suffix mapping: original gets suffix 1 or edited gets suffix 1 (2 levels).
- Source examples: 258 BFCL `live_simple` cases.

This gives `7 × 2 × 2 × 258 = 7,224` requests, with 258 requests per full-factorial cell. Each case uses a shared SHA256-derived seed across its 28 conditions. Swapping list order preserves each role's identity, tool name, description, and schema; suffix mapping is crossed separately.

The archived hashes match the repository inputs exactly:

| Manifest field | SHA-256 | Local v2 input match |
|---|---|---|
| Input | `3f34dff071b59cf8b1c14299366652429211946d47b4b3f438ccf04ef2cb8a4e` | Yes |
| Mapping | `1db5492731d8273e6df86cca355f84c7c5e24af89237da50b6b0f93a9b429262` | Yes |

This confirms the run used the prepared condition matrix and role/name mapping. The previous 3,096-request baseline remains a separate, confounded historical experiment and was not included in this archive.

## 3. Runtime parameters recorded in the manifest

| Parameter | Recorded value |
|---|---|
| Model label | Qwen2.5-7B-Instruct |
| Model directory | `/root/autodl-tmp/Qwen2.5-7B-Instruct` |
| Model revision | `null` (exact model commit was not pinned in this manifest) |
| Dtype | BF16 |
| GPU | NVIDIA GeForce RTX 4090 (AutoDL) |
| PyTorch | `2.8.0+cu128` |
| Transformers | `4.51.3` |
| CUDA runtime | `12.8` |
| Decode | `do_sample=true`, temperature `0.01`, top-p `1.0`, top-k `0`, repetition penalty `1.0` |
| Maximum new tokens | `4096` |
| Per-condition seed | SHA256-derived seed shared across the same source case's factorial conditions |
| RNG implementation | `torch.manual_seed` and `torch.cuda.manual_seed_all` immediately before generation |
| Model config SHA-256 | `7463bb0ea78315365e6c6b74de4e73bbcc8359dfb0c5a737584e077d42c0b03c` |
| Tokenizer config SHA-256 | `5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583` |
| Chat-template SHA-256 | `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f` |

The seed pairs pseudorandom initialization, but it does not guarantee identical token-by-token random streams when prompts differ. CUDA/backend nondeterminism may also affect outputs. The original target setup discussed by the team was an A100; the recorded 4090 is a hardware deviation and must be disclosed in Methods/Limitations. The `null` model revision limits checkpoint reproducibility; use the manifest hashes and acquire the exact weight revision if a strict rerun is needed.

## 4. Completeness and generation diagnostics

The archived `evaluation_status.json` reports:

| Check | Result |
|---|---:|
| Expected requests | 7,224 |
| Response records | 7,224 |
| Unique experiment IDs | 7,224 |
| Inference `status=ok` | 7,224 |
| Inference errors / missing | 0 / 0 |
| `inference_successful` | `true` |
| Scored rows | 7,224 |

The attempt log has 7,224 `started` events and 7,224 successful terminal events; every request's final attempt number is 1, so no retries are present. All responses ended with `finish_reason=stop`; none hit the 4,096-token cap.

Generation diagnostics across the 7,224 successful responses:

- 129 responses contained no parsed tool call.
- 7 responses had parser errors; all 7 are among the no-call responses.
- 6 responses contained multiple parsed calls.
- Median output length: 41 tokens; maximum: 731 tokens.
- Sum of per-request generation times: 7,208.04 seconds (about 2 h 00 m); mean 0.998 s/request; median 0.810 s/request; p95 2.061 s/request.
- Model load: 5.58 seconds; load peak memory 15,276,322,304 bytes (about 14.22 GiB).
- Maximum per-request peak allocated GPU memory: about 14.49 GiB.

Inference `status=ok` means generation completed; it does not mean a valid tool call or correct answer. No-call, parse-error, and multiple-call outputs remain included in the scoring denominators as specified below.

## 5. Scoring convention and observed descriptive results

The evaluator preserves historical role-level CUR and legacy CR, and adds selection rate/ratio, conditional argument accuracy, and strict overall correctness. The strict overall rule requires exactly one parsed call, exactly one checker diagnostic, a known candidate tool, checker-valid arguments, no parse/technical error, and no truncation. The strict rule is provisional pending TA/team confirmation.

Observed result checks:

- Full-run legacy CR: `5,217 / 7,224 = 72.19%`.
- Strict overall correctness: also `5,217 / 7,224 = 72.19%` in this run. This equality is data-specific: none of the six multi-call responses was legacy-CR-correct; it does not mean the metrics are definitionally identical.
- Clean-control marginal selection: edited identity `49.13%`, original identity `49.13%` after balancing order and suffix mapping.
- Clean-control marginal CR/strict overall: `72.29%`.

### Cue versus clean, paired at fixed order and suffix mapping

These are descriptive averages across matched case-level cue-vs-clean contrasts; they are not significance tests or confidence intervals.

| Cue | Edited-tool selection change vs clean |
|---|---:|
| Cue 1 | +11.05 percentage points |
| Cue 2 | +16.47 pp |
| Cue 3 | +14.34 pp |
| Cue 4 | +16.18 pp |
| Cue 5 | +28.78 pp |
| Cue 6 | +33.72 pp |
| Mean across cue/order/name cells | +20.09 pp |

Across all cues, the matched average edited-selection change was +20.09 pp and original-selection change was −20.14 pp. Edited-role CUR changed by +15.67 pp and original-role CUR by −15.75 pp. Mean legacy CR/strict-overall change was −0.08 pp. This pattern is consistent with cues shifting which equivalent tool is selected while leaving total task success roughly stable; it is descriptive and should be checked against the exact paired contrasts before making causal claims.

### Position and name effects

At fixed description and name mapping, moving the edited role from second to first position was associated with +32.64 pp edited-role selection and −33.06 pp original-role selection. At fixed description and order, changing the suffix assignment from original-suffix-1 to edited-suffix-1 was associated with +32.36 pp edited-role selection and −32.39 pp original-role selection. These large effects show why the old order-only results could not separate position and name preference.

### Marginal by description condition

| Condition | Edited selection | Original selection | E/O ratio | Edited conditional arg. acc. | Original conditional arg. acc. | Edited CUR | Original CUR | Legacy CR / strict overall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Clean control | 49.13% | 49.13% | 1.00 | 73.57% | 73.57% | 36.14% | 36.14% | 72.29% |
| Cue 1 | 60.17% | 38.08% | 1.58 | 74.24% | 71.25% | 44.67% | 27.13% | 71.80% |
| Cue 2 | 65.60% | 32.56% | 2.01 | 75.18% | 70.24% | 49.32% | 22.87% | 72.19% |
| Cue 3 | 63.47% | 34.69% | 1.83 | 76.18% | 68.72% | 48.35% | 23.84% | 72.19% |
| Cue 4 | 65.31% | 32.95% | 1.98 | 74.18% | 72.06% | 48.45% | 23.74% | 72.19% |
| Cue 5 | 77.91% | 20.45% | 3.81 | 75.00% | 70.14% | 58.43% | 14.34% | 72.77% |
| Cue 6 | 82.85% | 15.21% | 5.45 | 74.39% | 68.79% | 61.63% | 10.47% | 72.09% |

Selection rates are calculated independently per role, so they need not sum to 100% (a response can call both tools or neither). The huge selection ratios in individual cells should not be used without the underlying rates because a near-zero original selection denominator makes the ratio unstable.

## 6. Re-scoring and reproduction

The result archive already includes evaluation files. Local verification reran the repository evaluator against the ZIP's raw responses and the hash-matched v2 inputs/checker: the evaluation-status JSON matched exactly, and all 67 summary rows and every field matched the archived CSV.

Equivalent evaluation command from the AutoDL project root:

```bash
python table3/controlled_baseline/evaluate_controlled.py \
  --input table3/controlled_baseline/generated/full_factorial_v2/controlled_inputs.jsonl \
  --mapping table3/controlled_baseline/generated/full_factorial_v2/controlled_mapping.jsonl \
  --responses table3/results/qwen-controlled-autodl-full-v1/raw_responses.jsonl \
  --checker-root table3/controlled_baseline/vendor \
  --output-dir table3/results/qwen-controlled-autodl-evaluation-rerun-v1
```

The output directory must not already exist. The archived input/mapping hashes should be checked before scoring any moved or regenerated files.

## 7. Recommended next steps and report cautions

1. Confirm with the team/TA whether the provisional strict overall-correctness rule is acceptable.
2. Decide whether the RTX 4090 run is acceptable for the paper's stated baseline. If yes, report it accurately and document why the hardware differed from the planned A100. Do not label this an A100 result.
3. Identify the exact Qwen weight revision/commit. The current manifest has no revision value; config/tokenizer hashes alone do not uniquely identify all model weights.
4. Inspect the 129 no-call outputs, 7 parse-error records, and 6 multi-call outputs if parser behavior or strict overall scoring is central to the report.
5. Use `paired_factor_contrasts.csv` for the matched description, position, and name comparisons. Add uncertainty estimates before making inferential claims; none are included in the current summary.
6. Do not combine this run with the old 3,096-request historical run or the 16-request smoke. Do not claim that the full factorial has passed on A100.

## 8. Copy/paste context for a teammate's ChatGPT

> We have a 7,224-request Qwen2.5-7B-Instruct factorial baseline over 258 BFCL live_simple cases: clean plus six assertive-description cues × two tool orders × two suffix/name mappings. Order swaps preserve each role's identity; names are crossed separately. The complete AutoDL run is in `qwen-controlled-results.zip`; manifest input and mapping hashes match the repository v2 inputs. The archived evaluation was independently reproduced: 7,224/7,224 responses, all inference status `ok`, no missing IDs; all 67 summary rows match. It ran on an NVIDIA GeForce RTX 4090 with PyTorch 2.8.0+cu128, Transformers 4.51.3, CUDA 12.8, BF16; it is not an A100 run, and `model_revision` is null. There were 129 no-call outputs, 7 parser-error rows (all no-call), 6 multiple-call outputs, and no truncations. Full legacy CR and provisional strict overall were both 72.19%; equality is data-specific. Matched contrasts: cue manipulations increased edited-tool selection by an average 20.09 pp; moving edited role to first increased edited selection by 32.64 pp; assigning suffix 1 to edited increased it by 32.36 pp. These are descriptive, not significance-tested. Clean-control marginal selection is 49.13% per pseudo-role and total CR is 72.29%. Strict overall correctness remains pending TA confirmation. Please distinguish technical completion from answer correctness, disclose RTX 4090 hardware and unpinned model revision, and do not claim A100 validation or merge this with the historical 3,096-request run. Review the status handoff and summary/paired contrast files before drafting Results.
