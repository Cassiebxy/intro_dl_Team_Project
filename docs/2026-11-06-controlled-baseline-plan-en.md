# Team 12 | Controlled baseline revision plan

Date: November 6, 2026. Status: the team has accepted the experiment sequence below. This document specifies the next implementation. The revised experiments have yet to start. Freeze and record the exact cue text and paired decoding configuration before execution.

## 1. Objective and current evidence

Measure the effects of adding a cue and changing tool presentation order separately, then evaluate the normalizer under matched conditions.

- The historical Table 3 baseline contains 3,096 requests across 258 cases, six cues and two orders. Order and name suffix changed together. Selection and conditional correctness metrics have been recomputed, but generation has yet to be repeated under this plan.
- The first normalizer pilot fixed the name mapping and ran 22 development cases × four description conditions × two orders, totaling 176 requests from 13 tool groups. These are dependent repeated observations.
- Three cases generated malformed output in all eight settings, producing 24 parse failures. Fresh-process replays of their Clean / Original-first requests completed normally. The trigger remains unresolved, so correctness figures are preliminary until run stability is examined.

## 2. Phase 1 — Minimal four-cell experiment

For each case, construct functionally equivalent candidates A and B. Candidate identity follows its name, parameter schema and description. Initially fix the name mapping, such as suffix 1 for A and suffix 2 for B.

| Description condition | Order A→B | Order B→A |
|---|---|---|
| Clean: both candidates use the original functional description | Clean reference | Clean reference with reversed order |
| Assertive: add the same cue only to B | Cue effect at fixed order | Cue effect at the other order |

Compare Clean and Assertive within each column to estimate the specified cue's effect at that order. Compare orders within each row to estimate the order effect under fixed descriptions and name mapping. Report all four cells before pooling.

Reuse the pilot's 22 development cases for the initial check, including all previous generation failures. Four requests per case produce 88 requests per run. This checks the procedure and stability. Freeze a larger development evaluation set when expanding the study.

### Variables to hold fixed

- User query, system instruction, canonical functional sentence, parameter schema, allowed answers and scorer for each case.
- Exact cue string and placement. Append the cue at the end for the initial implementation, recording its complete text before execution.
- Model checkpoint, tokenizer, numerical precision, attention implementation, backend and output limit.
- Use the same seed for all four cells of a case. Derive it only from case ID and replicate index. Alternatively, adopt deterministic decoding uniformly and label it as a new configuration.
- Reversing the list changes only list order. Names and descriptions remain attached to A/B. Save requests and automatically verify the allowed field differences before inference.

## 3. Phase 2 — Run stability

After the first 88 requests, repeat the complete run in a fresh process and output directory with identical request order and seeds, totaling 176 requests. This baseline stability check is distinct from the existing 176-request normalizer pilot.

Compare raw text, parsed calls, tool choice, arguments, CR/REC, output length and termination reason per request. Count exact agreement, formatting-only changes, call changes and correctness changes separately.

If malformed generation recurs, record the first failing request and preceding requests, then replay that sequence to narrow the trigger. Change one computational setting at a time and rerun matched Clean and Assertive controls. Different output limits, precision or backends constitute separate diagnostic configurations.

Before interpreting primary effects, verify request construction, scoring consistency and replicate differences. If changes still affect the conclusions, add matched replicates, report variability and continue diagnosis. No arbitrary exact-agreement threshold is imposed here. Successful isolated replay does not establish full-run stability.

## 4. Phase 3 — Name mappings and cue wording

Independently swap name suffixes to form description state × list order × name mapping, giving eight cells. With 22 cases and one cue, each replicate contains 176 requests. Inspect mapping-specific results before balanced aggregation.

Then add cue variants. Pair every cue with the same functional sentence, cases, placement and configuration. For K cues, share Clean within a replicate rather than regenerating identical Clean controls for each cue. With two orders and two name mappings, request count is N × (K+1) × 2 × 2.

Paraphrasing the functional sentence is a separate later experiment. Review equivalence of capabilities, units, constraints and argument meanings before testing generalization. Report unseen wording, unseen cue families and unseen tool domains separately.

## 5. Phase 4 — Supplemental neutral control

Append a similar-length neutral sentence at the same location. It should neither recommend a candidate nor introduce new capabilities. Record the text and length measure in advance and manually review its meaning.

Compare Neutral−Clean and Assertive−Neutral. Similar length cannot ensure identical meaning, tone or token count. Interpret the latter contrast relative to the chosen neutral sentence. Complete the four-cell experiment and stability checks before this supplemental analysis.

## 6. Metrics and analysis

- SR is the proportion of cases with at least one parsed call selecting a specified candidate. Selection ratio is SR_B / SR_A, undefined when the denominator is zero.
- AAC is the proportion of selecting cases with at least one valid call and no invalid calls to that candidate. CUR divides those correct-use cases by all cases. CUR = SR × AAC when AAC is defined.
- CR accepts at least one correctly used candidate. For this simple task, REC requires exactly one parsed call with valid arguments, accepting either equivalent candidate. Freeze this convention and retain separate CR and REC columns.
- Report parse failures, length truncation, no calls, unknown tools and extra calls. Failures remain in total denominators.
- Primary contrasts are Assertive−Clean differences in SR, CUR and CR/REC within each order and mapping, accompanied by per-case improved, worsened and unchanged counts. Display cue effects for both orders to examine interaction.
- For the expanded study, use paired tool-group resampling for interval estimates. Resample all conditions together and retain within-group dependence. With only 13 current development groups, interpret intervals as exploratory.

## 7. Add the normalizer

After freezing matched baseline requests, scoring and inference configuration, add Manipulated→Normalizer and Clean→Normalizer. Normalize both candidate descriptions before frozen Qwen inference. Preserve case, name mapping, order and paired seed across conditions.

Assess movement toward Clean selection behavior, preservation of strict correctness, and retention of units, negation, required arguments and multilingual characters. Then compare untuned FLAN-T5-small, rule-based removal and the fine-tuned model. Use the final test split only after model and configuration selection.

## 8. Artifacts and completion criteria

For each run, save the versioned protocol, requests and hashes, model and data versions, seed policy, raw outputs, per-case scores, stratified metrics, anomaly records and plots. Use separate run directories and explicit labels for the historical baseline, revised controlled baseline and normalizer conditions.

The first deliverable comprises the four-cell matrix, 88 complete responses, an independent second replicate, paired difference tables and anomaly-review findings. Report later extensions separately. English GitHub reports distinguish completed runs from the planned work here.
