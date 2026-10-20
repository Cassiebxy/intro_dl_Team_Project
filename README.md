# Intro DL Team Project

**Mitigating Tool Preference Bias in LLM Agents via Trainable Description Normalization**

CMU 11-785 team project. We will reproduce tool-preference shifts caused by edited tool descriptions, then train FLAN-T5-small, FLAN-T5-base, and BART-base to normalize descriptions while preserving tool functionality, names, and parameter schemas.

## Current status

_Last updated: October 20, 2026 (America/New_York)._

- **Data preparation and automated EDA:** implemented and run locally, including pinned-source validation, structural checks, role/answer diagnostics, and review exports. Automated checks do not replace the remaining human semantic/group review.
- **Table 3 baseline:** local input construction, prompt adaptation, and scoring are implemented. All **3,096 requests** and their expected answers are frozen; **54 local tests passed**. A **20-request smoke run** completed with no technical failures, parsing failures, or output truncations. The full **3,096-request run completed on October 20, 2026 at 15:47 EDT**, and automated score replay matched the saved results. There were no technical failures or output truncations; one parsing failure remains in the denominator. **Part 3 independent review and team signoff are pending.**
- **Description normalization:** the planned FLAN-T5-small, FLAN-T5-base, and BART-base comparison, final train/dev/test splits, and normalizer training/evaluation remain pending.

The repository now includes a dated baseline handoff with browsable documentation, result tables, figures, and a complete evidence archive. The original experiment code is included as an evidence snapshot inside that archive; it has not yet been integrated as a top-level runnable package.

## Baseline overview (preliminary)

We are reproducing the **Qwen2.5-7B portion of Section 2 / Table 3** in *Tool Preferences in Agentic LLMs Are Unreliable*.

| Item | Current setup |
|---|---|
| Model | `Qwen/Qwen2.5-7B-Instruct`, frozen checkpoint revision; no model training |
| Data | 258 BFCL `live_simple` cases |
| Comparison | Two tools with identical functionality and parameter schemas; one keeps the original description and the other appends one fixed assertive cue |
| Conditions | Six assertive cues, each tested in both original-first and edited-first presentation orders |
| Full run size | 258 × 6 × 2 = **3,096 requests** |
| Local runtime | Apple Silicon GPU via PyTorch MPS and Transformers; unquantized BF16 weights |
| Metrics | Edited-tool CUR, original-tool CUR, their ratio, and CR; each cue combines both orders for a denominator of 516 |
| Current state | Full run and automated replay complete; independent scoring review and midterm integration pending |

**Metric definitions:** a tool counts toward correct usage rate (CUR) only if it is called correctly at least once and has no incorrect calls to that same tool. CR counts cases where at least one candidate tool meets that criterion. The two tools' CURs can overlap. The ratio is edited CUR divided by original CUR; it is undefined when original CUR is zero.

This stage measures description-induced tool preference before introducing our normalizer. It does not include normalizer training or the larger Table 13 comparison matrix. The local backend differs from the original CUDA/vLLM setup; those differences will be documented with the validated results.

**Documentation plan:** keep this overview brief until the midterm report is completed, then expand it with the final protocol, reproduction instructions, verified results, and limitations.

## Baseline handoff

Start at [the October 20 Table 3 handoff](handoffs/table3-baseline/2026-10-20/README.md). A [zero-context session handover](handoffs/table3-baseline/2026-10-20/HANDOVER_NEW_SESSION_ZH.md) explains completed work, blockers, next steps, and pitfalls.

- [Part 3 first prompt](handoffs/table3-baseline/2026-10-20/prompts/PART3_FIRST_PROMPT_ZH.md): independent scoring verification and remaining issues.
- [Part 4 first prompt](handoffs/table3-baseline/2026-10-20/prompts/PART4_FIRST_PROMPT_ZH.md): check Part 3 evidence and leftovers before paper comparison and midterm integration.
- [Review status and leftovers](handoffs/table3-baseline/2026-10-20/reviews/): initially pending; later sessions must read the latest versions.

The evidence archive includes all 3,096 raw responses and scores, frozen inputs/configuration, source snapshots, and a portable offline replay script. It contains no model weights or virtual environment. Pooled edited-tool CUR exceeds original-tool CUR for all six cues, but strong order/name-label dependence remains; this is a directional reproduction with documented differences, not an exact or order-robust replication.

## Repository layout

```text
.
├── README.md               # Project overview and repository guide
├── handoffs/table3-baseline/2026-10-20/  # Baseline evidence and Part 3/4 handoff
├── neurips_2019.sty         # LaTeX style used by the proposal
└── proposal/
    └── document.tex        # Project proposal source
```

The following directories are planned for publication as the local implementation is reviewed and shared:

| Directory | Purpose |
|---|---|
| `src/intro_dl/` | Data preparation, description normalization, downstream evaluation, and reporting |
| `configs/` | Shared protocol and model/experiment configurations |
| `scripts/` | Setup and experiment entry points |
| `tests/` | Data integrity, evaluation, and pipeline checks |
| `manifests/` | Data provenance, splits, and experiment case definitions |
| `locks/` | Dependency versions verified for each runtime environment |
| `docs/` | Setup instructions, evaluation protocol, and reproduction notes |
| `paper/` | Final report source and publication figures |
| `results/summary/` | Verified metrics, plots, and run references |

These top-level implementation paths are not yet published; selected source snapshots and the completed run's raw evidence are available inside the dated handoff archive. Model weights, checkpoints, credentials, virtual environments, and personal drafts stay outside the public repository.

## References

- [Tool Preferences in Agentic LLMs Are Unreliable](https://aclanthology.org/2025.emnlp-main.1060/)
- [Original paper's code and data](https://github.com/kazemf78/llm-unreliable-tool-preferences)

