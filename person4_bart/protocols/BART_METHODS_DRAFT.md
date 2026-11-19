# BART methods and results draft

This page records the draft from the engineering stage. The completed BFCL methods and results are documented in the [report draft](../BART_REPORT_EN.md) and [BFCL handoff report](../RESULTS_BFCL.md).

At this stage, we had completed the independent engineering setup and synthetic smoke test. The project data, frozen team protocol, and downstream results were still pending. The engineering metrics describe the synthetic run. See the [local status record](../STATUS.md).

## Methods used in the engineering run

BART uses the public `facebook/bart-base` pretrained weights at the revision recorded in `model_source.json`. It is an encoder–decoder model trained to minimize the token-level negative log-likelihood of the functional target description given the input description. Padding labels are set to -100, and gradient accumulation is weighted by the number of valid target tokens. BART rewrites only the description. The tool name, parameter schema, and question are taken from the source case.

The local run uses FP32, eager attention, MPS, and greedy generation. Train and validation files are separate, and generation has a fixed cap independent of gold target length. The run records source and code hashes, the random seed, training configuration, loss for each epoch, selected epoch, runtime, and sampled memory counters. The checkpoint stores weights, tokenizer, and configuration. After reloading, the workflow regenerates the outputs and compares them by ID.

## Details to record for the formal experiment

- Final `protocol_version` along with versions and hashes for the data, splits, grouping, and cue pool.
- Shared input template, dataset composition, tuning budget, early stopping, and model selection rule for all three models.
- Final BART hyperparameters, handling of truncation and exceptions, and counts for each failure type.
- Matched Qwen controls, evaluation matrix, weight revision, backend, and scorer version.
- Results for the three generalization slices, functional review, per-case diagnostics, and paired statistics at the tool-group level.

## Results and limitations

The engineering run verifies the local training, saving, reloading, generation, and audit workflow. Evaluating mitigation requires preference shifts relative to Clean, call correctness, and functionality preservation alongside training loss and exact match.

Comparisons between BART and FLAN-T5 reflect pretraining and instruction tuning differences as well as model architecture. Numerical behavior and randomness can differ across MPS and CUDA, so downstream comparisons require matched controls. Literal checks can miss semantic errors or flag valid paraphrases, which calls for independent human review.
