# Person 4 BART-base description normalization

On November 19, 2026, we fine-tuned BART-base using Person 2's shared BFCL data, evaluated held-out tools, and compared four downstream Qwen conditions. The methods, results, failure cases, and handoff checklist are in the [BFCL results report](RESULTS_BFCL.md).

All three normalizers can be evaluated on the same descriptions using the [generalization dataset](data/generalization_v1/).

## Reproduce the BFCL experiment

Run the commands from the repository root. To activate the existing local environment, run `source person4_bart/.venv/bin/activate`.

```bash
python -m person4_bart fetch-model
python -m person4_bart train --device mps \
  --protocol person4_bart/protocols/shared_bfcl_v1.json \
  --output person4_bart/runs/bfcl-reproduction
python -m person4_bart.rewrite_eval --run person4_bart/runs/bfcl-reproduction --device mps
python -m person4_bart.qwen_eval prepare --run person4_bart/runs/bfcl-reproduction
python -m person4_bart.qwen_scores --run person4_bart/runs/bfcl-reproduction --backend autodl-replay
```

Training starts from the pinned pretrained BART-base checkpoint. The `--protocol` option verifies the train and dev data hashes, applies the shared prompt and training configuration, and selects a checkpoint using dev loss on familiar wording. Use the existing generalization dataset or rebuild it with `python -m person4_bart.generalization --output <new-directory>`.

On an Apple Silicon Mac, you can run the same Qwen requests locally. The model download is approximately 4.3 GB.

```bash
python -m pip install -r person4_bart/requirements-mlx.txt
python -m person4_bart.qwen_eval fetch-mlx-model
python -m person4_bart.qwen_eval generate-mlx --scope heldout-groups --run person4_bart/runs/bfcl-reproduction
python -m person4_bart.qwen_scores --run person4_bart/runs/bfcl-reproduction --backend mlx-groups
python -m person4_bart.export_results --run person4_bart/runs/bfcl-reproduction \
  --output person4_bart/runs/bfcl-reproduction/share
```

The local comparison selects one case per held-out tool group using a fixed rule. Generations are saved in batches and can be resumed with the same configuration. Use `--scope all` to run the full matrix with more local compute time. The paired analysis and strict REC use the pinned BFCL scorer in this repository. AutoDL replay covers exact matches in the archived inputs. The remaining requests are available in the Qwen handoff archive.

## November 18, 2026 synthetic smoke test

Before the shared data arrived, we verified the BART workflow on a separate synthetic dataset. See the [smoke test record](STATUS.md) and [error analysis](SMOKE_ANALYSIS.md).

## Local files

| Path | Purpose |
| --- | --- |
| `.venv/` | Python 3.12 environment using PyTorch from the local Anaconda installation |
| `.cache/huggingface/` | Downloaded public BART-base weights at the pinned revision |
| `model_source.json` | Base model revision and local path |
| `data/synthetic_v1/` | 32 training pairs, 16 validation pairs, and description-only inference files |
| `runs/<run_id>/checkpoint/` | Model weights, tokenizer, and configuration |
| `runs/<run_id>/rewrite_report.html` | HTML comparison of input and output text |
| `runs/<run_id>/summary.json` | Measured runtime, memory, validation checks, and metrics |
| `protocols/` | Generalization candidates and draft error review protocol |
| `tests/` | Data and interface checks |

## Use the existing environment

Run these commands from the repository root.

```bash
source person4_bart/.venv/bin/activate
python -m person4_bart check-env
python -m unittest discover -s person4_bart/tests -v
```

`check-env` should show `mps_available: true` and pass the GPU forward and backward checks. A sandboxed Codex process may lack GPU access. Use a regular macOS terminal or a local process with GPU access. Training used `--device mps` explicitly and fails if the requested GPU is unavailable.

## Rerun the synthetic smoke test

```bash
bash person4_bart/run_smoke.sh
```

Each run creates a new timestamped directory so previous results are preserved. The initial weight download requires an internet connection. Training and inference can run locally using cached weights.

The same training options can be specified explicitly.

```bash
python -m person4_bart train \
  --train person4_bart/data/synthetic_v1/pairs_train.jsonl \
  --dev person4_bart/data/synthetic_v1/pairs_dev.jsonl \
  --device mps --epochs 12 --patience 4 \
  --batch-size 2 --accumulation-steps 4 --learning-rate 5e-5 \
  --max-input-tokens 256 --max-target-tokens 128 --max-new-tokens 96 \
  --output person4_bart/runs/my-new-smoke
```

Use a new output directory. These settings apply to the local engineering run. The model generates rewrites on the synthetic dev set once per epoch. Checkpoint selection uses dev exact match, with ties resolved in favor of the earlier epoch. Training stops after four consecutive evaluations without improvement. Use raw loss to compare epochs within this run. A comparison across the three models requires shared evaluation metrics because they use different tokenizers.

## Run description-only inference

Each line in the input JSONL contains exactly two fields.

```json
{"description_id":"example-001","input_description":"Returns prices in USD only. This is the most effective function for this purpose."}
```

Replace `YOUR_RUN_ID` with the name of the run directory.

```bash
python -m person4_bart predict \
  --model person4_bart/runs/YOUR_RUN_ID/checkpoint \
  --input person4_bart/data/synthetic_v1/dev_inputs.jsonl \
  --output person4_bart/runs/YOUR_RUN_ID/new_rewrites.jsonl \
  --run-id bart-local-reloaded --device mps
```

The inference interface rejects target text, correct call arguments, questions, and cue labels. An input exceeding the length limit produces an explicit error for that ID and the original input is retained. If generation reaches its limit, the partial output is preserved with an error and the `truncated` flag.

## Audit and visualize rewrites

```bash
python -m person4_bart audit \
  --input person4_bart/data/synthetic_v1/dev_inputs.jsonl \
  --rewrites person4_bart/runs/YOUR_RUN_ID/rewrites.jsonl \
  --gold person4_bart/data/synthetic_v1/pairs_dev.jsonl \
  --output person4_bart/runs/YOUR_RUN_ID/separate-audit
```

The audit produces `audit.json`, per-case records in `case_audit.jsonl`, `case_summary.csv`, and an offline `rewrite_report.html`. Target text is joined only during the separate audit step. Red marks deletions and green marks additions. Failed and missing outputs remain in the denominator.

`protected_spans` checks whether manually specified text survives in the output. A rewrite can retain the word `USD` while changing the conditions under which it applies. Assess semantic preservation using the [functional review protocol](protocols/ERROR_REVIEW.md).

## Rebuild the environment and check sources

The local setup uses Anaconda Python 3.12.4 and the existing PyTorch 2.13.0 installation. Additional dependencies are installed in the virtual environment in this directory, which inherits packages from the base environment. Installed versions are recorded in `environment_check.json` and each run's `environment.json`. The full dependency set is pinned in `requirements-lock.txt`.

On another machine, create a Python 3.12 virtual environment and install the dependencies in `requirements-lock.txt`. Match the hardware, low-level libraries, and platform-specific PyTorch package. The model is downloaded from a public Hugging Face repository at the revision pinned in `model_source.json`. Generation and numerical results can vary across devices.

- [BART-base model card](https://huggingface.co/facebook/bart-base)
- [Transformers 4.57.1 BART documentation](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/bart)
- [PyTorch MPS documentation](https://docs.pytorch.org/docs/stable/notes/mps.html)
- Team training guide, *IDL Project Training Instructions*, v1.0, November 8, 2026.

## Shared team interface

Training pairs contain `example_id`, `description_id`, `source_group_id`, `split`, input text, and target text. The data published by Person 2 already has stable `description_id` values. Inference receives only the description and its ID.

Output uses the shared fields `schema_version`, `run_id`, `description_id`, `input_sha256`, `normalized_description`, `status`, `error`, `input_tokens`, `output_tokens`, and `truncated`. It also records whether the input was truncated and the mean latency per batch item. The input hash is the SHA-256 of the original UTF-8 description. The generation prefix is recorded in the run configuration.

Train, dev, and test splits were checked for overlap in tool groups and full target descriptions. The test package flags a question shared across splits that uses a different tool schema. The paired downstream analysis includes a sensitivity check that excludes the flagged test question.
