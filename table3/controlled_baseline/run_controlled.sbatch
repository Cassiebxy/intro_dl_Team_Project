#!/usr/bin/env bash
# Qwen controlled-baseline interactive smoke runner (16 requests only).
# Submit from Delta with TABLE3_DIR pointing at the checked-out table3 directory.
#SBATCH --job-name=qwen-controlled
#SBATCH --account=bjfu-delta-gpu
#SBATCH --partition=gpuA100x4-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=00:30:00
#SBATCH --output=qwen_controlled_%j.out
#SBATCH --error=qwen_controlled_%j.err

set -euo pipefail

TABLE3_DIR="${TABLE3_DIR:?Set TABLE3_DIR to the repository's table3 directory}"
CONTROLLED_DIR="$TABLE3_DIR/controlled_baseline"
PYTHON_BIN="${PYTHON_BIN:-/scratch/bjfu/mzhao9/qwen-env/bin/python}"
MODEL_DIR="${MODEL_DIR:-/scratch/bjfu/mzhao9/Qwen2.5-7B-Instruct}"
MODE="${MODE:-smoke}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-4096}"
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false

if [[ "$MODE" != "smoke" || "${ALLOW_FULL_RUN:-0}" == "1" ]]; then
  echo "This interactive-queue script runs smoke only. Use run_controlled_long.sbatch for a separately approved full run." >&2
  exit 2
fi
INPUT="$CONTROLLED_DIR/generated/smoke_16_ta_reviewed_v2/controlled_inputs.jsonl"
MAPPING="$CONTROLLED_DIR/generated/smoke_16_ta_reviewed_v2/controlled_mapping.jsonl"
LIMIT=16
OUTPUT_DIR="$TABLE3_DIR/results/qwen-controlled-smoke-v1"

echo "job_id=$SLURM_JOB_ID host=$(hostname -f) start=$(date -Is) mode=$MODE limit=$LIMIT"
echo "table3_dir=$TABLE3_DIR model_dir=$MODEL_DIR output_dir=$OUTPUT_DIR"
RUN_ARGS=(--input "$INPUT" --mapping "$MAPPING" --output-dir "$OUTPUT_DIR"
  --model-dir "$MODEL_DIR" --limit "$LIMIT" --max-new-tokens "$MAX_NEW_TOKENS")
if [[ "${RETRY_ERRORS:-0}" == "1" ]]; then RUN_ARGS+=(--retry-errors); fi
"$PYTHON_BIN" "$CONTROLLED_DIR/run_qwen_controlled.py" "${RUN_ARGS[@]}"

EVAL_DIR="$OUTPUT_DIR/analysis-$(date -u +%Y%m%dT%H%M%SZ)"
"$PYTHON_BIN" "$CONTROLLED_DIR/evaluate_controlled.py" \
  --input "$INPUT" --mapping "$MAPPING" --responses "$OUTPUT_DIR/raw_responses.jsonl" \
  --checker-root "$CONTROLLED_DIR/vendor" --output-dir "$EVAL_DIR"
echo "finish=$(date -Is) evaluation=$EVAL_DIR"
