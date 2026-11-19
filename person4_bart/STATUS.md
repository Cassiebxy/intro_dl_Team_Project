# Person 4 synthetic smoke test record

This page records the November 18 engineering smoke test. Training and evaluation on the shared dataset are documented in the [BFCL results report](RESULTS_BFCL.md).

As of November 18, 2026, the smoke test artifacts were saved locally under `person4_bart/` ahead of the first commit and push.

## Completed and verified

| Item | Status and evidence |
| --- | --- |
| Python environment | `.venv/` uses Python 3.12.4 and PyTorch from Anaconda. Versions and constraints for 35 dependencies were verified in `requirements-lock.txt`. |
| Apple GPU | Forward and backward MPS checks passed on a 16 GB M4 MacBook Air. See `environment_check.json`. |
| BART base model | `facebook/bart-base` at revision `aadd2ab0ae0c8268c7c9693540e9904811f36177`. Cache details and the local path are in `model_source.json`. |
| Synthetic data | 32 training pairs across eight tool groups and 16 validation pairs across four disjoint tool groups. The synthetic set uses 25% clean identity pairs and predates the shared BFCL dataset. |
| Training and checkpoints | Full fine-tuning, saving, and reloading completed on MPS. The final run is in `runs/synthetic-smoke-20261118-02/`. |
| Output interface and visualization | Per-ID output includes hashes, errors, and truncation flags. Artifacts include offline HTML comparisons, JSONL and CSV records, and training curves. |
| Data and interface checks | All 12 unit tests passed. See [the test record](TEST_RESULTS.md). |
| Standalone inference | The saved checkpoint was run with `predict` on four additional clean synthetic descriptions, then the outputs were audited. |
| Draft generalization and review protocols | `protocols/` defines three generalization slices, eight cue candidates awaiting review, error criteria, and a blank review template. The final test was still pending at this stage. |

## Final engineering run

The selected run is `runs/synthetic-smoke-20261118-02/`. The first run, `...-01/`, is also available. The second run explicitly cleared summarization defaults inherited from the base model, disabled the no-repeat n-gram constraint, and verified that a natural EOS at the generation limit is counted as a normal finish.

- The run used MPS, FP32, and eager attention.
- Training used a microbatch size of 2, four gradient accumulation steps, an effective batch size of 8, AdamW, a learning rate of 5e-5, and seed 42.
- Input and target limits were 256 and 128 tokens, respectively. Greedy decoding used a fixed cap of 96 generated tokens independent of target length.
- Training completed seven epochs and 28 optimizer updates. Epoch 3 was selected. Training stopped after four consecutive exact-match evaluations without improvement.
- The synthetic run took **55.268 seconds**, including base model checks, training, validation, checkpoint saving and reloading, and final generation.
- After reloading, all 16 validation outputs matched the corresponding outputs from before saving.
- Synthetic validation achieved **16/16 exact matches** and 16/16 protected-span checks. Every output completed without errors or truncation. Training outputs achieved 32/32 exact matches.
- The highest sampled MPS driver allocation was 3,701,374,976 bytes (about 3.45 GiB). The highest sampled MPS tensor allocation was about 2.22 GiB. These counters measure allocations at sample times.

The data and source hashes at training time, complete configuration, and original metrics are saved in `run_config.json`, `history.jsonl`, `summary.json`, and `reload_check.json` in the run directory. BFCL training and evaluation interfaces were added after this run.

## Failure case

Of the four additional clean descriptions, three were preserved verbatim and one lost a functional constraint.

```text
Input  Uploads a file only after explicit authorization. The maximum file size is 5 MB.
Output Uploads a file only after explicit authorization.
```

**The 5 MB file limit was deleted, triggering both `over_delete` and `clean_harm`.** This example shows that an exact match on all 16 synthetic dev descriptions can coexist with loss of functionality on other examples.

The four examples were held aside from training, checkpoint selection, and later tuning. They received automated literal checks and model-assisted review. This small synthetic diagnostic predates the team's generalization study and independent human review. See `runs/synthetic-smoke-20261118-02/diagnostic_review/rewrite_report.html` and the [smoke test analysis](SMOKE_ANALYSIS.md).

## Scope of the run

This run verified the BART workflow on synthetic data and MPS. It preceded BFCL training, Qwen evaluation, and any conclusions about mitigation or generalization. At this stage, formal training called for alignment on C0/C1, the instruction, the model selection rule, and ID mappings, followed by training from the original BART-base checkpoint. The training interface also supports CUDA.

The local directory `runs/synthetic-smoke-20261118-02/` also contains `rewrite_report.html`, `diagnostic_review/rewrite_report.html`, and `training_curves.png`. See the [reproduction instructions](README.md) and [smoke test analysis](SMOKE_ANALYSIS.md).
