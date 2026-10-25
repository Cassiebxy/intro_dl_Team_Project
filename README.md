# Mitigating Tool Preference Bias in LLM Agents
## Trainable Description Normalization — CMU 11-785 Team Project

We study whether assertive wording in a tool description changes an LLM agent's choice between functionally equivalent tools. Our completed baseline reproduces the Qwen2.5-7B experiment from Table 3 of *Tool Preferences in Agentic LLMs Are Unreliable*. The next stage will evaluate trainable description normalization while preserving tool functionality and parameter schemas.

**Status — October 24, 2026:** the Table 3 baseline is complete, including the full run, offline score replay, technical review, and human signoff. The team-designated final midterm report is available; the PDF is preserved as supplied. Normalizer training and evaluation remain planned.

## Start here

- **[Final midterm report](reports/midterm/midterm_report.pdf)** ([version notes and earlier source](reports/midterm/README.md)) — motivation, methodology, baseline results, limitations, and next steps.
- **[Paper comparison](handoffs/table3-baseline/2026-10-20/tables/PAPER_VS_LOCAL_TABLE3.md)** and **[results by presentation order](handoffs/table3-baseline/2026-10-20/tables/ORDER_EFFECTS.md)**.
- **[Scoring review](handoffs/table3-baseline/2026-10-20/reviews/part3/REVIEW_REPORT.md)** and **[human signoff](handoffs/table3-baseline/2026-10-20/reviews/part3/HUMAN_SIGNOFF.md)**.
- **[Reproducibility and evidence](handoffs/table3-baseline/2026-10-20/README.md)** — frozen inputs, raw responses, scores, source snapshots, and portable offline replay.
- **[Current project status](handoffs/table3-baseline/2026-10-20/CURRENT_STATUS.md)** — supersedes outdated pending/local-only labels in historical handoffs.

## Completed baseline

| Component | Setup |
|---|---|
| Agent | `Qwen/Qwen2.5-7B-Instruct`; no model training |
| Checkpoint revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Data | 258 canonical BFCL `live_simple` cases |
| Conditions | Six assertive cues × two presentation orders |
| Requests | **3,096** total; 516 per cue and 258 per cue/order |
| Tool pair | Matching functionality and parameter schemas; one description appends an assertive cue |
| Runtime | Apple Silicon / PyTorch MPS, unquantized BF16 |
| Run completed | October 20, 2026, 15:47 EDT |
| Validation | All 3,096 saved scores matched offline replay; Part 3 technical review PASS and Kyrie human signoff PASS on October 21 |
| Run health | Zero technical failures, zero output truncations; one parse failure retained in the denominator |

## Results

Percentages pool both orders. See the [full comparison CSV](handoffs/table3-baseline/2026-10-20/tables/paper_vs_local_table3.csv) for cue text and paper reference values.

| Cue | Edited-tool CUR (%) | Original-tool CUR (%) | CUR ratio | CR (%) |
|---|---:|---:|---:|---:|
| 1 | 47.29 | 23.84 | 1.984 | 71.12 |
| 2 | 52.33 | 18.22 | 2.872 | 70.54 |
| 3 | 52.13 | 18.60 | 2.802 | 70.74 |
| 4 | 54.65 | 16.47 | 3.318 | 71.12 |
| 5 | 58.91 | 11.82 | 4.984 | 70.74 |
| 6 | 61.24 | 9.88 | 6.196 | 71.12 |

**Metrics:** a tool contributes to correct usage rate (CUR) if it has at least one correct call and no incorrect calls to that same tool in a request. CR is the fraction of requests where at least one candidate tool satisfies that criterion. The CURs may overlap in general. Ratio = edited CUR / original CUR; it is undefined when original CUR is zero. Parse failures remain in the fixed denominator.

The pooled edited-tool advantage ranges from **1.984× to 6.196×**. This is a directional reproduction with substantial order/name-label dependence: the first three cues do not favor the edited tool in the original-first condition. Tool position and name suffix are coupled, so the results do not isolate a causal position effect. Local CR is 4.08–5.86 percentage points below the paper; the cause has not been isolated. The local MPS/Transformers backend differs from the original CUDA/vLLM setup.

[Order effects](handoffs/table3-baseline/2026-10-20/tables/ORDER_EFFECTS.md), [failure counts](handoffs/table3-baseline/2026-10-20/reviews/part3/results/response_failure_counts.csv), and [checker edge cases](handoffs/table3-baseline/2026-10-20/reviews/part3/evidence/CASE_REVIEW.md) accompany the results. Repeated cases across conditions are paired observations, not 3,096 independent tasks.

## Reproduce and inspect

The [evidence package](handoffs/table3-baseline/2026-10-20/README.md) contains frozen configuration, raw responses, per-request scores, source snapshots, and a standard-library offline replay script. Replay requires no model download, GPU, or paid API. Model weights and virtual environments are excluded.

The [data-preparation module](table3/README.md) documents upstream data construction. The complete inference/scoring implementation is preserved inside the evidence ZIP; a consolidated top-level training/evaluation package has not yet been published.

## Next stage

See [final report follow-ups](reports/final/FINAL_REPORT_FOLLOWUPS.md) for the planned framework diagram, reporting clarifications, and open research items. The diagram was deferred from midterm because of the page limit.

1. Add clean-vs-clean controls and disentangle presentation order from tool-name labels.
2. Finalize grouped train/dev/test splits and train the planned FLAN-T5-small, FLAN-T5-base, and BART-base normalizers.
3. Evaluate preference reduction alongside functionality preservation and downstream CR.

These are planned extensions; the current results contain no trained normalizer.

## Repository guide

| Path | Contents |
|---|---|
| [`reports/midterm/`](reports/midterm/README.md) | Current report and source links |
| [`table3/`](table3/README.md) | Data preparation, pinned sources, generated inputs, validation |
| [`handoffs/table3-baseline/2026-10-20/`](handoffs/table3-baseline/2026-10-20/README.md) | Baseline evidence, tables, figures, scoring review, historical handoffs |
| [`proposal/document.tex`](proposal/document.tex) | Original proposal and initial plan |

## References

- [Tool Preferences in Agentic LLMs Are Unreliable](https://aclanthology.org/2025.emnlp-main.1060/)
- [Original paper's code and data](https://github.com/kazemf78/llm-unreliable-tool-preferences)

See the [report bibliography](reports/midterm/README.md) and [source attribution](handoffs/table3-baseline/2026-10-20/SOURCES_AND_ATTRIBUTION.md) for additional references and provenance.
