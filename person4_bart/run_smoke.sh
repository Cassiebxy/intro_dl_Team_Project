#!/usr/bin/env bash
set -euo pipefail
BART_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BART_PROJECT_ROOT"
BART_PYTHON="$BART_PROJECT_ROOT/person4_bart/.venv/bin/python"
if [[ ! -x "$BART_PYTHON" ]]; then
  echo 'Create person4_bart/.venv and install person4_bart/requirements.txt first.' >&2
  exit 1
fi
if [[ ! -f person4_bart/data/synthetic_v1/dataset_manifest.json ]]; then
  "$BART_PYTHON" -m person4_bart prepare
fi
if [[ ! -f person4_bart/model_source.json ]]; then
  "$BART_PYTHON" -m person4_bart fetch-model
fi
"$BART_PYTHON" -m person4_bart check-env
BART_RUN_PATH="person4_bart/runs/synthetic-smoke-$(date -u +%Y%m%dT%H%M%SZ)"
"$BART_PYTHON" -m person4_bart train --device mps --epochs 12 --patience 4 --output "$BART_RUN_PATH"
echo "Local results: $BART_PROJECT_ROOT/$BART_RUN_PATH"
