#!/usr/bin/env bash
# Full Qwen controlled factorial on Delta's production A100 queue.
# Submit only after the 16-request smoke and an explicit team budget decision.
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
if [[ "${ALLOW_FULL_RUN:-0}" != "1" ]]; then
  echo "Refusing full run: set ALLOW_FULL_RUN=1 only after smoke review and team budget approval." >&2
  exit 2
fi

TABLE3_DIR="${TABLE3_DIR:?Set TABLE3_DIR to the repository's table3 directory}"
CONTROLLED_DIR="$TABLE3_DIR/controlled_baseline"
PYTHON_BIN="${PYTHON_BIN:-/scratch/bjfu/mzhao9/qwen-env/bin/python}"
MODEL_DIR="${MODEL_DIR:-/scratch/bjfu/mzhao9/Qwen2.5-7B-Instruct}"
INPUT="$CONTROLLED_DIR/generated/full_factorial_v2/controlled_inputs.jsonl"
MAPPING="$CONTROLLED_DIR/generated/full_factorial_v2/controlled_mapping.jsonl"
OUTPUT_DIR="$TABLE3_DIR/results/qwen-controlled-factorial-v1"
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false

echo "job_id=$SLURM_JOB_ID host=$(hostname -f) start=$(date -Is) limit=7224"
echo "table3_dir=$TABLE3_DIR model_dir=$MODEL_DIR output_dir=$OUTPUT_DIR"
RUN_ARGS=(--input "$INPUT" --mapping "$MAPPING" --output-dir "$OUTPUT_DIR"
  --model-dir "$MODEL_DIR" --limit 7224 --allow-full-run --max-new-tokens 4096)
if [[ "${RETRY_ERRORS:-0}" == "1" ]]; then RUN_ARGS+=(--retry-errors); fi
"$PYTHON_BIN" "$CONTROLLED_DIR/run_qwen_controlled.py" "${RUN_ARGS[@]}"

EVAL_DIR="$OUTPUT_DIR/analysis-$(date -u +%Y%m%dT%H%M%SZ)"
"$PYTHON_BIN" "$CONTROLLED_DIR/evaluate_controlled.py" \
  --input "$INPUT" --mapping "$MAPPING" --responses "$OUTPUT_DIR/raw_responses.jsonl" \
  --checker-root "$CONTROLLED_DIR/vendor" --output-dir "$EVAL_DIR"
echo "finish=$(date -Is) evaluation=$EVAL_DIR"
