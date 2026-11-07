# Controlled Qwen Table 3 Baseline: Audit and Run Plan

Status: input matrix and CPU evaluation path prepared; **no new Qwen inference has run**. The old baseline files and results remain unchanged. This is not yet a corrected, completed baseline.

## 1. Existing-baseline audit

`table3/prepare_table3.py` creates two copies of each BFCL `live_simple` tool. It appends the cue only to the edited copy and keeps the question and argument schema constant. The role order then sets both list position and suffix identity:

| Historical order | First tool | Second tool |
|---|---|---|
| `original_first` | Original, `<base>1` | Edited, `<base>2` |
| `edited_first` | Edited, `<base>1` | Original, `<base>2` |

Thus each cue is constant across its two order rows, but **position and tool-name suffix are perfectly coupled**. A preference for `1` over `2` cannot be separated from a preference for the first position; the old order contrast is not a pure position effect. Nor can the old manipulated-only cells isolate a description effect from the position/name effects. The generator's `tool_name_to_role` metadata correctly records semantic roles, but it does not remove this experimental confounding.

The frozen historical package contains 3,096 requests, role mappings, expected answers, prompts, raw Qwen responses, parsed calls, and checker scores. These remain useful as the historical, confounded result and for reproducing the original CUR/CR tables. The November 6 meeting note also reports supplementary selection-rate and conditional-argument calculations by historical order. They must be labelled exploratory/historical and not pooled into the new controlled result. The 22-case, 176-request normalizer pilot mentioned in that note used a fixed name mapping, but it is a development-set pilot with different conditions and documented generation anomalies; it is not a replacement for this 258-case baseline.

Recalculated from the archived raw calls/mappings (not a controlled causal comparison):

| Historical order | Edited selection | Original selection | Edited/original selection ratio | Edited conditional arg accuracy | Original conditional arg accuracy | Provisional strict overall correctness |
|---|---:|---:|---:|---:|---:|---:|
| Original-first | 739/1,548 = 47.74% | 762/1,548 = 49.22% | 0.970 | 586/739 = 79.30% | 505/762 = 66.27% | 1,089/1,548 = 70.35% |
| Edited-first | 1,502/1,548 = 97.03% | 6/1,548 = 0.39% | 250.33 | 1,099/1,502 = 73.17% | 5/6 = 83.33% | 1,104/1,548 = 71.32% |

The very large edited-first selection ratio is consistent with the positional/name confound; the low six-request denominator for original conditional accuracy makes 83.33% particularly unstable. These added numbers are descriptive only and do not fix the experiment design.

### Reuse decision

- Reuse: the same 258 source questions, tool definitions/schemas, canonical expected arguments, six verified cue strings, pinned checker implementation, and historical outputs as a clearly separated comparison.
- Do not reuse any historical raw output in the new primary factorial table. Those outputs were generated on Apple MPS with per-request-ID seeds and the position-coupled name mapping. The new controlled run is specified for Delta A100, crosses name mapping independently, and uses a common case-level seed across cells. Mixing those generations would break the new within-case comparisons. The exact matching historical cells can be shown in a legacy appendix, but are not counted as corrected-baseline observations.
- All new results go under a fresh `table3/results/qwen-controlled-factorial-v1/` directory. No historical result path is an output target.

## 2. Controlled factorial design

The generated matrix crosses three factors independently:

| Factor | Levels | Meaning |
|---|---|---|
| Description condition | Clean control; cue 1–6 | In cue cells, only the edited-role description receives the exact cue. Clean control gives both tools the same unedited description. |
| Role order | Original-role first; edited-role first | Swaps list position while preserving each semantic role's tool name, description, and schema. In clean control these are stable identity labels for the otherwise equivalent candidates. |
| Name mapping | Original gets suffix 1; edited gets suffix 1 | Crosses suffix identity with both role orders, instead of deriving suffix from position. |

Full size: $7\times2\times2\times258=7{,}224$ requests. This includes 1,032 clean-control requests (4 cells × 258) and 6,192 manipulated requests (24 cells × 258). The six-cue rows are each compared with clean rows at the same order and name mapping; order is compared at fixed description/name; suffix mapping is compared at fixed description/order. For clean-control rows, report candidate A/B identity preferences; do not call either clean tool “manipulated.”

The matrix is fixed-seed paired by source case: all 28 cells for one case use the same SHA256-derived case seed. Sampling remains `do_sample=true`, temperature 0.01, top-p 1.0, top-k 0, repetition penalty 1.0, BF16 Qwen2.5-7B-Instruct at the pinned checkpoint, and the Qwen chat template/tool protocol. The seed pairing is an explicit protocol improvement; the upstream paper's seeds are unavailable. Backend differences from the historical MPS run remain a limitation.

## 3. Metrics and exact counting rules

All rates use **all requests in the relevant condition as the denominator** unless the conditional-accuracy denominator is explicitly described below. Missing, technical-error, malformed, no-call, unknown-name, and truncated outputs remain in the full denominator; they are not dropped.

1. **Historical role CUR** is retained exactly: a role is correct on a request if it has at least one checker-valid call and no checker-invalid calls to that role. Its denominator is all requests, including no-call/parse/technical failures. Legacy CR is true if either role satisfies CUR. Multiple calls are allowed by legacy CUR if every call to that role is valid; this preserves historical scoring.
2. **Selection rate** for a role counts a request once if at least one successfully parsed call names that candidate, regardless of argument validity; denominator is all requests. Repeated calls to the same tool still count as one selected request. If one response calls both tools, both roles are selected, so these rates need not sum to 100%. Unknown tool names do not select either candidate. A partially parsed response can count a successfully parsed candidate call for selection, while its parse error is preserved.
3. **Selection ratio** is edited-role selection rate divided by original-role selection rate. It is undefined (blank/null) when original-role selection rate is zero. In clean controls, interpret this as candidate-identity A/B selection ratio, not a description-bias ratio.
4. **Conditional argument accuracy** is calculated per role over requests that selected that role. Its numerator is selected requests where the existing BFCL simple checker marks that role correct (at least one valid call and no invalid calls to that role); its denominator is the role's selected-request count. It is undefined if that role was never selected. A malformed response with a successfully parsed call remains selected, but the checker still determines its argument correctness.
5. **Strict overall tool-call correctness (provisional operational convention)** requires exactly one parsed call, exactly one checker diagnostic, that call must name either candidate and pass the checker, no parse/technical/missing error, and no generation truncation. Denominator is all requests. No-call, multiple calls (including duplicate calls), unknown tools, malformed calls, invalid arguments, and truncation are incorrect. The evaluator also reports legacy CR separately. The TA note does not fully specify this strict convention, so the team should confirm it before using it as the paper's primary “overall correctness” label.

The evaluator emits per-request outputs, condition-level CSV/JSON, and paired factor contrasts: each cue versus clean at matched order/name, role-first versus role-second at matched description/name, and suffix assignments at matched description/order. These are descriptive contrasts; no significance claims or confidence intervals are added.

## 4. Validation, smoke, GPU budget, and approval boundary

The complete 7,224-row generator and identity/order invariants have passed local CPU validation. A separate 16-request, 16-distinct-case smoke input and a synthetic known-answer scorer check also pass. Those are **not** a real Qwen GPU smoke: no NCSA job has been submitted and no new model output exists.

Historical raw-response timings sum to about 2.49 hours for 3,096 requests (mean 2.89 seconds per response), which would extrapolate to about 5.8 active-generation hours for 7,224 at that old MPS rate. The meeting note reports a later 176-request MPS pilot took 2.18 hours (about 44.6 seconds/request), which would extrapolate to about 89 hours at that pilot rate. These measurements differ sharply because their runs and failure behavior differ; neither is a reliable A100 estimate. The second rate would exceed the team's 30 GPU-hour budget. Run the 16-request Delta smoke first, inspect output caps, errors, throughput, and GPU memory, then estimate a full run from measured A100 data. If that estimate approaches 30 hours, ask the team whether to reduce/sequence conditions before submitting more work.

No smoke/full Slurm job has been submitted from this workspace because the machine has no active Delta allocation or authenticated remote session. Use the provided Slurm script after uploading this folder and the model-ready input files to Delta. Full mode requires the explicit `ALLOW_FULL_RUN=1` guard.

## 5. Report outline

- **Methods:** 258 BFCL live_simple single-turn cases; seven description states; crossed role order and suffix mapping; fixed case-level seed; local Qwen revision and decode/checker protocol; factorial request count; input record contains case/question/tools/schemas/role map/expected arguments outside the prompt.
- **Results:** first present clean-control role/position/name preferences; then matched cue-minus-clean selection and CUR changes; then position and name-mapping contrasts; report conditional argument accuracy and strict overall correctness beside historical CUR/CR.
- **Limitations:** one inference per cell/case, backend differs from historical MPS, prompt/model randomness is only paired by a shared seed, suffix 1/2 is a narrow name manipulation, and strict overall correctness needs TA/team confirmation. Do not claim the earlier 3,096 rows isolated description bias.
