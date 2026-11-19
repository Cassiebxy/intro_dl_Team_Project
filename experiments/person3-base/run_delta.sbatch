#!/usr/bin/env bash
#SBATCH --job-name=p3-flan-base
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=00:30:00
#SBATCH --output=p3_%j.out
#SBATCH --error=p3_%j.err
set -euo pipefail
: "${PROJECT_DIR:?Set the absolute repository path}"
: "${PYTHON_BIN:?Set the absolute Python executable path}"
: "${MODEL_DIR:?Set the local FLAN-T5-base snapshot path}"
: "${RUN_DIR:?Set the absolute output path}"
MODE="${MODE:-smoke}"
RESUME="${RESUME:-0}"
cd "$PROJECT_DIR"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4
"$PYTHON_BIN" -c 'import torch, transformers; assert torch.cuda.is_available(), "CUDA unavailable"; print(torch.__version__, transformers.__version__, torch.cuda.get_device_name(0))'
"$PYTHON_BIN" -m pip freeze > "${SLURM_SUBMIT_DIR:-$PWD}/p3_environment_${SLURM_JOB_ID:-manual}.txt"
"$PYTHON_BIN" experiments/person3-base/pipeline.py audit
args=(train --model "$MODEL_DIR" --device cuda --output "$RUN_DIR")
case "$MODE" in
  smoke) args+=(--smoke --mode multi) ;;
  multi) args+=(--mode multi) ;;
  single) args+=(--mode single --single-cue "${SINGLE_CUE:-suffix_1}") ;;
  *) echo 'MODE must be smoke, multi, or single' >&2; exit 2 ;;
esac
if [[ "$RESUME" == 1 ]]; then args+=(--resume); fi
"$PYTHON_BIN" -u experiments/person3-base/pipeline.py "${args[@]}"
