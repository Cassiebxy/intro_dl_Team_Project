#!/usr/bin/env bash
set -euo pipefail
OUT=${1:?Provide a new output directory}
PYTHON=${PYTHON:-python}
[[ ! -e "$OUT" ]] || { echo 'Output already exists' >&2; exit 2; }
mkdir -p "$OUT"
for dataset in test generalization; do
  DATA=experiments/person2-small/data
  LIMIT=1680
  if [[ "$dataset" == generalization ]]; then
    DATA=person4_bart/data/generalization_v1
    LIMIT=2016
  fi
  for method in multi single rules; do
    DEST="$OUT/$dataset/$method"
    "$PYTHON" experiments/person3-base/prepare_qwen.py \
      --pairs "$DATA/pairs_test.jsonl" \
      --rewrites "experiments/person3-base/evidence/delta-24205857/$dataset/$method/rewrites.jsonl" \
      --method "base-$method" --output "$DEST"
    "$PYTHON" experiments/person3-base/run_qwen_handoff.py \
      --input "$DEST/controlled_inputs.jsonl" --mapping "$DEST/controlled_mapping.jsonl" \
      --limit "$LIMIT" --allow-full-run --validate-only > "$DEST/validation.json"
  done
done
cp experiments/person3-base/QWEN_HANDOFF.md "$OUT/README.md"
echo "Prepared and validated: $OUT; Qwen inference not run."
