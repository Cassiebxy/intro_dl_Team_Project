# Intro DL Team Project

**Mitigating Tool Preference Bias in LLM Agents via Trainable Description Normalization**

CMU 11-785 team project. We will reproduce tool-preference shifts caused by edited tool descriptions, then train FLAN-T5-small, FLAN-T5-base, and BART-base to normalize descriptions while preserving tool functionality, names, and parameter schemas.

## Current status

This repository currently contains the project proposal and its LaTeX template. Experiment code and project results are not yet available.

## Repository layout

```text
.
├── README.md               # Project overview and repository guide
├── neurips_2019.sty         # LaTeX style used by the proposal
└── proposal/
    └── document.tex        # Project proposal source
```

The following directories will be added as the experiment pipeline is implemented:

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

These are planned paths, not implemented components. Large datasets, model weights, checkpoints, raw run outputs, credentials, and personal drafts stay outside the public repository.

## References

- [Tool Preferences in Agentic LLMs Are Unreliable](https://aclanthology.org/2025.emnlp-main.1060/)
- [Original paper's code and data](https://github.com/kazemf78/llm-unreliable-tool-preferences)
