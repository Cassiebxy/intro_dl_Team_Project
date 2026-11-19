# Delta execution

Train the normalizer here; Person 1 runs downstream Qwen. No GPU jobs have been submitted by this code delivery.

## Preparation

Use the latest `person3-flan-t5-base` branch. Replace all paths and the account below with your actual values:

```bash
export PROJECT_DIR=/absolute/path/to/intro_dl_Team_Project
export PYTHON_BIN=/absolute/path/to/environment/bin/python
export MODEL_DIR=/absolute/path/to/flan-t5-base
export RUN_DIR=/absolute/path/to/person3-runs/smoke-v1
export DELTA_ACCOUNT=your-authorized-delta-gpu-account
cd "$PROJECT_DIR"
accounts
"$PYTHON_BIN" -m pip install -r experiments/person3-base/requirements.txt
```

Use a CUDA-enabled PyTorch environment. Select an authorized account from `accounts`; the old team script's `bjfu-delta-gpu` account is not assumed to be yours. Prepare a complete pretrained `google/flan-t5-base` snapshot before submission, record its immutable revision, and put it at MODEL_DIR. This must not be a small-model checkpoint. Jobs run offline and will fail if model files are missing. Dependency ranges are not a tested environment lock; each job records pip freeze.

## Smoke first

```bash
export MODE=smoke
sbatch --account="$DELTA_ACCOUNT" --partition=gpuA100x4-interactive \
  --time=00:30:00 --export=ALL experiments/person3-base/run_delta.sbatch
squeue -u "$USER"
```

Inspect `p3_<jobid>.out`, `p3_<jobid>.err`, `reload_check.json`, and `rewrites.jsonl`. Require a zero exit code, finite losses, successful reload, and sensible outputs before formal training. No training runtime has been measured.

## Formal training after smoke passes

```bash
export MODE=multi
export RUN_DIR=/absolute/path/to/person3-runs/base-multi-v1
sbatch --account="$DELTA_ACCOUNT" --partition=gpuA100x4 \
  --time=02:00:00 --export=ALL experiments/person3-base/run_delta.sbatch

export MODE=single
export RUN_DIR=/absolute/path/to/person3-runs/base-single-v1
sbatch --account="$DELTA_ACCOUNT" --partition=gpuA100x4 \
  --time=02:00:00 --export=ALL experiments/person3-base/run_delta.sbatch
```

Each arm requests one GPU. Two hours is a wall-time budget, not a measured estimate. Use distinct output paths. Follow README.md for selected-checkpoint evaluation and Qwen request export.

## Recovery

Once the old job has stopped, retain its MODE, RUN_DIR, model, seed, and environment, set `export RESUME=1`, and resubmit. At least one completed epoch and `resume.json` are required. If there is no completed epoch, use a fresh output directory. Reset `RESUME=0` for a new experiment.

Completed epochs are stored separately; the resume pointer is replaced only after epoch files are written. Partial-epoch work is repeated. CUDA recovery restores CPU and CUDA RNG state, but hardware/kernel differences may prevent bitwise reproducibility. MPS RNG recovery is not implemented. Do not submit concurrent jobs to one output path.

Recovery is implemented but not runtime-tested here. First resume the completed smoke run and compare regenerated outputs, then test an interrupted multi-epoch run before relying on continued-training recovery. This environment has no PyTorch, so syntax and data tests do not establish neural execution correctness.

Official submission/account guidance: [NCSA Delta running jobs](https://docs.ncsa.illinois.edu/systems/delta/en/latest/user_guide/running_jobs.html). Live queue access depends on your allocation.
