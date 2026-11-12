#!/usr/bin/env bash
# Full factorial runner. Submit only after reviewing the smoke and approving budget.
#SBATCH --job-name=qwen-controlled-full
#SBATCH --account=bjfu-delta-gpu
#SBATCH --partition=gpuA100x4
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=08:00:00
#SBATCH --output=qwen_controlled_full_%j.out
#SBATCH --error=qwen_controlled_full_%j.err

set -euo pipefail

if [ "${ALLOW_FULL_RUN:-0}" != "1" ]; then
  echo "ERROR: full run requires ALLOW_FULL_RUN=1 after approval" >&2
  exit 2
fi
if [ -z "${TABLE3_DIR:-}" ]; then
  echo "ERROR: set TABLE3_DIR to the table3 directory" >&2
  exit 2
fi

CONTROLLED_DIR="${TABLE3_DIR}/controlled_baseline"
PYTHON_BIN="${PYTHON_BIN:-/scratch/bjfu/mzhao9/qwen-env/bin/python}"
MODEL_DIR="${MODEL_DIR:-/scratch/bjfu/mzhao9/Qwen2.5-7B-Instruct}"
INPUT="${CONTROLLED_DIR}/generated/full_factorial_v2/controlled_inputs.jsonl"
MAPPING="${CONTROLLED_DIR}/generated/full_factorial_v2/controlled_mapping.jsonl"
OUTPUT_DIR="${TABLE3_DIR}/results/qwen-controlled-factorial-v1"
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

echo "job_id=${SLURM_JOB_ID:-manual} host=$(hostname -f) start=$(date -Is) limit=7224"
echo "table3_dir=${TABLE3_DIR} model_dir=${MODEL_DIR} output_dir=${OUTPUT_DIR}"

set +e
"${PYTHON_BIN}" "${CONTROLLED_DIR}/run_qwen_controlled.py" \
  --input "${INPUT}" \
  --mapping "${MAPPING}" \
  --output-dir "${OUTPUT_DIR}" \
  --model-dir "${MODEL_DIR}" \
  --limit 7224 \
  --allow-full-run \
  --max-new-tokens 4096 \
  --retry-errors
INFERENCE_RC=$?
set -e

EVAL_DIR="${OUTPUT_DIR}/analysis-$(date -u +%Y%m%dT%H%M%SZ)"
"${PYTHON_BIN}" "${CONTROLLED_DIR}/evaluate_controlled.py" \
  --input "${INPUT}" \
  --mapping "${MAPPING}" \
  --responses "${OUTPUT_DIR}/raw_responses.jsonl" \
  --checker-root "${CONTROLLED_DIR}/vendor" \
  --output-dir "${EVAL_DIR}"

"${PYTHON_BIN}" "${CONTROLLED_DIR}/check_inference_success.py" "${EVAL_DIR}/evaluation_status.json"
if [ "${INFERENCE_RC}" -ne 0 ]; then
  echo "ERROR: inference runner returned ${INFERENCE_RC}" >&2
  exit 1
fi

echo "finish=$(date -Is) evaluation=${EVAL_DIR}"
