#!/usr/bin/env bash
#SBATCH --job-name=qwen-paired
#SBATCH --account=bjfu-delta-gpu
#SBATCH --partition=gpuA100x4-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --output=qwen_paired_%j.out
#SBATCH --error=qwen_paired_%j.err
set -euo pipefail
TABLE3_DIR="${TABLE3_DIR:?Set TABLE3_DIR to the checkout table3 directory}"
CONTROLLED_DIR="$TABLE3_DIR/controlled_baseline"
PYTHON_BIN="${PYTHON_BIN:-/scratch/bjfu/mzhao9/qwen-env/bin/python}"
MODEL_DIR="${MODEL_DIR:-/scratch/bjfu/mzhao9/Qwen2.5-7B-Instruct}"
INPUT_DIR="$CONTROLLED_DIR/generated/paired_stability_16"
OUTPUT_ROOT="${OUTPUT_ROOT:-$TABLE3_DIR/results/qwen-paired-stability-$SLURM_JOB_ID}"
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
mkdir -p "$OUTPUT_ROOT"
for replicate in 1 2; do
  OUT="$OUTPUT_ROOT/replicate-$replicate"
  "$PYTHON_BIN" "$CONTROLLED_DIR/run_qwen_controlled.py" \
    --input "$INPUT_DIR/controlled_inputs.jsonl" --mapping "$INPUT_DIR/controlled_mapping.jsonl" \
    --model-dir "$MODEL_DIR" --output-dir "$OUT" --limit 16 --max-new-tokens 4096
  "$PYTHON_BIN" "$CONTROLLED_DIR/evaluate_controlled.py" \
    --input "$INPUT_DIR/controlled_inputs.jsonl" --mapping "$INPUT_DIR/controlled_mapping.jsonl" \
    --responses "$OUT/raw_responses.jsonl" --checker-root "$CONTROLLED_DIR/vendor" \
    --output-dir "$OUT/analysis"
done
"$PYTHON_BIN" "$CONTROLLED_DIR/check_paired_stability.py" compare \
  --input "$INPUT_DIR/controlled_inputs.jsonl" --first "$OUTPUT_ROOT/replicate-1" \
  --second "$OUTPUT_ROOT/replicate-2" --output "$OUTPUT_ROOT/stability.json"
