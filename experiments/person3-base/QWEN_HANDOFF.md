# Person 3 Qwen handoff

Status: text evaluation verified; six request packages exported and validated. No Qwen inference or downstream scoring has been performed for these packages.

## Recreate packages (CPU only)

From the repository root on branch `person3-flan-t5-base`:

```bash
bash experiments/person3-base/prepare_handoff.sh /path/to/new-person3-qwen-handoff
```

All required rewrites are versioned under `experiments/person3-base/evidence/delta-24205857/`. Model checkpoints are not needed for export.

| Dataset | Methods | Requests per method | Cases |
| --- | --- | ---: | ---: |
| Person 2 test | multi, single, rules | 1,680 | 42 |
| Shared generalization v1 | multi, single, rules | 2,016 | 42 |

Each package contains clean, manipulated, normalized, and clean-through-normalizer conditions, both orders, and both name mappings. Total: 11,088 records before deduplication. Coordinate the common evaluation matrix and budget before full execution. Controls repeat across methods: reuse only identical payloads with the same seed, model, backend, and decoding, preserving a mapping to every original request ID.

Only `controlled_inputs.jsonl` contains model inputs. Do not send `controlled_mapping.jsonl` scoring metadata as prompt text. Manifests record source hashes and `prepared_not_run` status. Validation does not run GPU inference.

## Person 1 execution

Use the team's exact frozen Qwen checkpoint, backend, decoding settings, and scorer. Do not mix quantized/local runs with AutoDL baseline results. The runner defaults to 16 requests; full execution requires an explicit count and `--allow-full-run`.

Example for one package on an allocated GPU, after matching all settings to the team's baseline:

```bash
python experiments/person3-base/run_qwen_handoff.py \
  --input /path/to/new-person3-qwen-handoff/test/multi/controlled_inputs.jsonl \
  --mapping /path/to/new-person3-qwen-handoff/test/multi/controlled_mapping.jsonl \
  --model-dir /path/to/team-frozen-qwen \
  --output-dir /path/to/new-qwen-results/test-multi \
  --limit 1680 --allow-full-run
```

Use 2016 for generalization. Confirm remaining runner defaults against the team's frozen settings. Return raw responses, attempts, run manifests, scores, and exact model/runtime/decoding details. Report failures and coverage; retain method/dataset/cue/order/name-mapping breakdowns and strict response correctness. Generalization flags question overlap for `live_simple_115-71-0`; report a sensitivity analysis excluding that case.

No downstream mitigation claim is supported yet. Compare matched clean/manipulated/normalized outcomes and paired transitions after scoring.

## Verified findings and storage

Multi-cue scores 89/95 on test and 71/114 on generalization; single-cue scores 86/95 and 58/114. Existing BART outputs rescore to 95/95 and 72/114. Fine-tuned small scores 104/115 on dev; matching small test/generalization outputs remain unavailable in the inspected snapshot.

Delta checkpoints: `/projects/bjfu/mlin14/person3-runs/multi-v1/checkpoint` (epoch 2) and `/projects/bjfu/mlin14/person3-runs/single-v1/checkpoint` (epoch 1). Large weights remain on Delta. Configurations contain pretrained file hashes; retain original revision.txt and runtime logs with the final archive. See README and evidence for error analysis and single-seed limitations.

The original runner hardcodes 7,224 requests. `run_qwen_handoff.py` changes only its full-package count to the supplied validated input length; it retains the original model loading, generation, resume, and parsing implementation. The explicit full-run guard remains required. GPU inference through this wrapper has not yet been tested.
