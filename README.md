# Intro DL Team Project

**Mitigating Tool Preference Bias in LLM Agents via Trainable Description Normalization**

CMU 11-785 team project. We will reproduce tool-preference shifts caused by edited tool descriptions, then train FLAN-T5-small, FLAN-T5-base, and BART-base to normalize descriptions while preserving tool functionality, names, and parameter schemas.

## Current status

_Last updated: October 20, 2026 (America/New_York)._

- **Data preparation and automated EDA:** implemented and run locally, including pinned-source validation, structural checks, role/answer diagnostics, and review exports. Automated checks do not replace the remaining human semantic/group review.
- **Table 3 baseline:** local input construction, prompt adaptation, and scoring are implemented. All **3,096 requests** and their expected answers are frozen; **54 local tests passed**. A **20-request smoke run** completed with no technical failures, parsing failures, or output truncations. The full reproduction run is **in progress**; final results have not yet been validated.
- **Description normalization:** the planned FLAN-T5-small, FLAN-T5-base, and BART-base comparison, final train/dev/test splits, and normalizer training/evaluation remain pending.

The experiment implementation and run artifacts are currently maintained locally; this GitHub update is documentation only. The tracked repository still contains the proposal and its LaTeX template.

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
| Current state | Smoke validation complete; full inference running; final scoring/replay and paper comparison pending |

**Metric definitions:** a tool counts toward correct usage rate (CUR) only if it is called correctly at least once and has no incorrect calls to that same tool. CR counts cases where at least one candidate tool meets that criterion. The two tools' CURs can overlap. The ratio is edited CUR divided by original CUR; it is undefined when original CUR is zero.

This stage measures description-induced tool preference before introducing our normalizer. It does not include normalizer training or the larger Table 13 comparison matrix. The local backend differs from the original CUDA/vLLM setup; those differences will be documented with the validated results.

**Documentation plan:** keep this overview brief until the midterm report is completed, then expand it with the final protocol, reproduction instructions, verified results, and limitations.

## Repository layout

```text
.
├── README.md               # Project overview and repository guide
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

These paths are not yet published in this repository; some components are already implemented locally as described above. Large datasets, model weights, checkpoints, raw run outputs, credentials, and personal drafts stay outside the public repository.

## References

- [Tool Preferences in Agentic LLMs Are Unreliable](https://aclanthology.org/2025.emnlp-main.1060/)
- [Original paper's code and data](https://github.com/kazemf78/llm-unreliable-tool-preferences)
